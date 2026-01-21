

import streamlit as st
import os
import sys

# Fix import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from utils.rag import process_pdfs, get_rag_answer
from utils.booking import (
    init_booking,
    update_booking,
    next_question,
    save_booking,
    get_bookings_by_email
)
from utils.intent import detect_intent, is_question
from utils.emailer import send_confirmation_email
from utils.admin import (
    get_all_bookings,
    cancel_booking,
    update_booking_status
)

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"



# ---------------- INSTRUCTIONS PAGE ----------------
def instructions_page():
    st.title("Doctor Appointment AI Assistant")

    st.markdown("""
    ### ✅ Features Implemented
    - RAG-based PDF Q&A
    - Multi-turn appointment booking
    - Booking retrieval by user (email-based)
    - SQLite persistence
    - Email confirmation (SMTP)
    - Admin dashboard (edit / cancel / export)
    - Improved UX (avatars, spinners)
    - Short-term memory (last 25 messages)
    """)


# ---------------- CHAT PAGE ----------------
def chat_page():
    st.title("🩺 Doctor Appointment AI Assistant")

    # -------- PDF Upload --------
    uploaded_files = st.file_uploader(
        "Upload clinic PDFs (timings, services, doctors)",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files and "rag_data" not in st.session_state:
        with st.spinner("Processing PDFs..."):
            st.session_state.rag_data = process_pdfs(uploaded_files)
        st.success("✅ PDFs processed successfully")

    # -------- Chat Memory --------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages[-25:]:
        avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # -------- User Input --------
    if prompt := st.chat_input("Ask a question or book an appointment..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=BOT_AVATAR):
            with st.spinner("🤖 Thinking..."):

                # ================= BOOKING RETRIEVAL =================
                if "awaiting_email_lookup" in st.session_state:
                    bookings = get_bookings_by_email(prompt)
                    del st.session_state.awaiting_email_lookup

                    if bookings:
                        response = "📋 **Your bookings:**\n\n"
                        for b in bookings:
                            response += (
                                f"- 📌 {b[0]} | {b[1]} | {b[2]} | {b[3]} | {b[4]}\n"
                            )
                    else:
                        response = "❌ No bookings found for this email."

                elif any(x in prompt.lower() for x in ["my booking", "my appointment"]):
                    st.session_state.awaiting_email_lookup = True
                    response = "📧 Please enter your email to retrieve your bookings."

                # ================= BOOKING MODE =================
                elif "booking" in st.session_state:

                    if prompt.lower() == "yes":
                        booking_id = save_booking(st.session_state.booking)

                        email_sent = send_confirmation_email(
                            st.session_state.booking["email"],
                            st.session_state.booking["name"],
                            booking_id,
                            st.session_state.booking["service"],
                            st.session_state.booking["date"],
                            st.session_state.booking["time"]
                        )

                        response = (
                            f"✅ **Appointment confirmed!**\n\n"
                            f"📌 Booking ID: `{booking_id}`"
                        )

                        if email_sent:
                            response += "\n\n📧 Confirmation email sent."
                        else:
                            response += "\n\n⚠️ Booking saved, email could not be sent."

                        del st.session_state.booking

                    elif prompt.lower() == "no":
                        response = "❌ Booking cancelled."
                        del st.session_state.booking

                    elif is_question(prompt) and "rag_data" in st.session_state:
                        info = get_rag_answer(prompt, st.session_state.rag_data)
                        response = info + "\n\n➡️ " + next_question(st.session_state.booking)

                    else:
                        st.session_state.booking = update_booking(
                            st.session_state.booking, prompt
                        )

                        if "_error" in st.session_state.booking:
                            response = st.session_state.booking["_error"]
                        else:
                            q = next_question(st.session_state.booking)
                            if q:
                                response = q
                            else:
                                b = st.session_state.booking
                                response = (
                                    "### 🔎 Please confirm your appointment:\n\n"
                                    f"👤 **Name:** {b['name']}\n"
                                    f"📧 **Email:** {b['email']}\n"
                                    f"📞 **Phone:** {b['phone']}\n"
                                    f"🩺 **Service:** {b['service']}\n"
                                    f"📅 **Date:** {b['date']}\n"
                                    f"⏰ **Time:** {b['time']}\n\n"
                                    "Type **YES** to confirm or **NO** to cancel."
                                )

                # ================= START BOOKING =================
                elif detect_intent(prompt) == "booking":
                    st.session_state.booking = init_booking()
                    response = (
                        "📝 Let’s start booking your appointment.\n\n"
                        + next_question(st.session_state.booking)
                    )

                # ================= GENERAL RAG =================
                else:
                    if "rag_data" in st.session_state:
                        response = get_rag_answer(prompt, st.session_state.rag_data)
                    else:
                        response = "📄 Please upload clinic PDFs first."

                st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )


# ---------------- ADMIN PAGE ----------------
def admin_page():
    st.title("📊 Admin Dashboard")

    df = get_all_bookings()
    if df.empty:
        st.info("No bookings available.")
        return

    st.markdown("### 🔍 Filter by Booking ID")
    booking_id = st.text_input("Booking ID")
    if booking_id:
        df = df[df["id"].str.contains(booking_id)]

    st.dataframe(df, use_container_width=True)

    st.markdown("### ✏️ Manage Booking")

    col1, col2 = st.columns(2)

    with col1:
        cancel_id = st.text_input("Cancel Booking ID")
        if st.button("❌ Cancel Booking"):
            cancel_booking(cancel_id)
            st.warning("Booking cancelled.")
            st.rerun()

    with col2:
        update_id = st.text_input("Update Booking ID")
        status = st.selectbox("New Status", ["CONFIRMED", "CANCELLED"])
        if st.button("✅ Update Status"):
            update_booking_status(update_id, status)
            st.success("Status updated.")
            st.rerun()

    st.markdown("### 📥 Export Bookings")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        csv,
        "appointments.csv",
        "text/csv"
    )


# ---------------- MAIN ----------------
def main():
    st.set_page_config(
        page_title="Doctor Appointment AI Assistant",
        page_icon="🩺",
        layout="wide"
    )

    with st.sidebar:
        page = st.radio("Go to:", ["Chat", "Admin", "Instructions"])
        if st.button("🗑️ Clear Session"):
            st.session_state.clear()
            st.rerun()

    if page == "Chat":
        chat_page()
    elif page == "Admin":
        admin_page()
    else:
        instructions_page()


if __name__ == "__main__":
    main()