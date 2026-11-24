import httpx
from app.config import settings

MODEL_ENDPOINTS = {
    "kidney_model": settings.KIDNEY_MODEL_URL,
    "liver_model": settings.LIVER_MODEL_URL,
    "heart_model": settings.HEART_MODEL_URL,
}

async def predict_disease(target: str, features: dict):
    endpoint = MODEL_ENDPOINTS.get(target)
    if not endpoint:
        raise ValueError(f"{target} endpoint is not configured. Set its URL in the environment.")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(endpoint, json=features)
        response.raise_for_status()
        return response.json()
