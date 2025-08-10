# services/visa_api.py
import os
from typing import Dict, Any
from core.http_client import get_json

async def check_visa_requirements(origin_country: str, destination_country: str) -> Dict[str, Any]:
    """
    Check visa requirements between countries.
    Uses a free visa API or fallback to basic info.
    """
    try:
        # Example: VisaList API or similar free service
        url = "https://rough-sun-2523.fly.dev/api"  # Free visa API
        params = {
            "origin": origin_country,
            "destination": destination_country
        }
        data = await get_json(url, params=params)
        
        return {
            "visa_required": data.get("visa_required", False),
            "visa_type": data.get("visa_type", "unknown"),
            "duration": data.get("duration", "unknown"),
            "requirements": data.get("requirements", []),
            "source": "visa_api"
        }
    except Exception:
        # Fallback basic info
        return {
            "visa_required": "unknown",
            "message": "Please check official embassy websites for visa requirements",
            "source": "fallback"
        }

async def get_safety_advisories(destination_country: str) -> Dict[str, Any]:
    """
    Get travel safety information for a destination.
    """
    try:
        # Example: Government travel advisory API
        # For now, return basic structure
        return {
            "safety_level": "check_official_sources",
            "advisories": [],
            "last_updated": None,
            "source": "placeholder"
        }
    except Exception:
        return {
            "safety_level": "unknown", 
            "message": "Check your government's travel advisory website"
        }
