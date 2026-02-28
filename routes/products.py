import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
from pydantic import ValidationError

from schemas.products import Product, CreateProduct, UpdateProduct, SearchProduct
from utils.helpers import aws_error_detail, ddb_decimal, normalize_product_item, get_next_product_id
from db.dynamodb import products_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


def format_validation_errors(errors: list) -> str:
    """Format Pydantic validation errors into a readable message"""
    error_messages = []
    for error in errors:
        field = error['loc'][0] if error['loc'] else 'unknown'
        message = error['msg']
        error_messages.append(f"{field}: {message}")
    return "; ".join(error_messages)


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
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """
    Get a specific product by ID
    """
    try:
        if product_id <= 0:
            raise HTTPException(status_code=400, detail="Product ID must be a positive integer")

        resp = products_table.get_item(Key={"ProductId": product_id})
        item = resp.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        return normalize_product_item(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=aws_error_detail(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch product")


@router.post("/products", response_model=Product)
def create_product(payload: CreateProduct):
    """
    Create a new product with auto-generated ID
    """
    try:
        # Validation is automatically done by Pydantic
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

        logger.info(f"Product created successfully with ID: {product_id}")
        return normalize_product_item(item)

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error creating product: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except ClientError as e:
        logger.error(f"Database error creating product: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create product")


@router.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, payload: UpdateProduct):
    """
    Update an existing product
    """
    try:
        if product_id <= 0:
            raise HTTPException(status_code=400, detail="Product ID must be a positive integer")

        # Check if product exists
        existing = products_table.get_item(Key={"ProductId": product_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        # Validation is automatically done by Pydantic
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

        logger.info(f"Product {product_id} updated successfully")
        return normalize_product_item(item)

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error updating product {product_id}: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error updating product {product_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error updating product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update product")


@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    """
    Delete a product by ID
    """
    try:
        if product_id <= 0:
            raise HTTPException(status_code=400, detail="Product ID must be a positive integer")

        existing = products_table.get_item(Key={"ProductId": product_id}).get("Item")
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        products_table.delete_item(Key={"ProductId": product_id})

        logger.info(f"Product {product_id} deleted successfully")
        return {"deleted": True, "productId": product_id}

    except HTTPException:
        raise

    except ClientError as e:
        logger.error(f"Database error deleting product {product_id}: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Unexpected error deleting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete product")


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

            if filters.minPrice is not None and (rate is None or rate < filters.minPrice):
                continue
            if filters.maxPrice is not None and (rate is None or rate > filters.maxPrice):
                continue

            filtered_items.append(item)

        return [normalize_product_item(x) for x in filtered_items]

    except ValidationError as e:
        error_detail = format_validation_errors(e.errors())
        logger.warning(f"Validation error searching products: {error_detail}")
        raise HTTPException(status_code=422, detail=error_detail)

    except ClientError as e:
        logger.error(f"Database error searching products: {aws_error_detail(e)}")
        raise HTTPException(status_code=500, detail=aws_error_detail(e))

    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search products")