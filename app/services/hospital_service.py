import math
import httpx
from app.config import settings

USER_AGENT = "HealthGenieAI/1.0 (educational healthcare navigation project)"


def haversine_distance(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * radius_km * math.asin(math.sqrt(a))


def validate_coordinates(latitude: float, longitude: float):
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude or longitude is outside the valid range.")


async def geocode_location(address: str):
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(12.0, connect=5.0),
        headers={"User-Agent": USER_AGENT},
    ) as client:
        response = await client.get(
            settings.NOMINATIM_URL,
            params={"q": address, "format": "jsonv2", "limit": 1},
        )
        response.raise_for_status()
        results = response.json()
    if not results:
        return None
    return {"latitude": float(results[0]["lat"]), "longitude": float(results[0]["lon"])}


async def find_nearby_hospitals_direct(latitude: float, longitude: float):
    """Direct Overpass implementation used by the MCP server and local fallback."""
    validate_coordinates(latitude, longitude)
    radius_m = max(1000, min(settings.HOSPITAL_SEARCH_RADIUS_KM, 50)) * 1000
    query = f"""[out:json][timeout:20];
    (node["amenity"~"^(hospital|clinic)$"](around:{radius_m},{latitude},{longitude});
     way["amenity"~"^(hospital|clinic)$"](around:{radius_m},{latitude},{longitude});
     relation["amenity"="hospital"](around:{radius_m},{latitude},{longitude}););
    out center tags;"""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(25.0, connect=8.0),
        headers={"User-Agent": USER_AGENT},
    ) as client:
        response = await client.post(settings.OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        data = response.json()

    facilities, seen = [], set()
    for item in data.get("elements", []):
        tags = item.get("tags", {})
        lat, lon = item.get("lat"), item.get("lon")
        if lat is None or lon is None:
            center = item.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue
        lat, lon = float(lat), float(lon)
        key = (tags.get("name", "").strip().lower(), round(lat, 5), round(lon, 5))
        if key in seen:
            continue
        seen.add(key)
        facilities.append({
            "name": tags.get("name", "Unnamed facility"),
            "type": tags.get("amenity"),
            "address": ", ".join(filter(None, [
                tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:postcode")
            ])),
            "latitude": lat, "longitude": lon,
            "distance_km": round(haversine_distance(latitude, longitude, lat, lon), 2),
            "specialty_verified": False,
            "listing_source": "OpenStreetMap",
            "verification_note": "Map listing only. Call to confirm operating status, emergency services, departments and specialist availability.",
            "map_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}",
        })
    facilities.sort(key=lambda item: item["distance_km"])
    return facilities[:10]


async def find_nearby_hospitals(latitude: float, longitude: float):
    """Prefer MCP; use direct Overpass REST when no MCP endpoint is configured."""
    from app.services.mcp_client import call_mcp_tool
    remote = await call_mcp_tool(
        "find_nearby_health_facilities",
        {"latitude": latitude, "longitude": longitude},
    )
    if remote is not None:
        return remote.get("facilities", [])
    return await find_nearby_hospitals_direct(latitude, longitude)
