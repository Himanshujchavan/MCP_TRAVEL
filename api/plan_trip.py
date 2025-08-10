# plan_trip.py
from fastapi import APIRouter
from models.trip import TripRequest, TripResponse
from services.ai_trip_planner import generate_itinerary

router = APIRouter()

@router.post("/", response_model=TripResponse)
async def plan_trip(request: TripRequest):
    payload = request.dict()
    result = await generate_itinerary(payload)

    # Normalize to TripResponse schema
    day_plans = [
        {"date": dp.get("date", request.start_date), "activities": dp.get("activities", [])}
        for dp in result.get("itinerary", [])
    ]
    return TripResponse(
        itinerary=day_plans,
        estimated_cost=result.get("estimated_cost")
    )
