#!/usr/bin/env python3
"""
Test the search_flight_options tool after fixing the parameter issue.
"""

import asyncio
import httpx
import json
import uuid

async def test_flight_search_fix():
    """Test the fixed search_flight_options tool."""
    print("🔧 TESTING FLIGHT SEARCH FIX")
    print("=" * 50)
    
    # Server details
    base_url = "https://mcp-travel.onrender.com/mcp/"
    auth_token = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Initialize session
        print("1. 🚀 Initializing session...")
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "flight-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await client.post(base_url, json=init_request, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to initialize: {response.text}")
            return
        
        # Extract session ID from SSE response
        session_id = None
        lines = response.text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    if 'result' in data:
                        print("✅ Session initialized successfully!")
                        # Use a simple session ID for testing
                        session_id = "test-session"
                        break
                except:
                    continue
        
        if not session_id:
            print("❌ Could not extract session ID")
            return
        
        # Test flight search tool
        print("\n2. ✈️ Testing search_flight_options...")
        
        flight_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "search_flight_options",
                "arguments": {
                    "origin": "NYC",
                    "destination": "LAX",
                    "departure_date": "2024-12-15",
                    "adults": 1,
                    "cabin_class": "economy"
                }
            }
        }
        
        # Add session ID to headers
        test_headers = headers.copy()
        test_headers["X-Session-ID"] = session_id
        
        response = await client.post(base_url, json=flight_request, headers=test_headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Flight search tool called successfully!")
            print("📄 Response preview:")
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        else:
            print(f"❌ Flight search failed: {response.text}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_flight_search_fix())
