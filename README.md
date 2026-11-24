# HealthGenie AI — FastAPI + LangGraph backend

A demo backend for the HealthGenie AI frontend. LangGraph handles intent routing and safety checks; kidney, liver and heart prediction forms remain frontend routes.

## Features in this branch

- Intent routing for kidney/liver/heart prediction redirects, medicine-reference lookup, nearby facilities, and general health questions.
- Emergency keyword guardrail runs before normal intent routing.
- Medicine reference lookups against the public **RxNorm** and **DailyMed** REST APIs. These identify drug concepts and official labels; they do not prescribe treatment.
- Nearby hospital/clinic map listings from OpenStreetMap Overpass, with asynchronous HTTP, approximate distance sorting and explicit verification caveats.
- Combined medicine-reference + nearby-facility requests.
- Stable response fields for the existing frontend: `intent`, `message`, `medicines`, `hospital_recommendation`, `action`, and `target`.

## Run locally (Windows PowerShell)

Use Python 3.11 if available:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If your machine has a different Python launcher/path, create the virtual environment with that installed Python executable. Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Example chat request:

```json
{
  "query": "Find hospitals near me",
  "location_data": {"latitude": 28.6139, "longitude": 77.2090}
}
```

Or provide a location string such as `"New Delhi, India"`. For best accuracy, pass browser coordinates in `location_data`.

## Environment variables

Copy `.env.example` to `.env`. Set `FRONTEND_URL` to the deployed frontend origin (no trailing slash). `GEMINI_API_KEY` is optional; the keyword classifier works without it. Never commit real API keys or patient information.

## Integrations and MCP note

The current implementation calls RxNorm, DailyMed, Nominatim and Overpass using their public HTTP APIs directly. **These are not MCP servers and this branch does not yet speak the MCP protocol.** Direct REST calls keep the Render deployment simple and avoid requiring a separately hosted MCP process. If you want actual MCP tool transport, deploy a trusted MCP server separately (or run a local stdio server alongside the backend) and add an MCP client/adapter after verifying the server's transport, tools and hosting requirements. Do not point a production backend at an untrusted public MCP endpoint.

Sources:
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Nominatim usage policy: https://operations.osmfoundation.org/policies/nominatim/
- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API
- OpenStreetMap copyright: https://www.openstreetmap.org/copyright

## Deploy to Render

1. Create a Render Web Service or Blueprint from this repository.
2. Set `FRONTEND_URL` to your Lovable/custom frontend's exact origin.
3. Add `GEMINI_API_KEY` only if you want LLM-assisted intent classification.
4. Deploy and verify `/health` and `/docs`.

The included `render.yaml` does not require kidney/liver/heart model URLs because those prediction forms are frontend-owned in the current architecture.

## Important safety and data limitations

- This is an educational prototype, not a medical device or clinically validated triage system.
- Emergency phrase matching is incomplete and can miss emergencies or raise false alarms. If symptoms may be life-threatening, contact local emergency services immediately. In India, dial **112**.
- HealthGenie must not select a drug or dose from symptoms. RxNorm is drug terminology; DailyMed contains US product labeling. They are not a personalized treatment recommendation and may not represent Indian brand availability or Indian regulatory labeling.
- The medicine lookup is intended for an exact medicine name or active ingredient. A matching search result does not prove that a medicine is suitable for a person.
- OpenStreetMap facility listings may be incomplete, outdated or incorrectly tagged. Department/specialist availability, emergency capability, opening hours and phone numbers are not verified. Call the facility before travelling.
- Public geocoding/map services have usage policies, rate limits and availability constraints. Cache responsibly and do not overload shared public services.
- Do not send identifiable patient health information to an external LLM or third-party API without appropriate consent, privacy safeguards and legal review.
- Prediction outputs are not confirmed diagnoses. Have a qualified healthcare professional interpret them.
