import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
import boto3
import re
from typing import Optional
from config.settings import AWS_REGION

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# ✅ UPDATED: Added 'box-bag' and 'leader-bag' entries
SIZE_TABLE_MAP = {
    "stitching":    "Stitching_Size_Table",
    "d-cut":        "D_Cut_Size_Table",
    "u-cut":        "U_Cut_Size_Table",
    "cake-bag-old": "Cake_Bag_Old_Size_Table",
    "cake-bag-new": "Cake_Bag_New_Size_Table",
    "side-gaget":   "Side_Gaget_Size_Table",
    "bottom-gaget": "Bottom_Gaget_Size_Table",
    "handle-bag":   "Handle_Bag_Size_Table",
    "box-bag":      "Box_Bag_Size_Table",
    "leader-bag":   "Leader_Bag_Size_Table",
}

CATEGORY_TO_SIZE_KEY = {
    "Stitching":              "stitching",
    "D-Cut Bag":              "d-cut",
    "U-Cut Bag":              "u-cut",
    "Cake Bag - Old Pattern": "cake-bag-old",
    "Cake Bag - New Pattern": "cake-bag-new",
    "Side Gaget Bag":         "side-gaget",
    "Bottom Gaget Bag":       "bottom-gaget",
    "Handle Bag":             "handle-bag",
    "Box Bag":                "box-bag",
    "Leader Bag":             "leader-bag",
}


class AddSizeRequest(BaseModel):
    size: str
    width: Optional[int] = None
    height: Optional[int] = None
    gusset: Optional[int] = None


def scan_all_items(table) -> list:
    """Full paginated scan of a DynamoDB table, returns all raw items."""
    response = table.scan()
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items


def get_next_id(items: list) -> int:
    """
    Derive the next numeric ID from existing items.
    ID is stored as a Number in DynamoDB; boto3 returns it as Decimal.
    """
    if not items:
        return 1
    max_id = max(
        int(item.get("ID", 0))
        for item in items
        if item.get("ID") is not None
    )
    return max_id + 1


def scan_size_table(table_name: str) -> list:
    """Scan a size table and return [{label, value}] options."""
    table = dynamodb.Table(table_name)
    items = scan_all_items(table)

    sizes = sorted(
        set(
            str(item.get("Size") or item.get("size", ""))
            for item in items
            if item.get("Size") or item.get("size")
        )
    )
    return [{"label": s, "value": s} for s in sizes]


@router.get("/sizes/{category}")
def get_sizes(category: str):
    """Return size options for a given product category."""
    table_name = SIZE_TABLE_MAP.get(category.lower())
    if not table_name:
        raise HTTPException(
            status_code=404,
            detail=f"No size table found for category '{category}'"
        )
    try:
        options = scan_size_table(table_name)
        return {"category": category, "options": options}
    except ClientError as e:
        logger.error(f"DynamoDB error fetching sizes for {category}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB Error: {e.response['Error']['Message']}"
        )


@router.post("/sizes/{category}")
def add_size(category: str, body: AddSizeRequest):
    """
    Add a new size value to the given category's DynamoDB table.
    ID is auto-incremented as a Number (matches DynamoDB key type N).
    Duplicate sizes (case-insensitive) are silently ignored.
    Returns the full updated list of size options for the category.
    """
    table_name = SIZE_TABLE_MAP.get(category.lower())
    if not table_name:
        raise HTTPException(
            status_code=404,
            detail=f"No size table found for category '{category}'"
        )

    size_value = body.size.strip()
    # Normalize X separators: "10X20X5" or "10x20x5" → "10 X 20 X 5"
    size_value = re.sub(r'\s*[Xx]\s*', ' X ', size_value)
    if not size_value:
        raise HTTPException(status_code=400, detail="Size value cannot be empty.")

    try:
        table = dynamodb.Table(table_name)

        # ── Fetch all existing items (needed for duplicate check + next ID) ──
        existing_items = scan_all_items(table)

        # ── Duplicate check (case-insensitive) ───────────────────────────────
        for item in existing_items:
            existing_size = str(item.get("Size") or item.get("size", ""))
            if existing_size.lower() == size_value.lower():
                logger.info(
                    f"Size '{size_value}' already exists in {table_name}, skipping insert."
                )
                options = scan_size_table(table_name)
                return {"category": category, "options": options, "duplicate": True}

        # ── Auto-increment numeric ID (matches DynamoDB key type N) ──────────
        new_id = get_next_id(existing_items)

        new_item = {
            "ID":   new_id,       # ✅ Number — matches partition key type N
            "Size": size_value,   # ✅ Size string value
        }

        # Use explicitly provided dimensions, or fall back to parsing the size string.
        # e.g. "67 X 12 X 16" → Width=67, Height=12, Gusset=16
        #      "16 X 21"      → Width=16, Height=21 (no Gusset)
        parts = [p.strip() for p in re.split(r'\s*[Xx]\s*', size_value) if p.strip()]

        def _get_dim(explicit_val, index: int):
            if explicit_val is not None:
                return explicit_val
            if index < len(parts):
                try:
                    return int(parts[index])
                except ValueError:
                    return None
            return None

        width_val  = _get_dim(body.width,  0)
        height_val = _get_dim(body.height, 1)
        gusset_val = _get_dim(body.gusset, 2)

        if width_val is not None:
            new_item["Width"] = width_val
        if height_val is not None:
            new_item["Height"] = height_val
        if gusset_val is not None:
            new_item["Gusset"] = gusset_val

        table.put_item(Item=new_item)
        logger.info(
            f"Added size '{size_value}' with ID={new_id} to {table_name}"
        )

        options = scan_size_table(table_name)
        return {"category": category, "options": options}

    except ClientError as e:
        logger.error(f"DynamoDB error adding size for {category}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB Error: {e.response['Error']['Message']}"
        )


@router.get("/sizes")
def get_all_sizes():
    """Return all size options for all categories in one call."""
    result = {}
    for category, table_name in SIZE_TABLE_MAP.items():
        try:
            result[category] = scan_size_table(table_name)
        except ClientError as e:
            logger.warning(f"Failed to fetch sizes for {category}: {e}")
            result[category] = []
    return result