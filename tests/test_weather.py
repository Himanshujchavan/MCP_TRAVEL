from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ...your test functions...
def test_weather_forecast():
    params = {"location": "Paris", "date": "2025-09-01"}
    response = client.get("/weather", params=params)
    assert response.status_code == 200
    assert "forecast" in response.json()
