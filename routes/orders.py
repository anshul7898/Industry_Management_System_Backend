import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
import traceback
import time

from schemas.orders import Order, CreateOrder, UpdateOrder
from utils.dynamodb_utils import (
    convert_items_to_python,
    convert_item_to_python,
    convert_product_for_storage,
)
from db.dynamodb import orders_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


def generate_order_id(agent_id: int) -> int:
    """Generate a unique numeric OrderId"""
    timestamp = int(time.time())
    order_id = int(str(agent_id) + str(timestamp)[-6:])
    logger.info(f"Generated OrderId: {order_id} from AgentId: {agent_id}")
    return order_id


def build_products_for_storage(products) -> list:
    """
    Convert a list of Product Pydantic models to DynamoDB-safe dicts.
    ✅ None values are excluded so DynamoDB never receives a null attribute.
    ✅ PlateRate    is stored as Decimal when provided.
    ✅ PlateType    ("Old"/"New") is stored as a plain string — never coerced to Decimal.
    ✅ DesignType   ("Old"/"New") is stored as a plain string — never coerced to Decimal.
    ✅ DesignStyle  ("Same Front/Back"/"Different Front/Back") stored as plain string.
    ✅ Design (old bool) and PlateAvailable (old bool) are fully removed — legacy guards only.
    """
    ddb_products = []
    for idx, product in enumerate(products):
        logger.info(f"Processing product {idx + 1}")

        # Step 1 — dump to plain dict
        raw = product.model_dump()

        # Step 2 — drop legacy boolean fields that no longer exist in the schema
        raw.pop("Design", None)
        raw.pop("PlateAvailable", None)

        # Step 3 — capture string-enum fields BEFORE the None-filter so they
        #           are never accidentally dropped
        plate_type   = raw.get("PlateType")    # "Old", "New", or None
        design_type  = raw.get("DesignType")   # "Old", "New", or None
        design_style = raw.get("DesignStyle")  # "Same Front/Back", "Different Front/Back", or None

        # Step 4 — filter out None values (DynamoDB does not accept nulls)
        product_dict = {k: v for k, v in raw.items() if v is not None}

        # Step 5 — convert known numeric fields to Decimal for DynamoDB
        #           String fields (PlateType, DesignType, DesignStyle, etc.)
        #           are NEVER touched here
        for numeric_field in (
            "Rate", "ProductAmount", "PlateRate",
            "SheetGSM", "BorderGSM", "HandleGSM", "Quantity",
        ):
            if numeric_field in product_dict:
                try:
                    product_dict[numeric_field] = Decimal(str(product_dict[numeric_field]))
                except Exception:
                    pass

        # Step 6a — explicitly set/clear PlateType
        if plate_type in ("Old", "New"):
            product_dict["PlateType"] = plate_type
        else:
            product_dict.pop("PlateType", None)

        # Step 6b — explicitly set/clear DesignType
        if design_type in ("Old", "New"):
            product_dict["DesignType"] = design_type
        else:
            product_dict.pop("DesignType", None)

        # Step 6c — explicitly set/clear DesignStyle
        if design_style in ("Same Front/Back", "Different Front/Back"):
            product_dict["DesignStyle"] = design_style
        else:
            product_dict.pop("DesignStyle", None)

        logger.info(f"Product {idx + 1} final dict       : {product_dict}")
        logger.info(f"Product {idx + 1} PlateType        : {product_dict.get('PlateType')}")
        logger.info(f"Product {idx + 1} DesignType       : {product_dict.get('DesignType')}")
        logger.info(f"Product {idx + 1} DesignStyle      : {product_dict.get('DesignStyle')}")
        logger.info(f"Product {idx + 1} PlateRate        : {product_dict.get('PlateRate')}")
        logger.info(f"Product {idx + 1} ProductCategory  : {product_dict.get('ProductCategory')}")

        # Step 7 — run through DynamoDB utility (handles any remaining type conversions)
        converted_product = convert_product_for_storage(product_dict)

        # Step 8 — safety net: restore PlateType if convert_product_for_storage dropped it
        if plate_type in ("Old", "New"):
            if converted_product.get("PlateType") != plate_type:
                logger.warning(
                    f"⚠️ PlateType corrupted by convert_product_for_storage "
                    f"— restoring to '{plate_type}'"
                )
                converted_product["PlateType"] = plate_type

        # Step 9 — safety net: restore DesignType if convert_product_for_storage dropped it
        if design_type in ("Old", "New"):
            if converted_product.get("DesignType") != design_type:
                logger.warning(
                    f"⚠️ DesignType corrupted by convert_product_for_storage "
                    f"— restoring to '{design_type}'"
                )
                converted_product["DesignType"] = design_type

        # Step 10 — safety net: restore DesignStyle if convert_product_for_storage dropped it
        if design_style in ("Same Front/Back", "Different Front/Back"):
            if converted_product.get("DesignStyle") != design_style:
                logger.warning(
                    f"⚠️ DesignStyle corrupted by convert_product_for_storage "
                    f"— restoring to '{design_style}'"
                )
                converted_product["DesignStyle"] = design_style

        if "ProductCategory" not in converted_product:
            logger.warning(f"⚠️ ProductCategory missing in product {idx + 1} after conversion!")

        logger.info(f"Product {idx + 1} after conversion: {converted_product}")
        ddb_products.append(converted_product)

    logger.info(f"✓ Converted {len(ddb_products)} product(s) for DynamoDB storage")
    return ddb_products


def build_order_item(order_id: int, payload, ddb_products: list) -> dict:
    """
    Build the DynamoDB item dict for an order.
    ✅ Optional top-level fields that are None are excluded.
    ✅ Dispatch Information fields included when provided.
    """
    item = {
        "OrderId": order_id,
        "AgentId": payload.AgentId,
        "Party_Name": payload.Party_Name,
        "AliasOrCompanyName": payload.AliasOrCompanyName,
        "Address": payload.Address,
        "City": payload.City,
        "State": payload.State,
        "Pincode": payload.Pincode,
        "Contact_Person1": payload.Contact_Person1,
        "TotalAmount": Decimal(str(payload.TotalAmount)),
        "Products": ddb_products,
    }

    # Optional contact fields
    if payload.Contact_Person2 is not None:
        item["Contact_Person2"] = payload.Contact_Person2
    if payload.Mobile1 is not None:
        item["Mobile1"] = payload.Mobile1
    if payload.Mobile2 is not None:
        item["Mobile2"] = payload.Mobile2
    if payload.Email is not None:
        item["Email"] = payload.Email

    # ── Dispatch Information (optional) ──────────────────────────
    if payload.BookingName is not None:
        item["BookingName"] = payload.BookingName
    if payload.TransportName is not None:
        item["TransportName"] = payload.TransportName
    if payload.DispatchContactNumber is not None:
        item["DispatchContactNumber"] = payload.DispatchContactNumber
    if payload.Destination is not None:
        item["Destination"] = payload.Destination

    return item


@router.get("/orders", response_model=List[Order])
def list_orders():
    """Retrieve all orders from DynamoDB."""
    try:
        logger.info("📋 Fetching all orders from DynamoDB")
        logger.info(f"Using table: {orders_table.table_name}")

        response = orders_table.scan()
        items = response.get("Items", [])

        logger.info(f"Scanned {len(items)} items from DynamoDB")

        converted_items = convert_items_to_python(items)
        logger.info(f"✓ Successfully retrieved {len(converted_items)} orders")
        return converted_items

    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error listing orders: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Retrieve a specific order by Order ID."""
    try:
        logger.info(f"🔍 Fetching order {order_id}")
        response = orders_table.get_item(Key={"OrderId": order_id})
        order = response.get("Item")

        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        converted_order = convert_item_to_python(order)
        logger.info(f"✓ Retrieved order {order_id}")
        return converted_order

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError fetching order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching order {order_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", response_model=Order)
def create_order(payload: CreateOrder):
    """Create a new order in DynamoDB with multiple products."""
    try:
        logger.info("➕ Creating new order")
        logger.info(f"Payload received with {len(payload.Products)} product(s)")

        if payload.TotalAmount is None or payload.TotalAmount < 0:
            raise ValueError("TotalAmount must be a valid non-negative number")

        order_id = generate_order_id(payload.AgentId)
        logger.info(f"Generated OrderId: {order_id}")

        ddb_products = build_products_for_storage(payload.Products)
        item = build_order_item(order_id, payload, ddb_products)

        logger.info(f"📝 Putting item to DynamoDB: {order_id}")
        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} created successfully with {len(ddb_products)} product(s)")

        return convert_item_to_python(item)

    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error creating order: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, payload: UpdateOrder):
    """Update an existing order in DynamoDB with multiple products."""
    try:
        logger.info(f"✏️ Updating order {order_id}")
        logger.info(f"Payload received with {len(payload.Products)} product(s)")

        if payload.TotalAmount is None or payload.TotalAmount < 0:
            raise ValueError("TotalAmount must be a valid non-negative number")

        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        ddb_products = build_products_for_storage(payload.Products)
        item = build_order_item(order_id, payload, ddb_products)

        logger.info(f"📝 Updating item in DynamoDB: {order_id}")
        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} updated successfully with {len(ddb_products)} product(s)")

        return convert_item_to_python(item)

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError updating order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error updating order {order_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
def delete_order(order_id: int):
    """Delete an order from DynamoDB."""
    try:
        logger.info(f"🗑️ Deleting order {order_id}")

        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        orders_table.delete_item(Key={"OrderId": order_id})
        logger.info(f"✓ Order {order_id} deleted successfully")

        return {
            "success": True,
            "orderId": order_id,
            "message": f"Order {order_id} deleted successfully"
        }

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError deleting order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error deleting order {order_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))