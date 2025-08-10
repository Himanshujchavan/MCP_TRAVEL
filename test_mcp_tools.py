#!/usr/bin/env python3
"""
Test script to verify MCP server tools are working correctly.
"""

import httpx
import json
import asyncio

MCP_URL = "http://localhost:8086/mcp"
AUTH_TOKEN = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"

async def test_mcp_tools():
    """Test the MCP server tools."""
    print("🧪 Testing AI Trip Planner MCP Server Tools...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test tools list
            print("\n📋 Getting available tools...")
            response = await client.post(
                f"{MCP_URL}/tools/list",
                headers=headers,
                json={}
            )
            
            if response.status_code == 200:
                tools_data = response.json()
                tools = tools_data.get("tools", [])
                print(f"✅ Found {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"   {i}. {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')}")
            else:
                print(f"❌ Failed to get tools list: {response.status_code}")
                print(f"Response: {response.text}")
                return
            
            # Test a simple tool (weather)
            print("\n🌤️  Testing weather tool...")
            weather_request = {
                "name": "get_weather",
                "arguments": {
                    "location": "Paris",
                    "days": 3
                }
            }
            
            response = await client.post(
                f"{MCP_URL}/tools/call",
                headers=headers,
                json=weather_request
            )
            
            if response.status_code == 200:
                weather_data = response.json()
                print("✅ Weather tool working!")
                print(f"   Response preview: {str(weather_data)[:200]}...")
            else:
                print(f"❌ Weather tool failed: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Test trip planning tool
            print("\n🗺️  Testing trip planning tool...")
            trip_request = {
                "name": "plan_trip",
                "arguments": {
                    "destination": "Tokyo",
                    "days": 5,
                    "budget": "moderate",
                    "interests": ["culture", "food"]
                }
            }
            
            response = await client.post(
                f"{MCP_URL}/tools/call",
                headers=headers,
                json=trip_request
            )
            
            if response.status_code == 200:
                trip_data = response.json()
                print("✅ Trip planning tool working!")
                print(f"   Response preview: {str(trip_data)[:200]}...")
            else:
                print(f"❌ Trip planning tool failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing MCP server: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
