from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Union
from decimal import Decimal


class Product(BaseModel):
    """Product schema for orders"""
    ProductType: str = Field(..., min_length=1, description="Type of product (Stitching or Machine)")

    # ProductCategory is optional, only used when ProductType is 'Machine'
    ProductCategory: Optional[str] = Field(
        None,
        description="Product category (only for Machine type products: Leader Bag, D-Cut Bag, U-Cut Bag, Cake bag - old Pattern, Cake bag - New Pattern, Side Gaget Bag, Bottom Gaget Bag)"
    )

    # ProductId is optional for now
    ProductId: Optional[int] = Field(
        None, description="Product ID (optional for now)"
    )

    # ProductSize can be either int (for Stitching) or str (for Machine types)
    ProductSize: Union[int, str] = Field(..., description="Product size (integer for Stitching, string for Machine)")
    BagMaterial: str = Field(..., min_length=1, description="Material of the bag")
    Quantity: int = Field(..., ge=0, description="Quantity must be non-negative")
    SheetGSM: int = Field(..., gt=0, description="Sheet GSM must be positive")
    SheetColor: str = Field(..., min_length=1, description="Color of the sheet")
    BorderGSM: int = Field(..., gt=0, description="Border GSM must be positive")
    BorderColor: str = Field(..., min_length=1, description="Color of the border")
    HandleType: str = Field(..., min_length=1, description="Type of handle")
    HandleColor: str = Field(..., min_length=1, description="Color of the handle")
    HandleGSM: int = Field(..., gt=0, description="Handle GSM must be positive")
    PrintingType: str = Field(..., min_length=1, description="Type of printing")
    PrintColor: str = Field(..., min_length=1, description="Color for printing")
    Color: Optional[str] = Field(None, description="Main color")
    Design: bool = Field(False, description="Whether product has design")
    PlateBlockNumber: Optional[str] = Field(None, description="Plate block number (Single/Double/Multi)")
    PlateAvailable: bool = Field(False, description="Whether plate is available")
    Rate: float = Field(..., gt=0, description="Rate must be positive")
    ProductAmount: float = Field(..., ge=0, description="Product amount (Rate × Quantity)")

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    @field_validator('ProductId', mode='before')
    @classmethod
    def coerce_empty_product_id_to_none(cls, v):
        """If frontend sends "" for an optional numeric field, convert it to None."""
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator('ProductCategory', mode='before')
    @classmethod
    def coerce_empty_product_category_to_none(cls, v):
        """If frontend sends "" for ProductCategory, convert it to None."""
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator('ProductSize', mode='before')
    @classmethod
    def coerce_product_size(cls, v):
        """ProductSize can be int (for Stitching) or str (for Machine types)."""
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            try:
                return int(v)
            except ValueError:
                return v
        return v

    @field_validator('Rate', 'ProductAmount', mode='before')
    @classmethod
    def convert_decimal_to_float(cls, v):
        """Convert Decimal to float if needed"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('PlateBlockNumber', mode='before')
    @classmethod
    def coerce_plate_block_number_to_str(cls, v):
        """Convert legacy integer values stored in DynamoDB to string"""
        if v is None:
            return None
        return str(v)


class Order(BaseModel):
    """Order response model with products array"""
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
    Products: List[Product] = Field(default_factory=list, description="List of products in the order")
    TotalAmount: float = Field(default=0, ge=0, description="Total amount of the order")

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    @field_validator('TotalAmount', mode='before')
    @classmethod
    def convert_total_decimal_to_float(cls, v):
        """Convert Decimal to float if needed"""
        if isinstance(v, Decimal):
            return float(v)
        return v


class BaseOrderModel(BaseModel):
    """Base model for order creation and updates"""
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
    Products: List[Product] = Field(..., min_length=1, description="At least one product is required")
    TotalAmount: float = Field(..., ge=0, description="Total amount of the order")

    model_config = ConfigDict(extra='allow', populate_by_name=True)


class CreateOrder(BaseOrderModel):
    """Model for creating a new order with multiple products"""
    pass


class UpdateOrder(BaseOrderModel):
    """Model for updating an existing order with multiple products"""
    pass