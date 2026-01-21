import sqlite3
import uuid
import re
from datetime import datetime

DB_NAME = "appointments.db"

REQUIRED_FIELDS = ["name", "email", "phone", "service", "date", "time"]

QUESTIONS = {
    "name": "Please provide your full name.",
    "email": "Please provide your email address.",
    "phone": "Please provide your phone number.",
    "service": "Which service do you want to book?",
    "date": "Preferred appointment date (YYYY-MM-DD)?",
    "time": "Preferred appointment time (e.g., 10 AM or 14:00)?"
}

# ---------------- DATABASE INIT ----------------
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


# ---------------- BOOKING STATE ----------------
def init_booking():
    return {}

def get_next_field(booking):
    for field in REQUIRED_FIELDS:
        if field not in booking:
            return field
    return None

def is_booking_complete(booking):
    return all(field in booking for field in REQUIRED_FIELDS)

def next_question(booking):
    field = get_next_field(booking)
    return QUESTIONS[field] if field else None


# ---------------- VALIDATION ----------------
def validate_input(field, value):
    value = value.strip()

    if field == "email":
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
            return False, "❌ Please enter a valid email address (example: name@gmail.com)."

    if field == "date":
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return False, "❌ Please enter date in YYYY-MM-DD format."

    if field == "time":
        if not re.match(r"^\d{1,2}(:\d{2})?\s?(AM|PM|am|pm)?$", value):
            return False, "❌ Please enter a valid time (e.g., 10 AM or 14:00)."

    if field == "phone":
        if not value.isdigit() or len(value) < 10:
            return False, "❌ Please enter a valid phone number."

    if field == "service":
        if len(value) < 3:
            return False, "❌ Please enter a valid service name."

    return True, value


def update_booking(booking, user_input):
    field = get_next_field(booking)
    if not field:
        return booking

    is_valid, result = validate_input(field, user_input)

    if not is_valid:
        booking["_error"] = result
        return booking

    booking[field] = result
    booking.pop("_error", None)
    return booking


# ---------------- SAVE BOOKING ----------------
def save_booking(booking):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        customer_id = "CUS-" + uuid.uuid4().hex[:6].upper()

        cur.execute(
            "INSERT INTO customers VALUES (?, ?, ?, ?)",
            (customer_id, booking["name"], booking["email"], booking["phone"])
        )

        booking_id = "APT-" + uuid.uuid4().hex[:6].upper()

        cur.execute(
            "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                booking_id,
                customer_id,
                booking["service"],
                booking["date"],
                booking["time"],
                "CONFIRMED",
                datetime.now().isoformat()
            )
        )

        conn.commit()
        conn.close()
        return booking_id

    except Exception as e:
        print("DB ERROR:", e)
        return None


# ---------------- BOOKING RETRIEVAL ----------------
def get_bookings_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            b.id,
            b.booking_type,
            b.date,
            b.time,
            b.status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.customer_id
        WHERE c.email = ?
        ORDER BY b.created_at DESC
    """, (email,))

    rows = cur.fetchall()
    conn.close()
    return rows
