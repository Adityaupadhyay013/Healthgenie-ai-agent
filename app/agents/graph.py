from langgraph.graph import StateGraph, START, END
from app.agents.state import HealthGenieState
from app.agents.intent_agent import classify_intent
from app.agents.supervisor import emergency_detection
from app.agents.medicine_agent import medicine_agent
from app.agents.hospital_agent import hospital_agent
from app.agents.response_agent import response_agent


def prediction_redirect_agent(state):
    routes = {
        "kidney_prediction": ("kidney_model", "kidney"),
        "liver_prediction": ("liver_model", "liver"),
        "heart_prediction": ("heart_model", "heart"),
    }
    target, page = routes[state["intent"]]
    return {
        "target": target,
        "action": "redirect",
        "message": f"Please complete the {page} prediction form. The prediction requires the relevant model input values.",
    }


def general_health_agent(state):
    return {
        "message": (
            "Hello! I'm HealthGenie AI. I can provide general health information, "
            "help you navigate disease prediction forms, retrieve medicine reference "
            "information by medicine name, and find nearby healthcare facilities. "
            "I cannot diagnose or prescribe treatment."
        ),
        "action": "suggest",
    }


def emergency_agent(state):
    return {
        "intent": "emergency",
        "action": "alert",
        "message": state.get("message") or (
            "Your message may describe an emergency. Contact India's emergency number "
            "112 or go to the nearest emergency department now. Do not wait for an AI assessment."
        ),
        "review_required": True,
    }


async def combined_healthcare_agent(state):
    """Run independent reference and facility lookups for a combined request."""
    import asyncio
    medicine_result, hospital_result = await asyncio.gather(
        medicine_agent(state), hospital_agent(state)
    )
    merged_sources = medicine_result.get("sources", []) + hospital_result.get("sources", [])
    merged_errors = medicine_result.get("errors", []) + hospital_result.get("errors", [])
    return {
        **medicine_result,
        **hospital_result,
        "intent": "healthcare_search",
        "medicines": medicine_result.get("medicines", []),
        "medicine_details": medicine_result.get("medicine_details", []),
        "hospitals": hospital_result.get("hospitals", []),
        "sources": merged_sources,
        "errors": merged_errors,
        "safety_flags": medicine_result.get("medication_safety_flags", []),
        "review_required": True,
        "message": (
            medicine_result.get("message", "") + " " +
            hospital_result.get("message", "")
        ).strip(),
        "action": "suggest",
    }


def route_after_emergency(state):
    return "classify" if not state.get("emergency_flag") else "emergency"


def route_intent(state):
    intent = state.get("intent", "general_health")
    if intent == "emergency":
        return "emergency"
    if intent in {"kidney_prediction", "liver_prediction", "heart_prediction"}:
        return "prediction"
    if intent == "medicine_information":
        return "medicine"
    if intent == "hospital_search":
        return "hospital"
    if intent == "healthcare_search":
        return "combined"
    return "general"


def build_graph():
    builder = StateGraph(HealthGenieState)
    nodes = {
        "emergency_check": emergency_detection,
        "intent_classifier": classify_intent,
        "emergency_response": emergency_agent,
        "prediction_redirect": prediction_redirect_agent,
        "medicine_agent": medicine_agent,
        "hospital_agent": hospital_agent,
        "combined_healthcare": combined_healthcare_agent,
        "general_health": general_health_agent,
        "response": response_agent,
    }
    for name, function in nodes.items():
        builder.add_node(name, function)
    builder.add_edge(START, "emergency_check")
    builder.add_conditional_edges(
        "emergency_check",
        route_after_emergency,
        {"classify": "intent_classifier", "emergency": "emergency_response"},
    )
    builder.add_conditional_edges(
        "intent_classifier",
        route_intent,
        {
            "emergency": "emergency_response",
            "prediction": "prediction_redirect",
            "medicine": "medicine_agent",
            "hospital": "hospital_agent",
            "combined": "combined_healthcare",
            "general": "general_health",
        },
    )
    for node in (
        "emergency_response", "prediction_redirect", "medicine_agent",
        "hospital_agent", "combined_healthcare", "general_health"
    ):
        builder.add_edge(node, "response")
    builder.add_edge("response", END)
    return builder.compile()


healthgenie_graph = build_graph()
