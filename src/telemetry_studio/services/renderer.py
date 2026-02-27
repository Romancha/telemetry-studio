"""Preview rendering service using gopro_overlay."""

import asyncio
import base64
import io
import re
import shlex
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFont

from telemetry_studio.config import settings
from telemetry_studio.constants import (
    DEFAULT_GPS_DOP_MAX,
    DEFAULT_GPS_SPEED_MAX,
    DEFAULT_UNITS_ALTITUDE,
    DEFAULT_UNITS_DISTANCE,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TEMPERATURE,
    UNIT_OPTIONS,
)

# Apply runtime patches if enabled
if settings.enable_gopro_patches:
    from telemetry_studio.patches import apply_patches

    apply_patches()

# Thread pool for running sync code that uses asyncio (geotiler)
_executor = ThreadPoolExecutor(max_workers=2)


# Shared font list for consistency between preview and CLI render
_FONTS_TO_TRY = [
    # Standard Roboto font (may be installed)
    "Roboto-Medium.ttf",
    # macOS system fonts
    "/Library/Fonts/SF-Pro.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Geneva.ttf",
    "/System/Library/Fonts/Monaco.ttf",
    "/Library/Fonts/Arial.ttf",
    # Linux common fonts
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    # Windows fonts
    "C:/Windows/Fonts/arial.ttf",
    # Generic names (PIL will search system paths)
    "Arial",
    "Helvetica",
]


def _find_available_font() -> str | None:
    """Find an available font file. Used by both preview and CLI render."""
    from pathlib import Path

    for font in _FONTS_TO_TRY:
        path = Path(font)
        if path.is_absolute() and path.exists():
            return str(path)
        # For non-absolute paths, try to find via font loader
        try:
            from gopro_overlay.font import load_font

            load_font(font)
            return font  # Font name is valid
        except (OSError, ImportError):
            continue

    return None


def _load_font_with_fallback():
    """Load font with fallback to system fonts. Uses same list as CLI."""
    from gopro_overlay.font import load_font

    for font_name in _FONTS_TO_TRY:
        try:
            return load_font(font_name)
        except OSError:
            continue

    # Last resort - use default PIL font
    return ImageFont.load_default()


@dataclass
class LayoutInfo:
    """Information about an available layout."""

    name: str
    display_name: str
    width: int
    height: int


def get_available_layouts() -> list[LayoutInfo]:
    """Get list of available layouts with their metadata."""
    layouts = []

    # Parse layout names to extract resolution
    layout_names = [
        "default-1920x1080",
        "default-2688x1512",
        "default-2704x1520",
        "default-3840x2160",
        "moto_1080",
        "moto_1080_2bars",
        "moto_1080_needle",
        "moto_2160",
        "moto_2160_2bars",
        "moto_2160_needle",
        "power-1920x1080",
        "example",
        "example-2",
    ]

    for name in layout_names:
        width, height = _parse_resolution(name)
        display_name = _format_display_name(name)
        layouts.append(
            LayoutInfo(
                name=name,
                display_name=display_name,
                width=width,
                height=height,
            )
        )

    return layouts


def _parse_resolution(name: str) -> tuple[int, int]:
    """Parse resolution from layout name."""
    # Try to extract WIDTHxHEIGHT pattern
    match = re.search(r"(\d+)x(\d+)", name)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Handle moto layouts
    if "2160" in name:
        return 3840, 2160
    elif "1080" in name:
        return 1920, 1080

    # Default fallback
    return 1920, 1080


def _format_display_name(name: str) -> str:
    """Format layout name for display."""
    # Replace underscores and hyphens with spaces
    display = name.replace("_", " ").replace("-", " ")
    # Capitalize words
    return display.title()


def get_available_units() -> dict:
    """Get available unit options from centralized constants."""
    return UNIT_OPTIONS


def get_available_map_styles() -> list[dict]:
    """Get available map styles from gopro_overlay."""
    from gopro_overlay.geo import available_map_styles

    # Map styles that require API keys (by prefix)
    API_KEY_PREFIXES = ["tf-", "geo-"]

    styles = available_map_styles()
    result = []
    for style in styles:
        # Format display name
        display_name = style.replace("-", " ").replace("_", " ").title()

        # Check if this style requires an API key
        requires_api_key = any(style.startswith(prefix) for prefix in API_KEY_PREFIXES)

        result.append(
            {
                "name": style,
                "display_name": display_name,
                "requires_api_key": requires_api_key,
            }
        )
    return result


def get_available_ffmpeg_profiles() -> list[dict]:
    """Get available FFmpeg encoding profiles."""
    from gopro_overlay.ffmpeg_profile import builtin_profiles

    # Profile descriptions
    profile_descriptions = {
        "nvgpu": "NVIDIA GPU acceleration (H.264, 25 Mbps)",
        "nnvgpu": "NVIDIA GPU with CUDA overlay (H.264, 25 Mbps)",
        "mov": "Lossless PNG codec (large files)",
        "vp9": "VP9 codec with alpha channel",
        "vp8": "VP8 codec with alpha channel",
        "mac_hevc": "macOS VideoToolbox HEVC (high quality)",
        "mac": "macOS VideoToolbox H.264 (high quality)",
        "qsv": "Intel QuickSync HEVC acceleration",
    }

    result = []

    # Add "default" option first
    result.append(
        {
            "name": "",
            "display_name": "Default",
            "description": "H.264, veryfast preset (balanced speed/quality)",
            "is_builtin": True,
        }
    )

    # Add builtin profiles
    for name in builtin_profiles:
        display_name = name.replace("_", " ").replace("-", " ").title()
        description = profile_descriptions.get(name, f"{name} encoding profile")

        result.append(
            {
                "name": name,
                "display_name": display_name,
                "description": description,
                "is_builtin": True,
            }
        )

    # TODO: Add user-defined profiles from ~/.gopro-graphics/ffmpeg-profiles.json

    return result


def _extract_video_frame(file_path: Path, time_ms: int, width: int, height: int) -> Image.Image | None:
    """Extract a frame from video at specified time."""
    from gopro_overlay.ffmpeg import FFMPEG
    from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro
    from gopro_overlay.timeunits import timeunits

    try:
        ffmpeg = FFMPEG()
        ffmpeg_gopro = FFMPEGGoPro(ffmpeg)

        frame_bytes = ffmpeg_gopro.load_frame(file_path, timeunits(millis=time_ms))
        if frame_bytes:
            # Convert raw RGBA bytes to PIL Image
            frame = Image.frombytes("RGBA", (width, height), frame_bytes)
            return frame
    except Exception as e:
        print(f"Failed to extract video frame: {e}")

    return None


def render_preview(
    file_path: Path,
    layout: str,
    frame_time_ms: int,
    units_speed: str = DEFAULT_UNITS_SPEED,
    units_altitude: str = DEFAULT_UNITS_ALTITUDE,
    units_distance: str = DEFAULT_UNITS_DISTANCE,
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE,
    map_style: str | None = None,
    gps_dop_max: float = DEFAULT_GPS_DOP_MAX,
    gps_speed_max: float = DEFAULT_GPS_SPEED_MAX,
    gpx_path: Path | None = None,
) -> tuple[bytes, int, int]:
    """Render a preview image for the given file and settings.

    Returns tuple of (png_bytes, width, height).
    """
    from gopro_overlay.ffmpeg import FFMPEG
    from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro
    from gopro_overlay.framemeta_gpx import timeseries_to_framemeta
    from gopro_overlay.geo import MapRenderer, MapStyler
    from gopro_overlay.gpmd_filters import standard as gps_filter_standard
    from gopro_overlay.layout import Overlay
    from gopro_overlay.layout_xml import Converters, layout_from_xml, load_xml_layout
    from gopro_overlay.loading import GoproLoader, load_external
    from gopro_overlay.privacy import NoPrivacyZone
    from gopro_overlay.timeunits import timeunits
    from gopro_overlay.units import units

    suffix = file_path.suffix.lower()

    # Set up converters with specified units
    converters = Converters(
        speed_unit=units_speed,
        distance_unit=units_distance,
        altitude_unit=units_altitude,
        temperature_unit=units_temperature,
    )

    # Load the layout XML
    layout_xml = load_xml_layout(Path(layout))

    # Get layout dimensions
    layout_info = None
    for info in get_available_layouts():
        if info.name == layout:
            layout_info = info
            break

    if layout_info is None:
        layout_info = get_available_layouts()[0]

    # Try to extract video frame as background (for video files)
    background = None
    if suffix in (".mp4", ".mov"):
        try:
            from telemetry_studio.services.metadata import get_display_dimensions, get_video_rotation

            # Get display dimensions accounting for rotation
            ffmpeg = FFMPEG()
            ffmpeg_gopro = FFMPEGGoPro(ffmpeg)
            recording = ffmpeg_gopro.find_recording(file_path)
            rotation = get_video_rotation(file_path)
            video_width, video_height = get_display_dimensions(
                recording.video.dimension.x, recording.video.dimension.y, rotation
            )

            background = _extract_video_frame(file_path, frame_time_ms, video_width, video_height)
            if background and background.size != (layout_info.width, layout_info.height):
                background = background.resize((layout_info.width, layout_info.height), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Failed to extract video frame for preview: {e}")

    # Create base image - use video frame or black background
    image = (
        background.convert("RGBA")
        if background
        else Image.new("RGBA", (layout_info.width, layout_info.height), (0, 0, 0, 255))
    )

    # Set up map renderer with cache
    cache_dir = Path(tempfile.gettempdir()) / "telemetry_studio_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    style = map_style or "osm"
    styler = MapStyler()

    with MapRenderer(cache_dir, styler).open(style) as renderer:
        # Load font with fallback
        font = _load_font_with_fallback()

        # Privacy zone
        privacy = NoPrivacyZone()

        if suffix in (".mp4", ".mov"):
            # Load GoPro video
            ffmpeg = FFMPEG()
            ffmpeg_gopro = FFMPEGGoPro(ffmpeg)

            # Create GPS filter with configured thresholds
            gps_filter = gps_filter_standard(
                dop_max=gps_dop_max,
                speed_max=units.Quantity(gps_speed_max, units.kph),
            )

            loader = GoproLoader(ffmpeg_gopro, units, gps_lock_filter=gps_filter)

            try:
                gopro = loader.load(file_path)
                framemeta = gopro.framemeta
            except (OSError, TypeError, ValueError) as e:
                if gpx_path:
                    # Video has no GPS — use external GPX/FIT file
                    timeseries = load_external(gpx_path, units)
                    framemeta = timeseries_to_framemeta(timeseries, units)
                else:
                    raise ValueError("Video file does not contain GPS metadata") from e

        else:
            # Load GPX or FIT file
            timeseries = load_external(file_path, units)
            framemeta = timeseries_to_framemeta(timeseries, units)

        # Parse the layout XML
        create_widgets = layout_from_xml(
            layout_xml,
            renderer=renderer,
            framemeta=framemeta,
            font=font,
            privacy=privacy,
            converters=converters,
        )

        # Create overlay
        overlay = Overlay(framemeta, create_widgets)

        # Draw at specified time
        pts = timeunits(millis=frame_time_ms)
        image = overlay.draw(pts, image)

    # Convert to PNG bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    return png_bytes, layout_info.width, layout_info.height


def image_to_base64(png_bytes: bytes) -> str:
    """Convert PNG bytes to base64 string."""
    return base64.b64encode(png_bytes).decode("utf-8")


async def render_preview_from_layout(
    layout,
    file_path: Path | None = None,
    frame_time_ms: int = 0,
    units_speed: str = DEFAULT_UNITS_SPEED,
    units_altitude: str = DEFAULT_UNITS_ALTITUDE,
    units_distance: str = DEFAULT_UNITS_DISTANCE,
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE,
    map_style: str | None = None,
    gps_dop_max: float = DEFAULT_GPS_DOP_MAX,
    gps_speed_max: float = DEFAULT_GPS_SPEED_MAX,
    gpx_path: Path | None = None,
) -> dict:
    """
    Render preview from an editor layout.

    Args:
        layout: EditorLayout object with widgets
        file_path: Optional path to uploaded video/gpx/fit file
        frame_time_ms: Time in milliseconds for the preview frame
        units_speed: Speed unit (kph, mph, knots, pace)
        units_altitude: Altitude unit (metre, foot)
        units_distance: Distance unit (km, mile)
        units_temperature: Temperature unit (degC, degF)
        map_style: Map style to use

    Returns:
        Dict with image_base64, width, height
    """
    from telemetry_studio.services.xml_converter import xml_converter

    # Convert layout to XML
    xml_content = xml_converter.layout_to_xml(layout)

    width = layout.canvas.width
    height = layout.canvas.height

    # If we have an uploaded file, try to render with actual data
    if file_path and file_path.exists():
        # Run in separate thread to avoid asyncio conflicts with geotiler
        loop = asyncio.get_running_loop()
        png_bytes, _, _ = await loop.run_in_executor(
            _executor,
            lambda: _render_layout_with_data(
                xml_content,
                file_path,
                frame_time_ms,
                width,
                height,
                units_speed,
                units_altitude,
                units_distance,
                units_temperature,
                map_style,
                gps_dop_max,
                gps_speed_max,
                gpx_path,
            ),
        )
        return {
            "image_base64": image_to_base64(png_bytes),
            "width": width,
            "height": height,
            "frame_time_ms": frame_time_ms,
        }

    # No file uploaded - render placeholder preview
    png_bytes = _render_layout_placeholder(xml_content, width, height)

    return {
        "image_base64": image_to_base64(png_bytes),
        "width": width,
        "height": height,
        "frame_time_ms": frame_time_ms,
    }


def _render_layout_with_data(
    xml_content: str,
    file_path: Path,
    frame_time_ms: int,
    width: int,
    height: int,
    units_speed: str = DEFAULT_UNITS_SPEED,
    units_altitude: str = DEFAULT_UNITS_ALTITUDE,
    units_distance: str = DEFAULT_UNITS_DISTANCE,
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE,
    map_style: str | None = None,
    gps_dop_max: float = DEFAULT_GPS_DOP_MAX,
    gps_speed_max: float = DEFAULT_GPS_SPEED_MAX,
    gpx_path: Path | None = None,
) -> tuple[bytes, int, int]:
    """Render layout XML with actual data from file."""
    from gopro_overlay.ffmpeg import FFMPEG
    from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro
    from gopro_overlay.framemeta_gpx import timeseries_to_framemeta
    from gopro_overlay.geo import MapRenderer, MapStyler
    from gopro_overlay.gpmd_filters import standard as gps_filter_standard
    from gopro_overlay.layout import Overlay
    from gopro_overlay.layout_xml import Converters, layout_from_xml
    from gopro_overlay.loading import GoproLoader, load_external
    from gopro_overlay.privacy import NoPrivacyZone
    from gopro_overlay.timeunits import timeunits
    from gopro_overlay.units import units

    suffix = file_path.suffix.lower()

    converters = Converters(
        speed_unit=units_speed,
        distance_unit=units_distance,
        altitude_unit=units_altitude,
        temperature_unit=units_temperature,
    )

    # Try to extract video frame as background (for MP4 files)
    background = None
    if suffix in (".mp4", ".mov"):
        try:
            from telemetry_studio.services.metadata import get_display_dimensions, get_video_rotation

            ffmpeg = FFMPEG()
            ffmpeg_gopro = FFMPEGGoPro(ffmpeg)
            recording = ffmpeg_gopro.find_recording(file_path)
            rotation = get_video_rotation(file_path)
            video_width, video_height = get_display_dimensions(
                recording.video.dimension.x, recording.video.dimension.y, rotation
            )

            background = _extract_video_frame(file_path, frame_time_ms, video_width, video_height)
            if background and background.size != (width, height):
                background = background.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Failed to extract video frame for editor preview: {e}")

    # Create base image - use video frame or black background
    image = background.convert("RGBA") if background else Image.new("RGBA", (width, height), (0, 0, 0, 255))

    # Set up map renderer
    cache_dir = Path(tempfile.gettempdir()) / "telemetry_studio_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    styler = MapStyler()
    style = map_style or "osm"

    with MapRenderer(cache_dir, styler).open(style) as renderer:
        font = _load_font_with_fallback()
        privacy = NoPrivacyZone()

        if suffix in (".mp4", ".mov"):
            ffmpeg = FFMPEG()
            ffmpeg_gopro = FFMPEGGoPro(ffmpeg)

            # Create GPS filter with configured thresholds
            gps_filter = gps_filter_standard(
                dop_max=gps_dop_max,
                speed_max=units.Quantity(gps_speed_max, units.kph),
            )

            loader = GoproLoader(ffmpeg_gopro, units, gps_lock_filter=gps_filter)
            try:
                gopro = loader.load(file_path)
                framemeta = gopro.framemeta
            except (OSError, TypeError, ValueError) as e:
                if gpx_path:
                    timeseries = load_external(gpx_path, units)
                    framemeta = timeseries_to_framemeta(timeseries, units)
                else:
                    raise ValueError(f"Could not load GPS data from video: {e}. Try adding a GPX/FIT file.") from e
        else:
            timeseries = load_external(file_path, units)
            framemeta = timeseries_to_framemeta(timeseries, units)

        create_widgets = layout_from_xml(
            xml_content,
            renderer=renderer,
            framemeta=framemeta,
            font=font,
            privacy=privacy,
            converters=converters,
        )

        overlay = Overlay(framemeta, create_widgets)
        pts = timeunits(millis=frame_time_ms)
        image = overlay.draw(pts, image)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue(), width, height


def _render_layout_placeholder(xml_content: str, width: int, height: int) -> bytes:
    """Render a placeholder preview showing widget positions."""
    from PIL import ImageDraw

    # Create dark background
    image = Image.new("RGBA", (width, height), (26, 26, 46, 255))
    draw = ImageDraw.Draw(image)

    # Draw grid
    grid_color = (50, 50, 80, 100)
    grid_size = 50
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # Draw center guides
    guide_color = (100, 100, 150, 100)
    draw.line([(width // 2, 0), (width // 2, height)], fill=guide_color, width=1)
    draw.line([(0, height // 2), (width, height // 2)], fill=guide_color, width=1)

    # Add text overlay
    try:
        font = _load_font_with_fallback()
        text = "Upload a file to see actual preview"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), text, fill=(150, 150, 150, 200), font=font)
    except Exception:
        pass

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_cli_command(
    session_id: str,
    output_file: str | None,
    layout: str,
    layout_xml_path: str | None = None,
    units_speed: str = DEFAULT_UNITS_SPEED,
    units_altitude: str = DEFAULT_UNITS_ALTITUDE,
    units_distance: str = DEFAULT_UNITS_DISTANCE,
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE,
    map_style: str | None = None,
    gpx_merge_mode: str = "OVERWRITE",
    video_time_alignment: str | None = None,
    ffmpeg_profile: str | None = None,
    gps_dop_max: float = DEFAULT_GPS_DOP_MAX,
    gps_speed_max: float = DEFAULT_GPS_SPEED_MAX,
) -> str:
    """Generate the CLI command for full video processing.

    Supports three modes:
    1. Video only (GoPro with embedded GPS)
    2. Video + GPX/FIT merge
    3. GPX/FIT only (overlay-only mode)

    Note: All paths and values are properly shell-escaped to prevent command injection.
    """
    import logging
    import os

    from telemetry_studio.services.file_manager import file_manager

    logger = logging.getLogger(__name__)

    files = file_manager.get_files(session_id)
    primary = file_manager.get_primary_file(session_id)
    secondary = file_manager.get_secondary_file(session_id)

    logger.info(f"generate_cli_command: session_id={session_id}")
    logger.info(f"generate_cli_command: files={files}")
    logger.info(f"generate_cli_command: primary={primary}")

    if not primary:
        raise ValueError(f"No primary file in session {session_id}. Available files: {files}")

    primary_path = primary.file_path
    primary_type = primary.file_type

    # Auto-generate output filename if not specified
    if not output_file:
        primary_dir = os.path.dirname(primary_path)
        primary_name = os.path.splitext(os.path.basename(primary_path))[0]
        output_file = os.path.join(primary_dir, f"{primary_name}_overlay.mp4")

    # Determine mode and build command
    if secondary and primary_type == "video":
        # Mode 2: Video + GPX/FIT merge
        cmd_parts = [
            "gopro-dashboard.py",
            shlex.quote(primary_path),
            shlex.quote(output_file),
            f"--gpx {shlex.quote(secondary.file_path)}",
            f"--gpx-merge {shlex.quote(gpx_merge_mode)}",
        ]
        if video_time_alignment:
            cmd_parts.append(f"--video-time-start {shlex.quote(video_time_alignment)}")
    elif primary_type in ("gpx", "fit"):
        # Mode 3: GPX/FIT only (overlay-only mode)
        # Get overlay size from layout
        layout_info = None
        for info in get_available_layouts():
            if info.name == layout:
                layout_info = info
                break
        if layout_info is None:
            layout_info = get_available_layouts()[0]

        cmd_parts = [
            "gopro-dashboard.py",
            shlex.quote(output_file),
            "--use-gpx-only",
            f"--gpx {shlex.quote(primary_path)}",
            f"--overlay-size {layout_info.width}x{layout_info.height}",
        ]
        if video_time_alignment:
            cmd_parts.append(f"--video-time-start {shlex.quote(video_time_alignment)}")
    else:
        # Mode 1: Video only (default - GoPro with embedded GPS)
        cmd_parts = [
            "gopro-dashboard.py",
            shlex.quote(primary_path),
            shlex.quote(output_file),
        ]
        if video_time_alignment:
            cmd_parts.append(f"--video-time-start {shlex.quote(video_time_alignment)}")

    # Handle layout - either custom XML or predefined
    if layout_xml_path:
        # Custom template: use --layout xml --layout-xml <path>
        cmd_parts.append("--layout xml")
        cmd_parts.append(f"--layout-xml {shlex.quote(layout_xml_path)}")
    else:
        # Map UI template names to CLI layout names
        # UI uses names like "default-1920x1080" but CLI only accepts "default", "speed-awareness", "xml"
        cli_layout = layout
        if layout.startswith("default-"):
            cli_layout = "default"
        elif layout.startswith("speed-awareness"):
            cli_layout = "speed-awareness"
        # Predefined layout: use --layout <name>
        cmd_parts.append(f"--layout {shlex.quote(cli_layout)}")

    # Always add unit options (CLI defaults differ from UI defaults)
    cmd_parts.append(f"--units-speed {shlex.quote(units_speed)}")
    cmd_parts.append(f"--units-altitude {shlex.quote(units_altitude)}")
    cmd_parts.append(f"--units-distance {shlex.quote(units_distance)}")
    cmd_parts.append(f"--units-temperature {shlex.quote(units_temperature)}")

    # Always add map style if specified
    if map_style:
        cmd_parts.append(f"--map-style {shlex.quote(map_style)}")

    # Add font option (auto-detect if Roboto-Medium.ttf is not available)
    font_path = _find_available_font()
    if font_path and font_path != "Roboto-Medium.ttf":
        cmd_parts.append(f"--font {shlex.quote(font_path)}")

    # Add FFmpeg profile if specified
    if ffmpeg_profile:
        cmd_parts.append(f"--profile {shlex.quote(ffmpeg_profile)}")

    # Add GPS filter parameters
    if gps_dop_max is not None:
        cmd_parts.append(f"--gps-dop-max {gps_dop_max}")
    if gps_speed_max is not None:
        cmd_parts.append(f"--gps-speed-max {gps_speed_max}")

    return " ".join(cmd_parts)
