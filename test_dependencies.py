#!/usr/bin/env python3
"""
Test script to verify all dependencies are working for AI Trip Planner MCP Server
"""
import sys
import importlib

def test_import(module_name, alias=None):
    """Test importing a module"""
    try:
        if alias:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name} (as {alias}) - OK")
        else:
            importlib.import_module(module_name)
            print(f"✅ {module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - FAILED: {e}")
        return False

def main():
    """Test all required dependencies"""
    print("🔍 Testing AI Trip Planner MCP Server Dependencies...\n")
    
    # Core dependencies
    dependencies = [
        'fastapi',
        'uvicorn', 
        'starlette',
        'fastmcp',
        'mcp',
        'httpx',
        'anyio',
        'aiofiles',
        'pydantic',
        'dotenv',
        'bs4',
        'markdownify',
        'readabilipy',
        'lxml',
        'html5lib',
        'regex',
        'PIL',
        'cryptography',
        'typing_extensions',
        'click',
        'rich',
        'pytest',
        'requests',
        'six'
    ]
    
    print("📦 Core Dependencies:")
    success_count = 0
    for dep in dependencies:
        if test_import(dep):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{len(dependencies)} dependencies available")
    
    # Test travel planning services
    print("\n🌍 Testing Travel Planning Services:")
    try:
        from services.ai_trip_planner import generate_itinerary
        from core.http_client import get_client
        from services.flights_api import search_flights
        from services.hotels_api import search_hotels
        from services.weather_api import get_forecast
        from services.places_api import search_places
        from services.events_api import search_events
        from services.restaurants_api import search_restaurants
        from services.visa_api import check_visa_requirements
        print("✅ All travel planning services - OK")
        success_count += 1
    except ImportError as e:
        print(f"❌ Travel planning services - FAILED: {e}")
    
    # Test MCP server components
    print("\n🚀 Testing MCP Server Components:")
    try:
        from mcp.types import TextContent, ImageContent, INVALID_PARAMS, INTERNAL_ERROR
        from mcp import ErrorData, McpError
        from fastmcp import FastMCP
        print("✅ MCP server components - OK")
        success_count += 1
    except ImportError as e:
        print(f"❌ MCP server components - FAILED: {e}")
    
    total_tests = len(dependencies) + 2
    print(f"\n🎯 Final Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("\n🎉 ALL DEPENDENCIES READY! Your AI Trip Planner MCP Server is ready to run!")
        return True
    else:
        print(f"\n⚠️  {total_tests - success_count} dependencies missing. Please install missing packages.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
