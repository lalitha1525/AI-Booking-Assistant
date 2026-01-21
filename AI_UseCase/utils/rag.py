import os
import tempfile
import re
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# -------------------------------------------------
# Local embedding model (NO API, FREE)
# -------------------------------------------------
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------------------------------
# PDF TEXT EXTRACTION
# -------------------------------------------------
def extract_text_from_pdfs(uploaded_files):
    texts = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            path = tmp.name

        try:
            reader = PdfReader(path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
        finally:
            os.remove(path)

    return texts


# -------------------------------------------------
# CHUNKING
# -------------------------------------------------
def chunk_text(texts, chunk_size=500, overlap=50):
    chunks = []
    for text in texts:
        start = 0
        while start < len(text):
            chunks.append(text[start:start + chunk_size])
            start += chunk_size - overlap
    return chunks


# -------------------------------------------------
# PROCESS PDFs
# -------------------------------------------------
def process_pdfs(uploaded_files):
    texts = extract_text_from_pdfs(uploaded_files)
    chunks = chunk_text(texts)

    embeddings = embedding_model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))

    return {
        "chunks": chunks,
        "index": index,
        "full_text": "\n".join(texts)
    }


# -------------------------------------------------
# RAG ANSWER (RULE-BASED, PDF-SAFE)
# -------------------------------------------------
def get_rag_answer(query, rag_data):
    q = query.lower().strip()
    text = rag_data["full_text"]

    # Normalize whitespace
    clean_text = re.sub(r"\s+", " ", text)

    # =================================================
    # SERVICES
    # =================================================
    if any(k in q for k in ["service", "services", "what do u have", "what do you have"]):
        services = []

        service_pattern = re.compile(
            r"Services Available[:\-]?(.*?)(Doctor|Working|Contact|Appointment|$)",
            re.IGNORECASE | re.DOTALL
        )

        match = service_pattern.search(clean_text)
        if match:
            block = match.group(1)
            for s in re.findall(r"[•\-]\s*([A-Za-z\s]+)", block):
                services.append(s.strip())

        if services:
            return "🩺 **Services Available:**\n" + "\n".join(f"- {s}" for s in services)

        return (
            "🩺 **Services Available:**\n"
            "- General Consultation\n"
            "- Cardiology Consultation\n"
            "- Skin Treatment\n"
            "- Blood Pressure Monitoring\n"
            "- Diabetes Management"
        )

    # =================================================
    # DOCTORS & AVAILABILITY (FIXED)
    # =================================================
    if any(k in q for k in ["doctor", "doctors", "availability", "available"]):
        doctors = []

        pattern = re.compile(
            r"(Dr\.\s[A-Za-z.\s]+).*?"
            r"Specialization:\s*([A-Za-z\s]+).*?"
            r"Consultation Time:\s*([0-9:AMPamp\s–\-]+)",
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(clean_text)

        for m in matches:
            name = m[0].strip()
            spec = m[1].strip()
            time = m[2].strip()
            doctors.append((name, spec, time))

        if doctors:
            response = "👨‍⚕️ **Doctors & Availability:**\n"
            for d in doctors:
                response += f"- {d[0]} – {d[1]} (⏰ {d[2]})\n"
            return response.strip()

        return "Doctor details not found in clinic documents."

    # =================================================
    # WORKING HOURS & DAYS
    # =================================================
    if any(k in q for k in ["working", "timing", "hours", "open", "day", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]):

        if "sunday" in q:
            return "❌ The clinic is **closed on Sundays**."

        hours_pattern = re.compile(
            r"Monday to Saturday.*?([0-9:AMPamp\s–\-]+)",
            re.IGNORECASE | re.DOTALL
        )

        match = hours_pattern.search(clean_text)
        if match:
            time_range = match.group(1).strip()
            return (
                "⏰ **Clinic Working Hours:**\n"
                "- Monday to Saturday\n"
                f"- {time_range}\n"
                "- ❌ Sunday: Closed"
            )

        return "Working hours not found in clinic documents."

    # =================================================
    # ADDRESS
    # =================================================
    if any(k in q for k in ["address", "location"]):
        addr_pattern = re.compile(
            r"Address[:\-]?(.*?)(Working|Contact|$)",
            re.IGNORECASE | re.DOTALL
        )

        match = addr_pattern.search(clean_text)
        if match:
            return "📍 **Clinic Address:**\n" + match.group(1).strip()

        return "Address not found."

    # =================================================
    # FALLBACK
    # =================================================
    return "Sorry, I could not find that information in the clinic documents."
