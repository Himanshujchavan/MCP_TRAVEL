from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api import plan_trip, fetch_destinations, weather, flights, hotels
from api.travel_endpoints import router as travel_router
from core.http_client import close_client
import uuid
import logging

# Load env from .env then override with local.env if present
load_dotenv(".env")
load_dotenv("local.env", override=True)

app = FastAPI(title="AI Trip Planner API", version="1.0.0")

# CORS: allow Next.js dev server and optional origins from env
origins = {
	"http://localhost:3000",
	"http://127.0.0.1:3000",
}
# Add optional FRONTEND_URL/NGROK_URL if present
for key in ("FRONTEND_URL", "NGROK_URL"):
	val = os.getenv(key)
	if val:
		origins.add(val)

app.add_middleware(
	CORSMiddleware,
	allow_origins=list(origins),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
	rid = request.headers.get("x-request-id") or str(uuid.uuid4())
	response = None
	try:
		response = await call_next(request)
		return response
	finally:
		if response is not None:
			response.headers["x-request-id"] = rid


@app.on_event("shutdown")
async def shutdown_event():
	# Close shared HTTP client
	try:
		await close_client()
	except Exception as e:
		logging.getLogger(__name__).warning(f"Error closing HTTP client: {e}")

app.include_router(plan_trip.router, prefix="/plan-trip", tags=["Trip Planning"])
app.include_router(fetch_destinations.router, prefix="/fetch-destinations", tags=["Destinations"])
app.include_router(weather.router, prefix="/weather", tags=["Weather"])
app.include_router(flights.router, prefix="/flights", tags=["Flights"])
app.include_router(hotels.router, prefix="/hotels", tags=["Hotels"])
app.include_router(travel_router, tags=["Comprehensive Travel Planning"])


@app.get("/")
def root():
	return {"status": "ok", "service": "AI Trip Planner API", "version": "1.0.0"}


@app.get("/health")
def health():
	return {"status": "healthy"}


@app.get("/favicon.ico")
def favicon():
	# Return 204 to avoid 404 noise when browsers request favicon
	return Response(status_code=204)


@app.get("/mcp")
def mcp_info():
	return {
		"status": "ok",
		"message": "This server exposes an HTTP API. Full MCP-over-HTTP is not implemented here.",
		"endpoints": [
			"/plan-trip",
			"/fetch-destinations",
			"/weather",
			"/flights",
			"/hotels",
			"/health",
		],
	}


@app.post("/mcp")
def mcp_not_implemented(request: Request):
	# Placeholder: return clear error for POST /mcp probes
	raise HTTPException(status_code=501, detail="MCP-over-HTTP endpoint not implemented. Use the HTTP API routes or run a dedicated MCP server.")


