# weather.py
from fastapi import APIRouter
# from ..services.weather_api import get_weather

router = APIRouter()

# @router.get("/")
# def get_weather_data(city: str):
#     return get_weather(city)

# Placeholder endpoint for demonstration
@router.get("/")
def get_weather_data(city: str):
	# Replace with actual OpenWeatherMap logic
	return {"weather": f"Weather data for {city}"}
