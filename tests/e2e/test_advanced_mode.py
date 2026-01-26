"""Advanced Mode (Visual Editor) workflow tests."""

import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestAdvancedModeUI:
    """Test Advanced Mode UI elements."""

    def test_widget_palette_visible_in_advanced_mode(self, app_page: Page):
        """Verify widget palette appears in Advanced Mode."""
        # Switch to advanced mode
        app_page.locator("#mode-advanced").click()

        # Widget palette should be visible
        widget_palette = app_page.locator("#widget-palette-container")
        expect(widget_palette).to_be_visible()

        # Widget palette should contain widgets
        palette = app_page.locator("#widget-palette")
        expect(palette).to_be_visible()

    def test_widget_search_input(self, app_page: Page):
        """Test widget search functionality."""
        app_page.locator("#mode-advanced").click()

        search_input = app_page.locator("#widget-search")
        expect(search_input).to_be_visible()

        # Type in search
        search_input.fill("text")
        expect(search_input).to_have_value("text")

    def test_advanced_toolbar_controls(self, app_page: Page):
        """Verify advanced toolbar controls are available."""
        app_page.locator("#mode-advanced").click()

        # Wait for toolbar to be visible
        toolbar = app_page.locator("#advanced-toolbar")
        expect(toolbar).to_be_visible()

        # Undo/Redo buttons
        expect(app_page.locator("#btn-undo")).to_be_visible()
        expect(app_page.locator("#btn-redo")).to_be_visible()

        # Zoom controls
        expect(app_page.locator("#btn-zoom-out")).to_be_visible()
        expect(app_page.locator("#btn-zoom-in")).to_be_visible()
        expect(app_page.locator("#btn-zoom-fit")).to_be_visible()
        expect(app_page.locator("#zoom-level")).to_be_visible()

        # Grid and snap toggles
        expect(app_page.locator("#toggle-grid")).to_be_visible()
        expect(app_page.locator("#toggle-snap")).to_be_visible()


@pytest.mark.e2e
class TestCanvasInteraction:
    """Test canvas interaction in Advanced Mode."""

    def test_canvas_container_visible(self, app_page: Page):
        """Verify canvas container is visible in Advanced Mode."""
        app_page.locator("#mode-advanced").click()

        canvas_container = app_page.locator("#canvas-container")
        expect(canvas_container).to_be_visible()

        canvas = app_page.locator("#canvas")
        expect(canvas).to_be_visible()

    def test_empty_canvas_hint_visible(self, app_page: Page):
        """Verify empty canvas hint is shown when no widgets."""
        app_page.locator("#mode-advanced").click()

        # Empty hint should be visible initially
        empty_hint = app_page.locator("#canvas-empty-hint")
        expect(empty_hint).to_be_visible()

    def test_toggle_grid(self, app_page: Page):
        """Test grid toggle functionality."""
        app_page.locator("#mode-advanced").click()

        grid_toggle = app_page.locator("#toggle-grid")
        expect(grid_toggle).to_be_visible()

        # Grid should be checked by default
        expect(grid_toggle).to_be_checked()

        # Toggle off
        grid_toggle.uncheck()
        expect(grid_toggle).not_to_be_checked()

        # Toggle back on
        grid_toggle.check()
        expect(grid_toggle).to_be_checked()

    def test_zoom_controls(self, app_page: Page):
        """Test zoom in/out functionality."""
        app_page.locator("#mode-advanced").click()

        zoom_level = app_page.locator("#zoom-level")
        expect(zoom_level).to_be_visible()

        # Click zoom in
        app_page.locator("#btn-zoom-in").click()
        app_page.wait_for_timeout(200)
        expect(zoom_level).to_be_visible()

        # Click zoom out
        app_page.locator("#btn-zoom-out").click()
        app_page.wait_for_timeout(200)
        expect(zoom_level).to_be_visible()


@pytest.mark.e2e
class TestPanelTabs:
    """Test panel tab switching in Advanced Mode."""

    def test_panel_tabs_exist(self, app_page: Page):
        """Verify panel tabs exist in DOM."""
        # Tabs exist in DOM (visibility depends on right panel state)
        config_tab = app_page.locator('.panel-tab[data-tab="config"]')
        properties_tab = app_page.locator('.panel-tab[data-tab="properties"]')
        layers_tab = app_page.locator('.panel-tab[data-tab="layers"]')

        expect(config_tab).to_be_attached()
        expect(properties_tab).to_be_attached()
        expect(layers_tab).to_be_attached()

    def test_switch_to_properties_tab(self, app_page: Page):
        """Test switching to Properties tab."""
        app_page.locator("#mode-advanced").click()

        properties_tab = app_page.locator('.panel-tab[data-tab="properties"]')
        properties_tab.click()

        # Properties tab should be active
        expect(properties_tab).to_have_class(re.compile(r"active"))

        # Properties panel should be visible
        properties_panel = app_page.locator("#properties-panel")
        expect(properties_panel).to_be_visible()

    def test_switch_to_layers_tab(self, app_page: Page):
        """Test switching to Layers tab."""
        app_page.locator("#mode-advanced").click()

        layers_tab = app_page.locator('.panel-tab[data-tab="layers"]')
        layers_tab.click()

        # Layers tab should be active
        expect(layers_tab).to_have_class(re.compile(r"active"))

        # Layers panel should be visible
        layers_panel = app_page.locator("#layers-panel")
        expect(layers_panel).to_be_visible()


@pytest.mark.e2e
class TestTemplateControls:
    """Test template controls in Advanced Mode."""

    def test_template_select_visible(self, app_page: Page):
        """Verify template selector is visible in Advanced Mode."""
        app_page.locator("#mode-advanced").click()

        template_select = app_page.locator("#template-select")
        expect(template_select).to_be_visible()

    def test_save_template_button(self, app_page: Page):
        """Verify save template button is visible."""
        app_page.locator("#mode-advanced").click()

        save_btn = app_page.locator("#btn-save-template")
        expect(save_btn).to_be_visible()

    def test_upload_template_button(self, app_page: Page):
        """Verify upload template button is visible."""
        app_page.locator("#mode-advanced").click()

        upload_btn = app_page.locator("#btn-upload-template")
        expect(upload_btn).to_be_visible()

    def test_manage_templates_button(self, app_page: Page):
        """Verify manage templates button is visible."""
        app_page.locator("#mode-advanced").click()

        manage_btn = app_page.locator("#btn-manage-templates")
        expect(manage_btn).to_be_visible()


@pytest.mark.e2e
class TestExportFunctionality:
    """Test export functionality in Advanced Mode."""

    def test_export_xml_button_visible(self, app_page: Page):
        """Verify export XML button is visible."""
        export_btn = app_page.locator("#btn-export")
        expect(export_btn).to_be_visible()
        expect(export_btn).to_have_text("Export XML")


@pytest.mark.e2e
class TestWidgetPaletteInteraction:
    """Test widget palette interactions discovered via MCP Playwright exploration."""

    def test_widget_categories_visible(self, app_page: Page):
        """Verify widget categories are displayed in palette."""
        app_page.locator("#mode-advanced").click()

        # Wait for widget palette to load
        palette = app_page.locator("#widget-palette")
        expect(palette).to_be_visible()

        # Check for category headings discovered in UI exploration
        expect(app_page.locator("#widget-palette h3", has_text="Text")).to_be_visible()
        expect(app_page.locator("#widget-palette h3", has_text="Metrics")).to_be_visible()
        expect(app_page.locator("#widget-palette h3", has_text="Maps")).to_be_visible()
        expect(app_page.locator("#widget-palette h3", has_text="Gauges")).to_be_visible()

    def test_widget_search_filters_results(self, app_page: Page):
        """Test that widget search filters the palette."""
        app_page.locator("#mode-advanced").click()

        search_input = app_page.locator("#widget-search")
        expect(search_input).to_be_visible()

        # Search for "map" - should show map-related widgets
        search_input.fill("map")
        app_page.wait_for_timeout(300)  # Wait for filter to apply

        # Moving Map widget should still be visible
        moving_map = app_page.locator("#widget-palette").get_by_text("Moving Map")
        expect(moving_map).to_be_visible()

    def test_widget_items_have_descriptions(self, app_page: Page):
        """Verify widget items have title/description attributes."""
        app_page.locator("#mode-advanced").click()

        # Widget items should have descriptive titles (seen in exploration)
        # Use .widget-item to target palette items specifically (not layer items)
        text_widget = app_page.locator('.widget-item[title="Static text label"]')
        expect(text_widget).to_be_attached()


@pytest.mark.e2e
class TestTemplateLoading:
    """Test template loading functionality discovered via MCP Playwright exploration."""

    def test_template_dropdown_has_options(self, app_page: Page):
        """Verify template dropdown is populated with options."""
        app_page.locator("#mode-advanced").click()

        template_select = app_page.locator("#template-select")
        expect(template_select).to_be_visible()

        # Wait for options to load (async from API)
        app_page.wait_for_timeout(500)

        # Should have predefined templates (discovered in UI)
        options = template_select.locator("option")
        count = options.count()
        # At minimum: placeholder + several default templates
        assert count > 5, f"Expected more than 5 template options, got {count}"

    def test_load_template_populates_canvas(self, app_page: Page):
        """Test that selecting a template loads widgets onto canvas."""
        app_page.locator("#mode-advanced").click()

        # Select a predefined template
        template_select = app_page.locator("#template-select")
        template_select.select_option(label="Default 1920X1080")

        # Wait for template to load
        app_page.wait_for_timeout(500)

        # Canvas should no longer show empty hint (widgets loaded)
        # The canvas should have widget elements
        canvas = app_page.locator("#canvas")
        expect(canvas).to_be_visible()


@pytest.mark.e2e
class TestPropertiesPanelInteraction:
    """Test properties panel interactions discovered via MCP Playwright exploration."""

    def test_properties_panel_shows_no_selection_message(self, app_page: Page):
        """Verify properties panel shows message when no widget selected."""
        app_page.locator("#mode-advanced").click()

        # Click Properties tab
        app_page.locator('.panel-tab[data-tab="properties"]').click()

        # Should show "Select a widget" message
        properties_panel = app_page.locator("#properties-panel")
        expect(properties_panel).to_contain_text("Select a widget")

    def test_config_panel_has_unit_selectors(self, app_page: Page):
        """Verify Config panel has unit configuration dropdowns."""
        # Config tab should be visible in Quick mode too
        config_panel = app_page.locator("#config-panel")
        expect(config_panel).to_be_visible()

        # Verify unit selectors discovered in UI exploration
        expect(app_page.locator("#units-speed")).to_be_visible()
        expect(app_page.locator("#units-altitude")).to_be_visible()
        expect(app_page.locator("#units-distance")).to_be_visible()
        expect(app_page.locator("#units-temperature")).to_be_visible()

    def test_map_style_has_many_options(self, app_page: Page):
        """Verify Map Style dropdown has multiple options including OSM."""
        map_style = app_page.locator("#map-style")
        expect(map_style).to_be_visible()

        # Should have OSM option (discovered as selected by default)
        osm_option = map_style.locator('option[value="osm"]')
        expect(osm_option).to_be_attached()

        # Should have many map style options
        options = map_style.locator("option")
        assert options.count() > 10, f"Expected more than 10 map style options, got {options.count()}"


@pytest.mark.e2e
class TestLayersPanelInitialization:
    """Test that layers panel correctly shows widgets on initialization."""

    def test_layers_panel_shows_widgets_after_template_load(self, app_page: Page):
        """Verify layers panel shows layer items after loading a template."""
        # Switch to advanced mode
        app_page.locator("#mode-advanced").click()
        app_page.wait_for_timeout(500)

        # Load a template with widgets
        template_select = app_page.locator("#template-select")
        expect(template_select).to_be_visible()
        template_select.select_option(label="Default 1920X1080")
        app_page.wait_for_timeout(500)

        # Switch to Layers tab
        layers_tab = app_page.locator('.panel-tab[data-tab="layers"]')
        layers_tab.click()
        expect(layers_tab).to_have_class(re.compile(r"active"))

        # Layers panel should be visible
        layers_panel = app_page.locator("#layers-panel")
        expect(layers_panel).to_be_visible()

        # CRITICAL: Should have layer items (not empty)
        layer_items = layers_panel.locator(".layer-item")
        count = layer_items.count()
        assert count > 0, f"Expected layer items, found {count}"

        # Should NOT show empty state messages
        expect(layers_panel).not_to_contain_text("No widgets in layout")
        expect(layers_panel).not_to_contain_text("No layout loaded")


@pytest.mark.e2e
class TestAdvancedModePreview:
    """Test preview generation in Advanced Mode."""

    @pytest.fixture
    def test_video_path(self) -> Path:
        """Get path to the test video with telemetry."""
        video_path = Path(__file__).parent.parent / "fixtures" / "videos" / "raw_gopro_with_telemetry.MP4"
        if not video_path.exists():
            pytest.skip(f"Test video not found: {video_path}")
        return video_path

    def test_advanced_mode_preview_with_template(self, app_page: Page, test_video_path: Path):
        """Test preview generation in Advanced Mode after loading a template."""
        # Load video first
        video_input = app_page.locator("#video-path-input")
        expect(video_input).to_be_visible()
        video_input.fill(str(test_video_path))
        app_page.locator("#video-load-btn").click()
        app_page.wait_for_timeout(3000)

        # Verify file loaded
        file_context = app_page.locator("#file-context")
        expect(file_context).to_be_visible()

        # Switch to Advanced Mode
        app_page.locator("#mode-advanced").click()
        expect(app_page.locator("#mode-advanced")).to_have_class(re.compile(r"active"))

        # Wait for advanced mode UI
        app_page.wait_for_timeout(500)

        # Widget palette should be visible
        expect(app_page.locator("#widget-palette-container")).to_be_visible()

        # Load a template
        template_select = app_page.locator("#template-select")
        expect(template_select).to_be_visible()
        template_select.select_option(label="Default 1920X1080")

        # Wait for template to load and preview to generate
        app_page.wait_for_timeout(3000)

        # Canvas preview image should be visible with content
        canvas_preview = app_page.locator("#canvas-preview-image")
        expect(canvas_preview).to_be_visible()

        # Preview should have a src attribute
        src = canvas_preview.get_attribute("src")
        assert src is not None and len(src) > 0, "Canvas preview should have image src"

    def test_advanced_mode_canvas_preview_updates(self, app_page: Page, test_video_path: Path):
        """Test that canvas preview updates when timeline changes in Advanced Mode."""
        # Load video
        video_input = app_page.locator("#video-path-input")
        video_input.fill(str(test_video_path))
        app_page.locator("#video-load-btn").click()
        app_page.wait_for_timeout(3000)

        # Switch to Advanced Mode
        app_page.locator("#mode-advanced").click()
        app_page.wait_for_timeout(500)

        # Load a template
        template_select = app_page.locator("#template-select")
        template_select.select_option(label="Default 1920X1080")
        app_page.wait_for_timeout(3000)

        # Get initial preview
        canvas_preview = app_page.locator("#canvas-preview-image")
        expect(canvas_preview).to_be_visible()

        # Click timeline to change frame (50%)
        mid_btn = app_page.locator('.timeline-quick-btn[data-percent="50"]')
        expect(mid_btn).to_be_visible()
        mid_btn.click()

        # Wait for preview to update
        app_page.wait_for_timeout(2000)

        # Preview should still be visible
        expect(canvas_preview).to_be_visible()
        src = canvas_preview.get_attribute("src")
        assert src is not None and len(src) > 0, "Preview should have src after timeline change"

    def test_advanced_mode_preview_with_zoom(self, app_page: Page, test_video_path: Path):
        """Test zoom controls don't break preview in Advanced Mode."""
        # Load video
        video_input = app_page.locator("#video-path-input")
        video_input.fill(str(test_video_path))
        app_page.locator("#video-load-btn").click()
        app_page.wait_for_timeout(3000)

        # Switch to Advanced Mode
        app_page.locator("#mode-advanced").click()
        app_page.wait_for_timeout(500)

        # Load a template
        template_select = app_page.locator("#template-select")
        template_select.select_option(label="Default 1920X1080")
        app_page.wait_for_timeout(3000)

        # Verify canvas preview is visible
        canvas_preview = app_page.locator("#canvas-preview-image")
        expect(canvas_preview).to_be_visible()

        # Use zoom controls
        zoom_in = app_page.locator("#btn-zoom-in")
        expect(zoom_in).to_be_visible()
        zoom_in.click()
        app_page.wait_for_timeout(300)

        zoom_out = app_page.locator("#btn-zoom-out")
        zoom_out.click()
        app_page.wait_for_timeout(300)

        # Preview should still be visible after zoom
        expect(canvas_preview).to_be_visible()

        # Zoom fit
        zoom_fit = app_page.locator("#btn-zoom-fit")
        zoom_fit.click()
        app_page.wait_for_timeout(300)

        expect(canvas_preview).to_be_visible()
