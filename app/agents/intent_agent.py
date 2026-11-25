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

    symptom_treatment_request = any(phrase in text for phrase in (
        "medicine for", "medicines for", "medication for", "tablet for",
        "drug for", "recommend me a medicine", "recommend medicine",
        "recommend medicines", "what medicine should i take",
        "which medicine should i take", "what can i take for",
    ))
    asks_medicine = any(x in text for x in (
        "medicine", "medication", "drug", "tablet", "capsule", "side effect",
        "dailymed", "rxnorm", "active ingredient"
    ))
    asks_hospital = any(x in text for x in (
        "hospital", "hospitals", "clinic", "clinics", "nearby", "near me",
        "emergency department"
    ))

    # Keep combined routing only when the user's current request explicitly
    # asks for both medicine-reference information and a healthcare facility.
    if asks_medicine and asks_hospital:
        return "healthcare_search"
    if symptom_treatment_request:
        return "general_health"
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
        "Classify the CURRENT user request into exactly one label: kidney_prediction, "
        "liver_prediction, heart_prediction, medicine_information, hospital_search, "
        "healthcare_search, general_health, emergency. Use healthcare_search only when "
        "the current user request explicitly asks for both medicine reference information "
        "and nearby facilities. Use hospital_search for a request to find hospitals or "
        "clinics, including 'near me', unless the user explicitly asks for medicine "
        "reference information too. A request to recommend a medicine for a symptom is "
        "general_health, not medicine_information. Never classify a hospital-only query "
        "as healthcare_search because previous chat turns mentioned medicines. Return "
        "only the label.\n"
        f"Current user request: {query}"
    )
    try:
        response = llm.invoke(f"{prompt}\nUser request: {query}")
        label = str(response.content).strip().lower().replace("`", "").split()[0].strip(".,:")
        if label not in VALID_INTENTS:
            label = fallback

        # Enforce the deterministic intent for facility-only and explicit combined
        # requests. The LLM must not pull unrelated prior-turn context into routing.
        if fallback in {"hospital_search", "healthcare_search", "emergency", "general_health"}:
            label = fallback
        return {"intent": label}
    except Exception:
        return {"intent": fallback}
