#!/usr/bin/env python3
"""
Setup script to create Windows Task Scheduler job for keep-alive monitoring.
"""

import os
import subprocess
import sys
from pathlib import Path

def create_task_scheduler_xml():
    """Create XML file for Windows Task Scheduler."""
    script_dir = Path(__file__).parent.absolute()
    ps_script = script_dir / "monitor.ps1"
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-08-10T12:00:00</Date>
    <Author>MCP Travel Server</Author>
    <Description>Keep-alive monitor for MCP Travel Server on Render</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2024-08-10T12:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "{ps_script}" single</Arguments>
      <WorkingDirectory>{script_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

    xml_file = script_dir / "MCPKeepAlive.xml"
    with open(xml_file, 'w', encoding='utf-16') as f:
        f.write(xml_content)
    
    return xml_file

def setup_windows_task():
    """Setup Windows Task Scheduler job."""
    print("🔧 Setting up Windows Task Scheduler...")
    
    try:
        # Create XML file
        xml_file = create_task_scheduler_xml()
        print(f"✅ Created task XML: {xml_file}")
        
        # Create the scheduled task
        task_name = "MCPTravelServerKeepAlive"
        cmd = [
            "schtasks", "/create",
            "/tn", task_name,
            "/xml", str(xml_file),
            "/f"  # Force overwrite if exists
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Task '{task_name}' created successfully!")
            print("\n📋 Task Details:")
            print(f"   Name: {task_name}")
            print(f"   Frequency: Every 5 minutes")
            print(f"   Action: Ping https://mcp-travel.onrender.com")
            print("\n🛠️ Management Commands:")
            print(f"   Start task: schtasks /run /tn {task_name}")
            print(f"   Stop task:  schtasks /end /tn {task_name}")
            print(f"   Delete task: schtasks /delete /tn {task_name} /f")
            print(f"   View logs: Get-Content {Path(__file__).parent}/monitor.log")
            
        else:
            print(f"❌ Failed to create task: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ schtasks command not found. Are you running on Windows?")
        return False
    except Exception as e:
        print(f"❌ Error setting up task: {e}")
        return False
    
    return True

def show_manual_options():
    """Show manual setup options."""
    script_dir = Path(__file__).parent.absolute()
    
    print("\n" + "="*60)
    print("🛠️ MANUAL SETUP OPTIONS")
    print("="*60)
    
    print("\n1️⃣ OPTION 1: Run Simple Monitor Script")
    print("   Command: python simple_monitor.py")
    print("   • Runs continuously in terminal")
    print("   • Pings server every 5 minutes")
    print("   • Logs to server_monitor.log")
    
    print("\n2️⃣ OPTION 2: Run Advanced Monitor")
    print("   Command: python keep_alive.py")
    print("   Options:")
    print("   • --hours 24    (run for 24 hours)")
    print("   • --interval 300 (ping every 5 minutes)")
    print("   • --debug       (verbose logging)")
    
    print("\n3️⃣ OPTION 3: Use Windows Batch File")
    print(f"   Double-click: {script_dir}/start_monitor.bat")
    print("   • Automatically activates virtual environment")
    print("   • Runs simple monitor script")
    
    print("\n4️⃣ OPTION 4: PowerShell Script")
    print(f"   Command: powershell -File {script_dir}/monitor.ps1")
    print("   • Single ping: monitor.ps1 single")
    print("   • Continuous: monitor.ps1")
    
    print("\n5️⃣ OPTION 5: Windows Task Scheduler (Manual)")
    print("   1. Open Task Scheduler")
    print("   2. Create Basic Task")
    print("   3. Trigger: Repeat every 5 minutes")
    print(f"   4. Action: powershell -File {script_dir}/monitor.ps1 single")

def main():
    """Main setup function."""
    print("🚀 MCP Travel Server Keep-Alive Setup")
    print("="*50)
    print("This will help you set up automatic server monitoring")
    print("to prevent your Render server from sleeping.\n")
    
    # Check if running on Windows
    if os.name != 'nt':
        print("⚠️  This setup is designed for Windows.")
        print("On Linux/Mac, you can use cron jobs with the Python scripts.")
        show_manual_options()
        return
    
    # Ask user preference
    print("Setup Options:")
    print("1. Automatic - Create Windows Scheduled Task (Recommended)")
    print("2. Manual - Show manual setup instructions")
    print("3. Test - Run a single ping test")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice == "1":
        if setup_windows_task():
            print("\n🎉 Automatic setup complete!")
            print("Your server will now be pinged every 5 minutes automatically.")
        else:
            print("\n⚠️  Automatic setup failed. See manual options below:")
            show_manual_options()
    
    elif choice == "2":
        show_manual_options()
    
    elif choice == "3":
        print("\n🧪 Running test ping...")
        import requests
        try:
            response = requests.get("https://mcp-travel.onrender.com", timeout=10)
            print(f"✅ Test successful! Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    else:
        print("Invalid choice. Run the script again.")

if __name__ == "__main__":
    main()
