import boto3
from config.settings import (
    AWS_REGION,
    ACCOUNTS_TABLE,
    AGENTS_TABLE,
    PARTY_TABLE,
    PRODUCTS_TABLE,
    ORDERS_TABLE,
)

# Let boto3 auto-discover credentials from the environment.
# Locally: reads AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY from .env via os.environ.
# Lambda: reads execution-role credentials including AWS_SESSION_TOKEN automatically.
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Get table references
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
agents_table = dynamodb.Table(AGENTS_TABLE)
party_table = dynamodb.Table(PARTY_TABLE)
products_table = dynamodb.Table(PRODUCTS_TABLE)
orders_table = dynamodb.Table(ORDERS_TABLE)