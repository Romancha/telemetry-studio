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
