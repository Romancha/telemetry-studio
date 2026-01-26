"""Runtime patches for gopro_overlay library.

This module provides runtime patches to extend gopro_overlay functionality
without modifying the original library. Changes include:
- Timecode extraction for Final Cut Pro compatibility
- Enhanced FFmpeg options (audio copy, metadata preservation)
"""

import logging

logger = logging.getLogger(__name__)

_patches_applied = False


def apply_patches() -> None:
    """Apply all runtime patches to gopro_overlay library.

    This function is idempotent and can be called multiple times safely.
    Patches are applied only once, subsequent calls are no-ops.
    """
    global _patches_applied

    if _patches_applied:
        logger.debug("Patches already applied, skipping")
        return

    from telemetry_studio.patches.ffmpeg_gopro_patches import patch_ffmpeg_gopro
    from telemetry_studio.patches.ffmpeg_overlay_patches import patch_ffmpeg_overlay

    patch_ffmpeg_gopro()
    patch_ffmpeg_overlay()

    _patches_applied = True
    logger.info("gopro_overlay runtime patches applied successfully")


def is_patched() -> bool:
    """Check if patches have been applied."""
    return _patches_applied


__all__ = ["apply_patches", "is_patched"]
