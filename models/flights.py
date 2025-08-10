# flights.py
from pydantic import BaseModel
from typing import List

class FlightSearchRequest(BaseModel):
	origin: str
	destination: str
	date: str  # YYYY-MM-DD

class FlightOption(BaseModel):
	airline: str
	price: float
	departure_time: str
	arrival_time: str
	duration: str

class FlightSearchResponse(BaseModel):
	flights: List[FlightOption]
