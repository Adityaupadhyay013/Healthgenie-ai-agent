# HealthGenie AI Backend

FastAPI + LangGraph starter backend intended to replace a Relay AI webhook while preserving the original frontend response fields.

## Run on Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell activation is blocked, use Command Prompt:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs and test `POST /api/chat`.

Example request preserving the old webhook shape:

```json
{
  "query": "Find hospitals near me",
  "location": "28.6139,77.2090"
}
```

Or use browser coordinates:

```json
{
  "query": "Find hospitals near me",
  "location_data": {"latitude": 28.6139, "longitude": 77.2090}
}
```

The original response keys are retained: `intent`, `message`, `medicines`, `hospital_recommendation`, `action`, and `target`. Extra fields include hospital details, medicine details, safety flags, sources and errors.

## Configure

Edit `.env`. Add your Gemini key if you want LLM-assisted intent classification. The backend has a simple keyword fallback when no key is configured. Add the real kidney/liver/heart prediction API URLs only after confirming their request schemas.

## Deploy

Push the folder to GitHub, create a Render Blueprint from the repository, then set the environment variables in Render. The included `render.yaml` defines the service.

## Limitations and safety

This is a demo foundation, not a clinically validated healthcare product. Emergency keyword detection is not reliable triage. OpenStreetMap results do not verify departments, specialists, or current availability. Public Nominatim and Overpass services have usage policies and rate limits; cache queries and use responsibly. The medicine catalogue is deliberately empty; only add medicine records reviewed by qualified clinicians and backed by authoritative sources. The prediction adapter requires real model endpoints and matching input schemas. Do not send identifiable patient health data to an unapproved external LLM provider. Obtain clinical, privacy, security and regulatory review before real patient use.
