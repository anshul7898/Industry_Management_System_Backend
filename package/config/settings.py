import os
from dotenv import load_dotenv
from typing import List

# Load .env file FIRST before reading any env vars
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# DynamoDB Table Names
ACCOUNTS_TABLE = os.getenv("ACCOUNTS_TABLE", "Accounts")
AGENTS_TABLE = os.getenv("AGENTS_TABLE", "Agent")
PARTY_TABLE = os.getenv("PARTY_TABLE", "Party")
PRODUCTS_TABLE = os.getenv("PRODUCTS_TABLE", "Product")
ORDERS_TABLE = os.getenv("ORDERS_TABLE", "Order")

# App Configuration
APP_NAME = "Orders Management API"
APP_VERSION = "1.0.0"

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]