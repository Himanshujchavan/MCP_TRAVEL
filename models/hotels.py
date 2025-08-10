# hotels.py
from pydantic import BaseModel
from typing import List

class HotelSearchRequest(BaseModel):
	location: str
	check_in: str  # YYYY-MM-DD
	check_out: str  # YYYY-MM-DD

class HotelOption(BaseModel):
	name: str
	price_per_night: float
	rating: float
	address: str

class HotelSearchResponse(BaseModel):
	hotels: List[HotelOption]
