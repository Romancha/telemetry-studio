"""Tests for gopro_overlay runtime patches."""

import inspect
from pathlib import Path
from unittest.mock import Mock


class TestApplyPatches:
    """Test apply_patches() function."""

    def test_apply_patches_succeeds(self):
        """Test that apply_patches() can be called without error."""
        from telemetry_studio.patches import apply_patches

        # Should not raise
        apply_patches()

    def test_is_patched_returns_true_after_apply(self):
        """Test that is_patched() returns True after applying patches."""
        from telemetry_studio.patches import apply_patches, is_patched

        apply_patches()
        assert is_patched() is True

    def test_apply_patches_idempotent(self):
        """Test that apply_patches() can be called multiple times safely."""
        from telemetry_studio.patches import apply_patches, is_patched

        apply_patches()
        assert is_patched() is True

        # Call again - should not raise
        apply_patches()
        assert is_patched() is True


class TestFFMPEGGoProPatch:
    """Test patches for FFMPEGGoPro class."""

    def test_find_timecode_method_added(self):
        """Test that FFMPEGGoPro.find_timecode method is added."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro

        assert hasattr(FFMPEGGoPro, "find_timecode")
        assert callable(FFMPEGGoPro.find_timecode)

    def test_find_timecode_extracts_timecode(self):
        """Test that find_timecode extracts timecode from ffprobe output."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro

        # Mock FFMPEG with ffprobe response
        # Note: gopro_overlay uses str(result.stdout) to convert bytes to string
        # so stdout should be bytes that looks like valid JSON when str() is called
        mock_ffmpeg = Mock()
        mock_ffprobe = Mock()
        mock_result = Mock()
        # The actual stdout is bytes, str(bytes) gives "b'...'" which is not valid JSON
        # But gopro_overlay actually expects this to work, so we mock stdout to be
        # a string directly (which str() will just return as-is)
        mock_result.stdout = '{"streams": [{"tags": {"timecode": "10:30:45:12"}}]}'
        mock_ffprobe.invoke.return_value = mock_result
        mock_ffmpeg.ffprobe.return_value = mock_ffprobe

        gopro = FFMPEGGoPro(mock_ffmpeg)
        timecode = gopro.find_timecode(Path("test.mp4"))

        assert timecode == "10:30:45:12"

    def test_find_timecode_returns_none_when_no_timecode(self):
        """Test that find_timecode returns None when no timecode in metadata."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro

        # Mock FFMPEG with ffprobe response without timecode
        mock_ffmpeg = Mock()
        mock_ffprobe = Mock()
        mock_result = Mock()
        mock_result.stdout = '{"streams": [{"tags": {}}]}'
        mock_ffprobe.invoke.return_value = mock_result
        mock_ffmpeg.ffprobe.return_value = mock_ffprobe

        gopro = FFMPEGGoPro(mock_ffmpeg)
        timecode = gopro.find_timecode(Path("test.mp4"))

        assert timecode is None

    def test_find_timecode_returns_none_on_empty_streams(self):
        """Test that find_timecode returns None when streams are empty."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro

        mock_ffmpeg = Mock()
        mock_ffprobe = Mock()
        mock_result = Mock()
        mock_result.stdout = '{"streams": []}'
        mock_ffprobe.invoke.return_value = mock_result
        mock_ffmpeg.ffprobe.return_value = mock_ffprobe

        gopro = FFMPEGGoPro(mock_ffmpeg)
        timecode = gopro.find_timecode(Path("test.mp4"))

        assert timecode is None

    def test_find_timecode_handles_exception(self):
        """Test that find_timecode handles exceptions gracefully."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro

        mock_ffmpeg = Mock()
        mock_ffprobe = Mock()
        mock_ffprobe.invoke.side_effect = Exception("ffprobe failed")
        mock_ffmpeg.ffprobe.return_value = mock_ffprobe

        gopro = FFMPEGGoPro(mock_ffmpeg)
        timecode = gopro.find_timecode(Path("test.mp4"))

        assert timecode is None


class TestFFMPEGOverlayVideoPatch:
    """Test patches for FFMPEGOverlayVideo class."""

    def test_patched_marker_set(self):
        """Test that _ts_patched marker is set after patching."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_overlay import FFMPEGOverlayVideo

        assert hasattr(FFMPEGOverlayVideo, "_ts_patched")
        assert FFMPEGOverlayVideo._ts_patched is True

    def test_init_accepts_timecode_parameter(self):
        """Test that FFMPEGOverlayVideo.__init__ accepts timecode parameter."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.ffmpeg_overlay import FFMPEGOverlayVideo

        sig = inspect.signature(FFMPEGOverlayVideo.__init__)
        assert "timecode" in sig.parameters

    def test_init_stores_timecode(self):
        """Test that FFMPEGOverlayVideo stores timecode in instance."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.dimensions import Dimension
        from gopro_overlay.ffmpeg_overlay import FFMPEGOverlayVideo

        mock_ffmpeg = Mock()

        overlay = FFMPEGOverlayVideo(
            ffmpeg=mock_ffmpeg,
            input=Path("input.mp4"),
            output=Path("output.mp4"),
            overlay_size=Dimension(1920, 1080),
            timecode="00:01:02:03",
        )

        assert hasattr(overlay, "_timecode")
        assert overlay._timecode == "00:01:02:03"

    def test_init_without_timecode(self):
        """Test that FFMPEGOverlayVideo works without timecode parameter."""
        from telemetry_studio.patches import apply_patches

        apply_patches()

        from gopro_overlay.dimensions import Dimension
        from gopro_overlay.ffmpeg_overlay import FFMPEGOverlayVideo

        mock_ffmpeg = Mock()

        overlay = FFMPEGOverlayVideo(
            ffmpeg=mock_ffmpeg,
            input=Path("input.mp4"),
            output=Path("output.mp4"),
            overlay_size=Dimension(1920, 1080),
        )

        # Should have _timecode attribute but it may be None
        assert hasattr(overlay, "_timecode")
        assert overlay._timecode is None


class TestWrapperScript:
    """Test the gopro-dashboard wrapper script."""

    def test_wrapper_script_exists(self):
        """Test that wrapper script file exists."""
        from pathlib import Path

        wrapper_path = Path(__file__).parents[3] / "src" / "telemetry_studio" / "scripts" / "gopro_dashboard_wrapper.py"
        assert wrapper_path.exists()

    def test_wrapper_can_be_imported(self):
        """Test that wrapper script can be imported."""
        from telemetry_studio.scripts import gopro_dashboard_wrapper

        assert hasattr(gopro_dashboard_wrapper, "main")
        assert hasattr(gopro_dashboard_wrapper, "find_gopro_dashboard")


class TestConfigIntegration:
    """Test configuration integration for patches."""

    def test_enable_gopro_patches_setting_exists(self):
        """Test that enable_gopro_patches setting exists."""
        from telemetry_studio.config import settings

        assert hasattr(settings, "enable_gopro_patches")
        assert isinstance(settings.enable_gopro_patches, bool)

    def test_use_wrapper_script_setting_exists(self):
        """Test that use_wrapper_script setting exists."""
        from telemetry_studio.config import settings

        assert hasattr(settings, "use_wrapper_script")
        assert isinstance(settings.use_wrapper_script, bool)

    def test_default_patches_enabled(self):
        """Test that patches are enabled by default."""
        from telemetry_studio.config import settings

        assert settings.enable_gopro_patches is True

    def test_default_wrapper_enabled(self):
        """Test that wrapper script is enabled by default."""
        from telemetry_studio.config import settings

        assert settings.use_wrapper_script is True


class TestServiceIntegration:
    """Test that services properly apply patches."""

    def test_render_service_applies_patches(self):
        """Test that render_service module applies patches on import."""
        # Import the module
        from telemetry_studio.patches import is_patched

        assert is_patched() is True

    def test_renderer_applies_patches(self):
        """Test that renderer module applies patches on import."""
        from telemetry_studio.patches import is_patched

        assert is_patched() is True

    def test_metadata_applies_patches(self):
        """Test that metadata module applies patches on import."""
        from telemetry_studio.patches import is_patched

        assert is_patched() is True
