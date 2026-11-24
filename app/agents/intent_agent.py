from app.services.llm import get_llm

VALID_INTENTS = {
    "kidney_prediction", "liver_prediction", "heart_prediction",
    "medicine_information", "hospital_search", "healthcare_search",
    "general_health", "emergency"
}


def fallback_intent(query: str) -> str:
    text = query.lower()
    urgent = [
        "severe chest pain", "chest pain and sweating", "cannot breathe",
        "can't breathe", "difficulty breathing", "unconscious",
        "severe bleeding", "signs of stroke", "sudden weakness on one side",
        "face drooping", "slurred speech", "not breathing", "suicidal",
    ]
    if any(term in text for term in urgent):
        return "emergency"

    asks_medicine = any(x in text for x in (
        "medicine", "medication", "drug", "tablet", "capsule", "side effect",
        "dailymed", "rxnorm", "active ingredient"
    ))
    asks_hospital = any(x in text for x in (
        "hospital", "clinic", "nearby", "near me", "emergency department"
    ))
    if asks_medicine and asks_hospital:
        return "healthcare_search"
    if asks_medicine:
        return "medicine_information"
    if asks_hospital:
        return "hospital_search"
    if "kidney" in text:
        return "kidney_prediction"
    if "liver" in text:
        return "liver_prediction"
    if "heart" in text:
        return "heart_prediction"
    return "general_health"


def classify_intent(state):
    query = state["query"]
    fallback = fallback_intent(query)
    if fallback == "emergency":
        return {"intent": "emergency"}
    llm = get_llm()
    if not llm:
        return {"intent": fallback}
    prompt = (
        "Classify the request into exactly one label: kidney_prediction, liver_prediction, "
        "heart_prediction, medicine_information, hospital_search, healthcare_search, "
        "general_health, emergency. Use healthcare_search when the user asks for both "
        "medicine reference information and nearby facilities. Use emergency for potentially "
        "urgent symptoms. Never treat symptom mentions alone as a request for a medicine. "
        "Return only the label."
    )
    try:
        response = llm.invoke(f"{prompt}\nUser request: {query}")
        label = str(response.content).strip().lower().replace("`", "").split()[0].strip(".,:")
        if label not in VALID_INTENTS:
            label = fallback
        # Preserve deterministic multi-intent and emergency detection.
        if fallback in {"healthcare_search", "emergency"}:
            label = fallback
        return {"intent": label}
    except Exception:
        return {"intent": fallback}
