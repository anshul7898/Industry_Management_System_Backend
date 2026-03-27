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


def convert_product_for_storage(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a product dict to DynamoDB storage format.
    Ensures all fields are properly typed and ProductCategory is included.
    """
    logger.info(f"Converting product to storage format: {product}")

    # Start with all fields that should be stored
    stored_product = {
        "ProductType": product.get("ProductType"),
        "ProductCategory": product.get("ProductCategory"),  # FIX: Include ProductCategory
        "ProductId": product.get("ProductId"),
        "ProductSize": product.get("ProductSize"),
        "BagMaterial": product.get("BagMaterial"),
        "Quantity": int(product.get("Quantity", 0)),
        "SheetGSM": int(product.get("SheetGSM", 0)),
        "SheetColor": product.get("SheetColor"),
        "BorderGSM": int(product.get("BorderGSM", 0)),
        "BorderColor": product.get("BorderColor"),
        "HandleType": product.get("HandleType"),
        "HandleColor": product.get("HandleColor"),
        "HandleGSM": int(product.get("HandleGSM", 0)),
        "PrintingType": product.get("PrintingType"),
        "PrintColor": product.get("PrintColor"),
        "Color": product.get("Color"),
        "Design": bool(product.get("Design", False)),
        "PlateBlockNumber": product.get("PlateBlockNumber"),
        "PlateAvailable": bool(product.get("PlateAvailable", False)),
        "Rate": Decimal(str(product.get("Rate", 0))),
        "ProductAmount": Decimal(str(product.get("ProductAmount", 0))),
    }

    # Remove None values to keep DynamoDB clean (optional custom fields)
    # But keep ProductCategory even if None for consistency
    cleaned_product = {
        k: v for k, v in stored_product.items()
        if v is not None or k in ["ProductCategory", "ProductId"]  # Keep these even if None
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