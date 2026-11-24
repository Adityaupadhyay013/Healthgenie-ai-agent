from app.services.hospital_service import find_nearby_hospitals


async def hospital_agent(state):
    latitude, longitude = state.get("latitude"), state.get("longitude")
    if latitude is None or longitude is None:
        return {
            "hospitals": [],
            "hospital_recommendation": "Please share your location or enter an address to search for nearby hospitals.",
            "message": "A location is needed to find nearby healthcare facilities.",
        }
    try:
        hospitals = await find_nearby_hospitals(latitude, longitude)
        return {
            "hospitals": hospitals,
            "hospital_recommendation": (
                f"Found {len(hospitals)} nearby healthcare facility listings."
                if hospitals else "No facility listings were found in the selected search radius."
            ),
            "message": (
                "Facilities are sorted by approximate straight-line distance using OpenStreetMap data. "
                "Listings and specialties are not independently verified; call before travelling."
            ),
            "sources": [{"title": "OpenStreetMap", "url": "https://www.openstreetmap.org/copyright"}],
        }
    except Exception:
        return {
            "hospitals": [],
            "hospital_recommendation": "Hospital search is temporarily unavailable. Please try again later.",
            "message": "The map-data service did not respond. This is not a confirmation that no hospitals are nearby.",
            "errors": ["Hospital discovery service unavailable."],
        }
