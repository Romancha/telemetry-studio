"""API test fixtures."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def api_test_video():
    """Real test video for API tests (skips if not available)."""
    from tests.fixtures.data import TEST_VIDEO_PATH

    path = Path(TEST_VIDEO_PATH)
    if not path.exists():
        pytest.skip(f"API test video not found: {path}")
    return path


@pytest.fixture
def mock_render_service():
    """Mock render_service for API tests that don't need real rendering."""
    mock = MagicMock()
    mock.start_render = AsyncMock(return_value=None)
    mock.cancel_render = AsyncMock(return_value=True)
    return mock
