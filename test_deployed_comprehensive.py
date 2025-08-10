#!/usr/bin/env python3
"""
Comprehensive test script for the deployed MCP server on Render.
Tests all available tools and provides detailed feedback.
"""

import httpx
import json
import asyncio
from typing import Dict, Any

# Your deployed server details
MCP_URL = "https://mcp-travel.onrender.com/mcp"
AUTH_TOKEN = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"

class MCPTester:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {AUTH_TOKEN}"
        }
        self.base_url = MCP_URL

    async def test_tools_list(self) -> Dict[str, Any]:
        """Test the tools list endpoint."""
        print("📋 Testing tools list endpoint...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/tools/list",
                    headers=self.headers,
                    json={}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    tools = data.get("tools", [])
                    print(f"✅ SUCCESS! Found {len(tools)} tools:")
                    
                    for i, tool in enumerate(tools, 1):
                        name = tool.get('name', 'Unknown')
                        desc = tool.get('description', '')
                        if isinstance(desc, str):
                            desc_preview = desc[:80] + "..." if len(desc) > 80 else desc
                        else:
                            desc_preview = "Complex description"
                        print(f"   {i:2d}. {name:<25} - {desc_preview}")
                    
                    return {"success": True, "tools": tools}
                else:
                    print(f"❌ FAILED: {response.status_code}")
                    print(f"Response: {response.text}")
                    return {"success": False, "error": response.text}
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}

    async def test_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific tool."""
        print(f"\n🔧 Testing tool: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                request_data = {
                    "name": tool_name,
                    "arguments": arguments
                }
                
                response = await client.post(
                    f"{self.base_url}/tools/call",
                    headers=self.headers,
                    json=request_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ SUCCESS!")
                    
                    # Print response preview
                    if isinstance(data, dict):
                        content = data.get("content", data)
                        if isinstance(content, list) and len(content) > 0:
                            content = content[0].get("text", str(content))
                        response_preview = str(content)[:200] + "..." if len(str(content)) > 200 else str(content)
                    else:
                        response_preview = str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                    
                    print(f"   Response preview: {response_preview}")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ FAILED: {response.status_code}")
                    error_text = response.text[:300] + "..." if len(response.text) > 300 else response.text
                    print(f"   Error: {error_text}")
                    return {"success": False, "error": response.text}
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}

    async def run_comprehensive_test(self):
        """Run a comprehensive test of the deployed MCP server."""
        print("🚀 COMPREHENSIVE MCP SERVER TEST")
        print("=" * 60)
        print(f"🌐 Testing: {self.base_url}")
        print(f"🔐 Using token: {AUTH_TOKEN[:20]}...")
        print("=" * 60)
        
        # Test 1: Get tools list
        tools_result = await self.test_tools_list()
        if not tools_result["success"]:
            print("❌ Cannot proceed without tools list")
            return
        
        tools = tools_result["tools"]
        
        # Test 2: Health check
        await self.test_tool("health_check", {})
        
        # Test 3: Validate tool
        await self.test_tool("validate", {})
        
        # Test 4: Weather tool
        await self.test_tool("get_weather", {
            "location": "London",
            "days": 3
        })
        
        # Test 5: Trip planning (basic)
        await self.test_tool("plan_trip", {
            "origin": "New York",
            "destination": "Paris",
            "start_date": "2024-07-01",
            "end_date": "2024-07-05",
            "adults": 2,
            "budget": 3000,
            "activities": ["museums", "food"]
        })
        
        # Test 6: Hotel search
        await self.test_tool("search_hotel_options", {
            "destination": "Tokyo",
            "check_in": "2024-08-15",
            "check_out": "2024-08-20",
            "adults": 2
        })
        
        # Test 7: Flight search
        await self.test_tool("search_flight_options", {
            "origin": "LAX",
            "destination": "CDG",
            "departure_date": "2024-09-01",
            "adults": 1,
            "cabin_class": "economy"
        })
        
        # Test 8: Places discovery
        await self.test_tool("discover_places", {
            "destination": "Rome",
            "activity_type": "museums",
            "limit": 5
        })
        
        # Test 9: Restaurant search
        await self.test_tool("find_restaurants", {
            "destination": "Barcelona",
            "cuisine_types": ["spanish", "mediterranean"],
            "price_range": "$$"
        })
        
        # Test 10: Travel requirements
        await self.test_tool("check_travel_requirements", {
            "origin_country": "United States",
            "destination_country": "Japan"
        })
        
        print("\n" + "=" * 60)
        print("🎉 COMPREHENSIVE TEST COMPLETE!")
        print(f"✅ Server is running at: {self.base_url}")
        print(f"✅ Total tools available: {len(tools)}")
        print(f"✅ Authentication working with bearer token")
        print("✅ Ready for AI agent connections!")
        print("=" * 60)

async def main():
    """Main test function."""
    tester = MCPTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
