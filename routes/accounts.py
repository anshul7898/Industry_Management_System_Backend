import logging
from uuid import uuid4
from typing import List
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError

from schemas.accounts import AccountTxn, CreateAccountTxn, UpdateAccountTxn
from utils.helpers import aws_error_detail, ddb_decimal, normalize_ddb_item
from db.dynamodb import accounts_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get("/accounts", response_model=List[AccountTxn])
def list_accounts():
    try:
        items = accounts_table.scan().get("Items", [])
        return [normalize_ddb_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@router.post("/accounts", response_model=AccountTxn)
def create_account(payload: CreateAccountTxn):
    try:
        txn_id = payload.txnId or f"TXN-{uuid4().hex[:8].upper()}"

        item = {
            "txnId": txn_id,
            "type": payload.type,
            "description": payload.description,
            "partyName": payload.partyName,
            "date": payload.date,
            "amount": ddb_decimal(payload.amount),
        }

        accounts_table.put_item(Item=item)
        return normalize_ddb_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")


@router.put("/accounts/{txn_id}", response_model=AccountTxn)
def update_account(txn_id: str, payload: UpdateAccountTxn):
    try:
        existing = accounts_table.get_item(Key={"txnId": txn_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        item = {
            "txnId": txn_id,
            **payload.dict(),
            "amount": ddb_decimal(payload.amount),
        }

        accounts_table.put_item(Item=item)
        return normalize_ddb_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating account: {str(e)}")


@router.delete("/accounts/{txn_id}")
def delete_account(txn_id: str):
    try:
        existing = accounts_table.get_item(Key={"txnId": txn_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        accounts_table.delete_item(Key={"txnId": txn_id})
        return {"deleted": True}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise