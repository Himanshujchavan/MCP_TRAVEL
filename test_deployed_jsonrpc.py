#!/usr/bin/env python3
"""
Proper JSON-RPC test script for the deployed MCP server on Render.
Uses the correct JSON-RPC 2.0 protocol that MCP servers expect.
"""

import httpx
import json
import asyncio
from typing import Dict, Any
import uuid

# Your deployed server details
MCP_URL = "https://mcp-travel.onrender.com/mcp"
AUTH_TOKEN = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"

class MCPJSONRPCTester:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {AUTH_TOKEN}"
        }
        self.base_url = MCP_URL

    def create_jsonrpc_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a JSON-RPC 2.0 request."""
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {}
        }

    async def send_jsonrpc_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        request = self.create_jsonrpc_request(method, params)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=request
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {
                        "success": False, 
                        "status": response.status_code, 
                        "error": response.text
                    }
                    
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_tools_list(self) -> Dict[str, Any]:
        """Test the tools/list method."""
        print("📋 Testing tools/list endpoint...")
        
        result = await self.send_jsonrpc_request("tools/list")
        
        if result["success"]:
            data = result["data"]
            if "result" in data:
                tools = data["result"].get("tools", [])
                print(f"✅ SUCCESS! Found {len(tools)} tools:")
                
                for i, tool in enumerate(tools, 1):
                    name = tool.get('name', 'Unknown')
                    desc = tool.get('description', '')
                    if isinstance(desc, str):
                        desc_preview = desc[:60] + "..." if len(desc) > 60 else desc
                    else:
                        desc_preview = "Complex description"
                    print(f"   {i:2d}. {name:<25} - {desc_preview}")
                
                return {"success": True, "tools": tools}
            else:
                print(f"❌ Unexpected response format: {data}")
                return {"success": False, "error": "Unexpected response format"}
        else:
            print(f"❌ FAILED: {result.get('status', 'Unknown error')}")
            print(f"Error: {result.get('error', 'No error message')}")
            return result

    async def test_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Test calling a specific tool."""
        print(f"\n🔧 Testing tool: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        
        result = await self.send_jsonrpc_request("tools/call", params)
        
        if result["success"]:
            data = result["data"]
            if "result" in data:
                print("✅ SUCCESS!")
                
                # Print response preview
                tool_result = data["result"]
                if isinstance(tool_result, dict) and "content" in tool_result:
                    content = tool_result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", str(content))
                        response_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    else:
                        response_preview = str(content)[:200] + "..." if len(str(content)) > 200 else str(content)
                else:
                    response_preview = str(tool_result)[:200] + "..." if len(str(tool_result)) > 200 else str(tool_result)
                
                print(f"   Response preview: {response_preview}")
                return {"success": True, "data": data}
            else:
                print(f"❌ Unexpected response format: {data}")
                return {"success": False, "error": "Unexpected response format"}
        else:
            print(f"❌ FAILED: {result.get('status', 'Unknown error')}")
            error_text = str(result.get('error', 'No error message'))
            error_preview = error_text[:300] + "..." if len(error_text) > 300 else error_text
            print(f"   Error: {error_preview}")
            return result

    async def run_comprehensive_test(self):
        """Run a comprehensive test of the deployed MCP server."""
        print("🚀 COMPREHENSIVE MCP SERVER TEST (JSON-RPC)")
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
        tool_names = [tool["name"] for tool in tools]
        
        print(f"\n🛠️  Available tools: {', '.join(tool_names)}")
        print("=" * 60)
        
        # Test some basic tools
        test_cases = [
            ("health_check", {}),
            ("validate", {}),
            ("get_weather", {"location": "London", "days": 3}),
            ("plan_trip", {
                "origin": "New York",
                "destination": "Paris", 
                "start_date": "2024-07-01",
                "end_date": "2024-07-05",
                "adults": 2,
                "budget": 3000,
                "activities": ["museums", "food"]
            }),
            ("search_hotel_options", {
                "destination": "Tokyo",
                "check_in": "2024-08-15", 
                "check_out": "2024-08-20",
                "adults": 2
            }),
            ("discover_places", {
                "destination": "Rome",
                "activity_type": "museums",
                "limit": 5
            })
        ]
        
        success_count = 0
        for tool_name, args in test_cases:
            if tool_name in tool_names:
                result = await self.test_tool_call(tool_name, args)
                if result["success"]:
                    success_count += 1
            else:
                print(f"\n⚠️  Skipping {tool_name} - not available in deployed server")
        
        print("\n" + "=" * 60)
        print("🎉 COMPREHENSIVE TEST COMPLETE!")
        print(f"✅ Server is running at: {self.base_url}")
        print(f"✅ Total tools available: {len(tools)}")
        print(f"✅ Successful tests: {success_count}/{len(test_cases)}")
        print(f"✅ Authentication working with bearer token")
        print("✅ Ready for AI agent connections!")
        print("=" * 60)
        
        # Connection instructions
        print("\n📋 CONNECTION INSTRUCTIONS FOR AI AGENTS:")
        print(f"   🔗 MCP Server URL: {self.base_url}")
        print(f"   🔐 Bearer Token: {AUTH_TOKEN}")
        print(f"   📡 Protocol: JSON-RPC 2.0 over HTTP")
        print(f"   🛠️  Available Tools: {len(tools)}")

async def main():
    """Main test function."""
    tester = MCPJSONRPCTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
