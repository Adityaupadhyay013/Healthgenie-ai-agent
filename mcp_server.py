"""HealthGenie MCP server.

Run with:
    uvicorn mcp_server:app --host 0.0.0.0 --port $PORT

The server exposes read-only medical-reference and facility-search tools. It does
not diagnose, prescribe, or modify patient records.
"""
import hmac
import os

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from app.services.medicine_service import search_medicine_references_direct
from app.services.hospital_service import find_nearby_hospitals_direct

AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "").strip()
if not AUTH_TOKEN:
    raise RuntimeError(
        "MCP_AUTH_TOKEN is required. Generate a strong random token and set it "
        "on both the MCP and FastAPI Render services."
    )

mcp = FastMCP("HealthGenie Healthcare Reference Tools")


@mcp.tool
async def search_medicine_reference(medicine_name_or_ingredient: str) -> dict:
    """Search RxNorm drug concepts and DailyMed official product-label references by exact medicine name or active ingredient.

    This tool returns reference matches and source links only. It does not select
    medicines for symptoms, recommend treatment, or provide dosage instructions.
    """
    if not medicine_name_or_ingredient.strip():
        return {"query": "", "medicines": [], "sources": []}
    return await search_medicine_references_direct(medicine_name_or_ingredient)


@mcp.tool
async def find_nearby_health_facilities(latitude: float, longitude: float) -> dict:
    """Find nearby hospital and clinic map listings from OpenStreetMap.

    Returns approximate straight-line distance and source links. Facility status,
    specialties, opening hours and emergency capabilities are not verified.
    """
    facilities = await find_nearby_hospitals_direct(latitude, longitude)
    return {
        "facilities": facilities,
        "source": "OpenStreetMap",
        "verification_note": (
            "Map listings are not independently verified. Call each facility to "
            "confirm operating status, services, departments and specialist availability."
        ),
    }


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Protect every MCP request with a shared service-to-service bearer token."""

    def __init__(self, app, token: str):
        super().__init__(app)
        self.token = token

    async def dispatch(self, request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {self.token}"
        if not hmac.compare_digest(supplied, expected):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


async def health(_request):
    return JSONResponse({"status": "healthy", "service": "healthgenie-mcp"})


mcp_asgi = mcp.http_app()
app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Mount("/", app=mcp_asgi),
    ],
    lifespan=mcp_asgi.lifespan,
    middleware=[Middleware(BearerTokenMiddleware, token=AUTH_TOKEN)],
)
