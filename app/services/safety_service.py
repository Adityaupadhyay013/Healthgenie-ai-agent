"""Conservative keyword guardrail; not a validated clinical triage system."""
import re

EMERGENCY_PATTERNS = [
    r"severe chest pain",
    r"chest pain.{0,40}(sweat|breathless|faint)",
    r"(cannot|can't|unable to) breathe",
    r"severe difficulty breathing",
    r"unconscious|not responding",
    r"severe bleeding|bleeding won't stop",
    r"(face droop|slurred speech|sudden weakness)",
    r"seizure.{0,30}(first|uncontrolled|not stopping)",
    r"overdose|poisoning",
    r"suicid(al|e)|want to kill myself",
]


def check_emergency(query: str):
    text = re.sub(r"\s+", " ", (query or "").lower()).strip()
    matches = [pattern for pattern in EMERGENCY_PATTERNS if re.search(pattern, text)]
    return {"emergency_flag": bool(matches), "matched_indicators": matches}
