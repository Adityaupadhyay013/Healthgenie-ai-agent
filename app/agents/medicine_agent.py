from app.services.medicine_service import load_medicine_database, search_medicines

def medicine_agent(state):
    query = state.get("query", "").lower()
    prediction = state.get("prediction_result") or {}
    disease = prediction.get("disease", "")
    if not disease:
        for record in load_medicine_database():
            for condition in record.get("conditions", []):
                if condition.lower() in query:
                    disease = condition
                    break
            if disease:
                break
    if not disease:
        return {
            "medicines": [], "medicine_details": [],
            "message": "Please specify the medical condition for which you want medicine information. HealthGenie does not prescribe medicines.",
            "review_required": True,
        }
    records = search_medicines(disease)
    return {
        "medicines": [x["generic_name"] for x in records if x.get("generic_name")],
        "medicine_details": records,
        "message": (
            "The following medicine information was retrieved from the curated catalogue. "
            "It is not a prescription. A qualified clinician must decide whether treatment is appropriate."
            if records else "No clinically reviewed medicine records are currently available for this condition."
        ),
        "review_required": True,
        "medication_safety_flags": [
            "Check allergies and current medications.",
            "Check contraindications and drug interactions.",
            "Review relevant laboratory results and patient history.",
            "A qualified clinician must approve treatment decisions.",
        ],
        "sources": [{"title": x.get("source_title", "Clinical source"), "url": x.get("source_url", "")} for x in records if x.get("source_url")],
    }
