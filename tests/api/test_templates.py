"""API tests for templates endpoints."""


class TestTemplatesList:
    """Tests for templates list endpoint."""

    async def test_list_templates_empty(self, async_client):
        """GET /api/templates/list returns empty list initially."""
        response = await async_client.get("/api/templates/list")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        # May or may not be empty depending on existing templates


class TestTemplatesSave:
    """Tests for template save endpoint."""

    async def test_save_template(self, async_client, sample_editor_layout):
        """POST /api/templates/save saves template."""
        response = await async_client.post(
            "/api/templates/save",
            json={
                "name": "Test Template",
                "layout": sample_editor_layout.model_dump(),
                "description": "Test description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Template"
        assert data["success"] is True
        assert "file_path" in data

    async def test_save_template_empty_name(self, async_client, sample_editor_layout):
        """POST /api/templates/save with empty name returns 400."""
        response = await async_client.post(
            "/api/templates/save",
            json={
                "name": "",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        assert response.status_code == 400

    async def test_save_template_invalid_chars(self, async_client, sample_editor_layout):
        """POST /api/templates/save rejects special characters."""
        response = await async_client.post(
            "/api/templates/save",
            json={
                "name": "Test/Template:With*Special?Chars",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        # API validates and rejects invalid characters
        assert response.status_code == 400
        assert "invalid characters" in response.json()["detail"]


class TestTemplatesLoad:
    """Tests for template load endpoint."""

    async def test_load_template(self, async_client, sample_editor_layout):
        """GET /api/templates/{name} loads template."""
        # Save first
        await async_client.post(
            "/api/templates/save",
            json={
                "name": "Load Test",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        # Load
        response = await async_client.get("/api/templates/Load%20Test")

        assert response.status_code == 200
        data = response.json()
        assert "layout" in data
        assert data["success"] is True

    async def test_load_template_not_found(self, async_client):
        """GET /api/templates/{name} with nonexistent template returns 404."""
        response = await async_client.get("/api/templates/Nonexistent%20Template")

        assert response.status_code == 404

    async def test_get_template_path(self, async_client, sample_editor_layout):
        """GET /api/templates/{name}/path returns file path."""
        # Save first
        await async_client.post(
            "/api/templates/save",
            json={
                "name": "Path Test",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        # Get path
        response = await async_client.get("/api/templates/Path%20Test/path")

        assert response.status_code == 200
        data = response.json()
        assert "file_path" in data
        assert data["file_path"].endswith(".xml")


class TestTemplatesDelete:
    """Tests for template delete endpoint."""

    async def test_delete_template(self, async_client, sample_editor_layout):
        """DELETE /api/templates/{name} deletes template."""
        # Save first
        await async_client.post(
            "/api/templates/save",
            json={
                "name": "Delete Test",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        # Delete
        response = await async_client.delete("/api/templates/Delete%20Test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        get_response = await async_client.get("/api/templates/Delete%20Test")
        assert get_response.status_code == 404

    async def test_delete_template_not_found(self, async_client):
        """DELETE /api/templates/{name} with nonexistent template returns 404."""
        response = await async_client.delete("/api/templates/Nonexistent%20Template")

        assert response.status_code == 404


class TestTemplatesRename:
    """Tests for template rename endpoint."""

    async def test_rename_template(self, async_client, sample_editor_layout):
        """PUT /api/templates/{name}/rename renames template."""
        # Save first
        await async_client.post(
            "/api/templates/save",
            json={
                "name": "Old Name",
                "layout": sample_editor_layout.model_dump(),
            },
        )

        # Rename
        response = await async_client.put(
            "/api/templates/Old%20Name/rename",
            json={"new_name": "New Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_name"] == "New Name"

        # Verify old name gone
        old_response = await async_client.get("/api/templates/Old%20Name")
        assert old_response.status_code == 404

        # Verify new name exists
        new_response = await async_client.get("/api/templates/New%20Name")
        assert new_response.status_code == 200

    async def test_rename_template_not_found(self, async_client):
        """PUT /api/templates/{name}/rename with nonexistent template returns 404."""
        response = await async_client.put(
            "/api/templates/Nonexistent/rename",
            json={"new_name": "New"},
        )

        assert response.status_code == 404
