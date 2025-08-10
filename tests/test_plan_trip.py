from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_plan_trip_success():
    payload = {
        "origin": "New York",
        "destination": "Tokyo",
        "start_date": "2025-09-01",
        "end_date": "2025-09-10",
        "budget": 2000
    }
    response = client.post("/plan-trip", json=payload)
    assert response.status_code == 200
    assert "itinerary" in response.json()

def test_plan_trip_missing_fields():
    response = client.post("/plan-trip", json={})
    assert response.status_code == 422
