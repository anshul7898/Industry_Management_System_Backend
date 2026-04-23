import logging
from typing import List
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
from pydantic import ValidationError

from schemas.party import Party, CreateParty, UpdateParty
from utils.helpers import aws_error_detail, normalize_party_item, get_next_party_id
from utils.dynamodb_utils import filter_deleted_items, is_item_deleted
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
        items = filter_deleted_items(party_table.scan().get("Items", []))
        return [normalize_party_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error listing parties: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch parties")


# ── NEW: Lookup party by Party Name ───────────────────────────────
@router.get("/party/by-name/{party_name}", response_model=Party)
def get_party_by_name(party_name: str):
    """
    Scan the Party table for a record whose PartyName matches
    the given party_name (case-insensitive). Returns the first match.
    Used by the Old Order flow to auto-fill the New Order form.
    """
    try:
        logger.info(f"🔍 Looking up party by name: {party_name}")
        response = party_table.scan()
        items = response.get("Items", [])

        # Case-insensitive match on PartyName
        match = next(
            (item for item in filter_deleted_items(items)
             if str(item.get("PartyName", "")).lower() == party_name.lower()),
            None,
        )

        if not match:
            logger.warning(f"⚠️ No party found with name: {party_name}")
            raise HTTPException(
                status_code=404,
                detail=f"No party found with name '{party_name}'",
            )

        logger.info(f"✓ Found party: {match.get('PartyId')}")
        return normalize_party_item(match)

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"DynamoDB error looking up party by name: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Unexpected error looking up party by name: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to lookup party")
# ─────────────────────────────────────────────────────────────────


@router.get("/party/{party_id}", response_model=Party)
def get_party(party_id: str):
    try:
        if not party_id or not party_id.strip():
            raise HTTPException(status_code=400, detail="Party ID is required")

        # Convert formatted ID to numeric
        # Format: "A01P001" -> extract "001" (numeric party_id)
        numeric_id = None
        if "P" in party_id:
            try:
                numeric_id = int(party_id.split("P")[-1])
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Party ID format")
        else:
            try:
                numeric_id = int(party_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Party ID")

        item = party_table.get_item(Key={"PartyId": numeric_id}).get("Item")
        if not item or is_item_deleted(item):
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
        # Get numeric agent_id - convert from formatted string if needed
        agent_id = payload.agentId
        numeric_agent_id = None
        
        if agent_id:
            if isinstance(agent_id, str) and agent_id.startswith("A"):
                try:
                    numeric_agent_id = int(agent_id[1:])
                except (ValueError, IndexError):
                    numeric_agent_id = None
            elif isinstance(agent_id, int):
                numeric_agent_id = agent_id
            elif isinstance(agent_id, str):
                try:
                    numeric_agent_id = int(agent_id)
                except ValueError:
                    numeric_agent_id = None
        
        if not numeric_agent_id:
            numeric_agent_id = 1  # Default agent
        
        party_id_num = get_next_party_id(numeric_agent_id)

        item = {
            "PartyId": party_id_num,
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
            "AgentId": numeric_agent_id,
            "deleted": False,
        }

        party_table.put_item(Item=item)

        logger.info(f"Party created successfully with ID: {party_id_num}")
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
def update_party(party_id: str, payload: UpdateParty):
    try:
        if not party_id or not party_id.strip():
            raise HTTPException(status_code=400, detail="Party ID is required")

        # Convert formatted ID to numeric
        numeric_id = None
        if "P" in party_id:
            try:
                numeric_id = int(party_id.split("P")[-1])
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Party ID format")
        else:
            try:
                numeric_id = int(party_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Party ID")

        existing = party_table.get_item(Key={"PartyId": numeric_id}).get("Item")
        if not existing or is_item_deleted(existing):
            raise HTTPException(status_code=404, detail="Party not found")

        # Get numeric agent_id
        numeric_agent_id = payload.agentId
        if isinstance(numeric_agent_id, str):
            if numeric_agent_id.startswith("A"):
                try:
                    numeric_agent_id = int(numeric_agent_id[1:])
                except (ValueError, IndexError):
                    numeric_agent_id = existing.get("AgentId")
            else:
                try:
                    numeric_agent_id = int(numeric_agent_id)
                except ValueError:
                    numeric_agent_id = existing.get("AgentId")

        item = {
            "PartyId": numeric_id,
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
            "AgentId": numeric_agent_id,
        }

        item["deleted"] = existing.get("deleted", False)
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
def delete_party(party_id: str):
    try:
        if not party_id or not party_id.strip():
            raise HTTPException(status_code=400, detail="Party ID is required")

        # Convert formatted ID to numeric
        numeric_id = None
        if "P" in party_id:
            try:
                numeric_id = int(party_id.split("P")[-1])
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Party ID format")
        else:
            try:
                numeric_id = int(party_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Party ID")

        existing = party_table.get_item(Key={"PartyId": numeric_id}).get("Item")
        if not existing or is_item_deleted(existing):
            raise HTTPException(status_code=404, detail="Party not found")

        party_table.update_item(
            Key={"PartyId": numeric_id},
            UpdateExpression="SET deleted = :deleted",
            ExpressionAttributeValues={":deleted": True},
        )

        logger.info(f"Party {party_id} soft deleted successfully")
        return {"deleted": True}

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error deleting party {party_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error deleting party {party_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete party")