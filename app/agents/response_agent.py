def response_agent(state):
    return {
        "intent": state.get("intent", "general_health"),
        "message": state.get("message", ""),
        "medicines": state.get("medicines", []),
        "medicine_details": state.get("medicine_details", []),
        "hospital_recommendation": state.get("hospital_recommendation", ""),
        "hospitals": state.get("hospitals", []),
        "action": state.get("action", "suggest"),
        "target": state.get("target", ""),
        "emergency_flag": state.get("emergency_flag", False),
        "safety_flags": state.get("medication_safety_flags", state.get("safety_flags", [])),
        "review_required": state.get("review_required", False),
        "sources": state.get("sources", []),
        "errors": state.get("errors", []),
    }
