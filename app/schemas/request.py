from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class LocationInput(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None

class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)
    location: Optional[str] = None
    location_data: Optional[LocationInput] = None
    session_id: Optional[str] = None
    patient_profile: Dict[str, Any] = Field(default_factory=dict)

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
