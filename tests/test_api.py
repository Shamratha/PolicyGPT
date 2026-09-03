from fastapi.testclient import TestClient
from app.main import app


def test_health_and_query():
    client=TestClient(app); health=client.get("/health")
    assert health.status_code==200 and health.json()["documents"]>=6
    response=client.post("/api/query",json={"query":"Can a student apply for scholarship help?"})
    assert response.status_code==200 and response.json()["domain"]=="education" and response.json()["citations"]
