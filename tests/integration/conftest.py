"""Integration test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def integration_test_video():
    """Real GoPro test video for integration tests (module-scoped for efficiency)."""
    from tests.fixtures.data import TEST_VIDEO_PATH

    path = Path(TEST_VIDEO_PATH)
    if not path.exists():
        pytest.skip(f"Integration test video not found: {path}")
    return path


@pytest.fixture(scope="module")
def integration_test_mov_video():
    """MOV video without GPS for integration tests (module-scoped for efficiency)."""
    from tests.fixtures.data import TEST_MOV_VIDEO_PATH

    path = Path(TEST_MOV_VIDEO_PATH)
    if not path.exists():
        pytest.skip(f"Integration test MOV video not found: {path}")
    return path


@pytest.fixture(scope="module")
def integration_test_run_gpx():
    """Real GPX file with run activity data (module-scoped for efficiency)."""
    from tests.fixtures.data import TEST_RUN_GPX_PATH

    path = Path(TEST_RUN_GPX_PATH)
    if not path.exists():
        pytest.skip(f"Integration test GPX not found: {path}")
    return path
