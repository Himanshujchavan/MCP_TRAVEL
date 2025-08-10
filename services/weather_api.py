# app/services/weather_api.py
import os
import httpx
from core.http_client import get_json
from typing import List, Dict, Any

OPENWEATHER_KEY = os.getenv("WEATHER_API_KEY")
BASE_OWM = "https://api.openweathermap.org/data/2.5"

async def get_weather(city: str, units: str = "metric") -> Dict[str, Any]:
    """
    Returns current weather + short forecast info for a city.
    """
    if not OPENWEATHER_KEY:
        raise RuntimeError("Missing WEATHER_API_KEY in env")

    url = f"{BASE_OWM}/weather"
    params = {"q": city, "appid": OPENWEATHER_KEY, "units": units}
    data = await get_json(url, params=params)

    normalized = {
        "city": data.get("name"),
        "coord": data.get("coord"),
        "temperature": data.get("main", {}).get("temp"),
        "feels_like": data.get("main", {}).get("feels_like"),
        "description": data.get("weather", [{}])[0].get("description"),
        "wind": data.get("wind"),
    }
    return normalized

async def get_forecast(city: str, units: str = "metric") -> List[Dict[str, Any]]:
    """
    5-day / 3-hour forecast simplified to daily summaries (best-effort).
    """
    url = f"{BASE_OWM}/forecast"
    params = {"q": city, "appid": OPENWEATHER_KEY, "units": units}
    data = await get_json(url, params=params)

    # group by date
    daily = {}
    for entry in data.get("list", []):
        date = entry.get("dt_txt", "").split(" ")[0]
        temps = daily.setdefault(date, {"temps": [], "descriptions": []})
        temps["temps"].append(entry.get("main", {}).get("temp"))
        temps["descriptions"].append(entry.get("weather", [{}])[0].get("description"))
    summary = []
    for date, info in daily.items():
        summary.append({
            "date": date,
            "temp_min": min(info["temps"]) if info["temps"] else None,
            "temp_max": max(info["temps"]) if info["temps"] else None,
            "description": max(set(info["descriptions"]), key=info["descriptions"].count) if info["descriptions"] else None
        })
    return summary
