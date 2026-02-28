from pydantic import BaseModel
from typing import Optional


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