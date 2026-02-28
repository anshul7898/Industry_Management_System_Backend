from pydantic import BaseModel
from typing import Optional


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
    productType: str
    productSize: float
    bagMaterial: str
    quantity: float
    sheetGSM: float
    sheetColor: str
    borderGSM: float
    borderColor: str
    handleType: str
    handleColor: str
    handleGSM: float
    printingType: str
    printColor: str
    color: str
    design: bool = False
    plateBlockNumber: float = 0
    plateAvailable: bool = False
    rate: float


class UpdateProduct(BaseModel):
    productType: str
    productSize: float
    bagMaterial: str
    quantity: float
    sheetGSM: float
    sheetColor: str
    borderGSM: float
    borderColor: str
    handleType: str
    handleColor: str
    handleGSM: float
    printingType: str
    printColor: str
    color: str
    design: bool = False
    plateBlockNumber: float = 0
    plateAvailable: bool = False
    rate: float


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
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None