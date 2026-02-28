import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ACCOUNTS_TABLE = os.getenv("ACCOUNTS_TABLE", "Accounts")
AGENTS_TABLE = os.getenv("AGENTS_TABLE", "Agent")
PARTY_TABLE = os.getenv("PARTY_TABLE", "Party")
PRODUCTS_TABLE = os.getenv("PRODUCTS_TABLE", "Product")
ORDERS_TABLE = os.getenv("ORDERS_TABLE", "Orders")

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Application Configuration
APP_NAME = "Bag Management API"
APP_VERSION = "1.0.0"