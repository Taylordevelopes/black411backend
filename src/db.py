# src/db.py

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

def get_connection():
    """
    Creates and returns a new psycopg2 database connection.
    """
    host = os.getenv("HOSTNAME")
    dbname = os.getenv("DBNAME")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")

    return psycopg2.connect(
        host=host,
        dbname=dbname,
        user=user,
        password=password
    )
