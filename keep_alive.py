#!/usr/bin/env python3
"""
Keep-Alive Ping Script for MCP Travel Server on Render

This script sends periodic requests to your deployed MCP server to prevent it from sleeping.
Render free tier puts services to sleep after 15 minutes of inactivity.
"""

import asyncio
import httpx
import json
import uuid
import logging
import sys
from datetime import datetime
from typing import Optional

# Configuration
MCP_SERVER_URL = "https://mcp-travel.onrender.com/mcp/"
AUTH_TOKEN = "oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE"
PING_INTERVAL = 300  # 5 minutes (300 seconds)
TIMEOUT = 30  # 30 seconds timeout for requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keep_alive.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MCPKeepAlive:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {AUTH_TOKEN}"
        }
        self.ping_count = 0
        self.success_count = 0
        self.error_count = 0

    async def create_health_ping(self) -> dict:
        """Create a minimal health check request."""
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            }
        }

    async def send_ping(self) -> bool:
        """Send a ping to the MCP server."""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                # Send health check request
                ping_request = await self.create_health_ping()
                
                logger.info(f"🏓 Sending ping #{self.ping_count + 1} to {MCP_SERVER_URL}")
                
                response = await client.post(
                    MCP_SERVER_URL,
                    headers=self.headers,
                    json=ping_request
                )
                
                self.ping_count += 1
                
                if response.status_code == 200:
                    self.success_count += 1
                    logger.info(f"✅ Ping successful! Server is alive (Status: {response.status_code})")
                    
                    # Log basic response info
                    content_type = response.headers.get('content-type', 'unknown')
                    logger.debug(f"   Content-Type: {content_type}")
                    logger.debug(f"   Response length: {len(response.text)} chars")
                    
                    return True
                else:
                    self.error_count += 1
                    logger.warning(f"⚠️  Ping returned status {response.status_code}")
                    logger.warning(f"   Response: {response.text[:200]}...")
                    return False
                    
        except httpx.TimeoutException:
            self.error_count += 1
            logger.error(f"⏰ Ping timeout after {TIMEOUT} seconds")
            return False
        except httpx.ConnectError:
            self.error_count += 1
            logger.error("🔌 Connection error - server might be down")
            return False
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Ping failed with error: {str(e)}")
            return False

    async def send_basic_ping(self) -> bool:
        """Send a basic HTTP GET request as fallback."""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                # Simple GET request to keep connection alive
                base_url = MCP_SERVER_URL.replace('/mcp/', '')
                
                logger.info(f"🏓 Sending basic ping to {base_url}")
                
                response = await client.get(base_url)
                
                # Even 404 is fine - it means server is responding
                if response.status_code in [404, 200, 301, 302, 307]:
                    logger.info(f"✅ Basic ping successful! Server responding (Status: {response.status_code})")
                    return True
                else:
                    logger.warning(f"⚠️  Basic ping returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Basic ping failed: {str(e)}")
            return False

    async def run_keep_alive(self, duration_hours: Optional[int] = None):
        """Run the keep-alive loop."""
        logger.info("🚀 Starting MCP Server Keep-Alive Service")
        logger.info(f"   Target: {MCP_SERVER_URL}")
        logger.info(f"   Interval: {PING_INTERVAL} seconds ({PING_INTERVAL/60:.1f} minutes)")
        if duration_hours:
            logger.info(f"   Duration: {duration_hours} hours")
        else:
            logger.info(f"   Duration: Indefinite (until stopped)")
        logger.info("=" * 60)

        start_time = datetime.now()
        end_time = None
        if duration_hours:
            end_time = start_time.replace(hour=start_time.hour + duration_hours)

        try:
            while True:
                current_time = datetime.now()
                
                # Check if we should stop (if duration is set)
                if end_time and current_time >= end_time:
                    logger.info("⏰ Scheduled duration completed")
                    break

                # Try MCP health check first
                success = await self.send_ping()
                
                # If MCP ping fails, try basic ping as fallback
                if not success:
                    logger.info("🔄 Trying basic ping as fallback...")
                    await self.send_basic_ping()

                # Log statistics every 10 pings
                if self.ping_count % 10 == 0:
                    uptime = current_time - start_time
                    success_rate = (self.success_count / self.ping_count * 100) if self.ping_count > 0 else 0
                    logger.info(f"📊 Stats: {self.ping_count} pings, {success_rate:.1f}% success, uptime: {uptime}")

                # Wait for next ping
                logger.debug(f"💤 Sleeping for {PING_INTERVAL} seconds...")
                await asyncio.sleep(PING_INTERVAL)

        except KeyboardInterrupt:
            logger.info("🛑 Keep-alive service stopped by user")
        except Exception as e:
            logger.error(f"💥 Keep-alive service crashed: {str(e)}")
        finally:
            # Final statistics
            total_time = datetime.now() - start_time
            success_rate = (self.success_count / self.ping_count * 100) if self.ping_count > 0 else 0
            
            logger.info("=" * 60)
            logger.info("📈 FINAL STATISTICS:")
            logger.info(f"   Total runtime: {total_time}")
            logger.info(f"   Total pings: {self.ping_count}")
            logger.info(f"   Successful: {self.success_count}")
            logger.info(f"   Failed: {self.error_count}")
            logger.info(f"   Success rate: {success_rate:.1f}%")
            logger.info("🏁 Keep-alive service ended")

async def main():
    """Main function with command line options."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Keep-Alive Service for MCP Travel Server")
    parser.add_argument("--hours", type=int, help="Run for specified number of hours (default: run indefinitely)")
    parser.add_argument("--interval", type=int, default=300, help="Ping interval in seconds (default: 300)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update interval if specified
    global PING_INTERVAL
    PING_INTERVAL = args.interval
    
    # Create and run keep-alive service
    keep_alive = MCPKeepAlive()
    await keep_alive.run_keep_alive(duration_hours=args.hours)

if __name__ == "__main__":
    # Handle different Python versions
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)
