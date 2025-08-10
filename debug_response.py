#!/usr/bin/env python3
"""
Debug the actual response from the FastMCP server.
"""

import httpx
import asyncio
import json
import uuid

async def debug_server_response():
    """Debug what the server is actually returning."""
    print("🔍 Debugging Server Response")
    print("=" * 40)
    
    base_url = "https://mcp-travel.onrender.com/mcp"
    auth_token = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {auth_token}"
    }
    
    init_request = {
        "jsonrpc": "2.0", 
        "id": "test-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(base_url, headers=headers, json=init_request)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Raw Content (first 500 chars): {response.text[:500]}")
            
            # Check if it's Server-Sent Events
            if 'text/event-stream' in response.headers.get('content-type', ''):
                print("\n📡 Server is using Server-Sent Events (SSE)")
                lines = response.text.split('\n')
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    print(f"Line {i}: {line}")
            else:
                try:
                    json_data = response.json()
                    print(f"\n📄 JSON Response: {json.dumps(json_data, indent=2)}")
                except:
                    print(f"\n❌ Not valid JSON: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_simple_health():
    """Try a simple direct approach."""
    print("\n" + "=" * 40)
    print("🏥 Testing Simple Health Check")
    print("=" * 40)
    
    # Try accessing via the web interface URL that might work
    test_urls = [
        "https://mcp-travel.onrender.com/health",
        "https://mcp-travel.onrender.com/",
        "https://mcp-travel.onrender.com/mcp/health"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in test_urls:
            try:
                print(f"\nTrying: {url}")
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_server_response())
    asyncio.run(test_simple_health())
