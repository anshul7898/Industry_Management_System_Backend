import logging
import time
from decimal import Decimal
from typing import List

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

# ── DynamoDB table ────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
roll_size_table = dynamodb.Table("Roll_Size_Table")


# ── Pydantic models ───────────────────────────────────────────────
class RollSizeCreate(BaseModel):
    size: str


class RollSizeResponse(BaseModel):
    sizes: List[str]


# ── Helper: fetch all sizes sorted ───────────────────────────────
def _fetch_all_sizes() -> List[str]:
    response = roll_size_table.scan()
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = roll_size_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    sizes = [str(item["Size"]) for item in items if "Size" in item]
    sizes.sort()
    return sizes


# ── GET /api/roll-sizes ───────────────────────────────────────────
@router.get("/roll-sizes", response_model=RollSizeResponse)
def list_roll_sizes():
    """Return all roll sizes from Roll_Size_Table, sorted."""
    try:
        sizes = _fetch_all_sizes()
        logger.info(f"✓ Retrieved {len(sizes)} roll size(s)")
        return {"sizes": sizes}
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError listing roll sizes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB Error: {e.response['Error']['Message']}",
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error listing roll sizes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /api/roll-sizes ──────────────────────────────────────────
@router.post("/roll-sizes", response_model=RollSizeResponse, status_code=201)
def add_roll_size(payload: RollSizeCreate):
    """
    Add a new roll size to Roll_Size_Table.
    Returns 409 if the size already exists.
    """
    size_val = payload.size.strip()
    if not size_val:
        raise HTTPException(status_code=422, detail="Size value cannot be empty.")

    try:
        existing_sizes = _fetch_all_sizes()
        if size_val in existing_sizes:
            raise HTTPException(status_code=409, detail=f"Roll size '{size_val}' already exists.")

        new_id = int(time.time() * 1000) % 10_000_000

        roll_size_table.put_item(
            Item={
                "ID": Decimal(str(new_id)),
                "Size": size_val,
            }
        )
        logger.info(f"✓ Roll size '{size_val}' added with ID {new_id}")

        updated_sizes = _fetch_all_sizes()
        return {"sizes": updated_sizes}

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError adding roll size: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB Error: {e.response['Error']['Message']}",
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error adding roll size: {e}")
        raise HTTPException(status_code=500, detail=str(e))