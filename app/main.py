from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas.request import ChatRequest, PredictionRequest
from app.agents.graph import healthgenie_graph
from app.services.hospital_service import geocode_location
from app.services.prediction_service import predict_disease

app = FastAPI(title="HealthGenie AI", description="LangGraph-powered healthcare assistant backend", version="2.0.0")
origins = list(dict.fromkeys([settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"]))
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"name": "HealthGenie AI", "status": "running", "orchestrator": "LangGraph"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    latitude = request.location_data.latitude if request.location_data else None
    longitude = request.location_data.longitude if request.location_data else None
    if request.location and (latitude is None or longitude is None):
        try:
            parts = request.location.split(",")
            if len(parts) == 2:
                latitude, longitude = float(parts[0].strip()), float(parts[1].strip())
        except (ValueError, TypeError):
            pass
    if request.location and latitude is None and longitude is None and settings.ENABLE_GEOCODING:
        try:
            coords = await geocode_location(request.location)
            if coords:
                latitude, longitude = coords["latitude"], coords["longitude"]
        except Exception:
            pass
    initial_state = {
        "query": request.query, "location": request.location,
        "latitude": latitude, "longitude": longitude,
        "patient_profile": request.patient_profile,
        "intent": "general_health", "target": "",
        "emergency_flag": False, "matched_indicators": [],
        "prediction_result": None, "medicines": [], "medicine_details": [],
        "hospitals": [], "hospital_recommendation": "",
        "medication_safety_flags": [], "safety_flags": [],
        "review_required": False, "sources": [], "errors": [],
        "message": "", "action": "suggest",
    }
    try:
        result = await healthgenie_graph.ainvoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="HealthGenie could not process this request.") from exc
    return {
        "intent": result.get("intent", "general_health"),
        "message": result.get("message", ""),
        "medicines": result.get("medicines", []),
        "hospital_recommendation": result.get("hospital_recommendation", ""),
        "action": result.get("action", "suggest"),
        "target": result.get("target", ""),
        "medicine_details": result.get("medicine_details", []),
        "hospitals": result.get("hospitals", []),
        "emergency_flag": result.get("emergency_flag", False),
        "safety_flags": result.get("safety_flags", []),
        "review_required": result.get("review_required", False),
        "sources": result.get("sources", []),
        "errors": result.get("errors", []),
    }

@app.post("/api/predict/{target}")
async def prediction(target: str, request: PredictionRequest):
    if target not in {"kidney_model", "liver_model", "heart_model"}:
        raise HTTPException(status_code=400, detail="Invalid prediction model.")
    try:
        result = await predict_disease(target, request.features)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Prediction service is unavailable.") from exc
    return {"target": target, "result": result, "message": "This ML model output is not a confirmed medical diagnosis. Discuss results with a qualified healthcare professional."}
