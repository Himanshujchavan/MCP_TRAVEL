# app/services/places_api.py
import os
import httpx
from core.http_client import get_json
from typing import List, Dict, Any

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
PLACES_TEXTSEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"

async def search_places(query: str, region: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query Google Places TextSearch for attractions.
    query examples: "things to do in Goa" or "museums in Rome"
    """
    if not GOOGLE_KEY:
        raise RuntimeError("Missing GOOGLE_PLACES_API_KEY in env")

    params = {"query": query, "key": GOOGLE_KEY}
    if region:
        params["region"] = region

    data = await get_json(PLACES_TEXTSEARCH, params=params)

    results = data.get("results", [])[:limit]
    normalized = []
    for p in results:
        normalized.append({
            "name": p.get("name"),
            "rating": p.get("rating"),
            "address": p.get("formatted_address"),
            "types": p.get("types", []),
            "place_id": p.get("place_id"),
            "photo_reference": (p.get("photos") or [{}])[0].get("photo_reference")
        })
    return normalized

async def get_place_details(place_id: str) -> Dict[str, Any]:
    params = {"place_id": place_id, "key": GOOGLE_KEY, "fields": "name,rating,formatted_address,opening_hours,website,photos"}
    data = await get_json(PLACE_DETAILS, params=params)
    return data.get("result", {})
