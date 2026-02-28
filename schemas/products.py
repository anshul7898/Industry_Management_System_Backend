from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Valid dropdown options
VALID_BAG_MATERIALS = {
    'Cotton Canvas', 'Jute', 'Organic Cotton', 'Recycled Polyester', 'Linen'
}

VALID_SHEET_COLORS = {
    'Natural White', 'Off White', 'Cream', 'Brown', 'Kraft'
}

VALID_BORDER_COLORS = {
    'Black', 'Brown', 'Navy Blue', 'White', 'Gray', 'Red'
}

VALID_HANDLE_TYPES = {
    'Double Stitched Cotton Rope', 'Single Stitched Cotton Rope',
    'Web Handle', 'Twisted Handle', 'Braided Handle'
}

VALID_HANDLE_COLORS = {
    'Beige', 'Black', 'Brown', 'White', 'Navy Blue', 'Red'
}

VALID_COLORS = {
    'White', 'Black', 'Cream', 'Brown', 'Navy Blue', 'Red', 'Green', 'Gray'
}

VALID_PRINTING_TYPES = {
    'Screen Printing', 'Digital Printing', 'Flexography',
    'Offset Printing', 'Embroidery'
}

VALID_PRINT_COLORS = {
    'Navy Blue', 'Black', 'White', 'Red', 'Gold', 'Silver', 'Green', 'Brown'
}

VALID_SHEET_GSMS = {200, 250, 300, 350, 400, 450, 500}
VALID_BORDER_GSMS = {50, 75, 90, 100, 120, 150}
VALID_HANDLE_GSMS = {100, 120, 150, 180, 200}


class Product(BaseModel):
    productId: int
    productType: Optional[str] = None
    productSize: Optional[float] = None
    bagMaterial: Optional[str] = None
    quantity: Optional[float] = None
    sheetGSM: Optional[float] = None
    sheetColor: Optional[str] = None
    borderGSM: Optional[float] = None
    borderColor: Optional[str] = None
    handleType: Optional[str] = None
    handleColor: Optional[str] = None
    handleGSM: Optional[float] = None
    printingType: Optional[str] = None
    printColor: Optional[str] = None
    color: Optional[str] = None
    design: Optional[bool] = False
    plateBlockNumber: Optional[float] = None
    plateAvailable: Optional[bool] = False
    rate: Optional[float] = None


class CreateProduct(BaseModel):
    productType: str = Field(..., min_length=1, max_length=255, description="Product type")
    productSize: float = Field(..., gt=0, description="Product size must be greater than 0")
    bagMaterial: str = Field(..., description="Bag material from predefined options")
    quantity: float = Field(..., ge=0, description="Quantity must be non-negative")
    sheetGSM: float = Field(..., description="Sheet GSM from predefined options")
    sheetColor: str = Field(..., description="Sheet color from predefined options")
    borderGSM: float = Field(..., description="Border GSM from predefined options")
    borderColor: str = Field(..., description="Border color from predefined options")
    handleType: str = Field(..., description="Handle type from predefined options")
    handleColor: str = Field(..., description="Handle color from predefined options")
    handleGSM: float = Field(..., description="Handle GSM from predefined options")
    printingType: str = Field(..., description="Printing type from predefined options")
    printColor: str = Field(..., description="Print color from predefined options")
    color: str = Field(..., description="Color from predefined options")
    design: bool = Field(False, description="Whether product has design")
    plateBlockNumber: float = Field(default=0, ge=0, description="Plate block number must be non-negative")
    plateAvailable: bool = Field(False, description="Whether plate is available")
    rate: float = Field(..., gt=0, description="Rate must be greater than 0")

    @field_validator('productType')
    @classmethod
    def validate_product_type(cls, v):
        """Validate product type"""
        if not v or not v.strip():
            raise ValueError("Product type cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Product type must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Product type cannot exceed 255 characters")

        return v.strip()

    @field_validator('productSize')
    @classmethod
    def validate_product_size(cls, v):
        """Validate product size"""
        if v is None or v <= 0:
            raise ValueError("Product size must be greater than 0")

        if v > 10000:
            raise ValueError("Product size seems too large (max 10000)")

        return float(v)

    @field_validator('bagMaterial')
    @classmethod
    def validate_bag_material(cls, v):
        """Validate bag material from predefined options"""
        if not v or not v.strip():
            raise ValueError("Bag material cannot be empty")

        if v.strip() not in VALID_BAG_MATERIALS:
            raise ValueError(
                f"Invalid bag material. Must be one of: {', '.join(sorted(VALID_BAG_MATERIALS))}"
            )

        return v.strip()

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validate quantity"""
        if v is None or v < 0:
            raise ValueError("Quantity must be non-negative")

        if v > 10000000:
            raise ValueError("Quantity seems too large (max 10,000,000)")

        return float(v)

    @field_validator('sheetGSM')
    @classmethod
    def validate_sheet_gsm(cls, v):
        """Validate sheet GSM from predefined options"""
        if v is None:
            raise ValueError("Sheet GSM is required")

        if float(v) not in VALID_SHEET_GSMS:
            raise ValueError(
                f"Invalid sheet GSM. Must be one of: {', '.join(map(str, sorted(VALID_SHEET_GSMS)))}"
            )

        return float(v)

    @field_validator('sheetColor')
    @classmethod
    def validate_sheet_color(cls, v):
        """Validate sheet color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Sheet color cannot be empty")

        if v.strip() not in VALID_SHEET_COLORS:
            raise ValueError(
                f"Invalid sheet color. Must be one of: {', '.join(sorted(VALID_SHEET_COLORS))}"
            )

        return v.strip()

    @field_validator('borderGSM')
    @classmethod
    def validate_border_gsm(cls, v):
        """Validate border GSM from predefined options"""
        if v is None:
            raise ValueError("Border GSM is required")

        if float(v) not in VALID_BORDER_GSMS:
            raise ValueError(
                f"Invalid border GSM. Must be one of: {', '.join(map(str, sorted(VALID_BORDER_GSMS)))}"
            )

        return float(v)

    @field_validator('borderColor')
    @classmethod
    def validate_border_color(cls, v):
        """Validate border color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Border color cannot be empty")

        if v.strip() not in VALID_BORDER_COLORS:
            raise ValueError(
                f"Invalid border color. Must be one of: {', '.join(sorted(VALID_BORDER_COLORS))}"
            )

        return v.strip()

    @field_validator('handleType')
    @classmethod
    def validate_handle_type(cls, v):
        """Validate handle type from predefined options"""
        if not v or not v.strip():
            raise ValueError("Handle type cannot be empty")

        if v.strip() not in VALID_HANDLE_TYPES:
            raise ValueError(
                f"Invalid handle type. Must be one of: {', '.join(sorted(VALID_HANDLE_TYPES))}"
            )

        return v.strip()

    @field_validator('handleColor')
    @classmethod
    def validate_handle_color(cls, v):
        """Validate handle color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Handle color cannot be empty")

        if v.strip() not in VALID_HANDLE_COLORS:
            raise ValueError(
                f"Invalid handle color. Must be one of: {', '.join(sorted(VALID_HANDLE_COLORS))}"
            )

        return v.strip()

    @field_validator('handleGSM')
    @classmethod
    def validate_handle_gsm(cls, v):
        """Validate handle GSM from predefined options"""
        if v is None:
            raise ValueError("Handle GSM is required")

        if float(v) not in VALID_HANDLE_GSMS:
            raise ValueError(
                f"Invalid handle GSM. Must be one of: {', '.join(map(str, sorted(VALID_HANDLE_GSMS)))}"
            )

        return float(v)

    @field_validator('printingType')
    @classmethod
    def validate_printing_type(cls, v):
        """Validate printing type from predefined options"""
        if not v or not v.strip():
            raise ValueError("Printing type cannot be empty")

        if v.strip() not in VALID_PRINTING_TYPES:
            raise ValueError(
                f"Invalid printing type. Must be one of: {', '.join(sorted(VALID_PRINTING_TYPES))}"
            )

        return v.strip()

    @field_validator('printColor')
    @classmethod
    def validate_print_color(cls, v):
        """Validate print color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Print color cannot be empty")

        if v.strip() not in VALID_PRINT_COLORS:
            raise ValueError(
                f"Invalid print color. Must be one of: {', '.join(sorted(VALID_PRINT_COLORS))}"
            )

        return v.strip()

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Color cannot be empty")

        if v.strip() not in VALID_COLORS:
            raise ValueError(
                f"Invalid color. Must be one of: {', '.join(sorted(VALID_COLORS))}"
            )

        return v.strip()

    @field_validator('plateBlockNumber')
    @classmethod
    def validate_plate_block_number(cls, v):
        """Validate plate block number"""
        if v is None:
            v = 0

        if v < 0:
            raise ValueError("Plate block number must be non-negative")

        if v > 1000:
            raise ValueError("Plate block number seems too large (max 1000)")

        return float(v)

    @field_validator('rate')
    @classmethod
    def validate_rate(cls, v):
        """Validate rate"""
        if v is None or v <= 0:
            raise ValueError("Rate must be greater than 0")

        if v > 1000000:
            raise ValueError("Rate seems too large (max 1,000,000)")

        # Validate decimal places (max 2 for currency)
        if len(str(v).split('.')[-1]) > 2 and '.' in str(v):
            raise ValueError("Rate can have maximum 2 decimal places")

        return float(v)


class UpdateProduct(BaseModel):
    productType: str = Field(..., min_length=1, max_length=255, description="Product type")
    productSize: float = Field(..., gt=0, description="Product size must be greater than 0")
    bagMaterial: str = Field(..., description="Bag material from predefined options")
    quantity: float = Field(..., ge=0, description="Quantity must be non-negative")
    sheetGSM: float = Field(..., description="Sheet GSM from predefined options")
    sheetColor: str = Field(..., description="Sheet color from predefined options")
    borderGSM: float = Field(..., description="Border GSM from predefined options")
    borderColor: str = Field(..., description="Border color from predefined options")
    handleType: str = Field(..., description="Handle type from predefined options")
    handleColor: str = Field(..., description="Handle color from predefined options")
    handleGSM: float = Field(..., description="Handle GSM from predefined options")
    printingType: str = Field(..., description="Printing type from predefined options")
    printColor: str = Field(..., description="Print color from predefined options")
    color: str = Field(..., description="Color from predefined options")
    design: bool = Field(False, description="Whether product has design")
    plateBlockNumber: float = Field(default=0, ge=0, description="Plate block number must be non-negative")
    plateAvailable: bool = Field(False, description="Whether plate is available")
    rate: float = Field(..., gt=0, description="Rate must be greater than 0")

    @field_validator('productType')
    @classmethod
    def validate_product_type(cls, v):
        """Validate product type"""
        if not v or not v.strip():
            raise ValueError("Product type cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Product type must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Product type cannot exceed 255 characters")

        return v.strip()

    @field_validator('productSize')
    @classmethod
    def validate_product_size(cls, v):
        """Validate product size"""
        if v is None or v <= 0:
            raise ValueError("Product size must be greater than 0")

        if v > 10000:
            raise ValueError("Product size seems too large (max 10000)")

        return float(v)

    @field_validator('bagMaterial')
    @classmethod
    def validate_bag_material(cls, v):
        """Validate bag material from predefined options"""
        if not v or not v.strip():
            raise ValueError("Bag material cannot be empty")

        if v.strip() not in VALID_BAG_MATERIALS:
            raise ValueError(
                f"Invalid bag material. Must be one of: {', '.join(sorted(VALID_BAG_MATERIALS))}"
            )

        return v.strip()

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validate quantity"""
        if v is None or v < 0:
            raise ValueError("Quantity must be non-negative")

        if v > 10000000:
            raise ValueError("Quantity seems too large (max 10,000,000)")

        return float(v)

    @field_validator('sheetGSM')
    @classmethod
    def validate_sheet_gsm(cls, v):
        """Validate sheet GSM from predefined options"""
        if v is None:
            raise ValueError("Sheet GSM is required")

        if float(v) not in VALID_SHEET_GSMS:
            raise ValueError(
                f"Invalid sheet GSM. Must be one of: {', '.join(map(str, sorted(VALID_SHEET_GSMS)))}"
            )

        return float(v)

    @field_validator('sheetColor')
    @classmethod
    def validate_sheet_color(cls, v):
        """Validate sheet color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Sheet color cannot be empty")

        if v.strip() not in VALID_SHEET_COLORS:
            raise ValueError(
                f"Invalid sheet color. Must be one of: {', '.join(sorted(VALID_SHEET_COLORS))}"
            )

        return v.strip()

    @field_validator('borderGSM')
    @classmethod
    def validate_border_gsm(cls, v):
        """Validate border GSM from predefined options"""
        if v is None:
            raise ValueError("Border GSM is required")

        if float(v) not in VALID_BORDER_GSMS:
            raise ValueError(
                f"Invalid border GSM. Must be one of: {', '.join(map(str, sorted(VALID_BORDER_GSMS)))}"
            )

        return float(v)

    @field_validator('borderColor')
    @classmethod
    def validate_border_color(cls, v):
        """Validate border color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Border color cannot be empty")

        if v.strip() not in VALID_BORDER_COLORS:
            raise ValueError(
                f"Invalid border color. Must be one of: {', '.join(sorted(VALID_BORDER_COLORS))}"
            )

        return v.strip()

    @field_validator('handleType')
    @classmethod
    def validate_handle_type(cls, v):
        """Validate handle type from predefined options"""
        if not v or not v.strip():
            raise ValueError("Handle type cannot be empty")

        if v.strip() not in VALID_HANDLE_TYPES:
            raise ValueError(
                f"Invalid handle type. Must be one of: {', '.join(sorted(VALID_HANDLE_TYPES))}"
            )

        return v.strip()

    @field_validator('handleColor')
    @classmethod
    def validate_handle_color(cls, v):
        """Validate handle color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Handle color cannot be empty")

        if v.strip() not in VALID_HANDLE_COLORS:
            raise ValueError(
                f"Invalid handle color. Must be one of: {', '.join(sorted(VALID_HANDLE_COLORS))}"
            )

        return v.strip()

    @field_validator('handleGSM')
    @classmethod
    def validate_handle_gsm(cls, v):
        """Validate handle GSM from predefined options"""
        if v is None:
            raise ValueError("Handle GSM is required")

        if float(v) not in VALID_HANDLE_GSMS:
            raise ValueError(
                f"Invalid handle GSM. Must be one of: {', '.join(map(str, sorted(VALID_HANDLE_GSMS)))}"
            )

        return float(v)

    @field_validator('printingType')
    @classmethod
    def validate_printing_type(cls, v):
        """Validate printing type from predefined options"""
        if not v or not v.strip():
            raise ValueError("Printing type cannot be empty")

        if v.strip() not in VALID_PRINTING_TYPES:
            raise ValueError(
                f"Invalid printing type. Must be one of: {', '.join(sorted(VALID_PRINTING_TYPES))}"
            )

        return v.strip()

    @field_validator('printColor')
    @classmethod
    def validate_print_color(cls, v):
        """Validate print color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Print color cannot be empty")

        if v.strip() not in VALID_PRINT_COLORS:
            raise ValueError(
                f"Invalid print color. Must be one of: {', '.join(sorted(VALID_PRINT_COLORS))}"
            )

        return v.strip()

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate color from predefined options"""
        if not v or not v.strip():
            raise ValueError("Color cannot be empty")

        if v.strip() not in VALID_COLORS:
            raise ValueError(
                f"Invalid color. Must be one of: {', '.join(sorted(VALID_COLORS))}"
            )

        return v.strip()

    @field_validator('plateBlockNumber')
    @classmethod
    def validate_plate_block_number(cls, v):
        """Validate plate block number"""
        if v is None:
            v = 0

        if v < 0:
            raise ValueError("Plate block number must be non-negative")

        if v > 1000:
            raise ValueError("Plate block number seems too large (max 1000)")

        return float(v)

    @field_validator('rate')
    @classmethod
    def validate_rate(cls, v):
        """Validate rate"""
        if v is None or v <= 0:
            raise ValueError("Rate must be greater than 0")

        if v > 1000000:
            raise ValueError("Rate seems too large (max 1,000,000)")

        if len(str(v).split('.')[-1]) > 2 and '.' in str(v):
            raise ValueError("Rate can have maximum 2 decimal places")

        return float(v)


class SearchProduct(BaseModel):
    """Model for searching products with optional filters"""
    productType: Optional[str] = None
    bagMaterial: Optional[str] = None
    sheetColor: Optional[str] = None
    borderColor: Optional[str] = None
    handleColor: Optional[str] = None
    printingType: Optional[str] = None
    printColor: Optional[str] = None
    color: Optional[str] = None
    design: Optional[bool] = None
    plateAvailable: Optional[bool] = None
    minPrice: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    maxPrice: Optional[float] = Field(None, ge=0, description="Maximum price filter")

    @field_validator('minPrice', 'maxPrice')
    @classmethod
    def validate_prices(cls, v):
        """Validate price filters"""
        if v is not None and v < 0:
            raise ValueError("Price must be non-negative")
        return v