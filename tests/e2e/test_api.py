"""End-to-end API tests using httpx async client."""

from __future__ import annotations

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    """Create an httpx async client."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health_check(self, client):
        resp = await client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "veridian-core"

    async def test_readiness_check(self, client):
        resp = await client.get("/v1/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data


@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register_and_login(self, client):
        # Register
        resp = await client.post("/v1/auth/register", json={
            "email": "test@veridian.dev",
            "password": "testpassword123",
            "full_name": "Test User",
        })
        assert resp.status_code in (201, 409)  # 409 if already exists

        # Login
        resp = await client.post("/v1/auth/login", json={
            "email": "test@veridian.dev",
            "password": "testpassword123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_bad_credentials(self, client):
        resp = await client.post("/v1/auth/login", json={
            "email": "nobody@veridian.dev",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestAnalyzeEndpoints:
    async def test_analyze_requires_auth(self, client):
        resp = await client.post("/v1/analyze", json={
            "text": "Test claim",
            "media_type": "text",
        })
        assert resp.status_code in (401, 403)

    async def test_analyze_with_token(self, client):
        # Login first
        login_resp = await client.post("/v1/auth/login", json={
            "email": "test@veridian.dev",
            "password": "testpassword123",
        })
        if login_resp.status_code != 200:
            pytest.skip("Auth not configured")

        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/v1/analyze",
            json={"text": "Test misinformation claim", "media_type": "text"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "analysis_id" in data
        assert data["status"] == "pending"
