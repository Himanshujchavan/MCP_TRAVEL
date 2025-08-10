
from pydantic import BaseModel
from typing import List, Optional

class TripRequest(BaseModel):
    # 1) Basic Trip Details
    origin: str
    destination: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    budget: Optional[float] = None

    # 2) Travelers
    travelers: Optional[int] = None
    adults: int = 1
    children: int = 0
    senior_citizens: int = 0

    # 3) Preferences
    accommodation_type: Optional[str] = "hotel"  # hotel, apartment, hostel
    hotel_rating: Optional[float] = None
    preferred_airlines: Optional[List[str]] = []
    cabin_class: Optional[str] = "economy"  # economy, business, first
    activities: Optional[List[str]] = []  # e.g., beach, museums, nightlife
    dietary_preferences: Optional[List[str]] = []  # e.g., vegetarian, halal
    transportation_mode: Optional[str] = "public"  # public, rental car

    # 4) Weather & Season
    weather_preference: Optional[str] = None  # warm, cold, snow, sunny, mild
    avoid_bad_weather: bool = False

    # 5) Special Needs & Accessibility
    special_needs: Optional[List[str]] = []  # child-friendly, wheelchair, pet-friendly
    dietary_restrictions: Optional[List[str]] = []  # vegetarian, vegan, gluten-free, halal, kosher
    
    # 6) AI Output Customization
    detail_level: Optional[str] = "basic"  # basic, detailed
    max_itinerary_days: Optional[int] = None
    language: Optional[str] = "en"
    trip_style: Optional[str] = None  # luxury, budget, backpacking, family-friendly
    
    # 7) User Interaction Mode
    user_goal: Optional[str] = None  # free-text description of trip goals

class DayPlan(BaseModel):
    date: str
    activities: List[str]

class TripResponse(BaseModel):
    itinerary: List[DayPlan]
    estimated_cost: Optional[float] = None
