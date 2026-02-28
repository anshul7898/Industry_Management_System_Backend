from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

# Valid dropdown options - MUST match frontend options
VALID_PRODUCT_TYPES = {
    'Shopping Bag', 'Grocery Bag', 'Provisions Bag'
}

VALID_BAG_MATERIALS = {
    'Cotton Canvas', 'Jute', 'Organic Cotton', 'Recycled Polyester', 'Linen', 'Cotton Blend'
}

VALID_HANDLE_TYPES = {
    'Double Stitched Cotton Rope', 'Single Stitched Cotton Rope',
    'Web Handle', 'Twisted Handle', 'Braided Handle', 'Ribbon Handle'
}

VALID_PRINTING_TYPES = {
    'Screen Printing', 'Digital Printing', 'Flexography',
    'Offset Printing', 'Embroidery', 'Stamping'
}

VALID_SHEET_COLORS = {
    'Natural White', 'Off White', 'Beige', 'Cream', 'Brown', 'Maroon', 'Kraft'
}

VALID_BORDER_COLORS = {
    'Black', 'Brown', 'Gold', 'Maroon', 'Navy Blue', 'White', 'Gray', 'Red'
}

VALID_HANDLE_COLORS = {
    'Beige', 'Black', 'Brown', 'Cream', 'Gold', 'Maroon', 'Navy Blue', 'Red', 'White'
}

VALID_COLORS = {
    'White', 'Black', 'Beige', 'Cream', 'Brown', 'Gold', 'Maroon', 'Navy Blue', 'Red', 'Green', 'Gray'
}

VALID_PRINT_COLORS = {
    'Navy Blue', 'Black', 'White', 'Red', 'Gold', 'Silver', 'Green', 'Brown', 'Maroon'
}

VALID_SHEET_GSMS = {200, 250, 300, 350, 400, 450, 500}
VALID_BORDER_GSMS = {50, 75, 90, 100, 120, 150}
VALID_HANDLE_GSMS = {100, 120, 150, 180, 200}


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
    Mobile1: Optional[int] = None  # Changed to Optional
    Mobile2: Optional[int] = None
    Email: Optional[str] = None  # Changed to Optional
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
    Mobile1: int = Field(..., ge=1000000000, le=9999999999, description="Mobile must be 10 digits")  # Keep required for new orders
    Mobile2: Optional[int] = Field(None, ge=1000000000, le=9999999999)
    Email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')  # Keep required for new orders
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

    @field_validator('ProductType')
    @classmethod
    def validate_product_type(cls, v):
        if v not in VALID_PRODUCT_TYPES:
            raise ValueError(
                f"Invalid ProductType '{v}'. Must be one of: {', '.join(sorted(VALID_PRODUCT_TYPES))}"
            )
        return v

    @field_validator('BagMaterial')
    @classmethod
    def validate_bag_material(cls, v):
        if v not in VALID_BAG_MATERIALS:
            raise ValueError(
                f"Invalid BagMaterial '{v}'. Must be one of: {', '.join(sorted(VALID_BAG_MATERIALS))}"
            )
        return v

    @field_validator('HandleType')
    @classmethod
    def validate_handle_type(cls, v):
        if v not in VALID_HANDLE_TYPES:
            raise ValueError(
                f"Invalid HandleType '{v}'. Must be one of: {', '.join(sorted(VALID_HANDLE_TYPES))}"
            )
        return v

    @field_validator('PrintingType')
    @classmethod
    def validate_printing_type(cls, v):
        if v not in VALID_PRINTING_TYPES:
            raise ValueError(
                f"Invalid PrintingType '{v}'. Must be one of: {', '.join(sorted(VALID_PRINTING_TYPES))}"
            )
        return v

    @field_validator('SheetColor')
    @classmethod
    def validate_sheet_color(cls, v):
        if v not in VALID_SHEET_COLORS:
            raise ValueError(
                f"Invalid SheetColor '{v}'. Must be one of: {', '.join(sorted(VALID_SHEET_COLORS))}"
            )
        return v

    @field_validator('BorderColor')
    @classmethod
    def validate_border_color(cls, v):
        if v not in VALID_BORDER_COLORS:
            raise ValueError(
                f"Invalid BorderColor '{v}'. Must be one of: {', '.join(sorted(VALID_BORDER_COLORS))}"
            )
        return v

    @field_validator('HandleColor')
    @classmethod
    def validate_handle_color(cls, v):
        if v not in VALID_HANDLE_COLORS:
            raise ValueError(
                f"Invalid HandleColor '{v}'. Must be one of: {', '.join(sorted(VALID_HANDLE_COLORS))}"
            )
        return v

    @field_validator('Color')
    @classmethod
    def validate_color(cls, v):
        if v not in VALID_COLORS:
            raise ValueError(
                f"Invalid Color '{v}'. Must be one of: {', '.join(sorted(VALID_COLORS))}"
            )
        return v

    @field_validator('PrintColor')
    @classmethod
    def validate_print_color(cls, v):
        if v not in VALID_PRINT_COLORS:
            raise ValueError(
                f"Invalid PrintColor '{v}'. Must be one of: {', '.join(sorted(VALID_PRINT_COLORS))}"
            )
        return v

    @field_validator('SheetGSM', mode='before')
    @classmethod
    def validate_sheet_gsm(cls, v):
        v = int(v)
        if v not in VALID_SHEET_GSMS:
            raise ValueError(
                f"Invalid SheetGSM '{v}'. Must be one of: {', '.join(map(str, sorted(VALID_SHEET_GSMS)))}"
            )
        return v

    @field_validator('BorderGSM', mode='before')
    @classmethod
    def validate_border_gsm(cls, v):
        v = int(v)
        if v not in VALID_BORDER_GSMS:
            raise ValueError(
                f"Invalid BorderGSM '{v}'. Must be one of: {', '.join(map(str, sorted(VALID_BORDER_GSMS)))}"
            )
        return v

    @field_validator('HandleGSM', mode='before')
    @classmethod
    def validate_handle_gsm(cls, v):
        v = int(v)
        if v not in VALID_HANDLE_GSMS:
            raise ValueError(
                f"Invalid HandleGSM '{v}'. Must be one of: {', '.join(map(str, sorted(VALID_HANDLE_GSMS)))}"
            )
        return v


class CreateOrder(BaseOrderModel):
    """Model for creating a new order"""
    pass


class UpdateOrder(BaseOrderModel):
    """Model for updating an existing order"""
    pass