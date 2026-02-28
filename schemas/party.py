from pydantic import BaseModel
from typing import Optional


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