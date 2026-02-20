import os
import boto3

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ORDERS_TABLE = os.getenv("ORDERS_TABLE", "Orders")  # must be "Orders"

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
orders_table = dynamodb.Table(ORDERS_TABLE)