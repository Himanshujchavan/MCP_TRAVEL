# app/services/flights_api.py
import os
import asyncio
import httpx
from core.http_client import get_json, post_json
from typing import List, Dict, Any, Optional

SKYSCANNER_KEY = os.getenv("SKYSCANNER_API_KEY")
SKYSCANNER_HOST = os.getenv("SKYSCANNER_HOST", "skyscanner44.p.rapidapi.com")  # set if needed

BASE_SKY_URL = f"https://{SKYSCANNER_HOST}"

async def _get_json(url: str, params: dict, headers: dict, timeout: int = 10, attempts: int = 2) -> dict:
    return await get_json(url, params=params, headers=headers)

async def search_flights(
    origin: str,
    destination: str,
    date: str,
    adults: int = 1,
    currency: str = "USD",
    cabin_class: str = "economy",
    preferred_airlines: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Returns normalized list of flight options.
    Uses RapidAPI Skyscanner-like endpoints (ensure SKYSCANNER_HOST matches the RapidAPI host).
    """
    if not SKYSCANNER_KEY:
        raise RuntimeError("Missing SKYSCANNER_API_KEY in env")

    url = f"{BASE_SKY_URL}/search"  # many RapidAPI wrappers use /search
    headers = {
        "X-RapidAPI-Key": SKYSCANNER_KEY,
        "X-RapidAPI-Host": SKYSCANNER_HOST
    }
    params = {
        "adults": str(adults),
        "origin": origin,
        "destination": destination,
        "departureDate": date,
        "currency": currency,
        "cabinClass": cabin_class,
    }
    if preferred_airlines:
        # Many RapidAPI wrappers accept comma-separated carriers
        params["carriers"] = ",".join(preferred_airlines)
    raw = await _get_json(url, params=params, headers=headers)
    # Normalization: adapt to the actual structure of chosen RapidAPI; below is a best-effort mapping
    flights = []
    # Example: raw.get("data") or raw.get("flights")
    candidates = raw.get("flights") or raw.get("data") or raw.get("results") or []
    for f in candidates:
        try:
            flights.append({
                "airline": f.get("airline") or f.get("carrier") or f.get("airlineName"),
                "price": float(f.get("price", f.get("priceTotal", 0)) or 0),
                "departure_time": f.get("departure") or f.get("departure_time") or f.get("depart"),
                "arrival_time": f.get("arrival") or f.get("arrival_time") or f.get("arrive"),
                "stops": f.get("stops", 0),
                "duration": f.get("duration")
            })
        except Exception:
            continue
    return flights

async def get_flight_details(flight_id: str) -> dict:
    """
    Get detailed information about a specific flight by its ID.
    """
    if not SKYSCANNER_KEY:
        raise RuntimeError("Missing SKYSCANNER_API_KEY in env")

    fly_host = os.getenv("FLY_SCRAPER_HOST", "fly-scraper.p.rapidapi.com")
    url = f"https://{fly_host}/flights/search-detail"
    headers = {
        "X-Rapidapi-Key": SKYSCANNER_KEY,
        "X-Rapidapi-Host": fly_host,
        "Content-Type": "application/json",
    }
    return await post_json(url, headers=headers, json={"flightId": flight_id})
