from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class Product(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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


class BaseProductModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    productType: str = Field(..., min_length=1, max_length=255, description="Product type")
    productSize: float = Field(..., gt=0, description="Product size must be greater than 0")
    bagMaterial: str = Field(..., min_length=1, description="Bag material")
    quantity: float = Field(..., ge=0, description="Quantity must be non-negative")
    sheetGSM: float = Field(..., description="Sheet GSM")
    sheetColor: str = Field(..., min_length=1, description="Sheet color")
    borderGSM: float = Field(..., description="Border GSM")
    borderColor: str = Field(..., min_length=1, description="Border color")
    handleType: str = Field(..., min_length=1, description="Handle type")
    handleColor: str = Field(..., min_length=1, description="Handle color")
    handleGSM: float = Field(..., description="Handle GSM")
    printingType: str = Field(..., min_length=1, description="Printing type")
    printColor: str = Field(..., min_length=1, description="Print color")
    color: str = Field(..., min_length=1, description="Color")
    design: bool = Field(False, description="Whether product has design")
    plateBlockNumber: Optional[float] = Field(None, ge=0, description="Plate block number must be non-negative")
    plateAvailable: bool = Field(False, description="Whether plate is available")
    rate: float = Field(..., gt=0, description="Rate must be greater than 0")


class CreateProduct(BaseProductModel):
    """Model for creating a new product"""
    pass


class UpdateProduct(BaseProductModel):
    """Model for updating an existing product"""
    pass


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