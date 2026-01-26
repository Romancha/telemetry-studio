"""Integration tests for renderer with real gopro-overlay."""

import pytest

from telemetry_studio.models.schemas import FileRole


@pytest.mark.integration
class TestRendererPreview:
    """Tests for preview rendering with real video."""

    def test_render_preview_returns_image(self, integration_test_video):
        """Render preview should return PNG image data."""
        from telemetry_studio.services.renderer import render_preview

        png_bytes, width, height = render_preview(
            file_path=integration_test_video,
            layout="default-1920x1080",
            frame_time_ms=5000,
        )

        # Should return image bytes
        assert len(png_bytes) > 0
        # PNG magic bytes
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        # Should be 1920x1080
        assert width == 1920
        assert height == 1080

    def test_render_preview_to_base64(self, integration_test_video):
        """Preview image should convert to base64."""
        import base64

        from telemetry_studio.services.renderer import image_to_base64, render_preview

        png_bytes, _, _ = render_preview(
            file_path=integration_test_video,
            layout="default-1920x1080",
            frame_time_ms=5000,
        )

        b64 = image_to_base64(png_bytes)

        # Should be valid base64
        decoded = base64.b64decode(b64)
        assert decoded == png_bytes

    def test_render_preview_different_frame(self, integration_test_video):
        """Preview at different frame times should work."""
        from telemetry_studio.services.renderer import render_preview

        png1, _, _ = render_preview(
            file_path=integration_test_video,
            layout="default-1920x1080",
            frame_time_ms=1000,
        )

        png2, _, _ = render_preview(
            file_path=integration_test_video,
            layout="default-1920x1080",
            frame_time_ms=10000,
        )

        # Both should be valid images but different (different frames)
        assert len(png1) > 0
        assert len(png2) > 0


@pytest.mark.integration
class TestRendererLayouts:
    """Tests for layout handling."""

    def test_get_available_layouts(self):
        """Should return list of available layouts."""
        from telemetry_studio.services.renderer import get_available_layouts

        layouts = get_available_layouts()

        assert len(layouts) > 0
        # Should have default layout
        layout_names = [layout.name for layout in layouts]
        assert any("default" in name for name in layout_names)

    def test_layout_has_dimensions(self):
        """Layouts should have width and height."""
        from telemetry_studio.services.renderer import get_available_layouts

        layouts = get_available_layouts()

        for layout in layouts:
            assert layout.width > 0
            assert layout.height > 0


@pytest.mark.integration
class TestRendererUnits:
    """Tests for unit options."""

    def test_get_available_units(self):
        """Should return unit options."""
        from telemetry_studio.services.renderer import get_available_units

        units = get_available_units()

        assert len(units) > 0
        # Units is a dict with category keys
        assert "speed" in units
        assert "altitude" in units

    def test_units_have_options(self):
        """Unit categories should have options."""
        from telemetry_studio.services.renderer import get_available_units

        units = get_available_units()

        for _category_name, category_data in units.items():
            assert "options" in category_data
            assert len(category_data["options"]) > 0


@pytest.mark.integration
class TestRendererMapStyles:
    """Tests for map style options."""

    def test_get_available_map_styles(self):
        """Should return map style options."""
        from telemetry_studio.services.renderer import get_available_map_styles

        styles = get_available_map_styles()

        assert len(styles) > 0
        # Should have OSM style
        style_names = [s["name"] for s in styles]
        assert "osm" in style_names or any("open" in name.lower() for name in style_names)


@pytest.mark.integration
class TestRendererFFmpegProfiles:
    """Tests for FFmpeg profile options."""

    def test_get_available_ffmpeg_profiles(self):
        """Should return FFmpeg profile options."""
        from telemetry_studio.services.renderer import get_available_ffmpeg_profiles

        profiles = get_available_ffmpeg_profiles()

        assert len(profiles) > 0
        # Should have at least one profile
        for profile in profiles:
            assert "name" in profile
            assert "display_name" in profile


@pytest.mark.integration
class TestRendererCLICommand:
    """Tests for CLI command generation."""

    def test_generate_cli_command_video_only(self, clean_file_manager, integration_test_video, monkeypatch):
        """Generate CLI command for video-only mode."""
        from telemetry_studio.services import file_manager as fm_module
        from telemetry_studio.services.renderer import generate_cli_command

        session_id = clean_file_manager.create_local_session()
        clean_file_manager.add_file(
            session_id=session_id,
            filename=integration_test_video.name,
            file_path=integration_test_video,
            file_type="video",
            role=FileRole.PRIMARY,
        )

        # Patch the singleton file_manager at the source module
        monkeypatch.setattr(fm_module, "file_manager", clean_file_manager)

        cmd = generate_cli_command(
            session_id=session_id,
            output_file="/tmp/output.mp4",
            layout="default-1920x1080",
        )

        assert "gopro-dashboard.py" in cmd
        assert str(integration_test_video) in cmd
        assert "--layout" in cmd
        assert "/tmp/output.mp4" in cmd

    def test_generate_cli_command_with_units(self, clean_file_manager, integration_test_video, monkeypatch):
        """Generate CLI command with custom units."""
        from telemetry_studio.services import file_manager as fm_module
        from telemetry_studio.services.renderer import generate_cli_command

        session_id = clean_file_manager.create_local_session()
        clean_file_manager.add_file(
            session_id=session_id,
            filename=integration_test_video.name,
            file_path=integration_test_video,
            file_type="video",
            role=FileRole.PRIMARY,
        )

        monkeypatch.setattr(fm_module, "file_manager", clean_file_manager)

        cmd = generate_cli_command(
            session_id=session_id,
            output_file="/tmp/output.mp4",
            layout="default-1920x1080",
            units_speed="mph",
            units_altitude="feet",
        )

        assert "--units-speed" in cmd
        assert "mph" in cmd
        assert "--units-altitude" in cmd
        assert "feet" in cmd

    def test_generate_cli_command_with_gpx(
        self, clean_file_manager, integration_test_video, sample_gpx_file, sample_video_metadata, monkeypatch
    ):
        """Generate CLI command with GPX merge."""
        from telemetry_studio.services import file_manager as fm_module
        from telemetry_studio.services.renderer import generate_cli_command

        session_id = clean_file_manager.create_local_session()
        clean_file_manager.add_file(
            session_id=session_id,
            filename=integration_test_video.name,
            file_path=integration_test_video,
            file_type="video",
            role=FileRole.PRIMARY,
            video_metadata=sample_video_metadata,
        )
        clean_file_manager.add_file(
            session_id=session_id,
            filename=sample_gpx_file.name,
            file_path=sample_gpx_file,
            file_type="gpx",
            role=FileRole.SECONDARY,
        )

        monkeypatch.setattr(fm_module, "file_manager", clean_file_manager)

        cmd = generate_cli_command(
            session_id=session_id,
            output_file="/tmp/output.mp4",
            layout="default-1920x1080",
        )

        assert "--gpx" in cmd
        assert str(sample_gpx_file) in cmd
        assert "--gpx-merge" in cmd

    def test_generate_cli_command_with_ffmpeg_profile(self, clean_file_manager, integration_test_video, monkeypatch):
        """Generate CLI command with FFmpeg profile."""
        from telemetry_studio.services import file_manager as fm_module
        from telemetry_studio.services.renderer import generate_cli_command

        session_id = clean_file_manager.create_local_session()
        clean_file_manager.add_file(
            session_id=session_id,
            filename=integration_test_video.name,
            file_path=integration_test_video,
            file_type="video",
            role=FileRole.PRIMARY,
        )

        monkeypatch.setattr(fm_module, "file_manager", clean_file_manager)

        cmd = generate_cli_command(
            session_id=session_id,
            output_file="/tmp/output.mp4",
            layout="default-1920x1080",
            ffmpeg_profile="nvenc",
        )

        assert "--profile" in cmd
        assert "nvenc" in cmd
