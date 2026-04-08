import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import boto3

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ORDERS_TABLE = os.getenv("ORDERS_TABLE", "Orders")

customers = [
    "Aarav Traders",
    "Mehta Industries",
    "Kumar Manufacturing",
    "Singh Engineering Works",
    "Sharma Metals",
    "Patel Supplies",
    "Rao Industrial Co.",
    "Verma Engineering",
    "Gupta Machinery",
    "Iyer Logistics",
]

products = [
    "Industrial Pump",
    "Conveyor Belt",
    "Hydraulic Valve",
    "Gear Motor",
    "Air Compressor",
    "Pressure Gauge",
    "CNC Spindle",
    "Control Panel",
    "VFD Drive",
    "Bearing Set",
]


def to_ymd(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def main():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(ORDERS_TABLE)

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = []

    for i in range(20):
        order_date = start + timedelta(days=i)
        delivery_date = order_date + timedelta(days=3 + (i % 10))

        order_id = f"ORD-{1001 + i}"
        product = products[i % len(products)]
        customer = customers[i % len(customers)]

        item = {
            "orderId": order_id,
            "description": f"{product} - Batch #{500 + (i % 50)}",
            "customerName": customer,
            "orderDate": to_ymd(order_date),
            "deliveryDate": to_ymd(delivery_date),
            # Optional metadata, safe to keep:
            "seedId": uuid4().hex,
            "seededAt": datetime.now(timezone.utc).isoformat(),
        }
        items.append(item)

    # Batch write (25 items max per batch) — 20 is safe
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

    print(f"Seeded {len(items)} items into DynamoDB table '{ORDERS_TABLE}' in {AWS_REGION}.")


if __name__ == "__main__":
    main()