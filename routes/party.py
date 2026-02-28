import logging
from typing import List
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
from pydantic import ValidationError

from schemas.party import Party, CreateParty, UpdateParty
from utils.helpers import aws_error_detail, normalize_party_item, get_next_party_id
from db.dynamodb import party_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


def format_validation_errors(errors: list) -> str:
    """Format Pydantic validation errors into a readable message"""
    error_messages = []
    for error in errors:
        field = error['loc'][0] if error['loc'] else 'unknown'
        message = error['msg']
        error_messages.append(f"{field}: {message}")
    return "; ".join(error_messages)


@router.get("/party", response_model=List[Party])
def list_parties():
    try:
        items = party_table.scan().get("Items", [])
        return [normalize_party_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error listing parties: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch parties")


@router.get("/party/{party_id}", response_model=Party)
def get_party(party_id: int):
    try:
        if party_id <= 0:
            raise HTTPException(status_code=400, detail="Party ID must be a positive integer")

        item = party_table.get_item(Key={"PartyId": party_id}).get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Party not found")
        return normalize_party_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting party {party_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch party")


@router.post("/party", response_model=Party)
def create_party(payload: CreateParty):
    try:
        # Validation is automatically done by Pydantic
        party_id = get_next_party_id()

        item = {
            "PartyId": party_id,
            "PartyName": payload.partyName,
            "AliasOrCompanyName": payload.aliasOrCompanyName,
            "Contact_Person1": payload.contact_Person1,
            "Contact_Person2": payload.contact_Person2,
            "Mobile1": payload.mobile1,
            "Mobile2": payload.mobile2,
            "Email": payload.email,
            "Address": payload.address,
            "City": payload.city,
            "State": payload.state,
            "Pincode": payload.pincode,
            "AgentId": payload.agentId,
            "OrderId": payload.orderId,
        }

        party_table.put_item(Item=item)

        logger.info(f"Party created successfully with ID: {party_id}")
        return normalize_party_item(item)

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error creating party: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except ClientError as e:
        logger.error(f"Database error creating party: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error creating party: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create party")


@router.put("/party/{party_id}", response_model=Party)
def update_party(party_id: int, payload: UpdateParty):
    try:
        if party_id <= 0:
            raise HTTPException(status_code=400, detail="Party ID must be a positive integer")

        # Check if party exists
        existing = party_table.get_item(Key={"PartyId": party_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Party not found")

        # Validation is automatically done by Pydantic
        item = {
            "PartyId": party_id,
            "PartyName": payload.partyName,
            "AliasOrCompanyName": payload.aliasOrCompanyName,
            "Contact_Person1": payload.contact_Person1,
            "Contact_Person2": payload.contact_Person2,
            "Mobile1": payload.mobile1,
            "Mobile2": payload.mobile2,
            "Email": payload.email,
            "Address": payload.address,
            "City": payload.city,
            "State": payload.state,
            "Pincode": payload.pincode,
            "AgentId": payload.agentId,
            "OrderId": payload.orderId,
        }

        party_table.put_item(Item=item)

        logger.info(f"Party {party_id} updated successfully")
        return normalize_party_item(item)

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error updating party {party_id}: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error updating party {party_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error updating party {party_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update party")


@router.delete("/party/{party_id}")
def delete_party(party_id: int):
    try:
        if party_id <= 0:
            raise HTTPException(status_code=400, detail="Party ID must be a positive integer")

        existing = party_table.get_item(Key={"PartyId": party_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Party not found")

        party_table.delete_item(Key={"PartyId": party_id})

        logger.info(f"Party {party_id} deleted successfully")
        return {"deleted": True}

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error deleting party {party_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error deleting party {party_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete party")