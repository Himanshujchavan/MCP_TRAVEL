# hotels.py
from fastapi import APIRouter
# from ..services.hotels_api import search_hotels

router = APIRouter()

# @router.get("/")
# def get_hotels(location: str, check_in: str, check_out: str):
#     return search_hotels(location, check_in, check_out)

# Placeholder endpoint for demonstration
@router.get("/")
def get_hotels(location: str, check_in: str, check_out: str):
	# Replace with actual Hotels.com logic
	return {"hotels": [f"Hotel in {location} from {check_in} to {check_out}"]}
