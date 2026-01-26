"""Pydantic request/response models for Telemetry Studio API."""

from enum import Enum

from pydantic import BaseModel, Field

from telemetry_studio.constants import (
    DEFAULT_UNITS_ALTITUDE,
    DEFAULT_UNITS_DISTANCE,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TEMPERATURE,
)


class FileRole(str, Enum):
    """Role of a file in the session."""

    PRIMARY = "primary"  # Main video or GPX/FIT for overlay-only mode
    SECONDARY = "secondary"  # GPX/FIT to merge with video


class VideoMetadata(BaseModel):
    """Metadata extracted from a video file."""

    width: int
    height: int
    duration_seconds: float
    frame_count: int
    frame_rate: float
    has_gps: bool


class GpxFitMetadata(BaseModel):
    """Metadata extracted from a GPX or FIT file."""

    gps_point_count: int
    duration_seconds: float | None = None


class FileInfo(BaseModel):
    """Information about a file in the session."""

    filename: str
    file_path: str
    file_type: str  # "video", "gpx", "fit"
    role: FileRole
    video_metadata: VideoMetadata | None = None
    gpx_fit_metadata: GpxFitMetadata | None = None


class GpxFitOptions(BaseModel):
    """Options for GPX/FIT processing."""

    merge_mode: str = "OVERWRITE"  # "EXTEND" or "OVERWRITE"
    video_time_alignment: str | None = None  # "file-created", "file-modified", "file-accessed"


class UploadResponse(BaseModel):
    """Response from file upload endpoint."""

    session_id: str
    files: list[FileInfo]  # All files in session with roles


class LayoutInfo(BaseModel):
    """Information about an available layout."""

    name: str
    display_name: str
    width: int
    height: int


class LayoutsResponse(BaseModel):
    """Response from layouts endpoint."""

    layouts: list[LayoutInfo]


class UnitOption(BaseModel):
    """A single unit option."""

    value: str
    label: str


class UnitCategory(BaseModel):
    """A category of units with available options."""

    name: str
    label: str
    options: list[UnitOption]
    default: str


class UnitOptionsResponse(BaseModel):
    """Response from unit options endpoint."""

    categories: list[UnitCategory]


class MapStyleOption(BaseModel):
    """A single map style option."""

    name: str
    display_name: str
    requires_api_key: bool = False


class MapStylesResponse(BaseModel):
    """Response from map styles endpoint."""

    styles: list[MapStyleOption]


class FFmpegProfileOption(BaseModel):
    """A single FFmpeg profile option."""

    name: str
    display_name: str
    description: str
    is_builtin: bool = True


class FFmpegProfilesResponse(BaseModel):
    """Response from FFmpeg profiles endpoint."""

    profiles: list[FFmpegProfileOption]


class PreviewRequest(BaseModel):
    """Request for generating a preview image."""

    session_id: str
    layout: str = "default-1920x1080"
    frame_time_ms: int = Field(default=0, ge=0)
    units_speed: str = DEFAULT_UNITS_SPEED
    units_altitude: str = DEFAULT_UNITS_ALTITUDE
    units_distance: str = DEFAULT_UNITS_DISTANCE
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE
    map_style: str | None = None


class PreviewResponse(BaseModel):
    """Response from preview generation endpoint."""

    image_base64: str
    width: int
    height: int
    frame_time_ms: int


class CommandRequest(BaseModel):
    """Request for generating a CLI command."""

    session_id: str
    layout: str = "default-1920x1080"
    layout_xml_path: str | None = None  # Path to custom template XML
    output_filename: str | None = None  # Auto-generated from input if not specified
    units_speed: str = DEFAULT_UNITS_SPEED
    units_altitude: str = DEFAULT_UNITS_ALTITUDE
    units_distance: str = DEFAULT_UNITS_DISTANCE
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE
    map_style: str | None = None
    gpx_fit_options: GpxFitOptions | None = None  # GPX/FIT merge options
    ffmpeg_profile: str | None = None  # FFmpeg encoding profile


class CommandResponse(BaseModel):
    """Response from command generation endpoint."""

    command: str
    input_file: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None


class LocalFileRequest(BaseModel):
    """Request for using a local file path."""

    file_path: str


class SecondaryFileRequest(BaseModel):
    """Request for adding a secondary GPX/FIT file."""

    session_id: str
    file_path: str  # For local mode


class ConfigResponse(BaseModel):
    """Response with app configuration."""

    local_mode: bool
    max_upload_size_bytes: int
    allowed_extensions: list[str]


# Template management models
class TemplateInfo(BaseModel):
    """Information about a saved template."""

    name: str
    file_path: str
    created_at: str | None = None
    modified_at: str | None = None
    canvas_width: int = 1920
    canvas_height: int = 1080
    description: str | None = None


class SaveTemplateRequest(BaseModel):
    """Request to save a custom template."""

    name: str
    layout: dict  # EditorLayout as dict from frontend
    description: str | None = None


class SaveTemplateResponse(BaseModel):
    """Response from saving template."""

    name: str
    file_path: str
    success: bool = True


class TemplateListResponse(BaseModel):
    """Response with list of templates."""

    templates: list[TemplateInfo]


class RenameTemplateRequest(BaseModel):
    """Request to rename a template."""

    new_name: str
