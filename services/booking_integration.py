# services/booking_integration.py
import os
from typing import Dict, Any, List
from core.http_client import get_json, post_json

BOOKING_PARTNER_ID = os.getenv("BOOKING_PARTNER_ID")
BOOKING_API_KEY = os.getenv("BOOKING_API_KEY")

async def get_booking_links(
    hotels: List[Dict[str, Any]], 
    flights: List[Dict[str, Any]],
    destination: str,
    start_date: str,
    end_date: str,
    adults: int = 1
) -> Dict[str, Any]:
    """
    Generate deep links for booking hotels and flights.
    Returns structured booking information.
    """
    booking_links = {
        "hotels": [],
        "flights": [],
        "packages": []
    }
    
    # Generate hotel booking links
    for hotel in hotels[:5]:  # Top 5 hotels
        try:
            hotel_link = await _generate_hotel_booking_link(
                hotel, destination, start_date, end_date, adults
            )
            if hotel_link:
                booking_links["hotels"].append(hotel_link)
        except Exception:
            continue
    
    # Generate flight booking links
    for flight in flights[:3]:  # Top 3 flights
        try:
            flight_link = await _generate_flight_booking_link(flight)
            if flight_link:
                booking_links["flights"].append(flight_link)
        except Exception:
            continue
    
    # Generate package deals if available
    try:
        packages = await _search_package_deals(destination, start_date, end_date, adults)
        booking_links["packages"] = packages
    except Exception:
        pass
    
    return booking_links

async def _generate_hotel_booking_link(
    hotel: Dict[str, Any], 
    destination: str, 
    start_date: str, 
    end_date: str, 
    adults: int
) -> Dict[str, Any]:
    """Generate booking link for a specific hotel"""
    
    # If we have Booking.com integration
    if BOOKING_PARTNER_ID and hotel.get("booking_id"):
        url = f"https://www.booking.com/hotel/{hotel['booking_id']}.html"
        params = {
            "checkin": start_date,
            "checkout": end_date,
            "group_adults": adults,
            "aid": BOOKING_PARTNER_ID
        }
        
        booking_url = url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        return {
            "hotel_name": hotel.get("name", ""),
            "price_per_night": hotel.get("price_per_night", 0),
            "rating": hotel.get("rating", 0),
            "booking_url": booking_url,
            "provider": "booking.com"
        }
    
    # Fallback: generic search URL
    hotel_name = hotel.get("name", "").replace(" ", "+")
    search_url = f"https://www.booking.com/searchresults.html?ss={destination}&checkin={start_date}&checkout={end_date}&group_adults={adults}"
    
    return {
        "hotel_name": hotel.get("name", ""),
        "price_per_night": hotel.get("price_per_night", 0),
        "rating": hotel.get("rating", 0),
        "booking_url": search_url,
        "provider": "booking.com",
        "note": "Search results page - find this hotel manually"
    }

async def _generate_flight_booking_link(flight: Dict[str, Any]) -> Dict[str, Any]:
    """Generate booking link for a specific flight"""
    
    # Most flight APIs don't provide direct booking links
    # Generate search URLs for major booking sites
    
    origin = flight.get("origin", "")
    destination = flight.get("destination", "")
    departure_date = flight.get("departure_date", "")
    airline = flight.get("airline", "")
    
    # Generate multiple booking options
    booking_options = []
    
    # Expedia
    expedia_url = f"https://www.expedia.com/Flights-Search?trip=oneway&leg1=from:{origin},to:{destination},departure:{departure_date}"
    booking_options.append({
        "provider": "expedia",
        "url": expedia_url
    })
    
    # Google Flights
    google_url = f"https://www.google.com/flights?hl=en#flt={origin}.{destination}.{departure_date}"
    booking_options.append({
        "provider": "google_flights", 
        "url": google_url
    })
    
    # Kayak
    kayak_url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}"
    booking_options.append({
        "provider": "kayak",
        "url": kayak_url
    })
    
    return {
        "flight_info": f"{airline} - {origin} to {destination}",
        "price": flight.get("price", 0),
        "departure_time": flight.get("departure_time", ""),
        "booking_options": booking_options
    }

async def _search_package_deals(
    destination: str, 
    start_date: str, 
    end_date: str, 
    adults: int
) -> List[Dict[str, Any]]:
    """Search for flight + hotel package deals"""
    
    # Package deal search URLs (no API integration needed)
    package_deals = [
        {
            "provider": "expedia_packages",
            "url": f"https://www.expedia.com/Hotel-Search?destination={destination}&startDate={start_date}&endDate={end_date}&rooms=1&adults={adults}",
            "description": "Flight + Hotel packages on Expedia",
            "estimated_savings": "Up to 30% off"
        },
        {
            "provider": "booking_flights",
            "url": f"https://www.booking.com/flights/?type=ROUNDTRIP&adults={adults}&checkin={start_date}&checkout={end_date}",
            "description": "Flight + Accommodation bundles",
            "estimated_savings": "Up to 25% off"
        },
        {
            "provider": "priceline_packages",
            "url": f"https://www.priceline.com/relax/at/{destination}",
            "description": "Vacation packages with exclusive deals",
            "estimated_savings": "Up to 40% off"
        }
    ]
    
    return package_deals

async def create_trip_summary_export(trip_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create exportable trip summary with all booking information.
    Returns data that can be exported to PDF, email, or calendar.
    """
    
    summary = {
        "trip_overview": {
            "destination": trip_data.get("destination", ""),
            "dates": f"{trip_data.get('start_date', '')} to {trip_data.get('end_date', '')}",
            "travelers": trip_data.get("adults", 1),
            "total_estimated_cost": trip_data.get("estimated_cost", 0)
        },
        "flight_options": trip_data.get("flights", [])[:3],
        "hotel_options": trip_data.get("hotels", [])[:5],
        "daily_itinerary": trip_data.get("itinerary", []),
        "restaurants": trip_data.get("restaurants", [])[:10],
        "events": trip_data.get("events", [])[:5],
        "important_info": {
            "visa_requirements": trip_data.get("visa_info", {}),
            "safety_advisories": trip_data.get("safety_info", {}),
            "weather_forecast": trip_data.get("forecast", [])[:7]  # Week ahead
        },
        "booking_links": trip_data.get("booking_links", {}),
        "export_formats": {
            "pdf_download": "/api/trip/export/pdf",
            "calendar_export": "/api/trip/export/calendar",
            "email_summary": "/api/trip/export/email"
        }
    }
    
    return summary
