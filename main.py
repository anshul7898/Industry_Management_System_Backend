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

# -------------------- AWS Setup --------------------
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ACCOUNTS_TABLE = os.getenv("ACCOUNTS_TABLE", "Accounts")
AGENTS_TABLE = os.getenv("AGENTS_TABLE", "Agent")
PARTY_TABLE = os.getenv("PARTY_TABLE", "Party")
PRODUCTS_TABLE = os.getenv("PRODUCTS_TABLE", "Product")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
agents_table = dynamodb.Table(AGENTS_TABLE)
party_table = dynamodb.Table(PARTY_TABLE)
products_table = dynamodb.Table(PRODUCTS_TABLE)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ===================== HELPERS ===========================
# =========================================================

def ddb_decimal(n: float) -> Decimal:
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
    def convert(value):
        if isinstance(value, Decimal):
            # Convert to int first
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
        "agentId": int(item["AgentId"]) if item.get("AgentId") and isinstance(item["AgentId"], Decimal) else item.get(
            "AgentId"),
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
                if isinstance(agent_id, Decimal):
                    agent_ids.append(int(agent_id))
                else:
                    agent_ids.append(int(agent_id))

        if not agent_ids:
            return 1

        return max(agent_ids) + 1
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
                if isinstance(party_id, Decimal):
                    party_ids.append(int(party_id))
                else:
                    party_ids.append(int(party_id))

        if not party_ids:
            return 1

        return max(party_ids) + 1
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
                if isinstance(product_id, Decimal):
                    product_ids.append(int(product_id))
                else:
                    product_ids.append(int(product_id))

        if not product_ids:
            return 1

        return max(product_ids) + 1
    except Exception as e:
        logger.error(f"Error getting next product ID: {str(e)}")
        raise


# =========================================================
# ===================== ORDERS ============================
# =========================================================

class Order(BaseModel):
    orderId: str
    description: Optional[str] = None
    customerName: Optional[str] = None
    orderDate: Optional[str] = None
    deliveryDate: Optional[str] = None


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


@app.get("/api/orders", response_model=List[Order])
def list_orders():
    try:
        return orders_table.scan().get("Items", [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


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

    orders_table.put_item(Item=item)
    return item


@app.put("/api/orders/{order_id}", response_model=Order)
def update_order(order_id: str, payload: UpdateOrder):
    existing = orders_table.get_item(Key={"orderId": order_id}).get("Item")
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    item = {"orderId": order_id, **payload.dict()}
    orders_table.put_item(Item=item)
    return item


@app.delete("/api/orders/{order_id}")
def delete_order(order_id: str):
    existing = orders_table.get_item(Key={"orderId": order_id}).get("Item")
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    orders_table.delete_item(Key={"orderId": order_id})
    return {"deleted": True}


# =========================================================
# ===================== ACCOUNTS ==========================
# =========================================================

class AccountTxn(BaseModel):
    txnId: str
    type: Optional[str] = None
    description: Optional[str] = None
    partyName: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None


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


@app.get("/api/accounts", response_model=List[AccountTxn])
def list_accounts():
    items = accounts_table.scan().get("Items", [])
    return [normalize_ddb_item(x) for x in items]


@app.post("/api/accounts", response_model=AccountTxn)
def create_account(payload: CreateAccountTxn):
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


@app.put("/api/accounts/{txn_id}", response_model=AccountTxn)
def update_account(txn_id: str, payload: UpdateAccountTxn):
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


@app.delete("/api/accounts/{txn_id}")
def delete_account(txn_id: str):
    existing = accounts_table.get_item(Key={"txnId": txn_id}).get("Item")
    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")

    accounts_table.delete_item(Key={"txnId": txn_id})
    return {"deleted": True}


# =========================================================
# ===================== AGENTS ============================
# =========================================================

class Agent(BaseModel):
    agentId: int
    aadhar_Details: Optional[str] = None
    address: Optional[str] = None
    mobile: Optional[str] = None
    name: Optional[str] = None


class AgentLightweight(BaseModel):
    agentId: int
    name: Optional[str] = None


class CreateAgent(BaseModel):
    aadhar_Details: str
    address: str
    mobile: str
    name: str


class UpdateAgent(BaseModel):
    aadhar_Details: str
    address: str
    mobile: str
    name: str


@app.get("/api/agents", response_model=List[Agent])
def list_agents():
    try:
        items = agents_table.scan().get("Items", [])
        return [normalize_agent_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@app.get("/api/agents/lightweight", response_model=List[AgentLightweight])
def list_agents_lightweight():
    """
    Returns a lightweight list of all agents: just AgentId and Name.
    """
    try:
        items = agents_table.scan().get("Items", [])
        result = []
        for item in items:
            agent_id = int(item["AgentId"]) if isinstance(item["AgentId"], Decimal) else item["AgentId"]
            name = item.get("Name")
            result.append(AgentLightweight(agentId=agent_id, name=name))
        return result
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@app.get("/api/agents/{agent_id}", response_model=Agent)
def get_agent(agent_id: int):
    try:
        resp = agents_table.get_item(Key={"AgentId": agent_id})
        item = resp.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Agent not found")
        return normalize_agent_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


@app.post("/api/agents", response_model=Agent)
def create_agent(payload: CreateAgent):
    try:
        # Auto-generate next agent ID
        agent_id = get_next_agent_id()

        # Create item with DynamoDB attribute names
        item = {
            "AgentId": agent_id,
            "Name": payload.name,
            "Mobile": payload.mobile,
            "Aadhar_Details": payload.aadhar_Details,
            "Address": payload.address,
        }

        # Put item in DynamoDB
        agents_table.put_item(Item=item)

        # Return normalized response
        return normalize_agent_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")


@app.put("/api/agents/{agent_id}", response_model=Agent)
def update_agent(agent_id: int, payload: UpdateAgent):
    try:
        existing = agents_table.get_item(Key={"AgentId": agent_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Agent not found")

        item = {
            "AgentId": agent_id,
            "Name": payload.name,
            "Mobile": payload.mobile,
            "Aadhar_Details": payload.aadhar_Details,
            "Address": payload.address,
        }

        agents_table.put_item(Item=item)
        return normalize_agent_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")


@app.delete("/api/agents/{agent_id}")
def delete_agent(agent_id: int):
    try:
        existing = agents_table.get_item(Key={"AgentId": agent_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Agent not found")

        agents_table.delete_item(Key={"AgentId": agent_id})
        return {"deleted": True}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


# =========================================================
# ===================== PARTY =============================
# =========================================================

class Party(BaseModel):
    partyId: int
    partyName: str
    aliasOrCompanyName: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    agentId: Optional[int] = None
    contact_Person1: Optional[str] = None
    contact_Person2: Optional[str] = None
    email: Optional[str] = None
    mobile1: Optional[str] = None
    mobile2: Optional[str] = None
    orderId: Optional[str] = None


class CreateParty(BaseModel):
    partyName: str
    aliasOrCompanyName: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    agentId: Optional[int] = None
    contact_Person1: Optional[str] = None
    contact_Person2: Optional[str] = None
    email: Optional[str] = None
    mobile1: Optional[str] = None
    mobile2: Optional[str] = None
    orderId: Optional[str] = None


class UpdateParty(BaseModel):
    partyName: str
    aliasOrCompanyName: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    agentId: Optional[int] = None
    contact_Person1: Optional[str] = None
    contact_Person2: Optional[str] = None
    email: Optional[str] = None
    mobile1: Optional[str] = None
    mobile2: Optional[str] = None
    orderId: Optional[str] = None


@app.get("/api/party", response_model=List[Party])
def list_parties():
    try:
        items = party_table.scan().get("Items", [])
        return [normalize_party_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@app.get("/api/party/{party_id}", response_model=Party)
def get_party(party_id: int):
    try:
        item = party_table.get_item(Key={"PartyId": party_id}).get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Party not found")
        return normalize_party_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


@app.post("/api/party", response_model=Party)
def create_party(payload: CreateParty):
    try:
        # Auto-generate next party ID
        party_id = get_next_party_id()

        item = {
            "PartyId": party_id,
            "PartyName": payload.partyName,
            "AliasOrCompanyName": payload.aliasOrCompanyName,
            "Address": payload.address,
            "City": payload.city,
            "State": payload.state,
            "Pincode": payload.pincode,
            "AgentId": payload.agentId,
            "Contact_Person1": payload.contact_Person1,
            "Contact_Person2": payload.contact_Person2,
            "Email": payload.email,
            "Mobile1": payload.mobile1,
            "Mobile2": payload.mobile2,
            "OrderId": payload.orderId,
        }

        party_table.put_item(Item=item)
        return normalize_party_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating party: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating party: {str(e)}")


@app.put("/api/party/{party_id}", response_model=Party)
def update_party(party_id: int, payload: UpdateParty):
    try:
        existing = party_table.get_item(Key={"PartyId": party_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Party not found")

        item = {
            "PartyId": party_id,
            "PartyName": payload.partyName,
            "AliasOrCompanyName": payload.aliasOrCompanyName,
            "Address": payload.address,
            "City": payload.city,
            "State": payload.state,
            "Pincode": payload.pincode,
            "AgentId": payload.agentId,
            "Contact_Person1": payload.contact_Person1,
            "Contact_Person2": payload.contact_Person2,
            "Email": payload.email,
            "Mobile1": payload.mobile1,
            "Mobile2": payload.mobile2,
            "OrderId": payload.orderId,
        }

        party_table.put_item(Item=item)
        return normalize_party_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating party: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating party: {str(e)}")


@app.delete("/api/party/{party_id}")
def delete_party(party_id: int):
    try:
        existing = party_table.get_item(Key={"PartyId": party_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Party not found")

        party_table.delete_item(Key={"PartyId": party_id})
        return {"deleted": True}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


# =========================================================
# ===================== PRODUCTS ==========================
# =========================================================

class Product(BaseModel):
    productId: int
    productType: Optional[str] = None
    productSize: Optional[float] = None
    bagMaterial: Optional[str] = None
    quantity: Optional[float] = None
    sheetGSM: Optional[float] = None
    sheetColor: Optional[str] = None
    borderGSM: Optional[float] = None
    borderColor: Optional[str] = None
    handleType: Optional[str] = None
    handleColor: Optional[str] = None
    handleGSM: Optional[float] = None
    printingType: Optional[str] = None
    printColor: Optional[str] = None
    color: Optional[str] = None
    design: Optional[bool] = False
    plateBlockNumber: Optional[float] = None
    plateAvailable: Optional[bool] = False
    rate: Optional[float] = None


class CreateProduct(BaseModel):
    productType: str
    productSize: float
    bagMaterial: str
    quantity: float
    sheetGSM: float
    sheetColor: str
    borderGSM: float
    borderColor: str
    handleType: str
    handleColor: str
    handleGSM: float
    printingType: str
    printColor: str
    color: str
    design: bool = False
    plateBlockNumber: float = 0
    plateAvailable: bool = False
    rate: float


class UpdateProduct(BaseModel):
    productType: str
    productSize: float
    bagMaterial: str
    quantity: float
    sheetGSM: float
    sheetColor: str
    borderGSM: float
    borderColor: str
    handleType: str
    handleColor: str
    handleGSM: float
    printingType: str
    printColor: str
    color: str
    design: bool = False
    plateBlockNumber: float = 0
    plateAvailable: bool = False
    rate: float


class SearchProduct(BaseModel):
    """Model for searching products with optional filters"""
    productType: Optional[str] = None
    bagMaterial: Optional[str] = None
    sheetColor: Optional[str] = None
    borderColor: Optional[str] = None
    handleColor: Optional[str] = None
    printingType: Optional[str] = None
    printColor: Optional[str] = None
    color: Optional[str] = None
    design: Optional[bool] = None
    plateAvailable: Optional[bool] = None
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None


@app.get("/api/products", response_model=List[Product])
def list_products():
    """
    Get all products from the database
    """
    try:
        items = products_table.scan().get("Items", [])
        return [normalize_product_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """
    Get a specific product by ID
    """
    try:
        resp = products_table.get_item(Key={"ProductId": product_id})
        item = resp.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


@app.post("/api/products", response_model=Product)
def create_product(payload: CreateProduct):
    """
    Create a new product with auto-generated ID
    """
    try:
        # Auto-generate next product ID
        product_id = get_next_product_id()

        # Create item with DynamoDB attribute names
        item = {
            "ProductId": product_id,
            "ProductType": payload.productType,
            "ProductSize": ddb_decimal(payload.productSize),
            "BagMaterial": payload.bagMaterial,
            "Quantity": ddb_decimal(payload.quantity),
            "SheetGSM": ddb_decimal(payload.sheetGSM),
            "SheetColor": payload.sheetColor,
            "BorderGSM": ddb_decimal(payload.borderGSM),
            "BorderColor": payload.borderColor,
            "HandleType": payload.handleType,
            "HandleColor": payload.handleColor,
            "HandleGSM": ddb_decimal(payload.handleGSM),
            "PrintingType": payload.printingType,
            "PrintColor": payload.printColor,
            "Color": payload.color,
            "Design": payload.design,
            "PlateBlockNumber": ddb_decimal(payload.plateBlockNumber),
            "PlateAvailable": payload.plateAvailable,
            "Rate": ddb_decimal(payload.rate),
        }

        # Put item in DynamoDB
        products_table.put_item(Item=item)

        # Return normalized response
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")


@app.put("/api/products/{product_id}", response_model=Product)
def update_product(product_id: int, payload: UpdateProduct):
    """
    Update an existing product
    """
    try:
        existing = products_table.get_item(Key={"ProductId": product_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        item = {
            "ProductId": product_id,
            "ProductType": payload.productType,
            "ProductSize": ddb_decimal(payload.productSize),
            "BagMaterial": payload.bagMaterial,
            "Quantity": ddb_decimal(payload.quantity),
            "SheetGSM": ddb_decimal(payload.sheetGSM),
            "SheetColor": payload.sheetColor,
            "BorderGSM": ddb_decimal(payload.borderGSM),
            "BorderColor": payload.borderColor,
            "HandleType": payload.handleType,
            "HandleColor": payload.handleColor,
            "HandleGSM": ddb_decimal(payload.handleGSM),
            "PrintingType": payload.printingType,
            "PrintColor": payload.printColor,
            "Color": payload.color,
            "Design": payload.design,
            "PlateBlockNumber": ddb_decimal(payload.plateBlockNumber),
            "PlateAvailable": payload.plateAvailable,
            "Rate": ddb_decimal(payload.rate),
        }

        products_table.put_item(Item=item)
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    """
    Delete a product by ID
    """
    try:
        existing = products_table.get_item(Key={"ProductId": product_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        products_table.delete_item(Key={"ProductId": product_id})
        return {"deleted": True, "productId": product_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


@app.post("/api/products/search", response_model=List[Product])
def search_products(filters: SearchProduct):
    """
    Search products with optional filters.
    Supports filtering by:
    - productType
    - bagMaterial
    - sheetColor
    - borderColor
    - handleColor
    - printingType
    - printColor
    - color
    - design (boolean)
    - plateAvailable (boolean)
    - minPrice / maxPrice (rate range)
    """
    try:
        # Scan all items
        items = products_table.scan().get("Items", [])

        # Apply filters
        filtered_items = []
        for item in items:
            # Check string filters
            if filters.productType and item.get("ProductType") != filters.productType:
                continue
            if filters.bagMaterial and item.get("BagMaterial") != filters.bagMaterial:
                continue
            if filters.sheetColor and item.get("SheetColor") != filters.sheetColor:
                continue
            if filters.borderColor and item.get("BorderColor") != filters.borderColor:
                continue
            if filters.handleColor and item.get("HandleColor") != filters.handleColor:
                continue
            if filters.printingType and item.get("PrintingType") != filters.printingType:
                continue
            if filters.printColor and item.get("PrintColor") != filters.printColor:
                continue
            if filters.color and item.get("Color") != filters.color:
                continue

            # Check boolean filters
            if filters.design is not None and item.get("Design") != filters.design:
                continue
            if filters.plateAvailable is not None and item.get("PlateAvailable") != filters.plateAvailable:
                continue

            # Check price range
            rate = item.get("Rate")
            if isinstance(rate, Decimal):
                rate = float(rate)

            if filters.minPrice is not None and rate < filters.minPrice:
                continue
            if filters.maxPrice is not None and rate > filters.maxPrice:
                continue

            filtered_items.append(item)

        # Normalize and return
        return [normalize_product_item(x) for x in filtered_items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")