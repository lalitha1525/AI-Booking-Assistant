import uuid
from datetime import datetime
from db.database import get_connection

def save_booking(data):
    conn = get_connection()
    cur = conn.cursor()

    customer_id = "CUS-" + uuid.uuid4().hex[:6].upper()
    booking_id = "APT-" + uuid.uuid4().hex[:6].upper()

    cur.execute(
        "INSERT INTO customers VALUES (?, ?, ?, ?)",
        (customer_id, data["name"], data["email"], data["phone"])
    )

    cur.execute(
        "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            booking_id,
            customer_id,
            data["service"],
            data["date"],
            data["time"],
            "CONFIRMED",
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()
    return booking_id


def get_bookings_by_email(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT b.id, b.booking_type, b.date, b.time, b.status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.customer_id
        WHERE c.email = ?
        ORDER BY b.created_at DESC
    """, (email,))

    rows = cur.fetchall()
    conn.close()
    return rows
