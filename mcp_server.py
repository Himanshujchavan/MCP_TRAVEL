"""
MCP stdio server for AI Trip Planner

Exposes tools:
- plan_trip
- search_flights
- search_hotels
- get_weather
- search_places

Run (from project root):
  python mcp_server.py

Then configure your MCP client (e.g., Puch AI) to launch this command.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv

# Load env files so services have API keys
load_dotenv(".env")
load_dotenv("local.env", override=True)

# Reuse existing services
from services.ai_trip_planner import generate_itinerary
from services.flights_api import search_flights as svc_search_flights
from services.hotels_api import search_hotels as svc_search_hotels
from services.weather_api import get_weather as svc_get_weather
from services.places_api import search_places as svc_search_places

# MCP server primitives
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from core.http_client import close_client


server = Server("ai-trip-planner")


def _json_content(payload: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload))]


@server.tool(
    name="plan_trip",
    description="Generate an itinerary using flights/hotels/weather/places and user preferences.",
    input_schema={
        "type": "object",
        "properties": {
            "origin": {"type": "string"},
            "destination": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
            "budget": {"type": "number"},
            "travelers": {"type": "integer"},
            "adults": {"type": "integer"},
            "children": {"type": "integer"},
            "senior_citizens": {"type": "integer"},
            "accommodation_type": {"type": "string"},
            "hotel_rating": {"type": "number"},
            "preferred_airlines": {"type": "array", "items": {"type": "string"}},
            "cabin_class": {"type": "string"},
            "activities": {"type": "array", "items": {"type": "string"}},
            "dietary_preferences": {"type": "array", "items": {"type": "string"}},
            "transportation_mode": {"type": "string"},
            "weather_preference": {"type": "string"},
            "avoid_bad_weather": {"type": "boolean"},
            "detail_level": {"type": "string"},
            "max_itinerary_days": {"type": "integer"},
            "language": {"type": "string"},
        },
        "required": ["origin", "destination", "start_date", "end_date"],
        "additionalProperties": True,
    },
)
async def tool_plan_trip(**kwargs: Dict[str, Any]):
    result = await generate_itinerary(kwargs)
    return _json_content(result)


@server.tool(
    name="search_flights",
    description="Search flights for a given origin, destination, and date.",
    input_schema={
        "type": "object",
        "properties": {
            "origin": {"type": "string"},
            "destination": {"type": "string"},
            "date": {"type": "string"},
            "adults": {"type": "integer", "default": 1},
            "currency": {"type": "string", "default": "USD"},
            "cabin_class": {"type": "string", "default": "economy"},
            "preferred_airlines": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["origin", "destination", "date"],
    },
)
async def tool_search_flights(**kwargs: Dict[str, Any]):
    flights = await svc_search_flights(
        kwargs["origin"],
        kwargs["destination"],
        kwargs["date"],
        adults=int(kwargs.get("adults", 1)),
        currency=kwargs.get("currency", "USD"),
        cabin_class=kwargs.get("cabin_class", "economy"),
        preferred_airlines=kwargs.get("preferred_airlines"),
    )
    return _json_content(flights)


@server.tool(
    name="search_hotels",
    description="Search hotels for a location and date range.",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string"},
            "check_in": {"type": "string"},
            "check_out": {"type": "string"},
            "adults": {"type": "integer", "default": 1},
            "accommodation_type": {"type": "string"},
            "min_rating": {"type": "number"},
            "page_size": {"type": "integer", "default": 10},
        },
        "required": ["location", "check_in", "check_out"],
    },
)
async def tool_search_hotels(**kwargs: Dict[str, Any]):
    hotels = await svc_search_hotels(
        kwargs["location"],
        kwargs["check_in"],
        kwargs["check_out"],
        adults=int(kwargs.get("adults", 1)),
        page_size=int(kwargs.get("page_size", 10)),
        accommodation_type=kwargs.get("accommodation_type"),
        min_rating=kwargs.get("min_rating"),
    )
    return _json_content(hotels)


@server.tool(
    name="get_weather",
    description="Get current weather for a city.",
    input_schema={
        "type": "object",
        "properties": {"city": {"type": "string"}, "units": {"type": "string", "default": "metric"}},
        "required": ["city"],
    },
)
async def tool_get_weather(**kwargs: Dict[str, Any]):
    data = await svc_get_weather(kwargs["city"], units=kwargs.get("units", "metric"))
    return _json_content(data)


@server.tool(
    name="search_places",
    description="Search places/attractions using a free-text query (e.g., 'museums in Rome').",
    input_schema={
        "type": "object",
        "properties": {"query": {"type": "string"}, "region": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["query"],
    },
)
async def tool_search_places(**kwargs: Dict[str, Any]):
    results = await svc_search_places(kwargs["query"], region=kwargs.get("region"), limit=kwargs.get("limit", 10))
    return _json_content(results)


async def amain():
    # Run MCP server over stdio
    try:
        async with stdio_server() as (read, write):
            await server.run(read, write)
    finally:
        # Close shared http client used by services
        try:
            await close_client()
        except Exception:
            pass


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
