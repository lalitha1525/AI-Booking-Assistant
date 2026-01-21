def detect_intent(text):
    text = text.lower()
    for word in ["book", "appointment", "schedule", "consult", "visit"]:
        if word in text:
            return "booking"
    return "general"


def is_question(text):
    text = text.lower()
    question_words = [
        "what", "which", "how", "when", "where",
        "services", "timing", "hours", "address", "doctors"
    ]
    return "?" in text or any(w in text for w in question_words)
