from conftest import rprint, pprint, inspect  # noqa: F401

from mqttbot.core.patterns.pattern_thread import PatternThread, PatternThreadHelper
from mqttbot.core.tasks.task_priority import TaskPriority

"""Tests for correct callback task generation

These tests generated various callback configurations that produce
the expect task sequences when the thread is started, suspended,
resumed, cancelled, or failed.
"""


class TestCallbackThreadConstruction:
    """Test PatternThread initialization and setup"""

    def test_create_pattern_thread(self, sample_waypoints, sample_patterns):
        thread = PatternThread(
            thread_id="test_thread",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )
        assert len(thread.task_queue) == 0

        PatternThreadHelper.build_task_sequence(thread, sample_patterns)
        inspect(thread)
