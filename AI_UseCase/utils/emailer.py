import streamlit as st
import smtplib
from email.message import EmailMessage

SMTP_EMAIL = st.secrets["SMTP_EMAIL"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]


def send_confirmation_email(to_email, name, booking_id, service, date, time):
    try:
        print("📧 Attempting to send email to:", to_email)

        msg = EmailMessage()
        msg["Subject"] = "Appointment Confirmation"
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        msg.set_content(
            f"""
Hello {name},

Your appointment has been successfully confirmed.

📌 Booking ID: {booking_id}
🩺 Service: {service}
📅 Date: {date}
⏰ Time: {time}

Please arrive 10 minutes early.

Thank you for choosing our clinic.

Regards,
ABC Health Care Clinic
"""
        )

        # Gmail SMTP (SSL)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully")
        return True

    except Exception as e:
        print("❌ Email failed:", e)
        return False
