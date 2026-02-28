import logging
from decimal import Decimal
from botocore.exceptions import ClientError
from db.dynamodb import agents_table, party_table, products_table

logger = logging.getLogger("uvicorn.error")


def ddb_decimal(n: float) -> Decimal:
    """Convert float to DynamoDB Decimal"""
    return Decimal(str(n))


def normalize_ddb_item(item: dict) -> dict:
    """
    Convert all DynamoDB Decimal values to float
    """
    out = {}
    for k, v in item.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out


def normalize_agent_item(item: dict) -> dict:
    """
    Convert DynamoDB item to API-safe response.
    Handles Decimal conversion properly.
    """
    def convert(value):
        if isinstance(value, Decimal):
            return str(value)
        return value

    return {
        "agentId": int(item["AgentId"]) if isinstance(item["AgentId"], Decimal) else item["AgentId"],
        "name": convert(item.get("Name")),
        "mobile": convert(item.get("Mobile")),
        "aadhar_Details": convert(item.get("Aadhar_Details")),
        "address": convert(item.get("Address")),
    }


def normalize_party_item(item: dict) -> dict:
    """
    Convert DynamoDB Party item to API-safe response.
    """
    def convert(value):
        if isinstance(value, Decimal):
            value = int(value)
        return str(value) if value is not None else None

    return {
        "partyId": int(item["PartyId"]) if isinstance(item["PartyId"], Decimal) else item["PartyId"],
        "partyName": item.get("PartyName"),
        "aliasOrCompanyName": item.get("AliasOrCompanyName"),
        "address": item.get("Address"),
        "city": item.get("City"),
        "state": item.get("State"),
        "pincode": convert(item.get("Pincode")),
        "agentId": int(item["AgentId"]) if item.get("AgentId") and isinstance(item["AgentId"], Decimal) else item.get("AgentId"),
        "contact_Person1": item.get("Contact_Person1"),
        "contact_Person2": item.get("Contact_Person2"),
        "email": item.get("Email"),
        "mobile1": convert(item.get("Mobile1")),
        "mobile2": convert(item.get("Mobile2")),
        "orderId": convert(item.get("OrderId")),
    }


def normalize_product_item(item: dict) -> dict:
    """
    Convert DynamoDB Product item to API-safe response.
    Handles Decimal conversion properly.
    """
    def convert_decimal(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    return {
        "productId": int(item["ProductId"]) if isinstance(item["ProductId"], Decimal) else item["ProductId"],
        "productType": item.get("ProductType"),
        "productSize": convert_decimal(item.get("ProductSize")),
        "bagMaterial": item.get("BagMaterial"),
        "quantity": convert_decimal(item.get("Quantity")),
        "sheetGSM": convert_decimal(item.get("SheetGSM")),
        "sheetColor": item.get("SheetColor"),
        "borderGSM": convert_decimal(item.get("BorderGSM")),
        "borderColor": item.get("BorderColor"),
        "handleType": item.get("HandleType"),
        "handleColor": item.get("HandleColor"),
        "handleGSM": convert_decimal(item.get("HandleGSM")),
        "printingType": item.get("PrintingType"),
        "printColor": item.get("PrintColor"),
        "color": item.get("Color"),
        "design": item.get("Design", False),
        "plateBlockNumber": convert_decimal(item.get("PlateBlockNumber")),
        "plateAvailable": item.get("PlateAvailable", False),
        "rate": convert_decimal(item.get("Rate")),
    }


def aws_error_detail(e: ClientError) -> str:
    """Extract error details from AWS ClientError"""
    code = e.response.get("Error", {}).get("Code", "ClientError")
    msg = e.response.get("Error", {}).get("Message", str(e))
    return f"{code}: {msg}"


def get_next_agent_id() -> int:
    """
    Get the next agent ID by finding the highest existing agent ID and adding 1
    """
    try:
        items = agents_table.scan().get("Items", [])
        if not items:
            return 1

        agent_ids = []
        for item in items:
            agent_id = item.get("AgentId")
            if agent_id:
                agent_ids.append(int(agent_id) if isinstance(agent_id, Decimal) else int(agent_id))

        return max(agent_ids) + 1 if agent_ids else 1
    except Exception as e:
        logger.error(f"Error getting next agent ID: {str(e)}")
        raise


def get_next_party_id() -> int:
    """
    Get the next party ID by finding the highest existing party ID and adding 1
    """
    try:
        items = party_table.scan().get("Items", [])
        if not items:
            return 1

        party_ids = []
        for item in items:
            party_id = item.get("PartyId")
            if party_id:
                party_ids.append(int(party_id) if isinstance(party_id, Decimal) else int(party_id))

        return max(party_ids) + 1 if party_ids else 1
    except Exception as e:
        logger.error(f"Error getting next party ID: {str(e)}")
        raise


def get_next_product_id() -> int:
    """
    Get the next product ID by finding the highest existing product ID and adding 1
    """
    try:
        items = products_table.scan().get("Items", [])
        if not items:
            return 1

        product_ids = []
        for item in items:
            product_id = item.get("ProductId")
            if product_id:
                product_ids.append(int(product_id) if isinstance(product_id, Decimal) else int(product_id))

        return max(product_ids) + 1 if product_ids else 1
    except Exception as e:
        logger.error(f"Error getting next product ID: {str(e)}")
        raise