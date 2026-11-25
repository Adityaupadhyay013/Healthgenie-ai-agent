import logging
import math

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

USER_AGENT = "HealthGenieAI/1.0 (educational healthcare navigation project)"
OVERPASS_FALLBACK_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)


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


def _overpass_endpoints():
    """Return configured and public fallback endpoints without duplicates."""
    configured = (settings.OVERPASS_URL or "").strip()
    return list(dict.fromkeys(
        endpoint for endpoint in (configured, *OVERPASS_FALLBACK_URLS) if endpoint
    ))


async def find_nearby_hospitals_direct(latitude: float, longitude: float):
    """Search OSM facility listings, retrying alternative Overpass instances."""
    validate_coordinates(latitude, longitude)
    radius_km = max(1, min(settings.HOSPITAL_SEARCH_RADIUS_KM, 50))
    radius_m = radius_km * 1000
    query = f"""[out:json][timeout:25];
    (node["amenity"~"^(hospital|clinic)$"](around:{radius_m},{latitude},{longitude});
     way["amenity"~"^(hospital|clinic)$"](around:{radius_m},{latitude},{longitude});
     relation["amenity"="hospital"](around:{radius_m},{latitude},{longitude}););
    out center tags;"""

    data = None
    last_error = None
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(35.0, connect=8.0),
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for endpoint in _overpass_endpoints():
            try:
                response = await client.post(endpoint, data={"data": query})
                response.raise_for_status()
                data = response.json()
                break
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                logger.warning("Overpass provider failed; trying fallback provider (%s)", type(exc).__name__)

    if data is None:
        raise RuntimeError("All Overpass hospital-search providers failed") from last_error

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
            "latitude": lat,
            "longitude": lon,
            "distance_km": round(haversine_distance(latitude, longitude, lat, lon), 2),
            "specialty_verified": False,
            "listing_source": "OpenStreetMap",
            "verification_note": "Map listing only. Call to confirm operating status, emergency services, departments and specialist availability.",
            "map_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}",
        })
    facilities.sort(key=lambda item: item["distance_km"])
    return facilities[:10]


async def find_nearby_hospitals(latitude: float, longitude: float):
    """Prefer MCP, but recover through direct multi-provider OSM search on failure."""
    from app.services.mcp_client import call_mcp_tool

    try:
        remote = await call_mcp_tool(
            "find_nearby_health_facilities",
            {"latitude": latitude, "longitude": longitude},
        )
        if remote is not None:
            facilities = remote.get("facilities", [])
            if facilities:
                return facilities
            logger.info("MCP hospital search returned no facilities; trying direct fallback")
    except Exception as exc:
        logger.warning("MCP hospital search failed; trying direct fallback (%s)", type(exc).__name__)

    return await find_nearby_hospitals_direct(latitude, longitude)
