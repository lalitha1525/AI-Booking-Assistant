import sqlite3
from app.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            booking_type TEXT,
            date TEXT,
            time TEXT,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    conn.commit()
    conn.close()
