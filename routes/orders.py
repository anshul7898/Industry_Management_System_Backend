import logging
from uuid import uuid4
from typing import List
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError

from schemas.orders import Order, CreateOrder, UpdateOrder
from utils.helpers import aws_error_detail
from db.dynamodb import orders_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get("/orders", response_model=List[Order])
def list_orders():
    try:
        return orders_table.scan().get("Items", [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@router.post("/orders", response_model=Order)
def create_order(payload: CreateOrder):
    try:
        order_id = payload.orderId or f"ORD-{uuid4().hex[:8].upper()}"

        item = {
            "orderId": order_id,
            "description": payload.description,
            "customerName": payload.customerName,
            "orderDate": payload.orderDate,
            "deliveryDate": payload.deliveryDate,
        }

        orders_table.put_item(Item=item)
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@router.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: str, payload: UpdateOrder):
    try:
        existing = orders_table.get_item(Key={"orderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")

        item = {"orderId": order_id, **payload.dict()}
        orders_table.put_item(Item=item)
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")


@router.delete("/orders/{order_id}")
def delete_order(order_id: str):
    try:
        existing = orders_table.get_item(Key={"orderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")

        orders_table.delete_item(Key={"orderId": order_id})
        return {"deleted": True}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise