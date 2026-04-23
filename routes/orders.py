import logging
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
import traceback
import time

from schemas.orders import Order, CreateOrder, UpdateOrder
from utils.dynamodb_utils import (
    convert_items_to_python,
    convert_item_to_python,
    convert_product_for_storage,
    filter_deleted_items,
    is_item_deleted,
)
from db.dynamodb import orders_table

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


def generate_order_id(agent_id: Optional[int]) -> str:
    """Generate a unique OrderId in format YYMMDDNNNN"""
    from datetime import date
    
    today = date.today()
    date_str = today.strftime('%y%m%d')  # YYMMDD format
    
    # Query existing orders for today to find the next sequence number
    try:
        response = orders_table.scan()
        items = response.get('Items', [])
        
        # Filter orders from today and extract sequence numbers
        today_orders = []
        for item in items:
            order_id = item.get('OrderId', '')
            # Check if it starts with today's date and is a string
            if isinstance(order_id, str) and order_id.startswith(date_str):
                today_orders.append(order_id)
        
        # Get the next sequence number (1-indexed)
        next_seq = len(today_orders) + 1
        order_id = f"{date_str}{next_seq:04d}"
        
    except Exception as e:
        logger.warning(f"Failed to query existing orders for sequence: {e}. Using fallback sequence.")
        # Fallback: use a simple counter based on timestamp
        timestamp = int(time.time())
        next_seq = (timestamp % 10000) % 9999 + 1
        order_id = f"{date_str}{next_seq:04d}"
    
    logger.info(f"Generated OrderId: {order_id} from AgentId: {agent_id}")
    return order_id


def build_products_for_storage(products) -> list:
    """
    Convert a list of Product Pydantic models to DynamoDB-safe dicts.
    FixAmount, QuantityType, JobWorkRate, GST, and ProductStatus are stored if present.

    ProductAmount stored here is the final value already computed by the
    frontend:
      - Pieces: (Qty × Rate) + GST_amount + PlateRate + FixAmount
      - KG:     (Qty × Rate) + GST_amount + JobWorkRate + PlateRate + FixAmount
    where GST_amount = (Qty × Rate) × (GST / 100)
    """
    ddb_products = []
    for idx, product in enumerate(products):
        logger.info(f"Processing product {idx + 1}")

        raw = product.model_dump()

        raw.pop("Design", None)
        raw.pop("PlateAvailable", None)

        plate_type    = raw.get("PlateType")
        design_type   = raw.get("DesignType")
        design_style  = raw.get("DesignStyle")
        product_status = raw.get("ProductStatus", "ToDo")  # Default to "ToDo" if not provided
        roll_size     = raw.get("RollSize")
        fix_amount    = raw.get("FixAmount")
        quantity_type = raw.get("QuantityType")
        job_work_rate = raw.get("JobWorkRate")
        gst           = raw.get("GST")          # ── NEW ──
        width         = raw.get("Width")
        height        = raw.get("Height")
        gusset        = raw.get("Gusset")

        product_dict = {k: v for k, v in raw.items() if v is not None}

        for numeric_field in (
            "Rate", "ProductAmount", "PlateRate",
            "SheetGSM", "BorderGSM", "HandleGSM", "Quantity",
        ):
            if numeric_field in product_dict:
                try:
                    product_dict[numeric_field] = Decimal(str(product_dict[numeric_field]))
                except Exception:
                    pass

        # Convert FixAmount to Decimal for DynamoDB storage
        if fix_amount is not None:
            try:
                product_dict["FixAmount"] = Decimal(str(fix_amount))
            except Exception:
                product_dict.pop("FixAmount", None)
        else:
            product_dict.pop("FixAmount", None)

        # Convert JobWorkRate to Decimal for DynamoDB storage
        if job_work_rate is not None:
            try:
                product_dict["JobWorkRate"] = Decimal(str(job_work_rate))
            except Exception:
                product_dict.pop("JobWorkRate", None)
        else:
            product_dict.pop("JobWorkRate", None)

        # ── NEW: Convert GST to Decimal for DynamoDB storage ─────────────────
        # GST is always stored even when 0, so the value is explicit on read-back.
        if gst is not None:
            try:
                product_dict["GST"] = Decimal(str(gst))
            except Exception:
                product_dict["GST"] = Decimal("0")
        else:
            product_dict["GST"] = Decimal("0")

        # Persist QuantityType as a plain string
        if quantity_type and str(quantity_type).strip() in ("KG", "Pieces"):
            product_dict["QuantityType"] = str(quantity_type).strip()
        else:
            product_dict.pop("QuantityType", None)

        if plate_type in ("Old", "New"):
            product_dict["PlateType"] = plate_type
        else:
            product_dict.pop("PlateType", None)

        if design_type in ("Old", "New"):
            product_dict["DesignType"] = design_type
        else:
            product_dict.pop("DesignType", None)

        if design_style in ("Same Front/Back", "Different Front/Back"):
            product_dict["DesignStyle"] = design_style
        else:
            product_dict.pop("DesignStyle", None)

        if roll_size and str(roll_size).strip():
            product_dict["RollSize"] = str(roll_size).strip()
        else:
            product_dict.pop("RollSize", None)

        logger.info(f"Product {idx + 1} final dict       : {product_dict}")
        logger.info(f"Product {idx + 1} PlateType        : {product_dict.get('PlateType')}")
        logger.info(f"Product {idx + 1} DesignType       : {product_dict.get('DesignType')}")
        logger.info(f"Product {idx + 1} DesignStyle      : {product_dict.get('DesignStyle')}")
        logger.info(f"Product {idx + 1} RollSize         : {product_dict.get('RollSize')}")
        logger.info(f"Product {idx + 1} PlateRate        : {product_dict.get('PlateRate')}")
        logger.info(f"Product {idx + 1} ProductCategory  : {product_dict.get('ProductCategory')}")
        logger.info(f"Product {idx + 1} FixAmount        : {product_dict.get('FixAmount')}")
        logger.info(f"Product {idx + 1} QuantityType     : {product_dict.get('QuantityType')}")
        logger.info(f"Product {idx + 1} JobWorkRate      : {product_dict.get('JobWorkRate')}")
        logger.info(f"Product {idx + 1} GST              : {product_dict.get('GST')}")  # ── NEW ──
        logger.info(f"Product {idx + 1} Width            : {product_dict.get('Width')}")
        logger.info(f"Product {idx + 1} Height           : {product_dict.get('Height')}")
        logger.info(f"Product {idx + 1} Gusset           : {product_dict.get('Gusset')}")

        converted_product = convert_product_for_storage(product_dict)

        if plate_type in ("Old", "New"):
            if converted_product.get("PlateType") != plate_type:
                logger.warning(f"⚠️ PlateType corrupted — restoring to '{plate_type}'")
                converted_product["PlateType"] = plate_type

        if design_type in ("Old", "New"):
            if converted_product.get("DesignType") != design_type:
                logger.warning(f"⚠️ DesignType corrupted — restoring to '{design_type}'")
                converted_product["DesignType"] = design_type

        if design_style in ("Same Front/Back", "Different Front/Back"):
            if converted_product.get("DesignStyle") != design_style:
                logger.warning(f"⚠️ DesignStyle corrupted — restoring to '{design_style}'")
                converted_product["DesignStyle"] = design_style

        if roll_size and str(roll_size).strip():
            if converted_product.get("RollSize") != str(roll_size).strip():
                logger.warning(f"⚠️ RollSize corrupted — restoring to '{roll_size}'")
                converted_product["RollSize"] = str(roll_size).strip()

        # Restore FixAmount if corrupted by convert_product_for_storage
        if fix_amount is not None:
            expected = Decimal(str(fix_amount))
            if converted_product.get("FixAmount") != expected:
                logger.warning(f"⚠️ FixAmount corrupted — restoring to '{fix_amount}'")
                converted_product["FixAmount"] = expected

        # Restore JobWorkRate if corrupted by convert_product_for_storage
        if job_work_rate is not None:
            expected_jwr = Decimal(str(job_work_rate))
            if converted_product.get("JobWorkRate") != expected_jwr:
                logger.warning(f"⚠️ JobWorkRate corrupted — restoring to '{job_work_rate}'")
                converted_product["JobWorkRate"] = expected_jwr

        # ── NEW: Restore GST if corrupted by convert_product_for_storage ─────
        expected_gst = Decimal(str(gst)) if gst is not None else Decimal("0")
        if converted_product.get("GST") != expected_gst:
            logger.warning(f"⚠️ GST corrupted — restoring to '{expected_gst}'")
            converted_product["GST"] = expected_gst

        # Restore Width, Height, Gusset if corrupted by convert_product_for_storage
        for dim_key, dim_val in (("Width", width), ("Height", height), ("Gusset", gusset)):
            if dim_val is not None:
                expected_dim = int(dim_val)
                if converted_product.get(dim_key) != expected_dim:
                    logger.warning(f"⚠️ {dim_key} corrupted — restoring to '{expected_dim}'")
                    converted_product[dim_key] = expected_dim
            else:
                converted_product.pop(dim_key, None)

        # Restore QuantityType if corrupted by convert_product_for_storage
        if quantity_type and str(quantity_type).strip() in ("KG", "Pieces"):
            expected_qt = str(quantity_type).strip()
            if converted_product.get("QuantityType") != expected_qt:
                logger.warning(f"⚠️ QuantityType corrupted — restoring to '{expected_qt}'")
                converted_product["QuantityType"] = expected_qt

        # ── NEW: Ensure ProductStatus is persisted (default to "ToDo") ─────────
        if product_status not in ("ToDo", "In-Progress", "Delivered"):
            product_status = "ToDo"
        converted_product["ProductStatus"] = product_status

        if "ProductCategory" not in converted_product:
            logger.warning(f"⚠️ ProductCategory missing in product {idx + 1} after conversion!")

        logger.info(f"Product {idx + 1} after conversion: {converted_product}")
        ddb_products.append(converted_product)

    logger.info(f"✓ Converted {len(ddb_products)} product(s) for DynamoDB storage")
    return ddb_products


def build_order_item(order_id: int, payload, ddb_products: list) -> dict:
    """
    Build the DynamoDB item dict for an order.
    TotalAmount = sum(ProductAmounts) + Carting.
    ProductAmount for each product already contains the GST component as
    computed by the frontend. We persist TotalAmount as-is.
    OrderStatus defaults to 'ToDo' if not provided.
    OrderStartDate defaults to today's date if not provided.
    
    CASCADING LOGIC (COMPLETE):
    1. NEW ORDER: All products = "ToDo", Order = "ToDo"
    
    2. SINGLE PRODUCT:
       DELIVERED:
         - If product marked as Delivered → order becomes Delivered
         - If order marked as Delivered → product becomes Delivered
       IN-PROGRESS:
         - If product marked as In-Progress → order becomes In-Progress
         - If order marked as In-Progress → product becomes In-Progress
       TODO:
         - If product marked as ToDo → order becomes ToDo
         - If order marked as ToDo → product becomes ToDo
    
    3. MULTIPLE PRODUCTS:
       DELIVERED:
         - If ALL products marked as Delivered → order becomes Delivered
         - If order marked as Delivered → ALL products become Delivered
       IN-PROGRESS:
         - If ALL products marked as In-Progress → order becomes In-Progress
         - If order marked as In-Progress → ALL products become In-Progress
       TODO:
         - If ALL products marked as ToDo → order becomes ToDo
         - If order marked as ToDo → ALL products become ToDo
    """
    # Convert OrderId to int if it's a string (e.g., "2604220001" -> 2604220001)
    order_id_value = int(order_id) if isinstance(order_id, str) else order_id
    
    # Handle cascading status logic
    order_status = payload.OrderStatus or "ToDo"
    product_count = len(ddb_products) if ddb_products else 0
    
    # Case 1: Single product order
    if product_count == 1:
        # Sync order status to product (order-to-product sync)
        if order_status == "Delivered":
            ddb_products[0]["ProductStatus"] = "Delivered"
        elif order_status == "In-Progress":
            ddb_products[0]["ProductStatus"] = "In-Progress"
        elif order_status == "ToDo":
            ddb_products[0]["ProductStatus"] = "ToDo"
        # Note: Product-to-order sync happens in get_order() and list_orders() 
        # when all products have the same status (auto-calculation on retrieval)
    
    # Case 2: Multiple products order
    elif product_count > 1:
        # If order status is directly set to Delivered, mark all products as Delivered
        if order_status == "Delivered":
            for product in ddb_products:
                product["ProductStatus"] = "Delivered"
        # If order status is directly set to In-Progress, mark all products as In-Progress
        elif order_status == "In-Progress":
            for product in ddb_products:
                product["ProductStatus"] = "In-Progress"
        # If order status is directly set to ToDo, mark all products as ToDo
        elif order_status == "ToDo":
            for product in ddb_products:
                product["ProductStatus"] = "ToDo"
        # Note: Product-to-order sync happens in get_order() and list_orders() 
        # when ALL products have the same status (auto-calculation on retrieval)
    
    item = {
        "OrderId": order_id_value,
        "deleted": False,
        "Products": ddb_products,
        "TotalAmount": Decimal(str(payload.TotalAmount)) if payload.TotalAmount is not None else Decimal("0"),
        "OrderStatus": order_status,
    }

    if payload.OrderStartDate is not None:
        item["OrderStartDate"] = payload.OrderStartDate.isoformat() if hasattr(payload.OrderStartDate, 'isoformat') else str(payload.OrderStartDate)
    
    if payload.OrderEndDate is not None:
        item["OrderEndDate"] = payload.OrderEndDate.isoformat() if hasattr(payload.OrderEndDate, 'isoformat') else str(payload.OrderEndDate)

    if payload.AgentId is not None:
        item["AgentId"] = payload.AgentId
    if payload.Party_Name is not None:
        item["Party_Name"] = payload.Party_Name
    if payload.AliasOrCompanyName is not None:
        item["AliasOrCompanyName"] = payload.AliasOrCompanyName
    if payload.Address is not None:
        item["Address"] = payload.Address
    if payload.City is not None:
        item["City"] = payload.City
    if payload.State is not None:
        item["State"] = payload.State
    if payload.Pincode is not None:
        item["Pincode"] = payload.Pincode
    if payload.Contact_Person1 is not None:
        item["Contact_Person1"] = payload.Contact_Person1
    if payload.Contact_Person2 is not None:
        item["Contact_Person2"] = payload.Contact_Person2
    if payload.Mobile1 is not None:
        item["Mobile1"] = payload.Mobile1
    if payload.Mobile2 is not None:
        item["Mobile2"] = payload.Mobile2
    if payload.Email is not None:
        item["Email"] = payload.Email
    if payload.BookingName is not None:
        item["BookingName"] = payload.BookingName
    if payload.TransportName is not None:
        item["TransportName"] = payload.TransportName
    if payload.DispatchContactNumber is not None:
        item["DispatchContactNumber"] = payload.DispatchContactNumber
    if payload.Destination is not None:
        item["Destination"] = payload.Destination

    # Persist Carting if provided
    if payload.Carting is not None:
        item["Carting"] = Decimal(str(payload.Carting))

    return item


@router.get("/orders", response_model=List[Order])
def list_orders():
    """Retrieve all orders from DynamoDB."""
    try:
        logger.info("📋 Fetching all orders from DynamoDB")
        response = orders_table.scan()
        items = filter_deleted_items(response.get("Items", []))
        converted_items = convert_items_to_python(items)
        
        # ── NEW: Auto-update order status based on product statuses ──────────
        for order in converted_items:
            products = order.get("Products", [])
            if products:
                # If all products are "Delivered", set order status to "Delivered"
                if all(p.get("ProductStatus") == "Delivered" for p in products):
                    order["OrderStatus"] = "Delivered"
                # If all products are "In-Progress", set order status to "In-Progress"
                elif all(p.get("ProductStatus") == "In-Progress" for p in products):
                    order["OrderStatus"] = "In-Progress"
                # If all products are "ToDo", set order status to "ToDo"
                elif all(p.get("ProductStatus") == "ToDo" for p in products):
                    order["OrderStatus"] = "ToDo"
        
        logger.info(f"✓ Successfully retrieved {len(converted_items)} orders")
        return converted_items
    except ClientError as e:
        logger.error(f"❌ DynamoDB ClientError listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"❌ Unexpected error listing orders: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Retrieve a specific order by Order ID."""
    try:
        response = orders_table.get_item(Key={"OrderId": order_id})
        order = response.get("Item")
        if not order or is_item_deleted(order):
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        order = convert_item_to_python(order)
        
        # ── Auto-update order status based on product statuses ──────────
        products = order.get("Products", [])
        if products:
            # If all products are "Delivered", set order status to "Delivered"
            if all(p.get("ProductStatus") == "Delivered" for p in products):
                order["OrderStatus"] = "Delivered"
            # If all products are "In-Progress", set order status to "In-Progress"
            elif all(p.get("ProductStatus") == "In-Progress" for p in products):
                order["OrderStatus"] = "In-Progress"
            # If all products are "ToDo", set order status to "ToDo"
            elif all(p.get("ProductStatus") == "ToDo" for p in products):
                order["OrderStatus"] = "ToDo"
        
        return order
    except HTTPException:
        raise
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", response_model=Order)
def create_order(payload: CreateOrder):
    """Create a new order in DynamoDB with multiple products."""
    try:
        from datetime import date
        
        logger.info(f"➕ Creating new order with {len(payload.Products)} product(s)")
        order_id = generate_order_id(payload.AgentId)
        ddb_products = build_products_for_storage(payload.Products)
        item = build_order_item(order_id, payload, ddb_products)
        
        # Set OrderStartDate to today if not provided
        if "OrderStartDate" not in item or item["OrderStartDate"] is None:
            item["OrderStartDate"] = date.today().isoformat()
        
        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} created with {len(ddb_products)} product(s)")
        return convert_item_to_python(item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, payload: UpdateOrder):
    """Update an existing order in DynamoDB."""
    try:
        from datetime import date
        
        logger.info(f"✏️ Updating order {order_id} with {len(payload.Products)} product(s)")
        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing or is_item_deleted(existing):
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        ddb_products = build_products_for_storage(payload.Products)
        item = build_order_item(order_id, payload, ddb_products)
        item["deleted"] = existing.get("deleted", False)
        
        # Auto-set OrderEndDate to today when status is changed to "Delivered"
        if payload.OrderStatus == "Delivered" and payload.OrderEndDate is None:
            item["OrderEndDate"] = date.today().isoformat()
        
        orders_table.put_item(Item=item)
        logger.info(f"✓ Order {order_id} updated with {len(ddb_products)} product(s)")
        return convert_item_to_python(item)
    except HTTPException:
        raise
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
def delete_order(order_id: int):
    """Delete an order from DynamoDB."""
    try:
        existing = orders_table.get_item(Key={"OrderId": order_id}).get("Item")
        if not existing or is_item_deleted(existing):
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        orders_table.update_item(
            Key={"OrderId": order_id},
            UpdateExpression="SET deleted = :deleted",
            ExpressionAttributeValues={":deleted": True},
        )
        logger.info(f"✓ Order {order_id} soft deleted")
        return {"success": True, "orderId": order_id, "message": f"Order {order_id} deleted successfully"}
    except HTTPException:
        raise
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))