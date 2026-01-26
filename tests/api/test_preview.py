"""API tests for preview endpoints."""

import base64


class TestPreviewGeneration:
    """Tests for /api/preview endpoint."""

    async def test_generate_preview(self, async_client, api_test_video):
        """POST /api/preview generates preview image."""
        # Create session
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Generate preview
        response = await async_client.post(
            "/api/preview",
            json={
                "session_id": session_id,
                "layout": "default-1920x1080",
                "frame_time_ms": 5000,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image_base64" in data
        assert data["width"] == 1920
        assert data["height"] == 1080
        assert data["frame_time_ms"] == 5000

    async def test_preview_base64_valid(self, async_client, api_test_video):
        """Preview image should be valid base64 PNG."""
        # Create session
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Generate preview
        response = await async_client.post(
            "/api/preview",
            json={
                "session_id": session_id,
                "layout": "default-1920x1080",
                "frame_time_ms": 5000,
            },
        )

        data = response.json()
        # Should be valid base64
        image_bytes = base64.b64decode(data["image_base64"])
        # Should be PNG
        assert image_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_preview_invalid_session(self, async_client):
        """POST /api/preview with invalid session returns 404."""
        response = await async_client.post(
            "/api/preview",
            json={
                "session_id": "invalid-session",
                "layout": "default-1920x1080",
                "frame_time_ms": 0,
            },
        )

        assert response.status_code == 404

    async def test_preview_with_custom_units(self, async_client, api_test_video):
        """POST /api/preview with custom units."""
        # Create session
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Generate preview with custom units
        response = await async_client.post(
            "/api/preview",
            json={
                "session_id": session_id,
                "layout": "default-1920x1080",
                "frame_time_ms": 5000,
                "units_speed": "mph",
                "units_altitude": "feet",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image_base64" in data

    async def test_preview_different_frame_times(self, async_client, api_test_video):
        """Preview at different frame times should work."""
        # Create session
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Preview at beginning
        resp1 = await async_client.post(
            "/api/preview",
            json={
                "session_id": session_id,
                "layout": "default-1920x1080",
                "frame_time_ms": 1000,
            },
        )

        # Preview later
        resp2 = await async_client.post(
            "/api/preview",
            json={
                "session_id": session_id,
                "layout": "default-1920x1080",
                "frame_time_ms": 10000,
            },
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["frame_time_ms"] == 1000
        assert resp2.json()["frame_time_ms"] == 10000
