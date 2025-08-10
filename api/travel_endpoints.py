# API endpoints for comprehensive travel planning workflow
from fastapi import APIRouter, HTTPException
from models.trip import TripRequest, TripResponse
from services.ai_trip_planner import generate_itinerary
from services.booking_integration import create_trip_summary_export
from typing import Dict, Any
import json

router = APIRouter(prefix="/api/v1/travel", tags=["travel-planning"])

@router.post("/plan", response_model=Dict[str, Any])
async def create_travel_plan(request: TripRequest):
    """
    Phase 1-3: Comprehensive travel planning with data gathering,
    planning, and detailed recommendations.
    """
    try:
        # Convert request to dict for orchestration
        payload = request.dict()
        
        # Generate comprehensive trip plan
        result = await generate_itinerary(payload)
        
        return {
            "status": "success",
            "trip_plan": result.get("trip_data", {}),
            "quick_summary": {
                "destination": payload.get("destination"),
                "dates": f"{payload.get('start_date')} to {payload.get('end_date')}",
                "estimated_cost": result.get("estimated_cost"),
                "total_activities": len(result.get("itinerary", [])),
                "hotels_found": len(result.get("trip_data", {}).get("hotels", [])),
                "flights_found": len(result.get("trip_data", {}).get("flights", [])),
                "restaurants_found": len(result.get("trip_data", {}).get("restaurants", [])),
                "events_found": len(result.get("trip_data", {}).get("events", []))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")

@router.get("/plan/{trip_id}/summary")
async def get_trip_summary(trip_id: str):
    """
    Phase 4: Generate formatted trip summary with booking links,
    maps, and export options.
    """
    # In a real implementation, you'd fetch trip data from database
    # For now, return structure for testing
    
    return {
        "trip_id": trip_id,
        "summary_ready": True,
        "export_options": {
            "pdf": f"/api/v1/travel/export/{trip_id}/pdf",
            "calendar": f"/api/v1/travel/export/{trip_id}/calendar", 
            "email": f"/api/v1/travel/export/{trip_id}/email"
        },
        "booking_integration": {
            "hotels_bookable": True,
            "flights_bookable": True,
            "packages_available": True
        },
        "maps_integration": {
            "route_map": f"/api/v1/travel/maps/{trip_id}/route",
            "places_map": f"/api/v1/travel/maps/{trip_id}/places",
            "interactive_map": f"/api/v1/travel/maps/{trip_id}/interactive"
        }
    }

@router.post("/plan/{trip_id}/book")
async def initiate_booking(trip_id: str, booking_request: Dict[str, Any]):
    """
    Phase 4: Initiate booking process for selected options.
    """
    booking_type = booking_request.get("type")  # hotel, flight, package
    selected_items = booking_request.get("items", [])
    
    if booking_type == "hotel":
        # Generate hotel booking links
        booking_links = []
        for item in selected_items:
            booking_links.append({
                "hotel_name": item.get("name"),
                "booking_url": f"https://booking.com/hotel/{item.get('id')}",
                "provider": "booking.com"
            })
        return {"booking_links": booking_links}
    
    elif booking_type == "flight":
        # Generate flight booking links
        booking_links = []
        for item in selected_items:
            booking_links.append({
                "flight": item.get("flight_number"),
                "booking_options": [
                    {"provider": "expedia", "url": f"https://expedia.com/flights/{item.get('id')}"},
                    {"provider": "kayak", "url": f"https://kayak.com/flights/{item.get('id')}"}
                ]
            })
        return {"booking_links": booking_links}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid booking type")

@router.get("/export/{trip_id}/{format}")
async def export_trip(trip_id: str, format: str):
    """
    Phase 4: Export trip in various formats (pdf, calendar, email).
    """
    if format not in ["pdf", "calendar", "email"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    # In real implementation, generate actual files
    return {
        "trip_id": trip_id,
        "format": format,
        "download_url": f"/downloads/{trip_id}.{format}",
        "status": "ready",
        "generated_at": "2024-01-15T10:30:00Z"
    }

@router.post("/feedback/{trip_id}")
async def submit_feedback(trip_id: str, feedback: Dict[str, Any]):
    """
    Phase 5: Collect user feedback for ongoing support.
    """
    feedback_type = feedback.get("type")  # rating, issue, suggestion
    rating = feedback.get("rating")  # 1-5
    comments = feedback.get("comments", "")
    
    # Store feedback (in real implementation)
    return {
        "feedback_received": True,
        "trip_id": trip_id,
        "follow_up_available": True,
        "support_contact": "support@travel-ai.com"
    }

@router.get("/support/{trip_id}")
async def get_ongoing_support(trip_id: str):
    """
    Phase 5: Provide ongoing travel support and real-time updates.
    """
    return {
        "trip_id": trip_id,
        "support_features": {
            "real_time_updates": True,
            "weather_alerts": True,
            "flight_status": True,
            "local_recommendations": True,
            "emergency_contacts": True
        },
        "current_alerts": [
            {
                "type": "weather",
                "message": "Light rain expected tomorrow, consider indoor activities",
                "severity": "low"
            }
        ],
        "emergency_info": {
            "local_emergency": "911",
            "embassy_contact": "+1-555-0123",
            "travel_insurance": "policy-123456"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "services": {
            "trip_planning": "operational",
            "booking_integration": "operational", 
            "export_services": "operational",
            "support_system": "operational"
        },
        "version": "1.0.0"
    }
