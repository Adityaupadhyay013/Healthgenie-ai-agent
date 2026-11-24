from app.services.llm import get_llm

VALID_INTENTS = {
    "kidney_prediction", "liver_prediction", "heart_prediction",
    "medicine_information", "hospital_search", "general_health", "emergency"
}

def fallback_intent(query: str) -> str:
    text = query.lower()
    urgent = ["severe chest pain", "chest pain and sweating", "cannot breathe",
              "can't breathe", "difficulty breathing", "unconscious",
              "severe bleeding", "signs of stroke", "sudden weakness on one side"]
    if any(term in text for term in urgent):
        return "emergency"
    if any(x in text for x in ("medicine", "medication", "drug", "tablet", "treatment")):
        return "medicine_information"
    if any(x in text for x in ("hospital", "clinic", "nearby", "near me")):
        return "hospital_search"
    if "kidney" in text: return "kidney_prediction"
    if "liver" in text: return "liver_prediction"
    if "heart" in text: return "heart_prediction"
    return "general_health"

def classify_intent(state):
    query = state["query"]
    llm = get_llm()
    if not llm:
        return {"intent": fallback_intent(query)}
    prompt = (
        "Classify into exactly one label: kidney_prediction, liver_prediction, "
        "heart_prediction, medicine_information, hospital_search, general_health, "
        "emergency. Return only the label. Use emergency for potentially urgent symptoms."
    )
    try:
        response = llm.invoke(f"{prompt}\nUser request: {query}")
        label = str(response.content).strip().lower().replace("`", "").split()[0].strip(".,:")
        return {"intent": label if label in VALID_INTENTS else fallback_intent(query)}
    except Exception:
        return {"intent": fallback_intent(query)}
