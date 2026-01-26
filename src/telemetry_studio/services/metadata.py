"""Metadata extraction service using gopro_overlay."""

import logging
from pathlib import Path

from telemetry_studio.config import settings
from telemetry_studio.models.schemas import GpxFitMetadata, VideoMetadata

# Apply runtime patches if enabled
if settings.enable_gopro_patches:
    from telemetry_studio.patches import apply_patches

    apply_patches()

logger = logging.getLogger(__name__)


def extract_video_metadata(file_path: Path) -> VideoMetadata | None:
    """Extract metadata from a video file using FFMPEGGoPro."""
    from gopro_overlay.ffmpeg import FFMPEG
    from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro

    try:
        ffmpeg = FFMPEG()
        ffmpeg_gopro = FFMPEGGoPro(ffmpeg)
        recording = ffmpeg_gopro.find_recording(file_path)

        video = recording.video
        has_gps = recording.data is not None

        return VideoMetadata(
            width=video.dimension.x,
            height=video.dimension.y,
            duration_seconds=video.duration.millis() / 1000.0,
            frame_count=video.frame_count,
            frame_rate=video.frame_rate(),
            has_gps=has_gps,
        )
    except Exception as e:
        import traceback

        print(f"ERROR extracting video metadata: {e}")
        traceback.print_exc()
        return None


def extract_gpx_fit_metadata(file_path: Path) -> GpxFitMetadata | None:
    """Extract metadata from a GPX or FIT file."""
    from gopro_overlay.loading import load_external
    from gopro_overlay.units import units

    try:
        timeseries = load_external(file_path, units)

        # Count GPS points
        point_count = len(timeseries)

        # Calculate duration if we have timestamps
        duration = None
        if point_count > 0:
            start_time = timeseries.min
            end_time = timeseries.max
            duration = (end_time - start_time).total_seconds()

        return GpxFitMetadata(
            gps_point_count=point_count,
            duration_seconds=duration,
        )
    except Exception as e:
        import traceback

        print(f"ERROR extracting GPX/FIT metadata: {e}")
        traceback.print_exc()
        return None


def get_file_type(file_path: Path) -> str:
    """Determine the file type from extension."""
    suffix = file_path.suffix.lower()
    return {".mp4": "video", ".gpx": "gpx", ".fit": "fit"}.get(suffix, "unknown")
