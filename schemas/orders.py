from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Union
from decimal import Decimal
import re


class Product(BaseModel):
    """Product schema for orders"""
    ProductType: str = Field(..., min_length=1, description="Type of product (Stitching or Machine)")

    ProductCategory: Optional[str] = Field(
        None,
        description="Product category (only for Machine type products)"
    )

    ProductId: Optional[int] = Field(
        None, description="Product ID (optional for now)"
    )

    ProductSize: Union[int, str] = Field(..., description="Product size (integer for Stitching, string for Machine)")
    BagMaterial: str = Field(..., min_length=1, description="Material of the bag")
    Quantity: int = Field(..., ge=0, description="Quantity must be non-negative")
    SheetGSM: int = Field(..., gt=0, description="Sheet GSM must be positive")
    SheetColor: str = Field(..., min_length=1, description="Color of the sheet")

    RollSize: Optional[str] = Field(None, description="Roll size (from Roll_Size_Table)")

    BorderGSM: Optional[int] = Field(None, description="Border GSM (not required for Machine type)")
    BorderColor: Optional[str] = Field(None, description="Color of the border (not required for Machine type)")

    HandleType: str = Field(..., min_length=1, description="Type of handle")
    HandleColor: str = Field(..., min_length=1, description="Color of the handle")
    HandleGSM: int = Field(..., gt=0, description="Handle GSM must be positive")
    PrintingType: str = Field(..., min_length=1, description="Type of printing")
    PrintColor: str = Field(..., min_length=1, description="Color for printing")
    Color: Optional[str] = Field(None, description="Main color")

    DesignType: Optional[str] = Field(None, description="Design type: 'Old' or 'New'")
    DesignStyle: Optional[str] = Field(None, description="Design style: 'Same Front/Back' or 'Different Front/Back'")

    PlateBlockNumber: Optional[str] = Field(None, description="Number of plates (1/2/3/4)")
    PlateType: Optional[str] = Field(None, description="Plate type: 'Old' or 'New'")
    PlateRate: Optional[float] = Field(None, ge=0, description="Rate of the printing plate (optional)")

    Rate: float = Field(..., gt=0, description="Rate must be positive")
    ProductAmount: float = Field(..., ge=0, description="Product amount (Rate × Quantity)")

    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    @field_validator('ProductId', mode='before')
    @classmethod
    def coerce_empty_product_id_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator('ProductCategory', mode='before')
    @classmethod
    def coerce_empty_product_category_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator('ProductSize', mode='before')
    @classmethod
    def coerce_product_size(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            try:
                return int(v)
            except ValueError:
                return v
        return v

    @field_validator('RollSize', mode='before')
    @classmethod
    def coerce_roll_size(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return str(v).strip()

    @field_validator('Rate', 'ProductAmount', mode='before')
    @classmethod
    def convert_decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('PlateRate', mode='before')
    @classmethod
    def convert_plate_rate_to_float(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, Decimal):
            return float(v)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @field_validator('PlateBlockNumber', mode='before')
    @classmethod
    def coerce_plate_block_number_to_str(cls, v):
        if v is None:
            return None
        return str(v)

    @field_validator('PlateType', mode='before')
    @classmethod
    def coerce_plate_type(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, str) and v.strip() in ("Old", "New"):
            return v.strip()
        return None

    @field_validator('DesignType', mode='before')
    @classmethod
    def coerce_design_type(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, str) and v.strip() in ("Old", "New"):
            return v.strip()
        return None

    @field_validator('DesignStyle', mode='before')
    @classmethod
    def coerce_design_style(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, str) and v.strip() in ("Same Front/Back", "Different Front/Back"):
            return v.strip()
        return None

    @field_validator('BorderColor', mode='before')
    @classmethod
    def coerce_empty_border_color_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator('BorderGSM', mode='before')
    @classmethod
    def coerce_empty_border_gsm_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if v == 0:
            return None
        return v


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

    BookingName: Optional[str] = Field(None, description="Booking name for dispatch")
    TransportName: Optional[str] = Field(None, description="Transport/courier name")
    DispatchContactNumber: Optional[str] = Field(None, description="Contact number for dispatch")
    Destination: Optional[str] = Field(None, description="Dispatch destination")

    # ── NEW: Carting charges ──────────────────────────────────────
    Carting: Optional[float] = Field(None, ge=0, description="Carting charges (optional)")

    Products: List[Product] = Field(default_factory=list, description="List of products in the order")
    TotalAmount: float = Field(default=0, ge=0, description="Total amount of the order")

    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    @field_validator('TotalAmount', mode='before')
    @classmethod
    def convert_total_decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v

    # ── NEW: Carting validator ────────────────────────────────────
    @field_validator('Carting', mode='before')
    @classmethod
    def convert_carting_to_float(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, Decimal):
            return float(v)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


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
    Email: Optional[str] = Field(None, max_length=255)

    BookingName: Optional[str] = Field(None, max_length=255)
    TransportName: Optional[str] = Field(None, max_length=255)
    DispatchContactNumber: Optional[str] = Field(None, max_length=20)
    Destination: Optional[str] = Field(None, max_length=255)

    # ── NEW: Carting charges ──────────────────────────────────────
    Carting: Optional[float] = Field(None, ge=0, description="Carting charges (optional)")

    Products: List[Product] = Field(..., min_length=1, description="At least one product is required")
    TotalAmount: float = Field(..., ge=0, description="Total amount of the order")

    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    @field_validator('Email', mode='before')
    @classmethod
    def validate_optional_email(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, str(v)):
            raise ValueError('Please enter a valid email address (e.g., user@example.com)')
        return v

    @field_validator('DispatchContactNumber', mode='before')
    @classmethod
    def coerce_dispatch_contact_number(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str) and v.strip() == "":
            return None
        return str(v).strip()

    # ── NEW: Carting validator ────────────────────────────────────
    @field_validator('Carting', mode='before')
    @classmethod
    def coerce_carting_to_float(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, Decimal):
            return float(v)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class CreateOrder(BaseOrderModel):
    pass


class UpdateOrder(BaseOrderModel):
    pass