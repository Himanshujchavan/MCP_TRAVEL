# Test your deployed MCP server using cURL commands

# 1. Test tools list (see all available tools)
curl -X POST https://mcp-travel.onrender.com/mcp/tools/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE" \
  -d "{}"

# 2. Test health check tool
curl -X POST https://mcp-travel.onrender.com/mcp/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE" \
  -d '{"name": "health_check", "arguments": {}}'

# 3. Test weather tool
curl -X POST https://mcp-travel.onrender.com/mcp/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE" \
  -d '{"name": "get_weather", "arguments": {"location": "Paris", "days": 3}}'

# 4. Test trip planning tool
curl -X POST https://mcp-travel.onrender.com/mcp/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE" \
  -d '{"name": "plan_trip", "arguments": {"origin": "New York", "destination": "Tokyo", "start_date": "2024-06-01", "end_date": "2024-06-05", "adults": 2}}'
