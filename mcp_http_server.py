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

# Import travel planning services
from services.ai_trip_planner import generate_itinerary
from services.flights_api import search_flights
from services.hotels_api import search_hotels
from services.weather_api import get_forecast
from services.places_api import search_places
from services.events_api import search_events
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
                expires_at=None,
            )
        return None


# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None


# --- Fetch Utility Class ---
class Fetch:
    USER_AGENT = "Puch/1.0 (Autonomous)"

    @classmethod
    async def fetch_url(
        cls,
        url: str,
        user_agent: str,
        force_raw: bool = False,
    ) -> tuple[str, str]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={"User-Agent": user_agent},
                    timeout=30,
                )
            except httpx.HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))

            if response.status_code >= 400:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - status code {response.status_code}"))

            page_raw = response.text

        content_type = response.headers.get("content-type", "")
        is_page_html = "text/html" in content_type

        if is_page_html and not force_raw:
            return cls.extract_content_from_html(page_raw), ""

        return (
            page_raw,
            f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n",
        )

    @staticmethod
    def extract_content_from_html(html: str) -> str:
        """Extract and convert HTML content to Markdown format."""
        ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
        if not ret or not ret.get("content"):
            return "<error>Page failed to be simplified from HTML</error>"
        content = markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)
        return content

    @staticmethod
    async def google_search_links(query: str, num_results: int = 5) -> list[str]:
        """
        Perform a scoped DuckDuckGo search and return a list of URLs.
        (Using DuckDuckGo because Google blocks most programmatic scraping.)
        """
        ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        links: list[str] = []

        async with httpx.AsyncClient() as client:
            resp = await client.get(ddg_url, headers={"User-Agent": Fetch.USER_AGENT})
            if resp.status_code != 200:
                return ["<error>Failed to perform search.</error>"]

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", class_="result__a", href=True):
            href = a["href"]
            if "http" in href:
                links.append(href)
            if len(links) >= num_results:
                break

        return links or ["<error>No results found.</error>"]


# --- MCP Server Setup ---
mcp = FastMCP(
    "AI Trip Planner MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)


# --- Tool: validate (required by Puch) ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER



# --- Travel Planning Tools ---

# Trip Planning Tool
TripPlannerDescription = RichToolDescription(
    description="Comprehensive AI-powered trip planner that handles flights, hotels, weather, activities, restaurants, and visa requirements.",
    use_when="Use this tool when users want to plan a complete trip with multiple components like flights, accommodations, activities, and dining.",
    side_effects="Generates a complete travel itinerary with bookings, weather forecasts, and travel advisories.",
)

@mcp.tool(description=TripPlannerDescription.model_dump_json())
async def plan_trip(
    origin: Annotated[str, Field(description="Starting city/airport code")],
    destination: Annotated[str, Field(description="Destination city/airport code")],
    start_date: Annotated[str, Field(description="Trip start date (YYYY-MM-DD)")],
    end_date: Annotated[str, Field(description="Trip end date (YYYY-MM-DD)")],
    adults: Annotated[int, Field(description="Number of adult travelers")] = 1,
    budget: Annotated[float | None, Field(description="Budget in USD")] = None,
    activities: Annotated[list[str], Field(description="Preferred activities (e.g., museums, nightlife, outdoor)")] = [],
    accommodation_type: Annotated[str | None, Field(description="Hotel, apartment, hostel")] = None,
    dietary_restrictions: Annotated[list[str], Field(description="Dietary needs (vegetarian, halal, etc.)")] = [],
) -> str:
    """Generate a comprehensive trip plan with flights, hotels, activities, restaurants, and travel info."""
    try:
        # Prepare trip request payload
        trip_payload = {
            "origin": origin,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "adults": adults,
            "budget": budget,
            "activities": activities,
            "accommodation_type": accommodation_type,
            "dietary_restrictions": dietary_restrictions,
            "avoid_bad_weather": True,
            "language": "en"
        }
        
        # Generate comprehensive trip plan
        result = await generate_itinerary(trip_payload)
        trip_data = result.get("trip_data", {})
        
        # Format response
        response = f"🌍 **Complete Trip Plan: {origin} → {destination}**\n\n"
        response += f"📅 **Dates**: {start_date} to {end_date}\n"
        response += f"👥 **Travelers**: {adults} adult(s)\n"
        
        if result.get("estimated_cost"):
            response += f"💰 **Estimated Cost**: ${result['estimated_cost']:.2f}\n\n"
        
        # Flight options
        flights = trip_data.get("flights", [])[:3]
        if flights:
            response += "✈️ **Flight Options:**\n"
            for i, flight in enumerate(flights, 1):
                response += f"{i}. {flight.get('airline', 'Unknown')} - ${flight.get('price', 'N/A')} - {flight.get('departure_time', 'TBD')}\n"
            response += "\n"
        
        # Hotel options
        hotels = trip_data.get("hotels", [])[:3]
        if hotels:
            response += "🏨 **Hotel Options:**\n"
            for i, hotel in enumerate(hotels, 1):
                response += f"{i}. {hotel.get('name', 'Unknown')} - ${hotel.get('price_per_night', 'N/A')}/night - ⭐{hotel.get('rating', 'N/A')}\n"
            response += "\n"
        
        # Daily itinerary
        itinerary = result.get("itinerary", [])
        if itinerary:
            response += "📋 **Daily Itinerary:**\n"
            for day in itinerary[:5]:  # Limit to 5 days
                response += f"**{day.get('date', 'TBD')}:**\n"
                for activity in day.get("activities", [])[:3]:
                    response += f"  • {activity}\n"
                response += "\n"
        
        # Restaurant recommendations
        restaurants = trip_data.get("restaurants", [])[:5]
        if restaurants:
            response += "🍽️ **Restaurant Recommendations:**\n"
            for restaurant in restaurants:
                response += f"• {restaurant.get('name', 'Unknown')} - {restaurant.get('cuisine', 'Various')} - {restaurant.get('price_level', '$')}\n"
            response += "\n"
        
        # Events and activities
        events = trip_data.get("events", [])[:3]
        if events:
            response += "🎭 **Events During Your Visit:**\n"
            for event in events:
                response += f"• {event.get('name', 'Unknown Event')} - {event.get('start_time', 'TBD')}\n"
            response += "\n"
        
        # Travel advisories
        visa_info = trip_data.get("visa_info", {})
        safety_info = trip_data.get("safety_info", {})
        if visa_info or safety_info:
            response += "ℹ️ **Important Travel Information:**\n"
            if visa_info.get("required"):
                response += f"• Visa Required: {visa_info.get('details', 'Check requirements')}\n"
            if safety_info.get("advisories"):
                response += f"• Safety Advisory: {safety_info.get('level', 'Standard precautions')}\n"
            response += "\n"
        
        # Booking links
        booking_links = trip_data.get("booking_links", {})
        if booking_links:
            response += "🔗 **Quick Booking Links:**\n"
            if booking_links.get("hotels"):
                response += f"• Hotels: {len(booking_links['hotels'])} options available\n"
            if booking_links.get("flights"):
                response += f"• Flights: {len(booking_links['flights'])} booking options\n"
            response += "\n"
        
        response += "✨ **Trip planning complete! Use the booking links to reserve your selections.**"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Trip planning failed: {str(e)}"))


# Weather Tool
WeatherDescription = RichToolDescription(
    description="Get detailed weather forecasts for travel destinations with travel-specific insights.",
    use_when="Use this when users need weather information for trip planning or current destination conditions.",
    side_effects="Returns weather forecast with travel recommendations and packing suggestions.",
)

@mcp.tool(description=WeatherDescription.model_dump_json())
async def get_weather(
    location: Annotated[str, Field(description="City or location name")],
    days: Annotated[int, Field(description="Number of forecast days (1-7)")] = 5,
) -> str:
    """Get weather forecast with travel-specific insights."""
    try:
        forecast = await get_forecast(location)
        
        if not forecast:
            return f"❌ Unable to get weather forecast for {location}"
        
        response = f"🌤️ **Weather Forecast for {location}**\n\n"
        
        for i, day in enumerate(forecast[:days]):
            date = day.get("date", "Unknown")
            temp_high = day.get("temperature_high", "N/A")
            temp_low = day.get("temperature_low", "N/A")
            description = day.get("description", "No description")
            
            response += f"**{date}**: {temp_high}°/{temp_low}° - {description}\n"
            
            # Add travel recommendations
            if "rain" in description.lower() or "storm" in description.lower():
                response += "  🌧️ *Recommend indoor activities*\n"
            elif "snow" in description.lower():
                response += "  ❄️ *Pack warm clothes, check transport*\n"
            elif "sun" in description.lower() or "clear" in description.lower():
                response += "  ☀️ *Perfect for outdoor activities*\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Weather lookup failed: {str(e)}"))


# Hotel Search Tool
HotelSearchDescription = RichToolDescription(
    description="Search for hotels and accommodations with filtering options for dates, price, and amenities.",
    use_when="Use this when users need to find specific hotel options or compare accommodations.",
    side_effects="Returns hotel options with prices, ratings, and booking information.",
)

@mcp.tool(description=HotelSearchDescription.model_dump_json())
async def search_hotel_options(
    destination: Annotated[str, Field(description="Destination city")],
    check_in: Annotated[str, Field(description="Check-in date (YYYY-MM-DD)")],
    check_out: Annotated[str, Field(description="Check-out date (YYYY-MM-DD)")],
    adults: Annotated[int, Field(description="Number of adults")] = 1,
    min_rating: Annotated[float | None, Field(description="Minimum hotel rating (1.0-5.0)")] = None,
    accommodation_type: Annotated[str | None, Field(description="hotel, apartment, hostel")] = None,
) -> str:
    """Search for hotel accommodations with detailed information."""
    try:
        hotels = await search_hotels(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            min_rating=min_rating,
            accommodation_type=accommodation_type
        )
        
        if not hotels:
            return f"❌ No hotels found for {destination} on {check_in} to {check_out}"
        
        response = f"🏨 **Hotel Options in {destination}**\n"
        response += f"📅 {check_in} to {check_out} | 👥 {adults} adult(s)\n\n"
        
        for i, hotel in enumerate(hotels[:8], 1):
            name = hotel.get("name", "Unknown Hotel")
            price = hotel.get("price_per_night", "N/A")
            rating = hotel.get("rating", "N/A")
            address = hotel.get("address", "Address not available")
            
            response += f"**{i}. {name}**\n"
            response += f"   💰 ${price}/night | ⭐ {rating} | 📍 {address}\n"
            
            # Add amenities if available
            amenities = hotel.get("amenities", [])
            if amenities:
                response += f"   🎯 {', '.join(amenities[:3])}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Hotel search failed: {str(e)}"))


# Flight Search Tool
FlightSearchDescription = RichToolDescription(
    description="Search for flights with options for dates, cabin class, and airline preferences.",
    use_when="Use this when users need to find flight options or compare airfares.",
    side_effects="Returns flight options with prices, times, and booking information.",
)

@mcp.tool(description=FlightSearchDescription.model_dump_json())
async def search_flight_options(
    origin: Annotated[str, Field(description="Origin city or airport code")],
    destination: Annotated[str, Field(description="Destination city or airport code")],
    departure_date: Annotated[str, Field(description="Departure date (YYYY-MM-DD)")],
    return_date: Annotated[str | None, Field(description="Return date for round trip")] = None,
    adults: Annotated[int, Field(description="Number of adult passengers")] = 1,
    cabin_class: Annotated[str, Field(description="economy, business, first")] = "economy",
) -> str:
    """Search for flight options with detailed information."""
    try:
        flights = await search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=adults,
            cabin_class=cabin_class
        )
        
        if not flights:
            return f"❌ No flights found from {origin} to {destination} on {departure_date}"
        
        trip_type = "Round Trip" if return_date else "One Way"
        response = f"✈️ **Flight Options: {origin} → {destination}**\n"
        response += f"📅 {departure_date} | 👥 {adults} adult(s) | 🎫 {cabin_class.title()} | {trip_type}\n\n"
        
        for i, flight in enumerate(flights[:6], 1):
            airline = flight.get("airline", "Unknown")
            price = flight.get("price", "N/A")
            departure_time = flight.get("departure_time", "TBD")
            arrival_time = flight.get("arrival_time", "TBD")
            duration = flight.get("duration", "N/A")
            stops = flight.get("stops", 0)
            
            response += f"**{i}. {airline}**\n"
            response += f"   💰 ${price} | 🕐 {departure_time} → {arrival_time} ({duration})\n"
            response += f"   ✈️ {stops} stop(s)\n\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Flight search failed: {str(e)}"))


# Places and Activities Tool
PlacesDescription = RichToolDescription(
    description="Discover places, attractions, and activities in a destination with ratings and details.",
    use_when="Use this when users want to explore what to do and see in a destination.",
    side_effects="Returns list of attractions, activities, and points of interest with details.",
)

@mcp.tool(description=PlacesDescription.model_dump_json())
async def discover_places(
    destination: Annotated[str, Field(description="Destination city or area")],
    activity_type: Annotated[str | None, Field(description="museums, restaurants, nightlife, outdoor, shopping")] = None,
    limit: Annotated[int, Field(description="Number of results to return")] = 10,
) -> str:
    """Discover places and activities in a destination."""
    try:
        query = f"{activity_type} in {destination}" if activity_type else f"things to do in {destination}"
        places = await search_places(query)
        
        if not places:
            return f"❌ No places found for {query}"
        
        response = f"🎯 **Places to Visit in {destination}**\n"
        if activity_type:
            response += f"🔍 Category: {activity_type.title()}\n"
        response += "\n"
        
        for i, place in enumerate(places[:limit], 1):
            name = place.get("name", "Unknown Place")
            rating = place.get("rating", "N/A")
            address = place.get("address", "Address not available")
            description = place.get("description", "")
            
            response += f"**{i}. {name}**\n"
            response += f"   ⭐ {rating} | 📍 {address}\n"
            
            if description:
                response += f"   📝 {description[:100]}{'...' if len(description) > 100 else ''}\n"
            
            response += "\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Places search failed: {str(e)}"))


# Restaurant Recommendations Tool
RestaurantDescription = RichToolDescription(
    description="Find restaurant recommendations with cuisine types, dietary filters, and price ranges.",
    use_when="Use this when users need dining recommendations for their destination.",
    side_effects="Returns restaurant suggestions with ratings, cuisine types, and dietary compatibility.",
)

@mcp.tool(description=RestaurantDescription.model_dump_json())
async def find_restaurants(
    destination: Annotated[str, Field(description="Destination city")],
    cuisine_types: Annotated[list[str], Field(description="Preferred cuisine types")] = [],
    dietary_restrictions: Annotated[list[str], Field(description="vegetarian, vegan, halal, kosher, gluten-free")] = [],
    price_range: Annotated[str | None, Field(description="$, $$, $$$, $$$$")] = None,
) -> str:
    """Find restaurant recommendations with dietary and cuisine preferences."""
    try:
        restaurants = await search_restaurants(
            city=destination,
            cuisine_types=cuisine_types,
            price_range=price_range,
            dietary_restrictions=dietary_restrictions
        )
        
        if not restaurants:
            return f"❌ No restaurants found in {destination} matching your criteria"
        
        response = f"🍽️ **Restaurant Recommendations in {destination}**\n"
        if cuisine_types:
            response += f"🍜 Cuisine: {', '.join(cuisine_types)}\n"
        if dietary_restrictions:
            response += f"🥗 Dietary: {', '.join(dietary_restrictions)}\n"
        if price_range:
            response += f"💰 Price Range: {price_range}\n"
        response += "\n"
        
        for i, restaurant in enumerate(restaurants[:10], 1):
            name = restaurant.get("name", "Unknown Restaurant")
            rating = restaurant.get("rating", "N/A")
            price_level = restaurant.get("price_level", "N/A")
            cuisine = restaurant.get("cuisine", "Various")
            address = restaurant.get("address", "Address not available")
            
            response += f"**{i}. {name}**\n"
            response += f"   ⭐ {rating} | 💰 {price_level} | 🍽️ {cuisine}\n"
            response += f"   📍 {address}\n\n"
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Restaurant search failed: {str(e)}"))


# Visa and Travel Advisory Tool
VisaDescription = RichToolDescription(
    description="Check visa requirements and travel safety advisories for international destinations.",
    use_when="Use this when users need visa information or safety updates for international travel.",
    side_effects="Returns visa requirements, application processes, and current safety advisories.",
)

@mcp.tool(description=VisaDescription.model_dump_json())
async def check_travel_requirements(
    origin_country: Annotated[str, Field(description="Traveler's home country")],
    destination_country: Annotated[str, Field(description="Destination country")],
) -> str:
    """Check visa requirements and travel safety advisories."""
    try:
        # Get visa requirements
        visa_info = await check_visa_requirements(origin_country, destination_country)
        safety_info = await get_safety_advisories(destination_country)
        
        response = f"📋 **Travel Requirements: {origin_country} → {destination_country}**\n\n"
        
        # Visa information
        if visa_info:
            response += "🛂 **Visa Requirements:**\n"
            if visa_info.get("required"):
                response += f"   ✅ Visa Required: {visa_info.get('type', 'Tourist visa')}\n"
                response += f"   ⏱️ Processing Time: {visa_info.get('processing_time', 'Check embassy')}\n"
                response += f"   💰 Fee: {visa_info.get('fee', 'Contact embassy')}\n"
            else:
                response += "   ✅ No visa required for tourist visits\n"
            
            if visa_info.get("duration"):
                response += f"   📅 Max Stay: {visa_info.get('duration')}\n"
            response += "\n"
        
        # Safety advisories
        if safety_info:
            response += "⚠️ **Safety Advisory:**\n"
            response += f"   🚨 Level: {safety_info.get('level', 'Standard precautions')}\n"
            
            if safety_info.get("advisories"):
                for advisory in safety_info["advisories"][:3]:
                    response += f"   • {advisory}\n"
            
            response += f"   📅 Last Updated: {safety_info.get('last_updated', 'N/A')}\n\n"
        
        response += "ℹ️ **Note**: Always verify current requirements with official embassy sources before travel."
        
        return response
        
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Travel requirements check failed: {str(e)}"))


# --- Run MCP Server ---
async def main():
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8086"))
    print(f"🚀 Starting MCP server on http://{host}:{port}")
    await mcp.run_async("streamable-http", host=host, port=port)


if __name__ == "__main__":
    asyncio.run(main())
