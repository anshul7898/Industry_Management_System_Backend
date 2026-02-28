from pydantic import BaseModel
from typing import Optional


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