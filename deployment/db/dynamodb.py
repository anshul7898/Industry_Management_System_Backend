import boto3
from config.settings import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    ACCOUNTS_TABLE,
    AGENTS_TABLE,
    PARTY_TABLE,
    PRODUCTS_TABLE,
    ORDERS_TABLE,
)

# Initialize DynamoDB resource with explicit credentials
dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Get table references
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
agents_table = dynamodb.Table(AGENTS_TABLE)
party_table = dynamodb.Table(PARTY_TABLE)
products_table = dynamodb.Table(PRODUCTS_TABLE)
orders_table = dynamodb.Table(ORDERS_TABLE)