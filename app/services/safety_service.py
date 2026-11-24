# Prototype keyword screen only; not a clinically validated triage system.
EMERGENCY_KEYWORDS = [
    "severe chest pain", "chest pain and sweating", "cannot breathe",
    "can't breathe", "difficulty breathing", "unconscious", "severe bleeding",
    "signs of stroke", "sudden weakness on one side",
]

def check_emergency(query: str):
    text = query.lower()
    matches = [term for term in EMERGENCY_KEYWORDS if term in text]
    return {"emergency_flag": bool(matches), "matched_indicators": matches}
