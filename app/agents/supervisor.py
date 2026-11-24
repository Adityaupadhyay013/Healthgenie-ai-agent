from app.services.safety_service import check_emergency

def emergency_detection(state):
    result = check_emergency(state.get("query", ""))
    if result["emergency_flag"]:
        return {
            "emergency_flag": True,
            "matched_indicators": result["matched_indicators"],
            "intent": "emergency",
            "action": "alert",
            "message": (
                "Your description includes a potential emergency warning sign. "
                "Contact local emergency services or go to the nearest emergency "
                "department now. Do not wait for an AI assessment."
            ),
        }
    return {"emergency_flag": False, "matched_indicators": []}
