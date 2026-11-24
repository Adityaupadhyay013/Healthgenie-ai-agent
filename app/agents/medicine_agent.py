from app.services.medicine_service import search_medicine_references


async def medicine_agent(state):
    query = state.get("query", "")
    try:
        result = await search_medicine_references(query)
    except Exception:
        result = {"query": "", "medicines": [], "sources": []}

    medicines = result.get("medicines", [])
    sources = result.get("sources", [])
    if not result.get("query"):
        message = (
            "Tell me the exact medicine or active ingredient you want to learn about. "
            "I can retrieve reference information and official labels, but I cannot "
            "select a medicine for symptoms or prescribe treatment."
        )
    elif medicines or sources:
        message = (
            "I found medicine-reference matches and/or official product-label sources. "
            "Check that the active ingredient and formulation match your package. "
            "This is reference information, not a recommendation or prescription; "
            "ask a qualified clinician or pharmacist whether it is appropriate for you."
        )
    else:
        message = (
            "I could not find a matching record in the connected medicine references. "
            "Try the exact generic name or active ingredient. HealthGenie does not "
            "recommend medicines based on symptoms."
        )

    return {
        "medicines": medicines,
        "medicine_details": medicines,
        "message": message,
        "review_required": True,
        "medication_safety_flags": [
            "Do not start, stop, or change a medicine based only on this assistant.",
            "Confirm the exact ingredient, strength, and formulation with a pharmacist.",
            "Check allergies, pregnancy status where relevant, current medicines, and contraindications with a clinician.",
            "Seek urgent care for severe or rapidly worsening symptoms.",
        ],
        "sources": sources,
    }
