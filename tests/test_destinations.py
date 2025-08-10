from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ...your test functions...
def test_fetch_destinations():
    params = {"location": "Rome"}
    response = client.get("/fetch-destinations", params=params)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
