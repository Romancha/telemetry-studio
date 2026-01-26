"""Unit tests for TemplateService."""

import pytest


class TestTemplateServiceSave:
    """Tests for saving templates."""

    def test_save_template_creates_xml(self, clean_template_service, sample_editor_layout):
        """Saving template creates XML file."""
        path = clean_template_service.save_template("My Template", sample_editor_layout)

        assert path.exists()
        assert path.suffix == ".xml"

    def test_save_template_creates_metadata(self, clean_template_service, sample_editor_layout):
        """Saving template creates metadata JSON file."""
        clean_template_service.save_template("My Template", sample_editor_layout)

        metadata_path = clean_template_service.templates_dir / "My_Template.json"
        assert metadata_path.exists()

    def test_save_template_with_description(self, clean_template_service, sample_editor_layout):
        """Template description is saved in metadata."""
        import json

        clean_template_service.save_template("My Template", sample_editor_layout, description="Test description")

        metadata_path = clean_template_service.templates_dir / "My_Template.json"
        metadata = json.loads(metadata_path.read_text())
        assert metadata["description"] == "Test description"

    def test_save_template_preserves_created_at(self, clean_template_service, sample_editor_layout):
        """Updating template preserves original created_at."""
        import json

        # Save initial
        clean_template_service.save_template("My Template", sample_editor_layout)
        metadata_path = clean_template_service.templates_dir / "My_Template.json"
        original_created = json.loads(metadata_path.read_text())["created_at"]

        # Update
        clean_template_service.save_template("My Template", sample_editor_layout, description="Updated")
        updated_created = json.loads(metadata_path.read_text())["created_at"]

        assert original_created == updated_created

    def test_template_exists(self, clean_template_service, sample_editor_layout):
        """template_exists returns correct status."""
        assert not clean_template_service.template_exists("My Template")

        clean_template_service.save_template("My Template", sample_editor_layout)

        assert clean_template_service.template_exists("My Template")


class TestTemplateServiceLoad:
    """Tests for loading templates."""

    def test_load_template(self, clean_template_service, sample_editor_layout):
        """Load saved template."""
        clean_template_service.save_template("Test", sample_editor_layout)

        loaded = clean_template_service.load_template("Test")

        assert loaded.metadata.name == "Test"
        assert len(loaded.widgets) == len(sample_editor_layout.widgets)

    def test_load_template_not_found(self, clean_template_service):
        """Loading nonexistent template raises error."""
        with pytest.raises(FileNotFoundError, match="not found"):
            clean_template_service.load_template("Nonexistent")

    def test_load_template_restores_canvas_size(self, clean_template_service, sample_editor_layout):
        """Loaded template has correct canvas size from metadata."""
        sample_editor_layout.canvas.width = 3840
        sample_editor_layout.canvas.height = 2160
        clean_template_service.save_template("4K", sample_editor_layout)

        loaded = clean_template_service.load_template("4K")

        assert loaded.canvas.width == 3840
        assert loaded.canvas.height == 2160

    def test_get_template_path(self, clean_template_service, sample_editor_layout):
        """Get absolute path to template."""
        clean_template_service.save_template("My Template", sample_editor_layout)

        path = clean_template_service.get_template_path("My Template")

        assert path.is_absolute()
        assert path.exists()
        assert path.suffix == ".xml"

    def test_get_template_path_not_found(self, clean_template_service):
        """Getting path to nonexistent template raises error."""
        with pytest.raises(FileNotFoundError, match="not found"):
            clean_template_service.get_template_path("Nonexistent")


class TestTemplateServiceList:
    """Tests for listing templates."""

    def test_list_templates_empty(self, clean_template_service):
        """List templates returns empty list when none exist."""
        templates = clean_template_service.list_templates()

        assert templates == []

    def test_list_templates(self, clean_template_service, sample_editor_layout):
        """List templates returns all templates."""
        clean_template_service.save_template("Template 1", sample_editor_layout)
        clean_template_service.save_template("Template 2", sample_editor_layout)

        templates = clean_template_service.list_templates()

        assert len(templates) == 2
        names = [t.name for t in templates]
        assert "Template 1" in names
        assert "Template 2" in names

    def test_list_templates_sorted_by_modified(self, clean_template_service, sample_editor_layout):
        """Templates sorted by modified_at, newest first."""
        import time

        clean_template_service.save_template("Old", sample_editor_layout)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        clean_template_service.save_template("New", sample_editor_layout)

        templates = clean_template_service.list_templates()

        assert templates[0].name == "New"

    def test_list_templates_includes_metadata(self, clean_template_service, sample_editor_layout):
        """Listed templates include metadata."""
        clean_template_service.save_template("Test", sample_editor_layout, description="Test desc")

        templates = clean_template_service.list_templates()

        assert templates[0].description == "Test desc"
        assert templates[0].canvas_width == sample_editor_layout.canvas.width


class TestTemplateServiceDelete:
    """Tests for deleting templates."""

    def test_delete_template(self, clean_template_service, sample_editor_layout):
        """Delete template removes files."""
        clean_template_service.save_template("To Delete", sample_editor_layout)

        deleted = clean_template_service.delete_template("To Delete")

        assert deleted
        assert not clean_template_service.template_exists("To Delete")

    def test_delete_template_not_found(self, clean_template_service):
        """Deleting nonexistent template returns False."""
        deleted = clean_template_service.delete_template("Nonexistent")

        assert not deleted

    def test_delete_removes_both_files(self, clean_template_service, sample_editor_layout):
        """Delete removes both XML and metadata files."""
        clean_template_service.save_template("Test", sample_editor_layout)
        xml_path = clean_template_service.templates_dir / "Test.xml"
        json_path = clean_template_service.templates_dir / "Test.json"

        clean_template_service.delete_template("Test")

        assert not xml_path.exists()
        assert not json_path.exists()


class TestTemplateServiceRename:
    """Tests for renaming templates."""

    def test_rename_template(self, clean_template_service, sample_editor_layout):
        """Rename template creates new files."""
        clean_template_service.save_template("Old Name", sample_editor_layout)

        clean_template_service.rename_template("Old Name", "New Name")

        assert not clean_template_service.template_exists("Old Name")
        assert clean_template_service.template_exists("New Name")

    def test_rename_template_not_found(self, clean_template_service):
        """Renaming nonexistent template raises error."""
        with pytest.raises(FileNotFoundError, match="not found"):
            clean_template_service.rename_template("Nonexistent", "New")

    def test_rename_template_overwrites_existing(self, clean_template_service, sample_editor_layout):
        """Renaming to existing name overwrites it."""
        clean_template_service.save_template("Template A", sample_editor_layout)
        clean_template_service.save_template("Template B", sample_editor_layout)

        clean_template_service.rename_template("Template A", "Template B")

        templates = clean_template_service.list_templates()
        names = [t.name for t in templates]
        assert "Template A" not in names
        assert "Template B" in names

    def test_rename_updates_metadata_name(self, clean_template_service, sample_editor_layout):
        """Rename updates name in metadata."""
        import json

        clean_template_service.save_template("Old", sample_editor_layout)
        clean_template_service.rename_template("Old", "New")

        metadata_path = clean_template_service.templates_dir / "New.json"
        metadata = json.loads(metadata_path.read_text())
        assert metadata["name"] == "New"


class TestTemplateServiceSanitization:
    """Tests for name sanitization and security."""

    def test_sanitize_removes_invalid_chars(self, clean_template_service):
        """Invalid characters replaced with underscores."""
        safe = clean_template_service._sanitize_name("My/Template:Name*?")

        assert "/" not in safe
        assert ":" not in safe
        assert "*" not in safe
        assert "?" not in safe

    def test_sanitize_replaces_multiple_spaces(self, clean_template_service):
        """Multiple spaces/underscores collapsed."""
        safe = clean_template_service._sanitize_name("My   Template   Name")

        assert "   " not in safe

    def test_sanitize_empty_name_raises(self, clean_template_service):
        """Empty name raises error."""
        with pytest.raises(ValueError, match="empty"):
            clean_template_service._sanitize_name("")

    def test_sanitize_whitespace_only_raises(self, clean_template_service):
        """Whitespace-only name raises error."""
        with pytest.raises(ValueError, match="empty"):
            clean_template_service._sanitize_name("   ")

    def test_sanitize_truncates_long_name(self, clean_template_service):
        """Long names are truncated."""
        long_name = "A" * 300
        safe = clean_template_service._sanitize_name(long_name)

        assert len(safe) <= 200

    def test_path_traversal_prevented(self, clean_template_service, sample_editor_layout):
        """Path traversal attempts are sanitized or prevented."""
        # The sanitize_name method replaces invalid chars with underscores
        # So "../../../etc/passwd" becomes something like "________etc_passwd"
        # This test verifies the resulting file is within templates_dir
        path = clean_template_service.save_template("../../../etc/passwd", sample_editor_layout)
        # The file should be within templates_dir, not at /etc/passwd
        assert (
            clean_template_service.templates_dir in path.parents or path.parent == clean_template_service.templates_dir
        )

    def test_validate_path_within_templates_dir(self, clean_template_service):
        """Path validation prevents escaping templates dir."""
        from pathlib import Path

        with pytest.raises(ValueError, match="escapes"):
            clean_template_service._validate_path_within_templates_dir(Path("/etc/passwd"))
