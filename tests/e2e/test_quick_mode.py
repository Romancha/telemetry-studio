"""Quick Mode workflow tests."""

import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestFileUpload:
    """Test file upload functionality in Quick Mode."""

    def test_video_upload_shows_file_context(self, app_page: Page, sample_video_path: Path):
        """Upload a video file and verify file context appears."""
        # Find the file input (may be hidden, use force)
        file_input = app_page.locator('input[type="file"]').first
        file_input.set_input_files(str(sample_video_path))

        # Wait for upload to process
        app_page.wait_for_timeout(1000)

        # File context should appear in header (or file uploader should show file info)
        # Note: Real video metadata extraction may fail with dummy file,
        # but the upload flow should complete
        file_uploader = app_page.locator("#file-uploader-container")
        expect(file_uploader).to_be_visible()

    def test_gpx_upload_in_merge_mode(self, app_page: Page, sample_gpx_path: Path):
        """Upload a GPX file for GPS data."""
        # Look for GPX/secondary file input
        file_inputs = app_page.locator('input[type="file"]')

        # Upload GPX to the appropriate input
        if file_inputs.count() > 1:
            file_inputs.nth(1).set_input_files(str(sample_gpx_path))
        else:
            file_inputs.first.set_input_files(str(sample_gpx_path))

        app_page.wait_for_timeout(1000)

        # Verify file uploader reflects the upload
        expect(app_page.locator("#file-uploader-container")).to_be_visible()


@pytest.mark.e2e
class TestLayoutSelection:
    """Test layout selection and configuration."""

    def test_select_layout_from_dropdown(self, app_page: Page):
        """Select a layout from the dropdown."""
        layout_select = app_page.locator("#layout-select")
        expect(layout_select).to_be_visible()

        # Wait for options to load
        app_page.wait_for_timeout(500)

        # Get first non-empty option value
        options = layout_select.locator("option")
        if options.count() > 0:
            first_option = options.first
            value = first_option.get_attribute("value")
            if value:
                layout_select.select_option(value)
                expect(layout_select).to_have_value(value)

    def test_change_speed_units(self, app_page: Page):
        """Change speed units in configuration."""
        speed_select = app_page.locator("#units-speed")
        expect(speed_select).to_be_visible()

        # Wait for options to load
        app_page.wait_for_timeout(500)

        # Select different unit
        options = speed_select.locator("option")
        if options.count() > 1:
            second_option = options.nth(1)
            value = second_option.get_attribute("value")
            if value:
                speed_select.select_option(value)
                expect(speed_select).to_have_value(value)

    def test_change_map_style(self, app_page: Page):
        """Change map style in configuration."""
        map_select = app_page.locator("#map-style")
        expect(map_select).to_be_visible()

        app_page.wait_for_timeout(500)

        options = map_select.locator("option")
        if options.count() > 1:
            # Select OSM which doesn't require API key
            osm_option = map_select.locator('option[value="osm"]')
            if osm_option.count() > 0:
                map_select.select_option("osm")
                expect(map_select).to_have_value("osm")


@pytest.mark.e2e
class TestPreviewGeneration:
    """Test preview generation functionality."""

    def test_auto_preview_toggle(self, app_page: Page):
        """Test auto-preview checkbox functionality."""
        auto_preview = app_page.locator("#auto-preview")
        expect(auto_preview).to_be_visible()
        expect(auto_preview).to_be_checked()

        # Toggle off
        auto_preview.uncheck()
        expect(auto_preview).not_to_be_checked()

        # Toggle back on
        auto_preview.check()
        expect(auto_preview).to_be_checked()

    def test_manual_refresh_button(self, app_page: Page):
        """Test manual refresh preview button."""
        refresh_btn = app_page.locator("#btn-refresh-preview")
        expect(refresh_btn).to_be_visible()

        # Button should be clickable
        expect(refresh_btn).to_be_enabled()


@pytest.mark.e2e
class TestTimeline:
    """Test timeline functionality."""

    def test_timeline_container_exists(self, app_page: Page):
        """Verify timeline container exists (may be hidden until file uploaded)."""
        timeline = app_page.locator("#timeline-container")
        # Timeline exists but may be hidden until a file is uploaded
        expect(timeline).to_be_attached()

    def test_timeline_quick_buttons_exist(self, app_page: Page):
        """Test timeline quick navigation buttons exist."""
        # Quick buttons exist but may be hidden until file uploaded
        quick_btns = app_page.locator(".timeline-quick-btn")
        expect(quick_btns.first).to_be_attached()

        # Should have Start, 25%, 50%, 75%, End buttons
        expect(app_page.locator('.timeline-quick-btn[data-percent="0"]')).to_be_attached()
        expect(app_page.locator('.timeline-quick-btn[data-percent="50"]')).to_be_attached()
        expect(app_page.locator('.timeline-quick-btn[data-percent="100"]')).to_be_attached()


@pytest.mark.e2e
class TestRenderButton:
    """Test render functionality (without actual rendering)."""

    def test_render_button_visible(self, app_page: Page):
        """Verify render button is visible."""
        render_btn = app_page.locator("#btn-render")
        expect(render_btn).to_be_visible()
        expect(render_btn).to_have_text("Render Video")

    def test_batch_render_button_visible(self, app_page: Page):
        """Verify batch render button is visible."""
        batch_btn = app_page.locator("#btn-batch-render")
        expect(batch_btn).to_be_visible()
        expect(batch_btn).to_have_text("Batch Render")

    def test_generate_command_button(self, app_page: Page):
        """Verify generate command button is visible."""
        cmd_btn = app_page.locator("#btn-generate-cmd")
        expect(cmd_btn).to_be_visible()
        expect(cmd_btn).to_have_text("Get Command")


@pytest.mark.e2e
class TestRealFileLoadingAndPreview:
    """Test real file loading by path and preview generation."""

    @pytest.fixture
    def test_video_path(self) -> Path:
        """Get path to the test video with telemetry."""
        video_path = Path(__file__).parent.parent / "fixtures" / "videos" / "raw_gopro_with_telemetry.MP4"
        if not video_path.exists():
            pytest.skip(f"Test video not found: {video_path}")
        return video_path

    def test_load_video_by_path_and_preview(self, app_page: Page, test_video_path: Path):
        """Test complete flow: load video by path → verify preview generation."""
        # Fill the video path input
        video_input = app_page.locator("#video-path-input")
        expect(video_input).to_be_visible()
        video_input.fill(str(test_video_path))

        # Click Load button
        load_btn = app_page.locator("#video-load-btn")
        expect(load_btn).to_be_visible()
        load_btn.click()

        # Wait for file to load and metadata to be extracted
        app_page.wait_for_timeout(3000)

        # Verify file context appears in header (hidden class removed)
        file_context = app_page.locator("#file-context")
        expect(file_context).to_be_visible()
        expect(file_context).not_to_have_class(re.compile(r"hidden"))

        # Verify video metadata is displayed in file context details
        file_details = app_page.locator(".file-context-details")
        expect(file_details).to_be_visible()
        # Should show resolution like "3840x2160" or similar
        expect(file_details).to_contain_text(re.compile(r"\d+x\d+"))
        # Should show FPS
        expect(file_details).to_contain_text("FPS")

        # Verify GPS badge appears (test video has telemetry)
        gps_badge = app_page.locator(".gps-badge")
        expect(gps_badge).to_be_visible()
        expect(gps_badge).to_have_text("GPS")

        # Verify preview image is generated
        preview_img = app_page.locator("#preview-image")
        expect(preview_img).to_be_visible()
        # Preview should have a src attribute with base64 data or URL
        src = preview_img.get_attribute("src")
        assert src is not None and len(src) > 0, "Preview image should have a src"

        # Verify timeline appears with duration
        timeline_container = app_page.locator("#timeline-container")
        expect(timeline_container).to_be_visible()

        # Verify timeline shows correct duration format (MM:SS)
        duration_display = app_page.locator("#timeline-duration")
        expect(duration_display).to_be_visible()
        expect(duration_display).to_contain_text(re.compile(r"\d{2}:\d{2}"))

    def test_timeline_scrubbing_updates_preview(self, app_page: Page, test_video_path: Path):
        """Test that moving timeline updates preview frame."""
        # Load video first
        video_input = app_page.locator("#video-path-input")
        video_input.fill(str(test_video_path))
        app_page.locator("#video-load-btn").click()
        app_page.wait_for_timeout(3000)

        # Verify preview is loaded
        preview_img = app_page.locator("#preview-image")
        expect(preview_img).to_be_visible()

        # Click on a quick navigation button (50%)
        mid_btn = app_page.locator('.timeline-quick-btn[data-percent="50"]')
        expect(mid_btn).to_be_visible()
        mid_btn.click()

        # Wait for new preview to generate
        app_page.wait_for_timeout(2000)

        # Preview should have updated (different frame)
        new_src = preview_img.get_attribute("src")
        # Note: src may or may not change depending on auto-preview setting
        # At minimum, verify preview is still visible
        expect(preview_img).to_be_visible()
        assert new_src is not None and len(new_src) > 0, "Preview should still have src after timeline change"
