# __init__.py
from fastapi import APIRouter
from api import plan_trip, fetch_destinations, weather, flights, hotels

api_router = APIRouter()
api_router.include_router(plan_trip.router, prefix="/plan-trip", tags=["Trip Planning"])
api_router.include_router(fetch_destinations.router, prefix="/fetch-destinations", tags=["Destinations"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(flights.router, prefix="/flights", tags=["Flights"])
api_router.include_router(hotels.router, prefix="/hotels", tags=["Hotels"])
