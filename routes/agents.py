import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError

from schemas.agents import Agent, AgentLightweight, CreateAgent, UpdateAgent
from utils.helpers import aws_error_detail, normalize_agent_item, get_next_agent_id
from db.dynamodb import agents_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get("/agents", response_model=List[Agent])
def list_agents():
    try:
        items = agents_table.scan().get("Items", [])
        return [normalize_agent_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@router.get("/agents/lightweight", response_model=List[AgentLightweight])
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


@router.get("/agents/{agent_id}", response_model=Agent)
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


@router.post("/agents", response_model=Agent)
def create_agent(payload: CreateAgent):
    try:
        agent_id = get_next_agent_id()

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
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")


@router.put("/agents/{agent_id}", response_model=Agent)
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
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")


@router.delete("/agents/{agent_id}")
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