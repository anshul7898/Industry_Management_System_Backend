import logging
from typing import List
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError

from schemas.party import Party, CreateParty, UpdateParty
from utils.helpers import aws_error_detail, normalize_party_item, get_next_party_id
from db.dynamodb import party_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get("/party", response_model=List[Party])
def list_parties():
    try:
        items = party_table.scan().get("Items", [])
        return [normalize_party_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@router.get("/party/{party_id}", response_model=Party)
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


@router.post("/party", response_model=Party)
def create_party(payload: CreateParty):
    try:
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
    except Exception as e:
        logger.error(f"Error creating party: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating party: {str(e)}")


@router.put("/party/{party_id}", response_model=Party)
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
    except Exception as e:
        logger.error(f"Error updating party: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating party: {str(e)}")


@router.delete("/party/{party_id}")
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