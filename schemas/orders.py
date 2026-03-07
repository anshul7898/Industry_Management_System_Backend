from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class Order(BaseModel):
    OrderId: int
    AgentId: int
    Party_Name: str
    AliasOrCompanyName: str
    Address: str
    City: str
    State: str
    Pincode: int
    Contact_Person1: str
    Contact_Person2: Optional[str] = None
    Mobile1: Optional[int] = None
    Mobile2: Optional[int] = None
    Email: Optional[str] = None
    ProductType: str
    ProductId: int
    ProductSize: int
    BagMaterial: str
    Quantity: int
    SheetGSM: int
    SheetColor: str
    BorderGSM: int
    BorderColor: str
    HandleType: str
    HandleColor: str
    HandleGSM: int
    PrintingType: str
    PrintColor: str
    Color: str
    Design: bool = False
    PlateBlockNumber: Optional[int] = None
    PlateAvailable: bool = False
    Rate: float
    TotalAmount: float

    model_config = ConfigDict(extra='allow', populate_by_name=True)


class BaseOrderModel(BaseModel):
    AgentId: int = Field(..., gt=0, description="Agent ID must be positive")
    Party_Name: str = Field(..., min_length=1, max_length=255)
    AliasOrCompanyName: str = Field(..., min_length=1, max_length=255)
    Address: str = Field(..., min_length=1, max_length=255)
    City: str = Field(..., min_length=1, max_length=100)
    State: str = Field(..., min_length=1, max_length=100)
    Pincode: int = Field(..., ge=100000, le=999999, description="Pincode must be 6 digits")
    Contact_Person1: str = Field(..., min_length=1, max_length=255)
    Contact_Person2: Optional[str] = Field(None, max_length=255)
    Mobile1: int = Field(..., ge=1000000000, le=9999999999, description="Mobile must be 10 digits")
    Mobile2: Optional[int] = Field(None, ge=1000000000, le=9999999999)
    Email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    ProductType: str
    ProductId: int = Field(..., gt=0)
    ProductSize: int = Field(..., gt=0)
    BagMaterial: str
    Quantity: int = Field(..., ge=0)
    SheetGSM: int
    SheetColor: str
    BorderGSM: int
    BorderColor: str
    HandleType: str
    HandleColor: str
    HandleGSM: int
    PrintingType: str
    PrintColor: str
    Color: str
    Design: bool = Field(False, description="Whether product has design")
    PlateBlockNumber: Optional[int] = Field(None, ge=0)
    PlateAvailable: bool = Field(False, description="Whether plate is available")
    Rate: float = Field(..., gt=0)
    TotalAmount: float = Field(..., ge=0)

    model_config = ConfigDict(extra='allow', populate_by_name=True)


class CreateOrder(BaseOrderModel):
    """Model for creating a new order"""
    pass


class UpdateOrder(BaseOrderModel):
    """Model for updating an existing order"""
    pass