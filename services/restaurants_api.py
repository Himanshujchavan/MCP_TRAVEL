# services/restaurants_api.py
import os
from typing import List, Dict, Any
from core.http_client import get_json

GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
YELP_KEY = os.getenv("YELP_API_KEY")

async def search_restaurants(
    city: str,
    cuisine_types: List[str] = None,
    price_range: str = None,
    dietary_restrictions: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for restaurants based on preferences.
    Combines Google Places and Yelp data.
    """
    restaurants = []
    
    # Try Google Places first
    if GOOGLE_PLACES_KEY:
        try:
            restaurants.extend(await _search_google_places(city, cuisine_types, price_range))
        except Exception:
            pass
    
    # Try Yelp for additional results
    if YELP_KEY:
        try:
            restaurants.extend(await _search_yelp(city, cuisine_types, price_range))
        except Exception:
            pass
    
    # Filter by dietary restrictions
    if dietary_restrictions:
        restaurants = _filter_by_dietary_restrictions(restaurants, dietary_restrictions)
    
    # Remove duplicates and limit results
    seen_names = set()
    unique_restaurants = []
    for restaurant in restaurants:
        name = restaurant.get("name", "").lower()
        if name not in seen_names:
            seen_names.add(name)
            unique_restaurants.append(restaurant)
    
    return unique_restaurants[:15]

async def _search_google_places(city: str, cuisine_types: List[str], price_range: str) -> List[Dict[str, Any]]:
    """Search Google Places API for restaurants"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    # Build search query
    query = f"restaurants in {city}"
    if cuisine_types:
        query += f" {' '.join(cuisine_types)}"
    
    params = {
        "query": query,
        "type": "restaurant",
        "key": GOOGLE_PLACES_KEY
    }
    
    data = await get_json(url, params=params)
    restaurants = []
    
    for place in data.get("results", []):
        # Map price level to readable format
        price_level = place.get("price_level", 0)
        price_map = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
        
        restaurants.append({
            "name": place.get("name", ""),
            "rating": place.get("rating", 0),
            "price_level": price_map.get(price_level, "Unknown"),
            "cuisine": ", ".join(place.get("types", [])),
            "address": place.get("formatted_address", ""),
            "photos": place.get("photos", []),
            "source": "google_places"
        })
    
    return restaurants

async def _search_yelp(city: str, cuisine_types: List[str], price_range: str) -> List[Dict[str, Any]]:
    """Search Yelp API for restaurants"""
    url = "https://api.yelp.com/v3/businesses/search"
    
    headers = {"Authorization": f"Bearer {YELP_KEY}"}
    params = {
        "location": city,
        "categories": "restaurants",
        "limit": 10
    }
    
    # Add cuisine types if specified
    if cuisine_types:
        params["categories"] += "," + ",".join(cuisine_types)
    
    # Add price filter if specified
    if price_range:
        price_map = {"$": "1", "$$": "2", "$$$": "3", "$$$$": "4"}
        if price_range in price_map:
            params["price"] = price_map[price_range]
    
    data = await get_json(url, params=params, headers=headers)
    restaurants = []
    
    for business in data.get("businesses", []):
        restaurants.append({
            "name": business.get("name", ""),
            "rating": business.get("rating", 0),
            "price_level": business.get("price", "Unknown"),
            "cuisine": ", ".join([cat["title"] for cat in business.get("categories", [])]),
            "address": business.get("location", {}).get("display_address", []),
            "phone": business.get("phone", ""),
            "url": business.get("url", ""),
            "source": "yelp"
        })
    
    return restaurants

def _filter_by_dietary_restrictions(restaurants: List[Dict[str, Any]], restrictions: List[str]) -> List[Dict[str, Any]]:
    """Filter restaurants based on dietary restrictions"""
    filtered = []
    
    for restaurant in restaurants:
        cuisine = restaurant.get("cuisine", "").lower()
        name = restaurant.get("name", "").lower()
        
        # Simple keyword matching for dietary restrictions
        suitable = True
        for restriction in restrictions:
            restriction = restriction.lower()
            
            if restriction == "vegetarian":
                if not any(keyword in cuisine or keyword in name 
                          for keyword in ["vegetarian", "vegan", "salad", "mediterranean"]):
                    # Don't exclude, just note it might not be ideal
                    pass
            elif restriction == "vegan":
                if not any(keyword in cuisine or keyword in name 
                          for keyword in ["vegan", "plant-based"]):
                    pass
            elif restriction == "gluten-free":
                if not any(keyword in cuisine or keyword in name 
                          for keyword in ["gluten-free", "gf"]):
                    pass
            elif restriction == "halal":
                if not any(keyword in cuisine or keyword in name 
                          for keyword in ["halal", "middle eastern", "turkish"]):
                    pass
            elif restriction == "kosher":
                if not any(keyword in cuisine or keyword in name 
                          for keyword in ["kosher", "jewish"]):
                    pass
        
        if suitable:
            filtered.append(restaurant)
    
    return filtered

async def get_restaurant_details(restaurant_name: str, city: str) -> Dict[str, Any]:
    """Get detailed information about a specific restaurant"""
    if GOOGLE_PLACES_KEY:
        try:
            url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {
                "input": f"{restaurant_name} {city}",
                "inputtype": "textquery",
                "fields": "place_id,name,rating,formatted_address,photos,opening_hours,price_level",
                "key": GOOGLE_PLACES_KEY
            }
            
            data = await get_json(url, params=params)
            if data.get("candidates"):
                place = data["candidates"][0]
                return {
                    "name": place.get("name", ""),
                    "rating": place.get("rating", 0),
                    "address": place.get("formatted_address", ""),
                    "price_level": place.get("price_level", 0),
                    "opening_hours": place.get("opening_hours", {}),
                    "photos": place.get("photos", [])
                }
        except Exception:
            pass
    
    return {"name": restaurant_name, "city": city, "details": "Details not available"}
