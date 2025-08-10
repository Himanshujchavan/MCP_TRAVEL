# Quick PowerShell test for your deployed MCP server
# Run these commands one by one in PowerShell

# Test 1: Check if server is responding
$headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json, text/event-stream"
    "Authorization" = "Bearer oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
}

# Test the tools list
$body = @{
    jsonrpc = "2.0"
    id = "test-1"
    method = "tools/list"
    params = @{}
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://mcp-travel.onrender.com/mcp" -Method POST -Headers $headers -Body $body
    Write-Host "✅ SUCCESS! Server is responding" -ForegroundColor Green
    Write-Host "Available tools:" -ForegroundColor Cyan
    $response.result.tools | ForEach-Object { Write-Host "  - $($_.name)" -ForegroundColor Yellow }
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

# Test health check
$healthBody = @{
    jsonrpc = "2.0"
    id = "test-2"  
    method = "tools/call"
    params = @{
        name = "health_check"
        arguments = @{}
    }
} | ConvertTo-Json

try {
    $healthResponse = Invoke-RestMethod -Uri "https://mcp-travel.onrender.com/mcp" -Method POST -Headers $headers -Body $healthBody
    Write-Host "✅ Health check passed!" -ForegroundColor Green
    Write-Host "Response: $($healthResponse.result.content[0].text)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}
