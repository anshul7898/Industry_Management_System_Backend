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
    ✅ None values are excluded so DynamoDB never receives a null attribute
       (e.g. BorderGSM / BorderColor are omitted entirely for Machine-type products).
    """
    ddb_products = []
    for idx, product in enumerate(products):
        logger.info(f"Processing product {idx + 1}")

        # Convert Pydantic model to dict, excluding None values
        product_dict = {k: v for k, v in product.model_dump().items() if v is not None}
        logger.info(f"Product {idx + 1} dict (None-filtered): {product_dict}")
        logger.info(f"Product {idx + 1} ProductCategory value: {product_dict.get('ProductCategory')}")

        converted_product = convert_product_for_storage(product_dict)
        logger.info(f"Product {idx + 1} after conversion: {converted_product}")

        if "ProductCategory" not in converted_product:
            logger.warning(f"⚠️ ProductCategory missing in product {idx + 1} after conversion!")

        ddb_products.append(converted_product)

    logger.info(f"✓ Converted {len(ddb_products)} product(s) for DynamoDB storage")
    return ddb_products


def build_order_item(order_id: int, payload, ddb_products: list) -> dict:
    """
    Build the DynamoDB item dict for an order.
    ✅ Optional top-level fields that are None are excluded to avoid
       DynamoDB null-attribute errors.
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

    # ✅ Only include optional fields when they have a value
    if payload.Contact_Person2 is not None:
        item["Contact_Person2"] = payload.Contact_Person2
    if payload.Mobile1 is not None:
        item["Mobile1"] = payload.Mobile1
    if payload.Mobile2 is not None:
        item["Mobile2"] = payload.Mobile2
    if payload.Email is not None:
        item["Email"] = payload.Email

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
        logger.error(f"Error Code: {e.response['Error']['Code']}")
        logger.error(f"Error Message: {e.response['Error']['Message']}")
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
        logger.info(f"Using table: {orders_table.table_name}")

        response = orders_table.get_item(Key={"OrderId": order_id})
        order = response.get("Item")

        if not order:
            logger.warning(f"⚠️ Order {order_id} not found")
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        converted_order = convert_item_to_python(order)
        logger.info(f"✓ Retrieved order {order_id}")
        return converted_order

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError fetching order {order_id}: {str(e)}")
        logger.error(f"Error Code: {e.response['Error']['Code']}")
        logger.error(f"Error Message: {e.response['Error']['Message']}")
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
        logger.info(f"Using table: {orders_table.table_name}")

        # ✅ Use shared helper — None fields (e.g. BorderGSM for Machine) are excluded
        ddb_products = build_products_for_storage(payload.Products)

        item = build_order_item(order_id, payload, ddb_products)

        logger.info(f"📝 Putting item to DynamoDB: {order_id}")
        logger.info(f"Item keys: {list(item.keys())}")
        logger.info(f"Products in item: {len(item['Products'])}")
        logger.info(f"First product keys: {list(item['Products'][0].keys()) if item['Products'] else 'No products'}")
        logger.info(f"TotalAmount: {item['TotalAmount']}")

        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} created successfully with {len(ddb_products)} product(s)")

        converted_item = convert_item_to_python(item)
        return converted_item

    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError creating order: {str(e)}")
        logger.error(f"Error Code: {e.response['Error']['Code']}")
        logger.error(f"Error Message: {e.response['Error']['Message']}")
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
        logger.info(f"Using table: {orders_table.table_name}")

        if payload.TotalAmount is None or payload.TotalAmount < 0:
            raise ValueError("TotalAmount must be a valid non-negative number")

        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            logger.warning(f"⚠️ Order {order_id} not found for update")
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        # ✅ Use shared helper — None fields (e.g. BorderGSM for Machine) are excluded
        ddb_products = build_products_for_storage(payload.Products)

        item = build_order_item(order_id, payload, ddb_products)

        logger.info(f"📝 Updating item in DynamoDB: {order_id}")
        logger.info(f"Products in item: {len(item['Products'])}")
        logger.info(f"First product keys: {list(item['Products'][0].keys()) if item['Products'] else 'No products'}")
        logger.info(f"TotalAmount: {item['TotalAmount']}")

        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} updated successfully with {len(ddb_products)} product(s)")

        converted_item = convert_item_to_python(item)
        return converted_item

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError updating order {order_id}: {str(e)}")
        logger.error(f"Error Code: {e.response['Error']['Code']}")
        logger.error(f"Error Message: {e.response['Error']['Message']}")
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
        logger.info(f"Using table: {orders_table.table_name}")

        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            logger.warning(f"⚠️ Order {order_id} not found for deletion")
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
        logger.error(f"Error Code: {e.response['Error']['Code']}")
        logger.error(f"Error Message: {e.response['Error']['Message']}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error deleting order {order_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))