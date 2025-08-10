# app/services/hotels_api.py
import os
import asyncio
import httpx
from core.http_client import get_json
from typing import List, Dict, Any, Optional

BOOKING_KEY = os.getenv("BOOKING_API_KEY")
BOOKING_HOST = os.getenv("BOOKING_HOST", "hotels4.p.rapidapi.com")
BASE_BOOKING_URL = f"https://{BOOKING_HOST}"

async def search_hotels(
    location: str,
    check_in: str,
    check_out: str,
    adults: int = 1,
    page_size: int = 10,
    accommodation_type: Optional[str] = None,
    min_rating: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Query hotels API and return list of normalized hotels.
    location can be city name or destinationId depending on the API used.
    """
    if not BOOKING_KEY:
        raise RuntimeError("Missing BOOKING_API_KEY in env")

    url = f"{BASE_BOOKING_URL}/properties/list"
    headers = {
        "X-RapidAPI-Key": BOOKING_KEY,
        "X-RapidAPI-Host": BOOKING_HOST
    }
    params = {
        "destination": location,
        "checkIn": check_in,
        "checkOut": check_out,
        "adults1": str(adults),
        "pageSize": str(page_size)
    }
    if accommodation_type:
        params["accommodationType"] = accommodation_type
    if isinstance(min_rating, (int, float)):
        params["minStarRating"] = str(min_rating)
    raw = await get_json(url, headers=headers, params=params)

    candidates = raw.get("results") or raw.get("data") or raw.get("searchResults", {}).get("results", []) or []
    hotels = []
    for h in candidates:
        try:
            hotels.append({
                "name": h.get("name") or h.get("hotelName"),
                "price_per_night": float(h.get("price", {}).get("current") or h.get("minPrice") or 0),
                "rating": float(h.get("rating") or h.get("starRating") or 0),
                "address": h.get("address", {}).get("streetAddress") if isinstance(h.get("address"), dict) else h.get("address"),
                "amenities": h.get("amenities") or []
            })
        except Exception:
            continue
    return hotels
