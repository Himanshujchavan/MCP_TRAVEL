#!/usr/bin/env python3
"""
Simple connection test for the deployed MCP server.
"""

import httpx
import asyncio
import json

async def test_simple_connection():
    """Test basic connectivity to the deployed server."""
    print("🔍 Testing basic connectivity to deployed server...")
    print("=" * 50)
    
    base_url = "https://mcp-travel.onrender.com"
    mcp_url = f"{base_url}/mcp"
    
    # Test 1: Check if the server is up
    print("1. Testing basic server connectivity...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(base_url)
            print(f"   Base URL status: {response.status_code}")
        except Exception as e:
            print(f"   Base URL error: {e}")
    
    # Test 2: Check MCP endpoint
    print("\n2. Testing MCP endpoint...")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(mcp_url, headers=headers, json={})
            print(f"   MCP endpoint status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   MCP endpoint error: {e}")
    
    # Test 3: Check with authentication
    print("\n3. Testing with authentication...")
    auth_headers = {
        "Content-Type": "application/json", 
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
    }
    
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "tools/list",
        "params": {}
    }
    
    # Try different URL variations
    urls_to_try = [
        f"{base_url}/mcp",
        f"{base_url}/mcp/",
    ]
    
    for test_url in urls_to_try:
        print(f"\n   Trying URL: {test_url}")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.post(test_url, headers=auth_headers, json=jsonrpc_request)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and "tools" in data["result"]:
                        tools = data["result"]["tools"]
                        print(f"   ✅ SUCCESS! Found {len(tools)} tools!")
                        for tool in tools[:5]:  # Show first 5 tools
                            print(f"      - {tool['name']}")
                        break
                    else:
                        print(f"   Response: {response.text[:200]}...")
                else:
                    print(f"   Response: {response.text[:200]}...")
            except Exception as e:
                print(f"   Error for {test_url}: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Quick Status Check:")
    print("   Server URL: https://mcp-travel.onrender.com/mcp")
    print("   Expected: JSON-RPC 2.0 protocol")
    print("   Auth: Bearer token required")

if __name__ == "__main__":
    asyncio.run(test_simple_connection())
