import asyncio
import builtins
import os
import subprocess
import tempfile
import sys
import time
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, AsyncMock

import pytest
from pydantic import TypeAdapter
from rich import inspect
from rich import print as rprint
from rich.pretty import pprint

from mqttbot.config.model.full_config import FullConfig
from mqttbot.config.model.step.service_step import ServiceStep
from mqttbot.core.events.event_manager import EventManager
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.tasks.task_compiler import TaskCompiler
from mqttbot.core.threads import scheduler
from mqttbot.core.threads.dynamic_handler import DynamicHandler
from mqttbot.core.threads.thread import TaskThread
from .mocks.message_service_mock import (
    MockMessageService,
    make_success_service,
    make_failure_service,
    make_delayed_service,
)
import yaml

builtins.rprint = rprint
builtins.pprint = pprint
builtins.inspect = inspect

"""Test configuration and fixtures."""

# Ensure the tests package directory is on sys.path so imports like `from mocks...` work
sys.path.insert(0, str(Path(__file__).parent))

__all__ = ["rprint", "pprint", "inspect"]

"""
Pytest configuration and shared fixtures.
"""


def pytest_addoption(parser):
    parser.addoption(
        "--requires-server", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_server: mark test as requiring docker server")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--requires-server"):
        return
    skip_slow = pytest.mark.skip(reason="need --requires-server option to run")
    for item in items:
        if "requires_server" in item.keywords:
            item.add_marker(skip_slow)


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
def mock_scheduler():
    """Create a fresh scheduler for each test"""
    return scheduler.create()


@pytest.fixture
def sample_steps():
    # container = HookDefinition.model_validate({"Step": data})
    # if this should be a callback
    return TypeAdapter(list[ServiceStep]).validate_python(
        [
            {
                "type": "oneshot",
                "service": "commands",
                "method": "sendCommand",
                "params": {
                    "message": "bal"
                }
            }
        ])


@pytest.fixture
def sample_patterns():
    """Sample pattern definitions for testing"""
    return FullConfig.model_validate(
        {
            "pattern_config": {
                "patterns": [
                    {
                        "pattern_id": "row_01",
                        "steps": [
                            "~ ~ ~-5",
                            "~ ~ ~-10",
                            {"type": "dwell", "params": {"period": "1"}},
                            "~ ~ ~5",
                        ]},
                    {
                        "pattern_id": "row_02",
                        "steps": [
                            "~5 ~ ~",
                            "~10 ~ ~",
                            "~-15 ~ ~",
                        ]},
                    {
                        "pattern_id": "simple",
                        "steps": [
                            "~ ~ ~10",
                        ]},
                ]
            }
        })


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


@pytest.fixture(scope="session")
def minecraft_client():
    """Start minecraft client before tests, stop after."""
    project_root = Path(__file__).parent.parent

    process = subprocess.Popen(
        ["./gradlew", "runClient"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for client to start
    time.sleep(10)

    yield process

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

@pytest.fixture
def sample_config():
    config_path = Path(__file__).parent.parent / "configs" / "config.yml"
    with open(config_path, "r") as f:
        yaml_data = yaml.safe_load(f)
    return FullConfig.model_validate(yaml_data)

@pytest.fixture
def sample_event_thread(
    sample_config,
) -> "TaskThread":

    pydantic_patterns = sample_config.pattern_config
    thread_configs = sample_config.thread_config
    event_configs = sample_config.event_handlers

    event_manager = EventManager(event_configs)

    handler_config = event_manager.get_handler_config("inventory", "inventory_full")

    task_compiler = TaskCompiler(pydantic_patterns)
    event_thread = TaskThread(
        thread_id="event-thread-1",
        main_source_provider=DynamicHandler(handler_config.steps, task_compiler),
        on_suspend_provider=DynamicHandler([], task_compiler),
        on_resume_provider=DynamicHandler([], task_compiler),
        on_cancel_provider=DynamicHandler([], task_compiler),
        on_failed_provider=DynamicHandler([], task_compiler),
        priority=ThreadPriority.HIGH,
    )
    return event_thread

@pytest.fixture
def mock_message_service() -> MockMessageService:
    """A controllable mock MessageService for tests (delayed by default)."""
    return make_delayed_service()


@pytest.fixture
def mock_success_message_service() -> MockMessageService:
    """A controllable mock MessageService for tests (delayed by default)."""
    return make_success_service()


async def step_until(scheduler, ctx, predicate, timeout=100):
    """
    Step the scheduler until the predicate is True or timeout is reached.
    """
    counter = 0
    while not predicate(scheduler) and counter < timeout:
        await scheduler.step(ctx)
        counter += 1
    return predicate(scheduler)


@pytest.fixture
def step_until_helper():
    return step_until
