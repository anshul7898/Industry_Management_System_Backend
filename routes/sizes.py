import logging
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
import boto3
from config.settings import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

SIZE_TABLE_MAP = {
    "stitching":    "Stitching_Size_Table",
    "d-cut":        "D_Cut_Size_Table",
    "u-cut":        "U_Cut_Size_Table",
    "cake-bag-old": "Cake_Bag_Old_Size_Table",
    "cake-bag-new": "Cake_Bag_New_Size_Table",
    "side-gaget":   "Side_Gaget_Size_Table",
    "bottom-gaget": "Bottom_Gaget_Size_Table",
    "handle-bag":   "Handle_Bag_Size_Table",
}


def scan_size_table(table_name: str) -> list:
    """Scan a size table and return [{label, value}] options."""
    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response.get("Items", [])

    # Support pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    # Each item is expected to have a 'Size' attribute
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