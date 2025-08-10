#!/usr/bin/env python3
"""
Simple Keep-Alive Monitor for MCP Travel Server

A lightweight script that runs continuously to keep your Render server awake.
Run this on your local machine or a VPS to prevent server sleeping.
"""

import time
import requests
import logging
from datetime import datetime
import json

# Configuration
SERVER_URL = "https://mcp-travel.onrender.com"
PING_INTERVAL = 300  # 5 minutes
TIMEOUT = 15  # 15 seconds timeout

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('server_monitor.log'),
        logging.StreamHandler()
    ]
)

def ping_server():
    """Send a simple ping to keep server alive."""
    try:
        # Simple GET request to the base URL
        response = requests.get(SERVER_URL, timeout=TIMEOUT)
        
        # Any response (even 404) means server is alive
        if response.status_code in [200, 404, 301, 302, 307]:
            logging.info(f"✅ Server alive (Status: {response.status_code})")
            return True
        else:
            logging.warning(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logging.error("⏰ Request timeout - server might be sleeping")
        return False
    except requests.exceptions.ConnectionError:
        logging.error("🔌 Connection error - server might be down")
        return False
    except Exception as e:
        logging.error(f"❌ Ping failed: {str(e)}")
        return False

def run_monitor():
    """Run the monitoring loop."""
    logging.info("🚀 Starting Server Keep-Alive Monitor")
    logging.info(f"   Target: {SERVER_URL}")
    logging.info(f"   Interval: {PING_INTERVAL} seconds ({PING_INTERVAL/60:.1f} minutes)")
    logging.info("   Press Ctrl+C to stop")
    logging.info("=" * 50)
    
    ping_count = 0
    success_count = 0
    start_time = datetime.now()
    
    try:
        while True:
            ping_count += 1
            logging.info(f"🏓 Ping #{ping_count} to {SERVER_URL}")
            
            if ping_server():
                success_count += 1
            
            # Log stats every hour (12 pings at 5-minute intervals)
            if ping_count % 12 == 0:
                uptime = datetime.now() - start_time
                success_rate = (success_count / ping_count * 100)
                logging.info(f"📊 Stats: {ping_count} pings, {success_rate:.1f}% success, runtime: {uptime}")
            
            # Wait for next ping
            time.sleep(PING_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("🛑 Monitor stopped by user")
    except Exception as e:
        logging.error(f"💥 Monitor crashed: {str(e)}")
    finally:
        # Final stats
        total_time = datetime.now() - start_time
        success_rate = (success_count / ping_count * 100) if ping_count > 0 else 0
        
        logging.info("=" * 50)
        logging.info("📈 FINAL STATISTICS:")
        logging.info(f"   Runtime: {total_time}")
        logging.info(f"   Total pings: {ping_count}")
        logging.info(f"   Success rate: {success_rate:.1f}%")
        logging.info("🏁 Monitor ended")

if __name__ == "__main__":
    run_monitor()
