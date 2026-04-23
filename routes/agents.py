import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
from pydantic import ValidationError

from schemas.agents import Agent, AgentLightweight, CreateAgent, UpdateAgent
from utils.helpers import aws_error_detail, normalize_agent_item, get_next_agent_id
from utils.dynamodb_utils import filter_deleted_items, is_item_deleted
from db.dynamodb import agents_table

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


@router.get("/agents", response_model=List[Agent])
def list_agents():
    try:
        items = filter_deleted_items(agents_table.scan().get("Items", []))
        return [normalize_agent_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")


@router.get("/agents/lightweight", response_model=List[AgentLightweight])
def list_agents_lightweight():
    """
    Returns a lightweight list of all agents: just AgentId and Name.
    AgentId is formatted as string (e.g., "A01", "A02")
    """
    try:
        items = filter_deleted_items(agents_table.scan().get("Items", []))
        result = []
        for item in items:
            agent_id = item["AgentId"]
            if isinstance(agent_id, Decimal):
                agent_id = int(agent_id)
            # Format numeric ID to string (1 -> "A01")
            if isinstance(agent_id, int):
                agent_id = f"A{agent_id:02d}"
            name = item.get("Name")
            result.append(AgentLightweight(agentId=agent_id, name=name))
        return result
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error listing lightweight agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")


@router.get("/agents/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    try:
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID is required")

        # Convert formatted string ID back to numeric (e.g., "A01" -> 1)
        numeric_id = None
        if agent_id.startswith("A"):
            try:
                numeric_id = int(agent_id[1:])
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Agent ID format")
        else:
            try:
                numeric_id = int(agent_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Agent ID")

        resp = agents_table.get_item(Key={"AgentId": numeric_id})
        item = resp.get("Item")
        if not item or is_item_deleted(item):
            raise HTTPException(status_code=404, detail="Agent not found")
        return normalize_agent_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent")


@router.post("/agents", response_model=Agent)
def create_agent(payload: CreateAgent):
    try:
        # Validation is automatically done by Pydantic
        agent_id = get_next_agent_id()

        item = {
            "AgentId": agent_id,
            "Name": payload.name,
            "Mobile": payload.mobile,
            "Aadhar_Details": payload.aadhar_Details,
            "Address": payload.address,
            "deleted": False,
        }

        agents_table.put_item(Item=item)

        logger.info(f"Agent created successfully with ID: {agent_id}")
        return normalize_agent_item(item)

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error creating agent: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except ClientError as e:
        logger.error(f"Database error creating agent: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.put("/agents/{agent_id}", response_model=Agent)
def update_agent(agent_id: str, payload: UpdateAgent):
    try:
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID is required")

        # Convert formatted string ID back to numeric (e.g., "A01" -> 1)
        numeric_id = None
        if agent_id.startswith("A"):
            try:
                numeric_id = int(agent_id[1:])
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Agent ID format")
        else:
            try:
                numeric_id = int(agent_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Agent ID")

        # Check if agent exists
        existing = agents_table.get_item(Key={"AgentId": numeric_id}).get("Item")
        if not existing or is_item_deleted(existing):
            raise HTTPException(status_code=404, detail="Agent not found")

        # Validation is automatically done by Pydantic
        item = {
            "AgentId": numeric_id,
            "Name": payload.name,
            "Mobile": payload.mobile,
            "Aadhar_Details": payload.aadhar_Details,
            "Address": payload.address,
        }

        item["deleted"] = existing.get("deleted", False)
        agents_table.put_item(Item=item)

        logger.info(f"Agent {agent_id} updated successfully")
        return normalize_agent_item(item)

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error updating agent {agent_id}: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error updating agent {agent_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error updating agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):
    try:
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID is required")

        # Convert formatted string ID back to numeric (e.g., "A01" -> 1)
        numeric_id = None
        if agent_id.startswith("A"):
            try:
                numeric_id = int(agent_id[1:])
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid Agent ID format")
        else:
            try:
                numeric_id = int(agent_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Agent ID")

        existing = agents_table.get_item(Key={"AgentId": numeric_id}).get("Item")
        if not existing or is_item_deleted(existing):
            raise HTTPException(status_code=404, detail="Agent not found")

        agents_table.update_item(
            Key={"AgentId": numeric_id},
            UpdateExpression="SET deleted = :deleted",
            ExpressionAttributeValues={":deleted": True},
        )

        logger.info(f"Agent {agent_id} soft deleted successfully")
        return {"deleted": True}

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error deleting agent {agent_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")