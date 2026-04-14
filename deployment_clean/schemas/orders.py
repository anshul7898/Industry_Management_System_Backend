from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Union
from decimal import Decimal
from datetime import date
import re


class Product(BaseModel):
    """Product schema for orders"""
    ProductType: Optional[str] = Field(None, description="Type of product (Stitching or Machine)")

    ProductCategory: Optional[str] = Field(
        None,
        description="Product category (only for Machine type products)"
    )

    ProductId: Optional[int] = Field(None, description="Product ID (optional for now)")

    ProductSize: Optional[Union[int, str]] = Field(None, description="Product size (integer for Stitching, string for Machine)")
    BagMaterial: Optional[str] = Field(None, description="Material of the bag")
    Quantity: Optional[int] = Field(None, description="Quantity must be non-negative")

    # ── QuantityType — 'KG' or 'Pieces' ──────────────────────────────────────
    QuantityType: Optional[str] = Field(
        None,
        description="Unit of quantity measurement: 'KG' or 'Pieces'"
    )

    SheetGSM: Optional[int] = Field(None, description="Sheet GSM must be positive")
    SheetColor: Optional[str] = Field(None, description="Color of the sheet")

    RollSize: Optional[str] = Field(None, description="Roll size (from Roll_Size_Table)")

    BorderGSM: Optional[int] = Field(None, description="Border GSM (not required for Machine type)")
    BorderColor: Optional[str] = Field(None, description="Color of the border (not required for Machine type)")

    HandleType: Optional[str] = Field(None, description="Type of handle")
    HandleColor: Optional[str] = Field(None, description="Color of the handle")
    AlternativeHandleColor: Optional[str] = Field(None, description="Alternative handle color")
    HandleGSM: Optional[int] = Field(None, description="Handle GSM must be positive")
    PrintingType: Optional[str] = Field(None, description="Type of printing")
    PrintColor: Optional[str] = Field(None, description="Color for printing")
    Color: Optional[str] = Field(None, description="Main color")

    DesignType: Optional[str] = Field(None, description="Design type: 'Old' or 'New'")
    DesignStyle: Optional[str] = Field(None, description="Design style: 'Same Front/Back' or 'Different Front/Back'")

    PlateBlockNumber: Optional[str] = Field(None, description="Number of plates (1/2/3/4)")
    PlateType: Optional[str] = Field(None, description="Plate type: 'Old' or 'New'")
    PlateRate: Optional[float] = Field(None, description="Rate of the printing plate (optional)")

    Rate: Optional[float] = Field(None, description="Rate must be positive")
    ProductAmount: Optional[float] = Field(None, description="Product amount (calculated with GST)")

    FixAmount: Optional[float] = Field(None, description="Fixed amount charge for this product (optional)")

    # JobWorkRate — only applicable for KG quantity type ──────────────────────
    JobWorkRate: Optional[float] = Field(None, description="Job work rate charge for KG quantity type (optional)")

    # ── NEW: GST — percentage applied on (Quantity × Rate), one of 0, 5, 18 ──
    GST: Optional[float] = Field(None, description="GST percentage on (Quantity × Rate): 0, 5, or 18")

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

    # QuantityType validator ───────────────────────────────────────────────────
    @field_validator('QuantityType', mode='before')
    @classmethod
    def coerce_quantity_type(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, str) and v.strip() in ("KG", "Pieces"):
            return v.strip()
        return None

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

    @field_validator('FixAmount', mode='before')
    @classmethod
    def convert_fix_amount_to_float(cls, v):
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

    # JobWorkRate validator ────────────────────────────────────────────────────
    @field_validator('JobWorkRate', mode='before')
    @classmethod
    def convert_job_work_rate_to_float(cls, v):
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

    # ── NEW: GST validator ────────────────────────────────────────────────────
    @field_validator('GST', mode='before')
    @classmethod
    def convert_gst_to_float(cls, v):
        if v is None:
            return 0.0
        if isinstance(v, str) and v.strip() == "":
            return 0.0
        if isinstance(v, Decimal):
            val = float(v)
        else:
            try:
                val = float(v)
            except (TypeError, ValueError):
                return 0.0
        # Only allow 0, 5, or 18
        if val not in (0.0, 5.0, 18.0):
            return 0.0
        return val

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
    OrderId: Optional[int] = None
    AgentId: Optional[int] = None
    Party_Name: Optional[str] = None
    AliasOrCompanyName: Optional[str] = None
    Address: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Pincode: Optional[int] = None
    Contact_Person1: Optional[str] = None
    Contact_Person2: Optional[str] = None
    Mobile1: Optional[int] = None
    Mobile2: Optional[int] = None
    Email: Optional[str] = None

    BookingName: Optional[str] = Field(None, description="Booking name for dispatch")
    TransportName: Optional[str] = Field(None, description="Transport/courier name")
    DispatchContactNumber: Optional[str] = Field(None, description="Contact number for dispatch")
    Destination: Optional[str] = Field(None, description="Dispatch destination")

    Carting: Optional[float] = Field(None, description="Carting charges (optional)")

    Products: List[Product] = Field(default_factory=list, description="List of products in the order")

    TotalAmount: Optional[float] = Field(None, description="Total amount of the order")

    OrderStatus: str = Field(default="ToDo", description="Order status: 'ToDo', 'In-Progress', or 'Done'")

    OrderStartDate: Optional[date] = Field(None, description="Order start date (defaults to today's date)")

    OrderEndDate: Optional[date] = Field(None, description="Order end date (blank by default, auto-calculated when status is 'Done')")

    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    @field_validator('TotalAmount', mode='before')
    @classmethod
    def convert_total_decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v

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

    @field_validator('OrderStatus', mode='before')
    @classmethod
    def validate_order_status(cls, v):
        if v is None:
            return "ToDo"
        if isinstance(v, str) and v.strip() == "":
            return "ToDo"
        status = v.strip() if isinstance(v, str) else str(v)
        valid_statuses = ("ToDo", "In-Progress", "Done")
        if status in valid_statuses:
            return status
        return "ToDo"

    @field_validator('OrderStartDate', mode='before')
    @classmethod
    def validate_order_start_date(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                return None
        return None

    @field_validator('OrderEndDate', mode='before')
    @classmethod
    def validate_order_end_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                return None
        return None


class BaseOrderModel(BaseModel):
    """Base model for order creation and updates"""
    AgentId: Optional[int] = Field(None, description="Agent ID")
    Party_Name: Optional[str] = Field(None, max_length=255)
    AliasOrCompanyName: Optional[str] = Field(None, max_length=255, description="Alias or company name (optional)")
    Address: Optional[str] = Field(None, max_length=255, description="Address (optional)")
    City: Optional[str] = Field(None, max_length=100)
    State: Optional[str] = Field(None, max_length=100)
    Pincode: Optional[int] = Field(None, description="Pincode must be 6 digits if provided (optional)")
    Contact_Person1: Optional[str] = Field(None, max_length=255)
    Contact_Person2: Optional[str] = Field(None, max_length=255)
    Mobile1: Optional[int] = Field(None, description="Mobile must be 10 digits")
    Mobile2: Optional[int] = Field(None)
    Email: Optional[str] = Field(None, max_length=255)

    BookingName: Optional[str] = Field(None, max_length=255)
    TransportName: Optional[str] = Field(None, max_length=255)
    DispatchContactNumber: Optional[str] = Field(None, max_length=20)
    Destination: Optional[str] = Field(None, max_length=255)

    Carting: Optional[float] = Field(None, description="Carting charges (optional)")

    Products: List[Product] = Field(default_factory=list, description="List of products in the order")

    TotalAmount: Optional[float] = Field(None, description="Total amount of the order")

    OrderStatus: str = Field(default="ToDo", description="Order status: 'ToDo', 'In-Progress', or 'Done'")

    OrderStartDate: Optional[date] = Field(None, description="Order start date (defaults to today's date)")

    OrderEndDate: Optional[date] = Field(None, description="Order end date (blank by default, auto-calculated when status is 'Done')")

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

    @field_validator('OrderStatus', mode='before')
    @classmethod
    def validate_order_status_base(cls, v):
        if v is None:
            return "ToDo"
        if isinstance(v, str) and v.strip() == "":
            return "ToDo"
        status = v.strip() if isinstance(v, str) else str(v)
        valid_statuses = ("ToDo", "In-Progress", "Done")
        if status in valid_statuses:
            return status
        return "ToDo"

    @field_validator('OrderStartDate', mode='before')
    @classmethod
    def validate_order_start_date_base(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                return None
        return None

    @field_validator('OrderEndDate', mode='before')
    @classmethod
    def validate_order_end_date_base(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                return None
        return None


class CreateOrder(BaseOrderModel):
    pass


class UpdateOrder(BaseOrderModel):
    pass