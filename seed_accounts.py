import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from decimal import Decimal

import boto3

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ACCOUNTS_TABLE = os.getenv("ACCOUNTS_TABLE", "Accounts")

parties = [
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

payment_modes = ["UPI", "NEFT", "RTGS", "Cash", "Card", "Cheque"]
types = ["RECEIVABLE", "PAYABLE"]


def to_ymd(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def main():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(ACCOUNTS_TABLE)

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    items = []
    for i in range(20):
        txn_date = start + timedelta(days=i)

        party = parties[i % len(parties)]
        kind = types[i % len(types)]
        mode = payment_modes[i % len(payment_modes)]

        base = 1500 + (i * 175)

        # ✅ DynamoDB requires Decimal for numbers (no float)
        amount = Decimal(str(base))
        if kind == "PAYABLE":
            amount = -amount

        item = {
            # ✅ Partition key
            "txnId": f"TXN-{3001 + i}",
            "partyName": party,
            "type": kind,  # RECEIVABLE or PAYABLE
            "amount": amount,
            "paymentMode": mode,
            "transactionDate": to_ymd(txn_date),
            "description": f"{kind.title()} transaction for {party} via {mode}",
            # Optional metadata
            "seedId": uuid4().hex,
            "seededAt": datetime.now(timezone.utc).isoformat(),
        }

        items.append(item)

    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

    print(
        f"Seeded {len(items)} items into DynamoDB table '{ACCOUNTS_TABLE}' in {AWS_REGION}."
    )


if __name__ == "__main__":
    main()