from dotenv import load_dotenv

load_dotenv()

import os
import logging
from decimal import Decimal
from uuid import uuid4
from typing import Optional, List

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db.dynamodb import orders_table

logger = logging.getLogger("uvicorn.error")

# -------------------- Accounts table handle --------------------
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ACCOUNTS_TABLE = os.getenv("ACCOUNTS_TABLE", "Accounts")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- helpers --------------------
def ddb_decimal(n: float) -> Decimal:
    # DynamoDB (boto3) requires Decimal, not float
    return Decimal(str(n))


def normalize_ddb_item(item: dict) -> dict:
    # Convert Decimal -> float for JSON responses
    out = dict(item)
    for k, v in list(out.items()):
        if isinstance(v, Decimal):
            out[k] = float(v)
    return out


def aws_error_detail(e: ClientError) -> str:
    code = e.response.get("Error", {}).get("Code", "ClientError")
    msg = e.response.get("Error", {}).get("Message", str(e))
    return f"{code}: {msg}"


# -------------------- Orders models --------------------
class Order(BaseModel):
    orderId: str
    # Make optional to avoid 500 if some DynamoDB items are incomplete
    description: Optional[str] = None
    customerName: Optional[str] = None
    orderDate: Optional[str] = None  # YYYY-MM-DD
    deliveryDate: Optional[str] = None  # YYYY-MM-DD


class CreateOrder(BaseModel):
    orderId: Optional[str] = None
    description: str
    customerName: str
    orderDate: str
    deliveryDate: str


class UpdateOrder(BaseModel):
    description: str
    customerName: str
    orderDate: str
    deliveryDate: str


# -------------------- Accounts models --------------------
class AccountTxn(BaseModel):
    txnId: str
    # Make optional to avoid 500 if older seeded rows are missing fields
    type: Optional[str] = None  # Incoming | Outgoing
    description: Optional[str] = None
    partyName: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    amount: Optional[float] = None  # returned to UI as number


class CreateAccountTxn(BaseModel):
    txnId: Optional[str] = None
    type: str
    description: str
    partyName: str
    date: str
    amount: float


class UpdateAccountTxn(BaseModel):
    type: str
    description: str
    partyName: str
    date: str
    amount: float


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "region": AWS_REGION,
        "ordersTable": orders_table.name,
        "accountsTable": accounts_table.name,
    }


# -------------------- Orders APIs --------------------
@app.get("/api/orders", response_model=List[Order])
def list_orders():
    try:
        resp = orders_table.scan()
        return resp.get("Items", [])
    except ClientError as e:
        logger.exception("Orders scan failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Orders endpoint crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    try:
        resp = orders_table.get_item(Key={"orderId": order_id})
        item = resp.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Order not found")
        return item
    except ClientError as e:
        logger.exception("Orders get_item failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Orders endpoint crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/orders", response_model=Order)
def create_order(payload: CreateOrder):
    order_id = payload.orderId or f"ORD-{uuid4().hex[:8].upper()}"

    item = {
        "orderId": order_id,
        "description": payload.description,
        "customerName": payload.customerName,
        "orderDate": payload.orderDate,
        "deliveryDate": payload.deliveryDate,
    }

    try:
        orders_table.put_item(Item=item)
        return item
    except ClientError as e:
        logger.exception("Orders put_item failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Orders create crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/orders/{order_id}", response_model=Order)
def update_order(order_id: str, payload: UpdateOrder):
    item = {
        "orderId": order_id,
        "description": payload.description,
        "customerName": payload.customerName,
        "orderDate": payload.orderDate,
        "deliveryDate": payload.deliveryDate,
    }

    try:
        existing = orders_table.get_item(Key={"orderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")

        orders_table.put_item(Item=item)
        return item
    except HTTPException:
        raise
    except ClientError as e:
        logger.exception("Orders update failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Orders update crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/orders/{order_id}")
def delete_order(order_id: str):
    try:
        existing = orders_table.get_item(Key={"orderId": order_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")

        orders_table.delete_item(Key={"orderId": order_id})
        return {"deleted": True, "orderId": order_id}
    except HTTPException:
        raise
    except ClientError as e:
        logger.exception("Orders delete failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Orders delete crashed")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Accounts APIs --------------------
@app.get("/api/accounts", response_model=List[AccountTxn])
def list_accounts():
    try:
        resp = accounts_table.scan()
        items = [normalize_ddb_item(x) for x in resp.get("Items", [])]
        return items
    except ClientError as e:
        logger.exception("Accounts scan failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Accounts endpoint crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{txn_id}", response_model=AccountTxn)
def get_account(txn_id: str):
    try:
        resp = accounts_table.get_item(Key={"txnId": txn_id})
        item = resp.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return normalize_ddb_item(item)
    except HTTPException:
        raise
    except ClientError as e:
        logger.exception("Accounts get_item failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Accounts get endpoint crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/accounts", response_model=AccountTxn)
def create_account(payload: CreateAccountTxn):
    txn_id = payload.txnId or f"TXN-{uuid4().hex[:8].upper()}"

    item = {
        "txnId": txn_id,
        "type": payload.type,  # Incoming | Outgoing
        "description": payload.description,
        "partyName": payload.partyName,
        "date": payload.date,
        "amount": ddb_decimal(payload.amount),
    }

    try:
        accounts_table.put_item(Item=item)
        return normalize_ddb_item(item)
    except ClientError as e:
        logger.exception("Accounts put_item failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Accounts create crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/accounts/{txn_id}", response_model=AccountTxn)
def update_account(txn_id: str, payload: UpdateAccountTxn):
    item = {
        "txnId": txn_id,
        "type": payload.type,
        "description": payload.description,
        "partyName": payload.partyName,
        "date": payload.date,
        "amount": ddb_decimal(payload.amount),
    }

    try:
        existing = accounts_table.get_item(Key={"txnId": txn_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        accounts_table.put_item(Item=item)
        return normalize_ddb_item(item)
    except HTTPException:
        raise
    except ClientError as e:
        logger.exception("Accounts update failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Accounts update crashed")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/accounts/{txn_id}")
def delete_account(txn_id: str):
    try:
        existing = accounts_table.get_item(Key={"txnId": txn_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        accounts_table.delete_item(Key={"txnId": txn_id})
        return {"deleted": True, "txnId": txn_id}
    except HTTPException:
        raise
    except ClientError as e:
        logger.exception("Accounts delete failed")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.exception("Accounts delete crashed")
        raise HTTPException(status_code=500, detail=str(e))