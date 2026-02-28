from pydantic import BaseModel
from typing import Optional


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