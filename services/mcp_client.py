# app/services/mcp_client.py
import os
import asyncio
import httpx
from typing import Dict, Any, Optional

MCP_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")  # example

async def _request_with_retries(url: str, json: Dict[str, Any], timeout: int = 10, attempts: int = 3) -> Dict[str, Any]:
    for i in range(attempts):
        try:
            async with httpx.AsyncClient(http1=True, timeout=timeout) as client:
                r = await client.post(url, json=json)
                r.raise_for_status()
                return r.json()
        except Exception as e:
            if i == attempts - 1:
                raise
            await asyncio.sleep(0.5 * (i + 1))
    return {}

async def get_ai_trip_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send request to MCP AI server and return structured plan.
    payload example: { "origin": "...", "destination": "...", "start_date": "...", "end_date": "...", "preferences": [...] }
    """
    url = f"{MCP_URL.rstrip('/')}/generate-itinerary"
    try:
        resp = await _request_with_retries(url, json=payload, timeout=20, attempts=3)
        # Expect MCP to return structured JSON. If not, fallback to simple stub.
        if isinstance(resp, dict) and resp:
            return resp
    except Exception as e:
        # fallback: small heuristic plan if MCP unavailable
        return {
            "itinerary": [
                {"date": payload.get("start_date"), "activities": [f"Arrive at {payload.get('destination')}"]},
                {"date": payload.get("end_date"), "activities": ["Departure / buffer day"]}
            ],
            "estimated_cost": None,
            "note": f"Used fallback plan because MCP unavailable: {str(e)}"
        }
    return {}
