from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ...your test functions...
def test_flights_search():
    params = {"origin": "NYC", "destination": "LAX", "date": "2025-09-01"}
    response = client.get("/flights", params=params)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
