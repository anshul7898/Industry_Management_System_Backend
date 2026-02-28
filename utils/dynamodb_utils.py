from decimal import Decimal
from typing import Any, Dict, List


def decimal_to_python(obj: Any) -> Any:
    """
    Convert DynamoDB Decimal types to Python int/float.
    This handles the conversion of all Decimal objects returned by boto3.
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
    Also ensures OrderId is always a string.
    """
    converted_items = []
    for item in items:
        converted_item = decimal_to_python(item)

        # Ensure OrderId is a string
        if "OrderId" in converted_item:
            converted_item["OrderId"] = str(converted_item["OrderId"])

        converted_items.append(converted_item)

    return converted_items


def convert_item_to_python(item: Dict) -> Dict:
    """
    Convert a single DynamoDB item to proper Python types.
    Also ensures OrderId is always a string.
    """
    converted_item = decimal_to_python(item)

    # Ensure OrderId is a string
    if "OrderId" in converted_item:
        converted_item["OrderId"] = str(converted_item["OrderId"])

    return converted_item