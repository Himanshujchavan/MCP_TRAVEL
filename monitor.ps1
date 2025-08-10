# PowerShell Keep-Alive Script for MCP Travel Server
# Can be run as a Windows Scheduled Task

param(
    [int]$IntervalMinutes = 5,
    [string]$LogPath = "C:\Users\chava\my-mcp-server\monitor.log"
)

$ServerUrl = "https://mcp-travel.onrender.com"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param([string]$Message)
    $LogEntry = "$Timestamp - $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogPath -Value $LogEntry
}

function Test-ServerAlive {
    try {
        $Response = Invoke-WebRequest -Uri $ServerUrl -TimeoutSec 15 -UseBasicParsing
        
        # Any response means server is alive
        if ($Response.StatusCode -in @(200, 404, 301, 302, 307)) {
            Write-Log "✅ Server alive (Status: $($Response.StatusCode))"
            return $true
        } else {
            Write-Log "⚠️ Unexpected status: $($Response.StatusCode)"
            return $false
        }
    }
    catch {
        Write-Log "❌ Ping failed: $($_.Exception.Message)"
        return $false
    }
}

# Single ping (for scheduled task)
if ($args.Count -eq 0 -or $args[0] -eq "single") {
    Write-Log "🏓 Single ping to $ServerUrl"
    Test-ServerAlive | Out-Null
}
# Continuous monitoring
else {
    Write-Log "🚀 Starting continuous monitor (Interval: $IntervalMinutes minutes)"
    
    $Count = 0
    try {
        while ($true) {
            $Count++
            Write-Log "🏓 Ping #$Count to $ServerUrl"
            Test-ServerAlive | Out-Null
            
            Start-Sleep -Seconds ($IntervalMinutes * 60)
        }
    }
    catch [System.Management.Automation.HaltCommandException] {
        Write-Log "🛑 Monitor stopped by user"
    }
}
