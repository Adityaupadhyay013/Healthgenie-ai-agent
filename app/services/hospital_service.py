import math
import httpx
from app.config import settings

def haversine_distance(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * radius_km * math.asin(math.sqrt(a))

async def geocode_location(address: str):
    headers = {"User-Agent": "HealthGenieAI-demo/1.0 (contact: project-owner)"}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            settings.NOMINATIM_URL,
            params={"q": address, "format": "jsonv2", "limit": 1},
            headers=headers,
        )
        response.raise_for_status()
        results = response.json()
    if not results:
        return None
    return {"latitude": float(results[0]["lat"]), "longitude": float(results[0]["lon"])}

def find_nearby_hospitals(latitude: float, longitude: float):
    radius_m = settings.HOSPITAL_SEARCH_RADIUS_KM * 1000
    query = f"""[out:json][timeout:25];
    (node["amenity"="hospital"](around:{radius_m},{latitude},{longitude});
     way["amenity"="hospital"](around:{radius_m},{latitude},{longitude});
     relation["amenity"="hospital"](around:{radius_m},{latitude},{longitude});
     node["amenity"="clinic"](around:{radius_m},{latitude},{longitude});
     way["amenity"="clinic"](around:{radius_m},{latitude},{longitude}););
    out center tags;"""
    headers = {"User-Agent": "HealthGenieAI-demo/1.0 (contact: project-owner)"}
    with httpx.Client(timeout=35) as client:
        response = client.post(settings.OVERPASS_URL, data={"data": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
    hospitals = []
    for item in data.get("elements", []):
        tags = item.get("tags", {})
        lat, lon = item.get("lat"), item.get("lon")
        if lat is None or lon is None:
            center = item.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue
        distance = haversine_distance(latitude, longitude, float(lat), float(lon))
        hospitals.append({
            "name": tags.get("name", "Unnamed facility"),
            "type": tags.get("amenity"),
            "address": ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:postcode")])),
            "latitude": float(lat), "longitude": float(lon),
            "distance_km": round(distance, 2),
            "specialty_verified": False,
            "map_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}",
        })
    hospitals.sort(key=lambda x: x["distance_km"])
    return hospitals[:10]
