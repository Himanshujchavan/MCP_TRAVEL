"""
AI Trip Planner Orchestration
- Consumes TripRequest-like payload
- Gathers external data (flights, hotels, weather, places)
- Applies simple weather avoidance and budget heuristics
- Optionally calls an MCP AI service; falls back to a heuristic plan
"""
from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta

from .flights_api import search_flights
from .hotels_api import search_hotels
from .weather_api import get_forecast
from .places_api import search_places
from .events_api import search_events
from .restaurants_api import search_restaurants
from .visa_api import check_visa_requirements, get_safety_advisories
from .booking_integration import get_booking_links, create_trip_summary_export
try:
    from .mcp_client import get_ai_trip_plan  # optional
except Exception:  # pragma: no cover
    get_ai_trip_plan = None


def _date_range(start_str: str, end_str: str, limit: int | None = None) -> List[str]:
    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except Exception:
        # Fallback: single day
        return [start_str]
    days: List[str] = []
    cur = start
    while cur <= end:
        days.append(cur.date().isoformat())
        cur += timedelta(days=1)
        if limit and len(days) >= limit:
            break
    return days


async def gather_external_data(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    adults: int = 1,
    activities: List[str] | None = None,
    cabin_class: str = "economy",
    preferred_airlines: List[str] | None = None,
    accommodation_type: str | None = None,
    hotel_rating: float | None = None,
    dietary_restrictions: List[str] | None = None,
) -> Dict[str, Any]:
    """Fetch flights, hotels, weather, and places in parallel and return a dict."""
    activities = activities or []

    # Build places queries from activities; fallback to generic
    place_queries = [f"{a} in {destination}" for a in activities] or [f"things to do in {destination}"]

    async def _gather_places():
        # Fetch top few results per query and flatten
        results: List[Dict[str, Any]] = []
        for q in place_queries[:3]:
            try:
                chunk = await search_places(q)
                results.extend(chunk[:5])
            except Exception:
                continue
        # de-duplicate by name
        seen = set()
        deduped = []
        for p in results:
            name = p.get("name")
            if name and name not in seen:
                seen.add(name)
                deduped.append(p)
        return deduped

    async def _gather_events():
        # Fetch events during travel dates
        try:
            return await search_events(destination, start_date, end_date, activities)
        except Exception:
            return []

    async def _gather_restaurants():
        # Fetch restaurant recommendations with dietary restrictions
        try:
            return await search_restaurants(
                destination, 
                activities, 
                dietary_restrictions=dietary_restrictions
            )
        except Exception:
            return []

    async def _gather_visa_safety():
        # Check visa requirements and safety advisories
        try:
            visa_info = await check_visa_requirements(origin, destination)
            safety_info = await get_safety_advisories(destination)
            return {"visa": visa_info, "safety": safety_info}
        except Exception:
            return {"visa": {}, "safety": {}}

    tasks = [
        asyncio.create_task(
            search_flights(
                origin,
                destination,
                start_date,
                adults=adults,
                cabin_class=cabin_class,
                preferred_airlines=preferred_airlines,
            )
        ),
        asyncio.create_task(
            search_hotels(
                destination,
                start_date,
                end_date,
                adults=adults,
                accommodation_type=accommodation_type,
                min_rating=hotel_rating,
            )
        ),
        asyncio.create_task(get_forecast(destination)),
        asyncio.create_task(_gather_places()),
        asyncio.create_task(_gather_events()),
        asyncio.create_task(_gather_restaurants()),
        asyncio.create_task(_gather_visa_safety()),
    ]
    flights, hotels, forecast, places, events, restaurants, visa_safety = await asyncio.gather(*tasks, return_exceptions=False)

    return {
        "flights": flights or [],
        "hotels": hotels or [],
        "forecast": forecast or [],
        "places": places or [],
        "events": events or [],
        "restaurants": restaurants or [],
        "visa_info": visa_safety.get("visa", {}),
        "safety_info": visa_safety.get("safety", {}),
    }


def _filter_days_by_weather(days: List[str], forecast: List[Dict[str, Any]], avoid_bad_weather: bool) -> List[str]:
    if not avoid_bad_weather or not forecast:
        return days
    bad_keywords = {"rain", "storm", "snow", "thunder"}
    bad_dates = set()
    for entry in forecast:
        desc = (entry.get("description") or "").lower()
        date = entry.get("date")
        if date and any(k in desc for k in bad_keywords):
            bad_dates.add(date)
    return [d for d in days if d not in bad_dates] or days  # never drop all days


def _estimate_cost(flights: List[Dict[str, Any]], hotels: List[Dict[str, Any]], nights: int) -> float | None:
    try:
        flight_prices = [f.get("price") for f in flights if isinstance(f.get("price"), (int, float))]
        flight_cost = min(flight_prices) if flight_prices else 0
        hotel_prices = [h.get("price_per_night") for h in hotels if isinstance(h.get("price_per_night"), (int, float))]
        nightly = sum(hotel_prices[:1]) or (hotel_prices[0] if hotel_prices else 0)  # pick top option
        hotel_cost = nightly * max(0, nights)
        return round(float(flight_cost + hotel_cost), 2)
    except Exception:
        return None


def _build_itinerary(days: List[str], places: List[Dict[str, Any]], language: str = "en") -> List[Dict[str, Any]]:
    # naive assignment: 3 activities per day
    itinerary: List[Dict[str, Any]] = []
    idx = 0
    for d in days:
        activities = []
        for _ in range(3):
            if idx < len(places):
                name = places[idx].get("name")
                if name:
                    activities.append(f"Visit {name}")
                idx += 1
        itinerary.append({"date": d, "activities": activities})
    return itinerary


async def generate_itinerary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Main orchestration entrypoint used by the API layer."""
    origin = payload.get("origin")
    destination = payload.get("destination")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    # Travelers and preferences
    adults = int(payload.get("adults") or 1)
    activities = payload.get("activities") or []
    avoid_bad_weather = bool(payload.get("avoid_bad_weather") or False)
    max_days = payload.get("max_itinerary_days")
    language = payload.get("language") or "en"

    # Gather data
    external = await gather_external_data(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        adults=adults,
        activities=activities,
        cabin_class=payload.get("cabin_class") or "economy",
        preferred_airlines=payload.get("preferred_airlines") or [],
        accommodation_type=payload.get("accommodation_type"),
        hotel_rating=payload.get("hotel_rating"),
        dietary_restrictions=payload.get("dietary_restrictions") or [],
    )

    # Days to plan
    days = _date_range(start_date, end_date, limit=max_days)
    days = _filter_days_by_weather(days, external.get("forecast", []), avoid_bad_weather)

    # Try MCP AI first (if available)
    itinerary: List[Dict[str, Any]] = []
    estimated_cost = None
    if get_ai_trip_plan is not None:
        mcp_payload = {
            "params": payload,
            "external": external,
            "days": days,
        }
        try:
            ai_resp = await get_ai_trip_plan(mcp_payload)
            itinerary = ai_resp.get("itinerary", []) if isinstance(ai_resp, dict) else []
            estimated_cost = ai_resp.get("estimated_cost") if isinstance(ai_resp, dict) else None
        except Exception:
            itinerary = []

    # Fallback: heuristic plan
    if not itinerary:
        itinerary = _build_itinerary(days, external.get("places", []), language=language)

    # Simple cost estimate
    estimated_cost = (
        estimated_cost
        if isinstance(estimated_cost, (int, float))
        else _estimate_cost(external.get("flights", []), external.get("hotels", []), nights=max(0, len(days) - 1))
    )

    # Generate booking links for top options
    booking_links = await get_booking_links(
        hotels=external.get("hotels", []),
        flights=external.get("flights", []),
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        adults=adults
    )

    # Create comprehensive trip response
    trip_data = {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "adults": adults,
        "itinerary": itinerary,
        "estimated_cost": estimated_cost,
        "flights": external.get("flights", []),
        "hotels": external.get("hotels", []),
        "restaurants": external.get("restaurants", []),
        "events": external.get("events", []),
        "forecast": external.get("forecast", []),
        "visa_info": external.get("visa_info", {}),
        "safety_info": external.get("safety_info", {}),
        "booking_links": booking_links
    }

    # Create exportable summary
    trip_summary = await create_trip_summary_export(trip_data)

    return {
        "itinerary": itinerary, 
        "estimated_cost": estimated_cost,
        "trip_data": trip_data,
        "trip_summary": trip_summary
    }


