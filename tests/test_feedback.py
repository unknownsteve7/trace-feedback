import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_categories_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/categories")
    assert response.status_code == 200
    cats = response.json()
    assert isinstance(cats, list)
    assert "Late/not arrived" in cats
    assert len(cats) >= 14

@pytest.mark.asyncio
async def test_submit_valid_feedback():
    payload = {
        "route_id": "784",
        "vehicle_id": "DL1PC9421",
        "category": "Late/not arrived",
        "rating": 2,
        "comment": "Test delay feedback from pytest"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/feedback", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "feedback_id" in data
    assert data["status"] == "received"

@pytest.mark.asyncio
async def test_submit_invalid_category_returns_422():
    payload = {
        "route_id": "784",
        "vehicle_id": "DL1PC9421",
        "category": "Alien Abduction",
        "rating": 1
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/feedback", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_admin_endpoints_auth():
    from app.config import settings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing header should be 422 or 403
        r_unauth = await ac.get("/admin/stats")
        assert r_unauth.status_code in (403, 422)

        # Invalid header should be 403
        r_forbidden = await ac.get("/admin/stats", headers={"x-api-key": "wrong_key"})
        assert r_forbidden.status_code == 403

        # Valid header should succeed
        r_auth = await ac.get("/admin/stats", headers={"x-api-key": settings.ADMIN_API_KEY})
        assert r_auth.status_code == 200
        stats = r_auth.json()
        assert "total_records" in stats
        assert stats["total_records"] >= 50

        # Export endpoint
        r_export = await ac.get("/admin/export?limit=10", headers={"x-api-key": settings.ADMIN_API_KEY})
        assert r_export.status_code == 200
        data = r_export.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "feedback_id" in data[0]
