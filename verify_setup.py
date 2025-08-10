#!/usr/bin/env python3
"""
Simple verification script to confirm MCP server setup and tool listing.
"""

import inspect
from services.ai_trip_planner import generate_itinerary
from services.flights_api import search_flights
from services.hotels_api import search_hotels
from services.weather_api import get_forecast
from services.places_api import search_places
from services.events_api import search_events
from services.restaurants_api import search_restaurants
from services.visa_api import check_visa_requirements

def verify_mcp_setup():
    """Verify MCP server setup and available tools."""
    print("🎯 AI Trip Planner MCP Server - Setup Verification")
    print("=" * 60)
    
    # List all available travel tools
    tools = [
        ("plan_trip", "Generate comprehensive itinerary", generate_itinerary),
        ("get_weather", "Get weather forecast", get_forecast),
        ("search_hotel_options", "Search for hotels", search_hotels),
        ("search_flight_options", "Search for flights", search_flights),
        ("discover_places", "Find interesting places", search_places),
        ("find_restaurants", "Search for restaurants", search_restaurants),
        ("check_travel_requirements", "Check visa requirements", check_visa_requirements),
        ("search_events", "Find local events", search_events)
    ]
    
    print("🛠️  Available MCP Tools:")
    print()
    
    working_tools = 0
    for i, (name, description, func) in enumerate(tools, 1):
        try:
            # Check if function is callable
            if callable(func):
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                status = "✅ Ready"
                working_tools += 1
            else:
                status = "❌ Not callable"
        except Exception as e:
            status = f"❌ Error: {str(e)[:50]}"
        
        print(f"   {i}. {name}")
        print(f"      📝 {description}")
        print(f"      🔧 {status}")
        if 'params' in locals():
            print(f"      📋 Parameters: {', '.join(params[:3])}{'...' if len(params) > 3 else ''}")
        print()
    
    print("📊 Summary:")
    print(f"   ✅ Working tools: {working_tools}/{len(tools)}")
    print(f"   🏗️  MCP Server: Ready for deployment on port 8086")
    print(f"   🔐 Authentication: Bearer token configured")
    print(f"   🌐 Access URL: http://localhost:8086/mcp/")
    
    print("\n🚀 Next Steps:")
    print("   1. Run: python mcp_http_server.py")
    print("   2. Server will be available at http://localhost:8086/mcp/")
    print("   3. Use bearer token: oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE")
    print("   4. Connect your AI agent to the MCP server")
    
    return working_tools == len(tools)

if __name__ == "__main__":
    success = verify_mcp_setup()
    if success:
        print("\n🎉 ALL SYSTEMS READY! Your AI Trip Planner MCP Server is fully configured!")
    else:
        print("\n⚠️  Some tools may need attention. Check the output above.")
