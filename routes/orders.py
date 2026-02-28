import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
import traceback
import time

from schemas.orders import Order, CreateOrder, UpdateOrder
from utils.helpers import aws_error_detail
from utils.dynamodb_utils import convert_items_to_python, convert_item_to_python
from db.dynamodb import orders_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


def generate_order_id(agent_id: int) -> int:
    """Generate a unique numeric OrderId"""
    timestamp = int(time.time())
    order_id = int(str(agent_id) + str(timestamp)[-6:])
    logger.info(f"Generated OrderId: {order_id} from AgentId: {agent_id}")
    return order_id


def ddb_decimal(value) -> Decimal:
    """Convert value to Decimal for DynamoDB storage"""
    if value is None:
        return None
    return Decimal(str(value))


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
    """Create a new order in DynamoDB."""
    try:
        logger.info("➕ Creating new order")
        logger.info(f"Payload: {payload.dict()}")

        # Generate unique numeric OrderId
        order_id = generate_order_id(payload.AgentId)
        logger.info(f"Generated OrderId: {order_id}")
        logger.info(f"Using table: {orders_table.table_name}")

        # Build item with all required and optional fields
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
            "Contact_Person2": payload.Contact_Person2,  # Always include, even if None
            "Mobile1": payload.Mobile1,  # Always include, even if None
            "Mobile2": payload.Mobile2,  # Always include, even if None
            "Email": payload.Email,  # Always include, even if None
            "ProductType": payload.ProductType,
            "ProductId": payload.ProductId,
            "ProductSize": payload.ProductSize,
            "BagMaterial": payload.BagMaterial,
            "Quantity": payload.Quantity,
            "SheetGSM": payload.SheetGSM,
            "SheetColor": payload.SheetColor,
            "BorderGSM": payload.BorderGSM,
            "BorderColor": payload.BorderColor,
            "HandleType": payload.HandleType,
            "HandleColor": payload.HandleColor,
            "HandleGSM": payload.HandleGSM,
            "PrintingType": payload.PrintingType,
            "PrintColor": payload.PrintColor,
            "Color": payload.Color,
            "Design": payload.Design,
            "Rate": ddb_decimal(payload.Rate),
            "TotalAmount": ddb_decimal(payload.TotalAmount),
            "PlateAvailable": payload.PlateAvailable,
        }

        # Add optional fields only if provided (but keep the ones above)
        if payload.PlateBlockNumber:
            item["PlateBlockNumber"] = payload.PlateBlockNumber

        logger.info(f"📝 Putting item to DynamoDB: {order_id}")
        logger.info(f"Item keys: {list(item.keys())}")

        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} created successfully")

        return convert_item_to_python(item)

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
    """Update an existing order in DynamoDB."""
    try:
        logger.info(f"✏️ Updating order {order_id}")
        logger.info(f"Using table: {orders_table.table_name}")

        # Check if order exists
        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing:
            logger.warning(f"⚠️ Order {order_id} not found for update")
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        # Build item with updated payload - always include all fields
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
            "Contact_Person2": payload.Contact_Person2,  # Always include, even if None
            "Mobile1": payload.Mobile1,  # Always include, even if None
            "Mobile2": payload.Mobile2,  # Always include, even if None
            "Email": payload.Email,  # Always include, even if None
            "ProductType": payload.ProductType,
            "ProductId": payload.ProductId,
            "ProductSize": payload.ProductSize,
            "BagMaterial": payload.BagMaterial,
            "Quantity": payload.Quantity,
            "SheetGSM": payload.SheetGSM,
            "SheetColor": payload.SheetColor,
            "BorderGSM": payload.BorderGSM,
            "BorderColor": payload.BorderColor,
            "HandleType": payload.HandleType,
            "HandleColor": payload.HandleColor,
            "HandleGSM": payload.HandleGSM,
            "PrintingType": payload.PrintingType,
            "PrintColor": payload.PrintColor,
            "Color": payload.Color,
            "Design": payload.Design,
            "Rate": ddb_decimal(payload.Rate),
            "TotalAmount": ddb_decimal(payload.TotalAmount),
            "PlateAvailable": payload.PlateAvailable,
        }

        # Add optional fields only if provided
        if payload.PlateBlockNumber:
            item["PlateBlockNumber"] = payload.PlateBlockNumber

        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} updated successfully")

        return convert_item_to_python(item)

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

        # Check if order exists
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