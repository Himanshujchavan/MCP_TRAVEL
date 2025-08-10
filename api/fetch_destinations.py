# fetch_destinations.py
from fastapi import APIRouter
# from ..services.places_api import search_places

router = APIRouter()

# @router.get("/")
# def get_destinations(location: str):
#     return search_places(location)

# Placeholder endpoint for demonstration
@router.get("/")
def get_destinations(location: str):
	# Replace with actual Google Places/TripAdvisor logic
	return {"destinations": [f"Top place in {location}"]}
