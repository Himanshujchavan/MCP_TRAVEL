# services/events_api.py
import os
from typing import List, Dict, Any
from core.http_client import get_json

EVENTBRITE_KEY = os.getenv("EVENTBRITE_API_KEY")
TICKETMASTER_KEY = os.getenv("TICKETMASTER_API_KEY")

async def search_events(
    city: str, 
    start_date: str, 
    end_date: str,
    categories: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for events during travel dates.
    Combines multiple event sources.
    """
    events = []
    
    # Try Eventbrite first
    if EVENTBRITE_KEY:
        try:
            events.extend(await _search_eventbrite(city, start_date, end_date, categories))
        except Exception:
            pass
    
    # Try Ticketmaster
    if TICKETMASTER_KEY:
        try:
            events.extend(await _search_ticketmaster(city, start_date, end_date, categories))
        except Exception:
            pass
    
    # Fallback: basic event suggestions
    if not events:
        events = _generate_basic_events(city, categories or [])
    
    return events[:10]  # Limit results

async def _search_eventbrite(city: str, start_date: str, end_date: str, categories: List[str]) -> List[Dict[str, Any]]:
    """Search Eventbrite API for events"""
    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "location.address": city,
        "start_date.range_start": f"{start_date}T00:00:00",
        "start_date.range_end": f"{end_date}T23:59:59",
        "token": EVENTBRITE_KEY
    }
    
    data = await get_json(url, params=params)
    events = []
    
    for event in data.get("events", []):
        events.append({
            "name": event.get("name", {}).get("text", ""),
            "description": event.get("description", {}).get("text", "")[:200],
            "start_time": event.get("start", {}).get("local", ""),
            "venue": event.get("venue_id", ""),
            "url": event.get("url", ""),
            "source": "eventbrite"
        })
    
    return events

async def _search_ticketmaster(city: str, start_date: str, end_date: str, categories: List[str]) -> List[Dict[str, Any]]:
    """Search Ticketmaster API for events"""
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "city": city,
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z",
        "apikey": TICKETMASTER_KEY
    }
    
    data = await get_json(url, params=params)
    events = []
    
    for event in data.get("_embedded", {}).get("events", []):
        events.append({
            "name": event.get("name", ""),
            "description": event.get("info", "")[:200] if event.get("info") else "",
            "start_time": event.get("dates", {}).get("start", {}).get("localDate", ""),
            "venue": event.get("_embedded", {}).get("venues", [{}])[0].get("name", ""),
            "url": event.get("url", ""),
            "source": "ticketmaster"
        })
    
    return events

def _generate_basic_events(city: str, categories: List[str]) -> List[Dict[str, Any]]:
    """Generate basic event suggestions when APIs fail"""
    basic_events = [
        {"name": f"Local Walking Tour in {city}", "description": "Explore the city's highlights", "source": "suggestion"},
        {"name": f"Food Market Visit in {city}", "description": "Experience local cuisine", "source": "suggestion"},
        {"name": f"Museum Day in {city}", "description": "Visit top museums and galleries", "source": "suggestion"}
    ]
    
    if "nightlife" in categories:
        basic_events.append({"name": f"Evening Entertainment in {city}", "description": "Local nightlife scene", "source": "suggestion"})
    
    if "music" in categories:
        basic_events.append({"name": f"Live Music Venues in {city}", "description": "Local music scene", "source": "suggestion"})
        
    return basic_events
