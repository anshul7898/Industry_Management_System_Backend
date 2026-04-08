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
    FixAmount, QuantityType, JobWorkRate, and GST are stored if present.

    ProductAmount stored here is the final value already computed by the
    frontend:
      - Pieces: (Qty × Rate) + GST_amount + PlateRate + FixAmount
      - KG:     (Qty × Rate) + GST_amount + JobWorkRate + PlateRate + FixAmount
    where GST_amount = (Qty × Rate) × (GST / 100)
    """
    ddb_products = []
    for idx, product in enumerate(products):
        logger.info(f"Processing product {idx + 1}")

        raw = product.model_dump()

        raw.pop("Design", None)
        raw.pop("PlateAvailable", None)

        plate_type    = raw.get("PlateType")
        design_type   = raw.get("DesignType")
        design_style  = raw.get("DesignStyle")
        roll_size     = raw.get("RollSize")
        fix_amount    = raw.get("FixAmount")
        quantity_type = raw.get("QuantityType")
        job_work_rate = raw.get("JobWorkRate")
        gst           = raw.get("GST")          # ── NEW ──

        product_dict = {k: v for k, v in raw.items() if v is not None}

        for numeric_field in (
            "Rate", "ProductAmount", "PlateRate",
            "SheetGSM", "BorderGSM", "HandleGSM", "Quantity",
        ):
            if numeric_field in product_dict:
                try:
                    product_dict[numeric_field] = Decimal(str(product_dict[numeric_field]))
                except Exception:
                    pass

        # Convert FixAmount to Decimal for DynamoDB storage
        if fix_amount is not None:
            try:
                product_dict["FixAmount"] = Decimal(str(fix_amount))
            except Exception:
                product_dict.pop("FixAmount", None)
        else:
            product_dict.pop("FixAmount", None)

        # Convert JobWorkRate to Decimal for DynamoDB storage
        if job_work_rate is not None:
            try:
                product_dict["JobWorkRate"] = Decimal(str(job_work_rate))
            except Exception:
                product_dict.pop("JobWorkRate", None)
        else:
            product_dict.pop("JobWorkRate", None)

        # ── NEW: Convert GST to Decimal for DynamoDB storage ─────────────────
        # GST is always stored even when 0, so the value is explicit on read-back.
        if gst is not None:
            try:
                product_dict["GST"] = Decimal(str(gst))
            except Exception:
                product_dict["GST"] = Decimal("0")
        else:
            product_dict["GST"] = Decimal("0")

        # Persist QuantityType as a plain string
        if quantity_type and str(quantity_type).strip() in ("KG", "Pieces"):
            product_dict["QuantityType"] = str(quantity_type).strip()
        else:
            product_dict.pop("QuantityType", None)

        if plate_type in ("Old", "New"):
            product_dict["PlateType"] = plate_type
        else:
            product_dict.pop("PlateType", None)

        if design_type in ("Old", "New"):
            product_dict["DesignType"] = design_type
        else:
            product_dict.pop("DesignType", None)

        if design_style in ("Same Front/Back", "Different Front/Back"):
            product_dict["DesignStyle"] = design_style
        else:
            product_dict.pop("DesignStyle", None)

        if roll_size and str(roll_size).strip():
            product_dict["RollSize"] = str(roll_size).strip()
        else:
            product_dict.pop("RollSize", None)

        logger.info(f"Product {idx + 1} final dict       : {product_dict}")
        logger.info(f"Product {idx + 1} PlateType        : {product_dict.get('PlateType')}")
        logger.info(f"Product {idx + 1} DesignType       : {product_dict.get('DesignType')}")
        logger.info(f"Product {idx + 1} DesignStyle      : {product_dict.get('DesignStyle')}")
        logger.info(f"Product {idx + 1} RollSize         : {product_dict.get('RollSize')}")
        logger.info(f"Product {idx + 1} PlateRate        : {product_dict.get('PlateRate')}")
        logger.info(f"Product {idx + 1} ProductCategory  : {product_dict.get('ProductCategory')}")
        logger.info(f"Product {idx + 1} FixAmount        : {product_dict.get('FixAmount')}")
        logger.info(f"Product {idx + 1} QuantityType     : {product_dict.get('QuantityType')}")
        logger.info(f"Product {idx + 1} JobWorkRate      : {product_dict.get('JobWorkRate')}")
        logger.info(f"Product {idx + 1} GST              : {product_dict.get('GST')}")  # ── NEW ──

        converted_product = convert_product_for_storage(product_dict)

        if plate_type in ("Old", "New"):
            if converted_product.get("PlateType") != plate_type:
                logger.warning(f"⚠️ PlateType corrupted — restoring to '{plate_type}'")
                converted_product["PlateType"] = plate_type

        if design_type in ("Old", "New"):
            if converted_product.get("DesignType") != design_type:
                logger.warning(f"⚠️ DesignType corrupted — restoring to '{design_type}'")
                converted_product["DesignType"] = design_type

        if design_style in ("Same Front/Back", "Different Front/Back"):
            if converted_product.get("DesignStyle") != design_style:
                logger.warning(f"⚠️ DesignStyle corrupted — restoring to '{design_style}'")
                converted_product["DesignStyle"] = design_style

        if roll_size and str(roll_size).strip():
            if converted_product.get("RollSize") != str(roll_size).strip():
                logger.warning(f"⚠️ RollSize corrupted — restoring to '{roll_size}'")
                converted_product["RollSize"] = str(roll_size).strip()

        # Restore FixAmount if corrupted by convert_product_for_storage
        if fix_amount is not None:
            expected = Decimal(str(fix_amount))
            if converted_product.get("FixAmount") != expected:
                logger.warning(f"⚠️ FixAmount corrupted — restoring to '{fix_amount}'")
                converted_product["FixAmount"] = expected

        # Restore JobWorkRate if corrupted by convert_product_for_storage
        if job_work_rate is not None:
            expected_jwr = Decimal(str(job_work_rate))
            if converted_product.get("JobWorkRate") != expected_jwr:
                logger.warning(f"⚠️ JobWorkRate corrupted — restoring to '{job_work_rate}'")
                converted_product["JobWorkRate"] = expected_jwr

        # ── NEW: Restore GST if corrupted by convert_product_for_storage ─────
        expected_gst = Decimal(str(gst)) if gst is not None else Decimal("0")
        if converted_product.get("GST") != expected_gst:
            logger.warning(f"⚠️ GST corrupted — restoring to '{expected_gst}'")
            converted_product["GST"] = expected_gst

        # Restore QuantityType if corrupted by convert_product_for_storage
        if quantity_type and str(quantity_type).strip() in ("KG", "Pieces"):
            expected_qt = str(quantity_type).strip()
            if converted_product.get("QuantityType") != expected_qt:
                logger.warning(f"⚠️ QuantityType corrupted — restoring to '{expected_qt}'")
                converted_product["QuantityType"] = expected_qt

        if "ProductCategory" not in converted_product:
            logger.warning(f"⚠️ ProductCategory missing in product {idx + 1} after conversion!")

        logger.info(f"Product {idx + 1} after conversion: {converted_product}")
        ddb_products.append(converted_product)

    logger.info(f"✓ Converted {len(ddb_products)} product(s) for DynamoDB storage")
    return ddb_products


def build_order_item(order_id: int, payload, ddb_products: list) -> dict:
    """
    Build the DynamoDB item dict for an order.
    TotalAmount = sum(ProductAmounts) + Carting.
    ProductAmount for each product already contains the GST component as
    computed by the frontend. We persist TotalAmount as-is.
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

    if payload.Contact_Person2 is not None:
        item["Contact_Person2"] = payload.Contact_Person2
    if payload.Mobile1 is not None:
        item["Mobile1"] = payload.Mobile1
    if payload.Mobile2 is not None:
        item["Mobile2"] = payload.Mobile2
    if payload.Email is not None:
        item["Email"] = payload.Email
    if payload.BookingName is not None:
        item["BookingName"] = payload.BookingName
    if payload.TransportName is not None:
        item["TransportName"] = payload.TransportName
    if payload.DispatchContactNumber is not None:
        item["DispatchContactNumber"] = payload.DispatchContactNumber
    if payload.Destination is not None:
        item["Destination"] = payload.Destination

    # Persist Carting if provided
    if payload.Carting is not None:
        item["Carting"] = Decimal(str(payload.Carting))

    return item


@router.get("/orders", response_model=List[Order])
def list_orders():
    """Retrieve all orders from DynamoDB."""
    try:
        logger.info("📋 Fetching all orders from DynamoDB")
        response = orders_table.scan()
        items = response.get("Items", [])
        converted_items = convert_items_to_python(items)
        logger.info(f"✓ Successfully retrieved {len(converted_items)} orders")
        return converted_items
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error listing orders: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Retrieve a specific order by Order ID."""
    try:
        response = orders_table.get_item(Key={"OrderId": order_id})
        order = response.get("Item")
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        return convert_item_to_python(order)
    except HTTPException:
        raise
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", response_model=Order)
def create_order(payload: CreateOrder):
    """Create a new order in DynamoDB with multiple products."""
    try:
        logger.info(f"➕ Creating new order with {len(payload.Products)} product(s)")
        if payload.TotalAmount is None or payload.TotalAmount < 0:
            raise ValueError("TotalAmount must be a valid non-negative number")
        order_id = generate_order_id(payload.AgentId)
        ddb_products = build_products_for_storage(payload.Products)
        item = build_order_item(order_id, payload, ddb_products)
        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} created with {len(ddb_products)} product(s)")
        return convert_item_to_python(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, payload: UpdateOrder):
    """Update an existing order in DynamoDB."""
    try:
        logger.info(f"✏️ Updating order {order_id} with {len(payload.Products)} product(s)")
        if payload.TotalAmount is None or payload.TotalAmount < 0:
            raise ValueError("TotalAmount must be a valid non-negative number")
        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        ddb_products = build_products_for_storage(payload.Products)
        item = build_order_item(order_id, payload, ddb_products)
        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} updated with {len(ddb_products)} product(s)")
        return convert_item_to_python(item)
    except HTTPException:
        raise
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
def delete_order(order_id: int):
    """Delete an order from DynamoDB."""
    try:
        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        orders_table.delete_item(Key={"OrderId": order_id})
        logger.info(f"✓ Order {order_id} deleted")
        return {"success": True, "orderId": order_id, "message": f"Order {order_id} deleted successfully"}
    except HTTPException:
        raise
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))