import psycopg2
from dotenv import load_dotenv
import os
from typing import Tuple, Any

# Load environment variables
load_dotenv()

# Fetch database credentials from .env
DB_CONFIG = {
    "user": os.getenv("user"),
    "password": os.getenv("password"),
    "host": os.getenv("host"),
    "port": os.getenv("port"),
    "dbname": os.getenv("dbname")
}

def get_db_connection() -> Tuple[Any, Any]:
    """Create and return a database connection and cursor"""
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    return connection, cursor