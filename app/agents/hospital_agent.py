from app.services.hospital_service import find_nearby_hospitals

def hospital_agent(state):
    latitude, longitude = state.get("latitude"), state.get("longitude")
    if latitude is None or longitude is None:
        return {
            "hospitals": [],
            "hospital_recommendation": "Please share your location or enter an address to search for nearby hospitals.",
            "message": "A location is needed to find nearby hospitals.",
        }
    try:
        hospitals = find_nearby_hospitals(latitude, longitude)
        return {
            "hospitals": hospitals,
            "hospital_recommendation": f"Found {len(hospitals)} nearby healthcare facilities." if hospitals else "No facilities were found in the selected search radius.",
            "message": "Nearby facilities are listed by distance. Department and specialist availability must be confirmed directly with each facility.",
        }
    except Exception:
        return {"hospitals": [], "hospital_recommendation": "Hospital search is temporarily unavailable. Please try again later.", "errors": ["Hospital discovery service unavailable."]}
