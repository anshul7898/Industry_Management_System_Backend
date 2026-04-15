"""DynamoDB utility functions for data conversion."""

from decimal import Decimal
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger("uvicorn.error")


def convert_item_to_python(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert DynamoDB item to Python types.
    Handles Decimal → float, nested dicts, and lists.
    """
    if isinstance(item, dict):
        return {k: convert_item_to_python(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [convert_item_to_python(v) for v in item]
    elif isinstance(item, Decimal):
        # Convert Decimal to float, preserving precision for monetary values
        return float(item)
    else:
        return item


def convert_items_to_python(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert a list of DynamoDB items to Python types."""
    return [convert_item_to_python(item) for item in items]


def is_item_deleted(item: Dict[str, Any]) -> bool:
    """Return True if the DynamoDB item is marked deleted."""
    if not isinstance(item, dict):
        return False
    deleted = item.get("deleted", False)
    if isinstance(deleted, bool):
        return deleted
    if isinstance(deleted, str):
        return deleted.strip().lower() == "true"
    if isinstance(deleted, (int, float)):
        return bool(deleted)
    return False


def filter_deleted_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only items not marked as deleted."""
    return [item for item in items if not is_item_deleted(item)]


def convert_product_for_storage(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a product dict to DynamoDB storage format.
    Ensures all fields are properly typed and ProductCategory is included.
    ✅ PlateRate is now explicitly included so it is persisted to DynamoDB.
    """
    logger.info(f"Converting product to storage format: {product}")

    # ✅ Resolve PlateRate — accept float/int/Decimal/str; store as Decimal.
    #    If absent or None, keep as None (will be filtered out below unless
    #    the user explicitly provided 0, in which case Decimal("0") is stored).
    raw_plate_rate = product.get("PlateRate")
    plate_rate_decimal = None
    if raw_plate_rate is not None:
        try:
            plate_rate_decimal = Decimal(str(raw_plate_rate))
        except Exception:
            plate_rate_decimal = None

    # Start with all fields that should be stored
    stored_product = {
        "ProductType": product.get("ProductType"),
        "ProductCategory": product.get("ProductCategory"),
        "ProductId": product.get("ProductId"),
        "ProductSize": product.get("ProductSize"),
        "Width": int(product["Width"]) if product.get("Width") is not None else None,
        "Height": int(product["Height"]) if product.get("Height") is not None else None,
        "Gusset": int(product["Gusset"]) if product.get("Gusset") is not None else None,
        "BagMaterial": product.get("BagMaterial"),
        "Quantity": int(product.get("Quantity", 0)),
        "SheetGSM": int(product.get("SheetGSM", 0)),
        "SheetColor": product.get("SheetColor"),
        "BorderGSM": int(product.get("BorderGSM", 0)) if product.get("BorderGSM") is not None else None,
        "BorderColor": product.get("BorderColor"),
        "HandleType": product.get("HandleType"),
        "HandleColor": product.get("HandleColor"),
        "AlternativeHandleColor": product.get("AlternativeHandleColor"),
        "HandleGSM": int(product.get("HandleGSM", 0)),
        "PrintingType": product.get("PrintingType"),
        "PrintColor": product.get("PrintColor"),
        "Color": product.get("Color"),
        "Design": bool(product.get("Design", False)),
        "PlateBlockNumber": product.get("PlateBlockNumber"),
        "PlateAvailable": bool(product.get("PlateAvailable", False)),
        # ✅ NEW: PlateRate stored as Decimal (None → omitted by cleanup below)
        "PlateRate": plate_rate_decimal,
        "Rate": Decimal(str(product.get("Rate", 0))),
        "ProductAmount": Decimal(str(product.get("ProductAmount", 0))),
    }

    # Remove None values to keep DynamoDB clean.
    # ProductCategory and ProductId are kept even when None for schema consistency.
    cleaned_product = {
        k: v for k, v in stored_product.items()
        if v is not None or k in ["ProductCategory", "ProductId"]
    }

    logger.info(f"Product after storage conversion: {cleaned_product}")
    return cleaned_product


def convert_product_from_storage(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a product from DynamoDB storage format to Python types.
    Handles Decimal → float conversion.
    """
    if not isinstance(product, dict):
        return product

    converted = {}
    for key, value in product.items():
        if isinstance(value, Decimal):
            converted[key] = float(value)
        elif isinstance(value, dict):
            converted[key] = convert_product_from_storage(value)
        elif isinstance(value, list):
            converted[key] = [
                convert_product_from_storage(item) if isinstance(item, dict) else
                (float(item) if isinstance(item, Decimal) else item)
                for item in value
            ]
        else:
            converted[key] = value

    return converted