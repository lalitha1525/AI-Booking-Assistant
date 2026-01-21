import sqlite3
import pandas as pd

DB_NAME = "appointments.db"


# ---------------- GET ALL BOOKINGS ----------------
def get_all_bookings():
    try:
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
            JOIN customers c
            ON b.customer_id = c.customer_id
            ORDER BY b.created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print("ADMIN ERROR:", e)
        return pd.DataFrame()


# ---------------- CANCEL BOOKING ----------------
def cancel_booking(booking_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "UPDATE bookings SET status = 'CANCELLED' WHERE id = ?",
            (booking_id,)
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("CANCEL ERROR:", e)
        return False


# ---------------- UPDATE BOOKING STATUS ----------------
def update_booking_status(booking_id, status):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            (status, booking_id)
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("UPDATE STATUS ERROR:", e)
        return False
