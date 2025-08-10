#!/usr/bin/env python3
"""
Test script for the deployed MCP server on Render.
"""

import httpx
import json
import asyncio

# Your deployed server details
MCP_URL = "https://mcp-travel.onrender.com/mcp"
AUTH_TOKEN = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"

async def test_deployed_server():
    """Test the deployed MCP server on Render."""
    print("🧪 Testing Deployed AI Trip Planner MCP Server")
    print("🌐 URL: https://mcp-travel.onrender.com/mcp/")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test tools list
            print("📋 Testing tools list endpoint...")
            response = await client.post(
                f"{MCP_URL}/tools/list",
                headers=headers,
                json={}
            )
            
            if response.status_code == 200:
                tools_data = response.json()
                tools = tools_data.get("tools", [])
                print(f"✅ SUCCESS! Found {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    name = tool.get('name', 'Unknown')
                    desc = tool.get('description', 'No description')[:50]
                    print(f"   {i}. {name} - {desc}...")
                print()
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            # Test health check tool
            print("🏥 Testing health check...")
            health_request = {
                "name": "health_check",
                "arguments": {}
            }
            
            response = await client.post(
                f"{MCP_URL}/tools/call",
                headers=headers,
                json=health_request
            )
            
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Health check successful!")
                print(f"   Response: {health_data}")
                print()
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print()
            
            # Test a sample trip planning tool
            print("🗺️  Testing trip planning tool...")
            trip_request = {
                "name": "plan_trip",
                "arguments": {
                    "origin": "New York",
                    "destination": "Paris",
                    "start_date": "2024-06-01",
                    "end_date": "2024-06-05",
                    "adults": 2,
                    "budget": 5000,
                    "activities": ["museums", "food"]
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
                print(f"   Response preview: {str(trip_data)[:150]}...")
                print()
            else:
                print(f"❌ Trip planning failed: {response.status_code}")
                print(f"Response: {response.text}")
                print()
                
            print("🎉 DEPLOYMENT TEST COMPLETE!")
            print("Your MCP server is ready for AI agents to connect!")
            print()
            print("📋 Connection Details for AI Agents:")
            print(f"   🔗 URL: {MCP_URL}/")
            print(f"   🔐 Bearer Token: {AUTH_TOKEN}")
            print(f"   🛠️  Available Tools: {len(tools)}")
            
            return True
                
        except Exception as e:
            print(f"❌ Error testing deployed server: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_deployed_server())
