from typing import Any, Dict, List, Optional, TypedDict

class HealthGenieState(TypedDict, total=False):
    query: str
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    patient_profile: Dict[str, Any]
    intent: str
    target: str
    emergency_flag: bool
    matched_indicators: List[str]
    prediction_result: Optional[Dict[str, Any]]
    medicines: List[str]
    medicine_details: List[Dict[str, Any]]
    medication_safety_flags: List[str]
    safety_flags: List[str]
    review_required: bool
    hospitals: List[Dict[str, Any]]
    hospital_recommendation: Any
    message: str
    action: str
    sources: List[Dict[str, Any]]
    errors: List[str]
