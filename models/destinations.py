# destinations.py
from pydantic import BaseModel
from typing import List

class DestinationRequest(BaseModel):
	location: str

class Place(BaseModel):
	name: str
	category: str
	rating: float
	address: str

class DestinationResponse(BaseModel):
	places: List[Place]
