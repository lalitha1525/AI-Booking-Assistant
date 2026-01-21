import sqlite3
import uuid
from datetime import datetime
import pandas as pd

DB_NAME = "appointments.db"


# ---------------- INIT DB ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
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


# ---------------- SAVE BOOKING ----------------
def save_booking_to_db(booking):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        customer_id = "CUS-" + uuid.uuid4().hex[:6].upper()
        booking_id = "APT-" + uuid.uuid4().hex[:6].upper()

        # Save customer
        cur.execute("""
            INSERT INTO customers VALUES (?, ?, ?, ?)
        """, (
            customer_id,
            booking["name"],
            booking["email"],
            booking["phone"]
        ))

        # Save booking
        cur.execute("""
            INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            booking_id,
            customer_id,
            booking["service"],
            booking["date"],
            booking["time"],
            "CONFIRMED",
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        return booking_id

    except Exception as e:
        print("DB ERROR:", e)
        return None


# ---------------- USER BOOKING RETRIEVAL ----------------
def get_bookings_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT b.id, c.name, b.booking_type, b.date, b.time, b.status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.customer_id
        WHERE c.email = ?
    """
    df = pd.read_sql_query(query, conn, params=(email,))
    conn.close()
    return df


# ---------------- ADMIN ----------------
def get_all_bookings():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT 
            b.id,
            c.name,
            c.email,
            c.phone,
            b.booking_type,
            b.date,
            b.time,
            b.status,
            b.created_at
        FROM bookings b
        JOIN customers c ON b.customer_id = c.customer_id
        ORDER BY b.created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cancel_booking(booking_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        UPDATE bookings SET status='CANCELLED'
        WHERE id=?
    """, (booking_id,))
    conn.commit()
    conn.close()


def update_booking_status(booking_id, status):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        UPDATE bookings SET status=?
        WHERE id=?
    """, (status, booking_id))
    conn.commit()
    conn.close()
