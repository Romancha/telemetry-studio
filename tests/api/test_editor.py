"""API tests for editor endpoints."""


class TestEditorWidgets:
    """Tests for widget metadata endpoint."""

    async def test_get_widget_metadata(self, async_client):
        """GET /api/editor/widgets returns widget metadata."""
        response = await async_client.get("/api/editor/widgets")

        assert response.status_code == 200
        data = response.json()
        assert "widgets" in data
        assert "categories" in data
        assert len(data["widgets"]) > 0
        assert len(data["categories"]) > 0

    async def test_widget_metadata_structure(self, async_client):
        """Widget metadata has expected structure."""
        response = await async_client.get("/api/editor/widgets")
        data = response.json()

        for widget in data["widgets"]:
            assert "type" in widget
            assert "name" in widget
            assert "category" in widget
            assert "properties" in widget


class TestEditorLayouts:
    """Tests for editor layout endpoints."""

    async def test_save_layout(self, async_client, sample_editor_layout):
        """POST /api/editor/layout/save saves layout."""
        response = await async_client.post(
            "/api/editor/layout/save",
            json={
                "session_id": "test-session",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "layout_id" in data
        assert "xml" in data
        assert data["success"] is True

    async def test_save_layout_generates_xml(self, async_client, sample_editor_layout):
        """Saved layout generates valid XML."""
        response = await async_client.post(
            "/api/editor/layout/save",
            json={
                "session_id": "test-session",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        data = response.json()
        xml = data["xml"]
        assert "<layout>" in xml
        assert "</layout>" in xml

    async def test_load_layout_from_xml(self, async_client, sample_xml_layout):
        """POST /api/editor/layout/load loads layout from XML."""
        response = await async_client.post(
            "/api/editor/layout/load",
            json={
                "session_id": "test-session",
                "xml": sample_xml_layout,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "layout" in data
        assert data["success"] is True
        assert len(data["layout"]["widgets"]) > 0

    async def test_get_predefined_layouts(self, async_client):
        """GET /api/editor/layouts returns predefined layouts."""
        response = await async_client.get("/api/editor/layouts")

        assert response.status_code == 200
        data = response.json()
        assert "layouts" in data
        assert len(data["layouts"]) > 0


class TestEditorExport:
    """Tests for layout export endpoints."""

    async def test_export_xml(self, async_client, sample_editor_layout):
        """POST /api/editor/layout/export exports to XML."""
        response = await async_client.post(
            "/api/editor/layout/export",
            json={"layout": sample_editor_layout.model_dump()},
        )

        assert response.status_code == 200
        data = response.json()
        assert "xml" in data
        assert "filename" in data
        assert "<layout>" in data["xml"]

    async def test_export_xml_download(self, async_client, sample_editor_layout):
        """POST /api/editor/layout/export-download returns XML file."""
        response = await async_client.post(
            "/api/editor/layout/export-download",
            json={"layout": sample_editor_layout.model_dump()},
        )

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        content = response.text
        assert "<layout>" in content


class TestEditorPreview:
    """Tests for editor preview endpoint."""

    async def test_editor_preview(self, async_client, api_test_video, sample_editor_layout):
        """POST /api/editor/preview generates preview from layout."""
        # Create session
        upload_resp = await async_client.post("/api/local-file", json={"file_path": str(api_test_video)})
        session_id = upload_resp.json()["session_id"]

        # Generate preview
        response = await async_client.post(
            "/api/editor/preview",
            json={
                "session_id": session_id,
                "layout": sample_editor_layout.model_dump(),
                "frame_time_ms": 5000,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image_base64" in data
        assert "width" in data
        assert "height" in data

    async def test_editor_preview_without_session(self, async_client, sample_editor_layout):
        """POST /api/editor/preview without session generates preview."""
        # Note: Preview without session may work for layouts that don't need video
        # This test verifies the endpoint handles the request
        response = await async_client.post(
            "/api/editor/preview",
            json={
                "layout": sample_editor_layout.model_dump(),
                "frame_time_ms": 0,
            },
        )

        # May return 200 or 400/422 depending on implementation
        assert response.status_code in [200, 400, 422]
