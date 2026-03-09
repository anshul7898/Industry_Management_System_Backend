from decimal import Decimal
from typing import Any, Dict, List


def decimal_to_python(obj: Any) -> Any:
    """
    Convert DynamoDB Decimal types to Python int/float.
    This handles the conversion of all Decimal objects returned by boto3.
    Recursively processes nested structures including Products arrays.
    """
    if isinstance(obj, Decimal):
        # Check if it's an integer or float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_python(item) for item in obj]
    return obj


def convert_items_to_python(items: List[Dict]) -> List[Dict]:
    """
    Convert all DynamoDB items to proper Python types.
    Handles nested Products arrays and ensures OrderId is a string.

    Args:
        items: List of DynamoDB items

    Returns:
        List of converted items with proper Python types
    """
    converted_items = []
    for item in items:
        converted_item = decimal_to_python(item)

        # Ensure OrderId is a string
        if "OrderId" in converted_item:
            converted_item["OrderId"] = str(converted_item["OrderId"])

        # Ensure Products array exists and is properly formatted
        if "Products" not in converted_item:
            converted_item["Products"] = []
        elif not isinstance(converted_item["Products"], list):
            converted_item["Products"] = [converted_item["Products"]]

        converted_items.append(converted_item)

    return converted_items


def convert_item_to_python(item: Dict) -> Dict:
    """
    Convert a single DynamoDB item to proper Python types.
    Handles nested Products arrays and ensures OrderId is a string.

    Args:
        item: Single DynamoDB item

    Returns:
        Converted item with proper Python types
    """
    if not item:
        return {}

    converted_item = decimal_to_python(item)

    # Ensure OrderId is a string
    if "OrderId" in converted_item:
        converted_item["OrderId"] = str(converted_item["OrderId"])

    # Ensure Products array exists and is properly formatted
    if "Products" not in converted_item:
        converted_item["Products"] = []
    elif not isinstance(converted_item["Products"], list):
        converted_item["Products"] = [converted_item["Products"]]

    return converted_item


def convert_product_for_storage(product: dict) -> dict:
    """
    Convert a product dict for DynamoDB storage.
    Filters out None values and converts numeric fields to Decimal.

    Args:
        product: Product dictionary from frontend

    Returns:
        Product dict with Decimal values, excluding None values
    """
    if not product:
        return {}

    result = {}

    # String fields - include even if None
    string_fields = [
        "ProductType", "SheetColor", "BorderColor", "HandleType",
        "HandleColor", "PrintingType", "PrintColor", "Color", "BagMaterial"
    ]

    for field in string_fields:
        value = product.get(field)
        if value is not None:
            result[field] = value

    # Numeric fields that should be integers
    int_fields = [
        "ProductId", "ProductSize", "Quantity", "SheetGSM",
        "BorderGSM", "HandleGSM", "PlateBlockNumber"
    ]

    for field in int_fields:
        value = product.get(field)
        if value is not None:
            try:
                result[field] = int(value)
            except (ValueError, TypeError):
                result[field] = value

    # Numeric fields that should be Decimal
    decimal_fields = ["Rate", "TotalAmount"]

    for field in decimal_fields:
        value = product.get(field)
        if value is not None:
            try:
                result[field] = Decimal(str(value))
            except (ValueError, TypeError):
                result[field] = value

    # Boolean fields
    bool_fields = ["Design", "PlateAvailable"]
    for field in bool_fields:
        value = product.get(field)
        result[field] = bool(value) if value is not None else False

    return result