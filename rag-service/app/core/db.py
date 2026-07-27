"""Database connection utilities using psycopg2."""

import psycopg2
from app.core.config import settings

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD
    )
    return conn
