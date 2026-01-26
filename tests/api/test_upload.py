"""API tests for upload endpoints."""


class TestUploadConfig:
    """Tests for /api/config endpoint."""

    async def test_get_config(self, async_client):
        """GET /api/config returns configuration."""
        response = await async_client.get("/api/config")

        assert response.status_code == 200
        data = response.json()
        assert "local_mode" in data
        assert "max_upload_size_bytes" in data
        assert "allowed_extensions" in data

    async def test_config_has_allowed_extensions(self, async_client):
        """Config includes allowed file extensions."""
        response = await async_client.get("/api/config")
        data = response.json()

        assert len(data["allowed_extensions"]) > 0
        # Should include video and GPX/FIT extensions
        extensions = data["allowed_extensions"]
        assert any(".mp4" in ext.lower() for ext in extensions)


class TestLocalFileUpload:
    """Tests for /api/local-file endpoint."""

    async def test_local_file_creates_session(self, async_client, api_test_video):
        """POST /api/local-file creates session."""
        response = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"].startswith("local:")
        assert len(data["files"]) == 1

    async def test_local_file_extracts_metadata(self, async_client, api_test_video):
        """POST /api/local-file extracts video metadata."""
        response = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})

        data = response.json()
        file_info = data["files"][0]
        assert file_info["file_type"] == "video"
        assert file_info["role"] == "primary"
        assert file_info["video_metadata"] is not None
        assert file_info["video_metadata"]["width"] > 0

    async def test_local_file_not_found(self, async_client):
        """POST /api/local-file with nonexistent file returns 404."""
        response = await async_client.post("/api/local-file", json={"file_path": "/nonexistent/file.mp4"})

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_local_file_invalid_extension(self, async_client, temp_dir):
        """POST /api/local-file with invalid extension returns 400."""
        # Create a file with invalid extension
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("hello")

        response = await async_client.post("/api/local-file", json={"file_path": str(txt_file)})

        assert response.status_code == 400


class TestSecondaryFileUpload:
    """Tests for /api/local-file-secondary endpoint."""

    async def test_add_secondary_gpx(self, async_client, api_test_video, sample_gpx_file):
        """POST /api/local-file-secondary adds GPX file."""
        # Create session with video
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Add secondary GPX
        response = await async_client.post(
            "/api/local-file-secondary",
            json={"session_id": session_id, "file_path": str(sample_gpx_file)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 2
        secondary = next(f for f in data["files"] if f["role"] == "secondary")
        assert secondary["file_type"] == "gpx"

    async def test_secondary_invalid_session(self, async_client, sample_gpx_file):
        """POST /api/local-file-secondary with invalid session returns 404."""
        response = await async_client.post(
            "/api/local-file-secondary",
            json={"session_id": "invalid-session", "file_path": str(sample_gpx_file)},
        )

        assert response.status_code == 404


class TestSessionManagement:
    """Tests for session endpoints."""

    async def test_get_session(self, async_client, api_test_video):
        """GET /api/session/{session_id} returns session info."""
        # Create session
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Get session
        response = await async_client.get(f"/api/session/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert len(data["files"]) == 1

    async def test_get_session_not_found(self, async_client):
        """GET /api/session/{session_id} with invalid ID returns 404."""
        response = await async_client.get("/api/session/invalid-session-id")

        assert response.status_code == 404

    async def test_remove_secondary_file(self, async_client, api_test_video, sample_gpx_file):
        """DELETE /api/session/{session_id}/secondary removes secondary file."""
        # Create session with video and GPX
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        await async_client.post(
            "/api/local-file-secondary",
            json={"session_id": session_id, "file_path": str(sample_gpx_file)},
        )

        # Remove secondary
        response = await async_client.delete(f"/api/session/{session_id}/secondary")

        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 1
        assert data["files"][0]["role"] == "primary"
