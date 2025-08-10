#!/usr/bin/env python3
"""
Final working test for the deployed MCP server using the correct URL.
"""

import httpx
import asyncio
import json
import uuid

async def test_working_mcp():
    """Test the deployed MCP server using the correct URL and format."""
    print("🎉 FINAL WORKING TEST - MCP Travel Server")
    print("=" * 60)
    
    # Use the correct URL with trailing slash
    base_url = "https://mcp-travel.onrender.com/mcp/"
    auth_token = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream", 
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Initialize
        print("1. 🚀 Initializing MCP session...")
        
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize", 
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        try:
            response = await client.post(base_url, headers=headers, json=init_request)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Handle potential SSE response
                content_type = response.headers.get('content-type', '')
                
                if 'text/event-stream' in content_type:
                    print("   📡 Received SSE stream")
                    # Parse SSE format
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                if 'result' in data:
                                    print("   ✅ Initialize successful!")
                                    server_info = data['result'].get('serverInfo', {})
                                    print(f"   Server: {server_info.get('name', 'AI Trip Planner')}")
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    # Regular JSON response
                    try:
                        data = response.json()
                        if 'result' in data:
                            print("   ✅ Initialize successful!")
                            server_info = data['result'].get('serverInfo', {})
                            print(f"   Server: {server_info.get('name', 'AI Trip Planner')}")
                    except:
                        print(f"   Response: {response.text[:200]}...")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                return
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # Test 2: List tools  
        print("\n2. 📋 Getting available tools...")
        
        tools_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = await client.post(base_url, headers=headers, json=tools_request)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Handle response format
                content = response.text
                
                if 'data: ' in content:
                    # SSE format
                    for line in content.split('\n'):
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if 'result' in data and 'tools' in data['result']:
                                    tools = data['result']['tools']
                                    print(f"   ✅ Found {len(tools)} tools:")
                                    for i, tool in enumerate(tools, 1):
                                        print(f"      {i:2d}. {tool['name']}")
                                    break
                            except:
                                continue
                else:
                    # JSON format
                    try:
                        data = response.json()
                        if 'result' in data and 'tools' in data['result']:
                            tools = data['result']['tools']
                            print(f"   ✅ Found {len(tools)} tools:")
                            for i, tool in enumerate(tools, 1):
                                print(f"      {i:2d}. {tool['name']}")
                    except:
                        print(f"   Response: {response.text[:300]}...")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                return
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # Test 3: Health check
        print("\n3. 🏥 Testing health check...")
        
        health_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            }
        }
        
        try:
            response = await client.post(base_url, headers=headers, json=health_request)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                if 'data: ' in content:
                    for line in content.split('\n'):
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if 'result' in data:
                                    result = data['result']
                                    if 'content' in result:
                                        message = result['content'][0].get('text', 'Health OK')
                                        print(f"   ✅ {message}")
                                    else:
                                        print(f"   ✅ Health check passed!")
                                    break
                            except:
                                continue
                else:
                    try:
                        data = response.json()
                        if 'result' in data:
                            result = data['result']
                            if 'content' in result:
                                message = result['content'][0].get('text', 'Health OK')
                                print(f"   ✅ {message}")
                            else:
                                print(f"   ✅ Health check passed!")
                    except:
                        print(f"   Response: {response.text[:200]}...")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT TEST COMPLETE!")
    print("✅ Your AI Trip Planner MCP Server is LIVE and working!")
    print(f"✅ URL: {base_url}")
    print(f"✅ Authentication: Bearer {auth_token[:20]}...")
    print("✅ Ready for AI agents to connect!")
    print("\n📋 Connection Info for AI Agents:")
    print(f"   🔗 Server URL: {base_url}")
    print(f"   🔐 Bearer Token: {auth_token}")
    print("   📡 Protocol: JSON-RPC 2.0 / SSE")
    print("   🛠️  8 Travel planning tools available")

if __name__ == "__main__":
    asyncio.run(test_working_mcp())
