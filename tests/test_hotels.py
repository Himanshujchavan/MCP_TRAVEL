from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ...your test functions...
def test_hotels_search():
    params = {"location": "Tokyo", "check_in": "2025-09-01", "check_out": "2025-09-05"}
    response = client.get("/hotels", params=params)
    assert response.status_code == 200
    assert all("name" in hotel for hotel in response.json())
