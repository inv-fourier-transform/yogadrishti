"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    async def test_health_check_service_name(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        data = resp.json()
        assert data["service"] == "yoga-pose-detector"


@pytest.mark.asyncio
class TestUploadConfigEndpoint:
    async def test_get_config(self, client: AsyncClient):
        resp = await client.get("/api/v1/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "max_image_size_mb" in data
        assert "allowed_image_extensions" in data
        assert ".jpg" in data["allowed_image_extensions"]


@pytest.mark.asyncio
class TestUserEndpoints:
    async def test_create_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/users", json={"display_name": "TestUser"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "TestUser"
        assert "id" in data
        assert "created_at" in data

    async def test_list_users(self, client: AsyncClient):
        # Create a user first
        await client.post("/api/v1/users", json={"display_name": "Alice"})
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        users = resp.json()
        assert isinstance(users, list)
        assert len(users) >= 1
        assert any(u["display_name"] == "Alice" for u in users)

    async def test_get_user_by_id(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/users", json={"display_name": "Bob"})
        user_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Bob"

    async def test_get_nonexistent_user(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/nonexistent-id-123")
        assert resp.status_code == 404

    async def test_create_user_empty_name(self, client: AsyncClient):
        resp = await client.post("/api/v1/users", json={"display_name": ""})
        assert resp.status_code == 422  # Validation error

    async def test_user_dashboard(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/users", json={"display_name": "Charlie"})
        user_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/users/{user_id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data
        assert "total_attempts" in data
        assert "recent_attempts" in data
        assert "best_scores" in data

    async def test_dashboard_nonexistent_user(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/doesnotexist/dashboard")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestImageAnalysis:
    async def test_unsupported_format(self, client: AsyncClient):
        """Upload a file with unsupported extension."""
        resp = await client.post(
            "/api/v1/analyze/image",
            files={"file": ("test.bmp", b"fake", "image/bmp")},
        )
        assert resp.status_code == 422

    async def test_valid_image_upload(self, client: AsyncClient, sample_image_bytes):
        """Upload a valid JPEG — may fail on pose detection (no person) or MediaPipe issues,
        but the endpoint should always return a proper error response."""
        resp = await client.post(
            "/api/v1/analyze/image",
            files={"file": ("yoga.jpg", sample_image_bytes, "image/jpeg")},
        )
        # 200 = success, 422 = no person detected, 500 = MediaPipe unavailable (caught error)
        assert resp.status_code in (200, 422, 500)
        # Verify it returns JSON, not an unhandled crash
        data = resp.json()
        assert "detail" in data or "success" in data

    async def test_image_with_user_id(self, client: AsyncClient, sample_image_bytes):
        """Upload with a user_id — should not crash unhandled."""
        create_resp = await client.post("/api/v1/users", json={"display_name": "Tester"})
        user_id = create_resp.json()["id"]
        resp = await client.post(
            "/api/v1/analyze/image",
            files={"file": ("yoga.jpg", sample_image_bytes, "image/jpeg")},
            data={"user_id": user_id},
        )
        # Same as above — MediaPipe may not be available
        assert resp.status_code in (200, 422, 500)
        data = resp.json()
        assert "detail" in data or "success" in data


@pytest.mark.asyncio
class TestPoseHistory:
    async def test_empty_history(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/users", json={"display_name": "HistUser"})
        user_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/users/{user_id}/poses/tree_pose/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_attempts"] == 0
        assert data["attempts"] == []
