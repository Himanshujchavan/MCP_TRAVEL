# weather.py
from pydantic import BaseModel
from typing import List

class WeatherRequest(BaseModel):
	city: str

class WeatherData(BaseModel):
	date: str
	temperature: float
	description: str

class WeatherResponse(BaseModel):
	forecast: List[WeatherData]
