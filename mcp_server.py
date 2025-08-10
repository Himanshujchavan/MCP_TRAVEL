"""
MCP stdio server for Essential Travel Tools

Exposes only 4 essential tools:
- get_weather
- discover_places  
- find_restaurants
- check_travel_requirements

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

# Import only the 4 essential services
from services.weather_api import get_forecast
from services.places_api import search_places as svc_search_places
from services.restaurants_api import search_restaurants as svc_search_restaurants
from services.visa_api import check_visa_requirements, get_safety_advisories

# MCP server primitives
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from core.http_client import close_client


server = Server("essential-travel-assistant")


def _json_content(payload: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload))]


@server.tool(
    name="get_weather",
    description="Get detailed weather forecasts for travel destinations with travel-specific insights.",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "Location for weather forecast"},
        },
        "required": ["location"],
    },
)
async def tool_get_weather(**kwargs: Dict[str, Any]):
    forecast = await get_forecast(kwargs["location"])
    return _json_content(forecast)


@server.tool(
    name="discover_places",
    description="Discover places, attractions, and activities in a destination with ratings and details.",
    input_schema={
        "type": "object",
        "properties": {
            "destination": {"type": "string", "description": "Travel destination"},
            "category": {"type": "string", "description": "Category of places (attractions, museums, parks, etc.)"},
        },
        "required": ["destination"],
    },
)
async def tool_discover_places(**kwargs: Dict[str, Any]):
    places = await svc_search_places(
        location=kwargs["destination"],
        category=kwargs.get("category", "tourist_attraction")
    )
    return _json_content(places)


@server.tool(
    name="find_restaurants",
    description="Find restaurant recommendations with cuisine types, dietary filters, and price ranges.",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "Location to search for restaurants"},
            "cuisine_type": {"type": "string", "description": "Type of cuisine (italian, chinese, etc.)"},
            "price_range": {"type": "string", "description": "Price range (budget, mid-range, upscale)"},
        },
        "required": ["location"],
    },
)
async def tool_find_restaurants(**kwargs: Dict[str, Any]):
    restaurants = await svc_search_restaurants(
        location=kwargs["location"],
        cuisine=kwargs.get("cuisine_type"),
        price_range=kwargs.get("price_range")
    )
    return _json_content(restaurants)


@server.tool(
    name="check_travel_requirements",
    description="Check visa requirements and travel safety advisories for international destinations.",
    input_schema={
        "type": "object",
        "properties": {
            "destination_country": {"type": "string", "description": "Destination country"},
            "origin_country": {"type": "string", "description": "Origin/passport country"},
        },
        "required": ["destination_country", "origin_country"],
    },
)
async def tool_check_travel_requirements(**kwargs: Dict[str, Any]):
    # Get visa requirements
    visa_info = await check_visa_requirements(
        kwargs["origin_country"], 
        kwargs["destination_country"]
    )
    
    # Get safety information
    safety_info = await get_safety_advisories(kwargs["destination_country"])
    
    result = {
        "visa_requirements": visa_info,
        "safety_advisories": safety_info
    }
    return _json_content(result)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(close_client())
