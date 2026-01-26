#!/usr/bin/env python3
"""Wrapper for gopro-dashboard.py that applies telemetry-studio runtime patches.

This script serves as a drop-in replacement for gopro-dashboard.py,
applying patches for:
- Timecode extraction and preservation (Final Cut Pro compatibility)
- Enhanced FFmpeg options (audio copy, metadata preservation)

Usage:
    python gopro_dashboard_wrapper.py [gopro-dashboard.py arguments...]

The wrapper:
1. Applies runtime patches to gopro_overlay library
2. Locates and executes the original gopro-dashboard.py script
3. Passes through all command-line arguments
"""

import logging
import runpy
import shutil
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_gopro_dashboard() -> Path | None:
    """Locate the original gopro-dashboard.py script.

    Searches in:
    1. bin/ directory relative to project root (development)
    2. System PATH (installed via pip)

    Returns:
        Path to gopro-dashboard.py or None if not found
    """
    # Check bin/ directory relative to telemetry-studio project root
    # This script is at: src/telemetry_studio/scripts/gopro_dashboard_wrapper.py
    # Project root is 4 levels up
    current_file = Path(__file__)
    project_root = current_file.parents[3]
    bin_script = project_root / "bin" / "gopro-dashboard.py"
    if bin_script.exists():
        return bin_script

    # Check PATH
    path_script = shutil.which("gopro-dashboard.py")
    if path_script:
        return Path(path_script)

    return None


def main():
    """Main entry point for the gopro-dashboard wrapper."""
    # Apply patches BEFORE importing anything from gopro_overlay
    # This ensures all classes are patched when gopro-dashboard.py loads them
    from telemetry_studio.patches import apply_patches

    apply_patches()
    logger.info("Patches applied successfully")

    # Find the original gopro-dashboard.py
    dashboard_script = find_gopro_dashboard()

    if not dashboard_script:
        logger.error("gopro-dashboard.py not found. Ensure gopro-overlay is installed: uv add gopro-overlay")
        sys.exit(1)

    logger.info(f"Executing: {dashboard_script}")

    # Execute gopro-dashboard.py using runpy
    # This runs the script in the current interpreter with patches applied
    # sys.argv[0] will be the wrapper, but the script receives all args
    sys.argv[0] = str(dashboard_script)

    try:
        # Run the script as __main__
        runpy.run_path(str(dashboard_script), run_name="__main__")
    except SystemExit as e:
        # Propagate exit codes from gopro-dashboard.py
        sys.exit(e.code)
    except Exception as e:
        logger.exception(f"Failed to execute gopro-dashboard.py: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
