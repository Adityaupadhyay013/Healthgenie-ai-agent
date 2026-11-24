# HealthGenie AI — FastAPI, LangGraph and MCP

A demo healthcare-navigation assistant. LangGraph handles emergency-first routing and prediction-form redirects. The kidney, liver and heart ML forms remain frontend-owned. A separate authenticated MCP service exposes read-only medicine-reference and nearby-facility tools.

## Architecture

```text
Lovable / React frontend
        |
        | HTTPS /api/chat
        v
FastAPI + LangGraph (healthgenie-backend)
        |
        | MCP Streamable HTTP + Bearer token
        v
HealthGenie MCP service (healthgenie-mcp)
   |             |               |
   v             v               v
 RxNorm       DailyMed        OpenStreetMap
 drug terms   official labels  Overpass listings
```

The MCP server exposes:
- `search_medicine_reference(medicine_name_or_ingredient)`
- `find_nearby_health_facilities(latitude, longitude)`

The FastAPI app calls these tools through the official Python MCP SDK when `MCP_SERVER_URL` is configured. If it is blank, local development falls back to the same direct REST adapters. MCP errors are surfaced as safe service failures by the agents; they are not silently converted into made-up results.

## Local setup

Use Python 3.11:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the MCP server in terminal 1:

```powershell
$env:MCP_AUTH_TOKEN = "replace-with-a-long-random-secret"
uvicorn mcp_server:app --reload --host 127.0.0.1 --port 8001
```

Run FastAPI in terminal 2 with the same token:

```powershell
$env:MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"
$env:MCP_AUTH_TOKEN = "replace-with-a-long-random-secret"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:
- FastAPI docs: http://127.0.0.1:8000/docs
- FastAPI health: http://127.0.0.1:8000/health
- MCP health: http://127.0.0.1:8001/health

To test the MCP server using the MCP Inspector, configure its Streamable HTTP URL as `http://127.0.0.1:8001/mcp` and supply the HTTP header `Authorization: Bearer <same-token>`. Do not expose an unauthenticated MCP endpoint.

## Render deployment

The included `render.yaml` declares two independent web services from the same repository.

1. Deploy the Blueprint from GitHub.
2. Generate a strong random token locally, for example with Python:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
3. In the Render dashboard, set **the exact same** `MCP_AUTH_TOKEN` value on both services. Do not commit it to GitHub or put it in frontend code.
4. Set `MCP_SERVER_URL` on the FastAPI service to the MCP service's HTTPS endpoint plus `/mcp`, e.g. `https://healthgenie-mcp.onrender.com/mcp`.
5. Set `FRONTEND_URL` on FastAPI to the exact deployed Lovable/custom frontend origin.
6. Optionally set `GEMINI_API_KEY` on FastAPI for LLM-assisted intent classification.
7. Verify both `/health` endpoints. Then test the MCP connection with a medicine-name query and a nearby-hospital query.

Render may place free services to sleep. The first request can be slow while the MCP service wakes up. For a live demo, wake both services before presenting or use an always-on plan.

## MCP protocol and dependencies

- Server: FastMCP, mounted as a Streamable HTTP ASGI app.
- Client: official `mcp` Python SDK using `ClientSession` and `streamable_http_client`.
- Authentication: service-to-service static bearer token, kept only in server environment variables.
- The two tools are read-only. Do not add patient-record writes or treatment actions without a separate security and clinical review.

## Data sources and limitations

- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Nominatim policy: https://operations.osmfoundation.org/policies/nominatim/
- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API
- OpenStreetMap copyright: https://www.openstreetmap.org/copyright

RxNorm is drug terminology; DailyMed contains US product labeling. They do not establish Indian brand availability or Indian regulatory labeling. The medicine tool searches an exact medicine name or ingredient and returns reference matches and source links only; it does not recommend drugs for symptoms or provide doses.

OpenStreetMap facilities can be incomplete, outdated or incorrectly tagged. Specialist departments, current operating status, emergency services, hours and phone numbers are not verified. Call a facility before travelling.

## Safety and privacy

This is an educational prototype, not a medical device or clinically validated triage system. Emergency keyword matching is incomplete and can miss emergencies or raise false alarms. If symptoms may be life-threatening, contact local emergency services immediately; in India call **112**. Never delay emergency care to use this assistant.

Do not send identifiable patient health information to an external LLM or third-party service without appropriate consent, privacy safeguards and legal review. Prediction outputs are not diagnoses. A qualified healthcare professional must interpret them.
