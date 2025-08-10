AI Trip Planner – Backend (FastAPI) + MCP Server

Backend
- FastAPI server with routes:
	- GET /health
	- POST /plan-trip
	- GET /fetch-destinations
	- GET /weather
	- GET /flights
	- GET /hotels
- CORS enabled for Next.js dev (http://localhost:3000). Set FRONTEND_URL to add more origins.

Run locally
1) Activate venv and install deps
2) Start API
3) (Optional) Expose via ngrok

MCP server (stdio)
- Entry: mcp_server.py (launch via `python mcp_server.py`).
- Tools: plan_trip, search_flights, search_hotels, get_weather, search_places.
- Use with MCP clients (e.g., Puch AI) by launching this process.

MCP server (HTTP with Bearer auth)
- Entry: mcp_http_server.py (launch via `python mcp_http_server.py`).
- Env required:
	- AUTH_TOKEN or MCP_BEARER_TOKEN: Bearer token your client must send
	- MY_NUMBER: value returned by the validate tool
- Default bind: 0.0.0.0:8086 (override MCP_HTTP_HOST / MCP_HTTP_PORT)
- Client must send: `Authorization: Bearer <token>`

Next.js integration (frontend)
Create API route handlers that call this backend. Example (app/api/plan-trip/route.ts):

import { NextResponse } from 'next/server'

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(req: Request) {
	const body = await req.json()
	const res = await fetch(`${BASE_URL}/plan-trip/`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
		cache: 'no-store',
	})
	const data = await res.json()
	return NextResponse.json(data, { status: res.status })
}

Repeat similarly for flights, hotels, weather, and fetch-destinations routes (GET with query params).

Env variables
- Put API keys in .env or local.env for the Python backend.
- In Next.js, set NEXT_PUBLIC_BACKEND_URL to your FastAPI URL.

