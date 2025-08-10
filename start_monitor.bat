@echo off
REM Start Keep-Alive Monitor for MCP Travel Server
REM This batch file starts the Python monitor script

echo Starting MCP Travel Server Keep-Alive Monitor...
echo.
echo Target: https://mcp-travel.onrender.com
echo Interval: 5 minutes
echo.
echo Press Ctrl+C to stop the monitor
echo.

REM Change to script directory
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the monitor
python simple_monitor.py

pause
