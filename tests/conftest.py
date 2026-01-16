import asyncio
import os
import tempfile
from pathlib import Path
from typing import Generator, Any
from unittest.mock import Mock, AsyncMock

import pytest

from mqttbot.core.scheduler import Scheduler

"""
Pytest configuration and shared fixtures.
"""


# Fixture to set XDG_STATE_HOME to a temp directory
@pytest.fixture
def xdg_state_home(tmp_path: Path, monkeypatch):
    """
    Sets the XDG_STATE_HOME environment variable to a
    temporary directory provided by tmp_path.
    """

    # 1. Convert the pathlib.Path object to a string for os.environ
    temp_dir = str(tmp_path / "xdg_state")

    # 2. Use monkeypatch to set the environment variable
    #    This ensures it is automatically restored/unset after the test completes.
    monkeypatch.setenv("XDG_STATE_HOME", temp_dir)

    # 3. Optional: Print for debugging (you can remove this)
    print(f"\n[Test Setup] Setting XDG_STATE_HOME to: {os.environ.get('XDG_STATE_HOME')}")

    # 4. Return the path, in case the test needs to access the directory directly
    return Path(temp_dir)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_data_dir() -> Path:
    """Path to the sample data directory for tests."""
    return Path(__file__).parent / "fixtures" / "sample_data"


@pytest.fixture
def event_loop():
    """Provide an event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_ctx():
    """Mock context for tasks"""
    return {
        "message_sender": Mock(),
        "blackboard": Mock(),
        "baritone_service": AsyncMock(),
    }


@pytest.fixture
def scheduler():
    """Create a fresh scheduler for each test"""
    return Scheduler()


@pytest.fixture
def sample_patterns() -> dict[str, Any]:
    """Sample pattern definitions for testing"""
    return {
        "patterns": {
            "row_01": {
                "steps": [
                    "~ ~ ~-5",
                    "~ ~ ~-10",
                    {"type": "dwell", "params": {"period": "1s"}},
                    "~ ~ ~5",
                ]},
            "row_02": {
                "steps": [
                    "~5 ~ ~",
                    "~10 ~ ~",
                    "~-15 ~ ~",
                ]},
            "simple": {
                "steps": [
                    "~ ~ ~10",
                ]},
        }
    }


@pytest.fixture
def sample_waypoints():
    """Sample waypoint definitions for testing"""
    return [
        {
            "x": 100,
            "y": 64,
            "z": 100,
            "patterns": ["row_01", "row_02"],
        },
        {
            "x": 150,
            "y": 64,
            "z": 100,
            "patterns": ["simple"],
        },
    ]
