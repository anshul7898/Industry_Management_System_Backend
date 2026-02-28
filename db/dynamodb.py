import boto3
from config.settings import AWS_REGION, ACCOUNTS_TABLE, AGENTS_TABLE, PARTY_TABLE, PRODUCTS_TABLE, ORDERS_TABLE

# Initialize DynamoDB resource for ap-south-1
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Get table references
accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
agents_table = dynamodb.Table(AGENTS_TABLE)
party_table = dynamodb.Table(PARTY_TABLE)
products_table = dynamodb.Table(PRODUCTS_TABLE)
orders_table = dynamodb.Table(ORDERS_TABLE)