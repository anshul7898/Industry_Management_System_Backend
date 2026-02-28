import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError

from schemas.products import Product, CreateProduct, UpdateProduct, SearchProduct
from utils.helpers import aws_error_detail, ddb_decimal, normalize_product_item, get_next_product_id
from db.dynamodb import products_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get("/products", response_model=List[Product])
def list_products():
    """
    Get all products from the database
    """
    try:
        items = products_table.scan().get("Items", [])
        return [normalize_product_item(x) for x in items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """
    Get a specific product by ID
    """
    try:
        resp = products_table.get_item(Key={"ProductId": product_id})
        item = resp.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


@router.post("/products", response_model=Product)
def create_product(payload: CreateProduct):
    """
    Create a new product with auto-generated ID
    """
    try:
        product_id = get_next_product_id()

        item = {
            "ProductId": product_id,
            "ProductType": payload.productType,
            "ProductSize": ddb_decimal(payload.productSize),
            "BagMaterial": payload.bagMaterial,
            "Quantity": ddb_decimal(payload.quantity),
            "SheetGSM": ddb_decimal(payload.sheetGSM),
            "SheetColor": payload.sheetColor,
            "BorderGSM": ddb_decimal(payload.borderGSM),
            "BorderColor": payload.borderColor,
            "HandleType": payload.handleType,
            "HandleColor": payload.handleColor,
            "HandleGSM": ddb_decimal(payload.handleGSM),
            "PrintingType": payload.printingType,
            "PrintColor": payload.printColor,
            "Color": payload.color,
            "Design": payload.design,
            "PlateBlockNumber": ddb_decimal(payload.plateBlockNumber),
            "PlateAvailable": payload.plateAvailable,
            "Rate": ddb_decimal(payload.rate),
        }

        products_table.put_item(Item=item)
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")


@router.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, payload: UpdateProduct):
    """
    Update an existing product
    """
    try:
        existing = products_table.get_item(Key={"ProductId": product_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        item = {
            "ProductId": product_id,
            "ProductType": payload.productType,
            "ProductSize": ddb_decimal(payload.productSize),
            "BagMaterial": payload.bagMaterial,
            "Quantity": ddb_decimal(payload.quantity),
            "SheetGSM": ddb_decimal(payload.sheetGSM),
            "SheetColor": payload.sheetColor,
            "BorderGSM": ddb_decimal(payload.borderGSM),
            "BorderColor": payload.borderColor,
            "HandleType": payload.handleType,
            "HandleColor": payload.handleColor,
            "HandleGSM": ddb_decimal(payload.handleGSM),
            "PrintingType": payload.printingType,
            "PrintColor": payload.printColor,
            "Color": payload.color,
            "Design": payload.design,
            "PlateBlockNumber": ddb_decimal(payload.plateBlockNumber),
            "PlateAvailable": payload.plateAvailable,
            "Rate": ddb_decimal(payload.rate),
        }

        products_table.put_item(Item=item)
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")


@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    """
    Delete a product by ID
    """
    try:
        existing = products_table.get_item(Key={"ProductId": product_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        products_table.delete_item(Key={"ProductId": product_id})
        return {"deleted": True, "productId": product_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise


@router.post("/products/search", response_model=List[Product])
def search_products(filters: SearchProduct):
    """
    Search products with optional filters.
    Supports filtering by:
    - productType
    - bagMaterial
    - sheetColor
    - borderColor
    - handleColor
    - printingType
    - printColor
    - color
    - design (boolean)
    - plateAvailable (boolean)
    - minPrice / maxPrice (rate range)
    """
    try:
        items = products_table.scan().get("Items", [])

        filtered_items = []
        for item in items:
            # Check string filters
            if filters.productType and item.get("ProductType") != filters.productType:
                continue
            if filters.bagMaterial and item.get("BagMaterial") != filters.bagMaterial:
                continue
            if filters.sheetColor and item.get("SheetColor") != filters.sheetColor:
                continue
            if filters.borderColor and item.get("BorderColor") != filters.borderColor:
                continue
            if filters.handleColor and item.get("HandleColor") != filters.handleColor:
                continue
            if filters.printingType and item.get("PrintingType") != filters.printingType:
                continue
            if filters.printColor and item.get("PrintColor") != filters.printColor:
                continue
            if filters.color and item.get("Color") != filters.color:
                continue

            # Check boolean filters
            if filters.design is not None and item.get("Design") != filters.design:
                continue
            if filters.plateAvailable is not None and item.get("PlateAvailable") != filters.plateAvailable:
                continue

            # Check price range
            rate = item.get("Rate")
            if isinstance(rate, Decimal):
                rate = float(rate)

            if filters.minPrice is not None and rate < filters.minPrice:
                continue
            if filters.maxPrice is not None and rate > filters.maxPrice:
                continue

            filtered_items.append(item)

        return [normalize_product_item(x) for x in filtered_items]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")