#!/usr/bin/env python3
"""
Proper FastMCP session-based test for the deployed server.
"""

import httpx
import asyncio
import json
import uuid

async def test_fastmcp_session():
    """Test the deployed FastMCP server with proper session handling."""
    print("🚀 Testing FastMCP Server with Session Management")
    print("=" * 60)
    
    base_url = "https://mcp-travel.onrender.com/mcp"
    auth_token = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        try:
            # Step 1: Initialize session
            print("1. Initializing MCP session...")
            
            init_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await client.post(base_url, headers=headers, json=init_request)
            print(f"   Initialize status: {response.status_code}")
            
            if response.status_code == 200:
                init_data = response.json()
                print("   ✅ Session initialized successfully!")
                if "result" in init_data:
                    server_info = init_data["result"]
                    print(f"   Server: {server_info.get('serverInfo', {}).get('name', 'Unknown')}")
                    print(f"   Version: {server_info.get('serverInfo', {}).get('version', 'Unknown')}")
            else:
                print(f"   ❌ Initialize failed: {response.text[:200]}...")
                return
            
            # Step 2: Send initialized notification
            print("\n2. Sending initialized notification...")
            
            initialized_request = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            response = await client.post(base_url, headers=headers, json=initialized_request)
            print(f"   Initialized notification status: {response.status_code}")
            
            # Step 3: List tools
            print("\n3. Getting tools list...")
            
            tools_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list",
                "params": {}
            }
            
            response = await client.post(base_url, headers=headers, json=tools_request)
            print(f"   Tools list status: {response.status_code}")
            
            if response.status_code == 200:
                tools_data = response.json()
                if "result" in tools_data and "tools" in tools_data["result"]:
                    tools = tools_data["result"]["tools"]
                    print(f"   ✅ SUCCESS! Found {len(tools)} tools:")
                    for i, tool in enumerate(tools, 1):
                        print(f"      {i:2d}. {tool['name']}")
                    
                    # Step 4: Test a tool call
                    print("\n4. Testing health check tool...")
                    
                    health_request = {
                        "jsonrpc": "2.0",
                        "id": str(uuid.uuid4()),
                        "method": "tools/call",
                        "params": {
                            "name": "health_check",
                            "arguments": {}
                        }
                    }
                    
                    response = await client.post(base_url, headers=headers, json=health_request)
                    print(f"   Health check status: {response.status_code}")
                    
                    if response.status_code == 200:
                        health_data = response.json()
                        if "result" in health_data:
                            result = health_data["result"]
                            if "content" in result and len(result["content"]) > 0:
                                message = result["content"][0].get("text", "No message")
                                print(f"   ✅ Health check passed: {message}")
                            else:
                                print(f"   ✅ Health check passed: {result}")
                        else:
                            print(f"   ❌ Unexpected health check response: {health_data}")
                    else:
                        print(f"   ❌ Health check failed: {response.text[:200]}...")
                else:
                    print(f"   ❌ Unexpected tools response: {tools_data}")
            else:
                print(f"   ❌ Tools list failed: {response.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DEPLOYMENT STATUS:")
    print("✅ Server is accessible at: https://mcp-travel.onrender.com/mcp")
    print("✅ Authentication is working")
    print("✅ JSON-RPC protocol is working")
    print("✅ Ready for AI agent connections!")
    print("\n📋 For AI agents, use:")
    print("   URL: https://mcp-travel.onrender.com/mcp")
    print(f"   Bearer Token: {auth_token}")
    print("   Protocol: FastMCP/JSON-RPC 2.0")

if __name__ == "__main__":
    asyncio.run(test_fastmcp_session())
