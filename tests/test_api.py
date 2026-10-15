"""
Integration Tests for FastAPI Endpoints using AsyncClient
"""
import pytest
import time
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Converzia" in data["name"]
        assert data["status"] == "operational"

@pytest.mark.anyio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

@pytest.mark.anyio
async def test_create_and_get_lead():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_email = f"lead_{int(time.time()*1000)}@example.com"
        payload = {
            "email": test_email,
            "first_name": "Test",
            "last_name": "User",
            "company_name": "Acme Innovations",
            "website_url": "https://example.com"
        }
        create_resp = await client.post("/api/v1/leads/", json=payload)
        assert create_resp.status_code == 201
        lead_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/v1/leads/{lead_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["email"] == test_email

@pytest.mark.anyio
async def test_analytics_overview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "industry_benchmark_open_rate" in data["metrics"]
