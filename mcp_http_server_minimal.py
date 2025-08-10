import asyncio
from typing import Annotated
import os

from dotenv import load_dotenv

# Load env (support both .env and local.env overrides)
load_dotenv(".env")
load_dotenv("local.env", override=True)

from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import TextContent, ImageContent, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field, AnyUrl

import httpx
import markdownify
import readabilipy

# Import only the needed travel services
from services.weather_api import get_forecast
from services.places_api import search_places
from services.restaurants_api import search_restaurants
from services.visa_api import check_visa_requirements, get_safety_advisories

# --- Config ---
TOKEN = os.environ.get("AUTH_TOKEN") or os.environ.get("MCP_BEARER_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")

assert TOKEN is not None, "Please set AUTH_TOKEN or MCP_BEARER_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"


# --- Auth Provider ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                subject="puch-client"
            )
        return None


# --- Tool descriptions ---
class WeatherDescription(BaseModel):
    """Weather forecasting for travel destinations."""
    type: str = "function"
    function: dict = {
        "name": "get_weather",
        "description": "Get detailed weather forecasts for travel destinations with travel-specific insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location for weather forecast"
                }
            },
            "required": ["location"]
        }
    }

class PlacesDescription(BaseModel):
    """Place discovery for travel destinations."""
    type: str = "function"
    function: dict = {
        "name": "discover_places",
        "description": "Discover places, attractions, and activities in a destination with ratings and details.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Travel destination"
                },
                "category": {
                    "type": "string",
                    "description": "Category of places (attractions, museums, parks, etc.)"
                }
            },
            "required": ["destination"]
        }
    }

class RestaurantDescription(BaseModel):
    """Restaurant discovery for travel destinations."""
    type: str = "function" 
    function: dict = {
        "name": "find_restaurants",
        "description": "Find restaurant recommendations with cuisine types, dietary filters, and price ranges.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location to search for restaurants"
                },
                "cuisine_type": {
                    "type": "string",
                    "description": "Type of cuisine (italian, chinese, etc.)"
                },
                "price_range": {
                    "type": "string",
                    "description": "Price range (budget, mid-range, upscale)"
                }
            },
            "required": ["location"]
        }
    }

class VisaDescription(BaseModel):
    """Travel requirements and visa information."""
    type: str = "function"
    function: dict = {
        "name": "check_travel_requirements", 
        "description": "Check visa requirements and travel safety advisories for international destinations.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_country": {
                    "type": "string",
                    "description": "Destination country"
                },
                "origin_country": {
                    "type": "string", 
                    "description": "Origin/passport country"
                }
            },
            "required": ["destination_country", "origin_country"]
        }
    }


# --- Initialize MCP ---
mcp = FastMCP("AI Travel Assistant", 
             description="Essential travel planning tools: weather, places, restaurants, and travel requirements.")


# --- Essential Tools Only ---

@mcp.tool
async def health_check() -> str:
    """Check if the MCP server is running properly."""
    return "✅ MCP Travel Assistant is running! Available tools: weather, places, restaurants, travel requirements."

@mcp.tool(description=WeatherDescription.model_dump_json())
async def get_weather(
    location: Annotated[str, Field(description="Location for weather forecast")],
) -> str:
    """Get detailed weather forecasts for travel destinations with travel-specific insights."""
    try:
        forecast = await get_forecast(location)
        
        if not forecast:
            return f"❌ Unable to get weather forecast for {location}"
        
        # Format weather response for travel planning
        response = f"🌤️ **Weather Forecast for {location}**\n\n"
        
        # Current conditions
        current = forecast.get("current", {})
        if current:
            temp = current.get("temperature", "N/A")
            condition = current.get("condition", "N/A")
            humidity = current.get("humidity", "N/A")
            wind = current.get("wind_speed", "N/A")
            
            response += f"**Current Conditions:**\n"
            response += f"🌡️ {temp}°C | {condition}\n"
            response += f"💧 Humidity: {humidity}% | 💨 Wind: {wind} km/h\n\n"
        
        # Daily forecast
        daily = forecast.get("daily", [])
        if daily:
            response += "**7-Day Forecast:**\n"
            for day in daily[:7]:
                date = day.get("date", "")
                high = day.get("high_temp", "N/A")
                low = day.get("low_temp", "N/A") 
                condition = day.get("condition", "N/A")
                rain_chance = day.get("rain_chance", 0)
                
                response += f"📅 {date}: {high}/{low}°C | {condition}"
                if rain_chance > 30:
                    response += f" | ☔ {rain_chance}% rain"
                response += "\n"
        
        # Travel tips
        response += "\n🎒 **Travel Tips:**\n"
        if current.get("temperature", 0) < 10:
            response += "• Pack warm clothing and layers\n"
        elif current.get("temperature", 0) > 30:
            response += "• Stay hydrated and wear sun protection\n"
        
        if any(day.get("rain_chance", 0) > 50 for day in daily[:3]):
            response += "• Bring rain gear or umbrella\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Weather forecast failed: {str(e)}"))

@mcp.tool(description=PlacesDescription.model_dump_json())
async def discover_places(
    destination: Annotated[str, Field(description="Travel destination")],
    category: Annotated[str | None, Field(description="Category of places (attractions, museums, parks, etc.)")] = None,
) -> str:
    """Discover places, attractions, and activities in a destination with ratings and details."""
    try:
        places = await search_places(
            location=destination,
            category=category or "tourist_attraction"
        )
        
        if not places:
            return f"❌ No places found in {destination}"
        
        response = f"🌍 **Places to Discover in {destination}**\n"
        if category:
            response += f"📂 Category: {category.title()}\n\n"
        
        for i, place in enumerate(places[:8], 1):
            name = place.get("name", "Unknown Place")
            rating = place.get("rating", "N/A")
            address = place.get("address", "Address not available")
            description = place.get("description", "")
            
            response += f"**{i}. {name}**\n"
            response += f"   ⭐ Rating: {rating} | 📍 {address}\n"
            
            if description:
                # Truncate long descriptions
                desc_short = description[:150] + "..." if len(description) > 150 else description
                response += f"   📝 {desc_short}\n"
            
            # Add category/type if available
            place_type = place.get("types", [])
            if place_type:
                response += f"   🏷️ {', '.join(place_type[:2])}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Places search failed: {str(e)}"))

@mcp.tool(description=RestaurantDescription.model_dump_json())
async def find_restaurants(
    location: Annotated[str, Field(description="Location to search for restaurants")],
    cuisine_type: Annotated[str | None, Field(description="Type of cuisine (italian, chinese, etc.)")] = None,
    price_range: Annotated[str | None, Field(description="Price range (budget, mid-range, upscale)")] = None,
) -> str:
    """Find restaurant recommendations with cuisine types, dietary filters, and price ranges."""
    try:
        restaurants = await search_restaurants(
            location=location,
            cuisine=cuisine_type,
            price_range=price_range
        )
        
        if not restaurants:
            return f"❌ No restaurants found in {location}"
        
        response = f"🍽️ **Restaurant Recommendations in {location}**\n"
        if cuisine_type:
            response += f"🍕 Cuisine: {cuisine_type.title()}\n"
        if price_range:
            response += f"💰 Price Range: {price_range.title()}\n"
        response += "\n"
        
        for i, restaurant in enumerate(restaurants[:8], 1):
            name = restaurant.get("name", "Unknown Restaurant")
            rating = restaurant.get("rating", "N/A")
            cuisine = restaurant.get("cuisine", "")
            price = restaurant.get("price_level", "")
            address = restaurant.get("address", "")
            
            response += f"**{i}. {name}**\n"
            response += f"   ⭐ {rating}"
            
            if cuisine:
                response += f" | 🍴 {cuisine}"
            if price:
                response += f" | 💰 {price}"
            response += "\n"
            
            if address:
                response += f"   📍 {address}\n"
            
            # Add special features
            features = restaurant.get("features", [])
            if features:
                response += f"   ✨ {', '.join(features[:3])}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Restaurant search failed: {str(e)}"))

@mcp.tool(description=VisaDescription.model_dump_json())
async def check_travel_requirements(
    destination_country: Annotated[str, Field(description="Destination country")],
    origin_country: Annotated[str, Field(description="Origin/passport country")],
) -> str:
    """Check visa requirements and travel safety advisories for international destinations."""
    try:
        # Get visa requirements
        visa_info = await check_visa_requirements(origin_country, destination_country)
        
        # Get safety information
        safety_info = await get_safety_advisories(destination_country)
        
        response = f"🛂 **Travel Requirements: {origin_country} → {destination_country}**\n\n"
        
        # Visa Information
        if visa_info:
            visa_required = visa_info.get("visa_required", "Unknown")
            duration = visa_info.get("max_stay", "")
            
            response += "**📋 Visa Requirements:**\n"
            
            if visa_required == "no":
                response += f"✅ No visa required for {origin_country} passport holders\n"
            elif visa_required == "yes":
                response += f"🆔 Visa required for {origin_country} passport holders\n"
            else:
                response += f"ℹ️ Visa status: {visa_required}\n"
            
            if duration:
                response += f"⏱️ Maximum stay: {duration}\n"
            
            # Additional visa details
            requirements = visa_info.get("requirements", [])
            if requirements:
                response += f"📄 Requirements: {', '.join(requirements)}\n"
        
        response += "\n"
        
        # Safety Information
        if safety_info:
            advisory_level = safety_info.get("advisory_level", "")
            summary = safety_info.get("summary", "")
            
            response += "**⚠️ Safety Information:**\n"
            
            if advisory_level:
                if "low" in advisory_level.lower():
                    response += f"🟢 Safety Level: {advisory_level}\n"
                elif "medium" in advisory_level.lower():
                    response += f"🟡 Safety Level: {advisory_level}\n"
                elif "high" in advisory_level.lower():
                    response += f"🔴 Safety Level: {advisory_level}\n"
                else:
                    response += f"📊 Safety Level: {advisory_level}\n"
            
            if summary:
                response += f"📰 {summary}\n"
            
            # Health recommendations
            health = safety_info.get("health", {})
            if health:
                vaccines = health.get("recommended_vaccines", [])
                if vaccines:
                    response += f"💉 Recommended vaccines: {', '.join(vaccines)}\n"
        
        response += "\n🔍 **Always verify current requirements with official embassy sources before travel.**"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Travel requirements check failed: {str(e)}"))


# --- Initialize with auth ---
auth_provider = SimpleBearerAuthProvider(TOKEN)
mcp.auth.set_provider(auth_provider)


async def main():
    """Run the MCP server on the port specified by Render or default to 8086."""
    port = int(os.environ.get("PORT", 8086))
    print(f"🚀 Starting Essential Travel MCP Server on port {port}")
    print(f"🌐 Available tools: weather, places, restaurants, travel requirements")
    print(f"🔑 Auth: Bearer token authentication")
    await mcp.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8086))
    uvicorn.run(
        "mcp_http_server:mcp.app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
