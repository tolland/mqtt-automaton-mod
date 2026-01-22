from mqttbot.core.patterns.pattern_thread import PatternThread, PatternThreadHelper
from mqttbot.core.patterns.patterns_config_parser import PatternsConfigParser
from mqttbot.core.tasks.dwell_task import DwellTask
from mqttbot.core.tasks.goto_task import GotoTask
from mqttbot.core.tasks.task_priority import TaskPriority

"""Tests for PatternThread - pattern expansion into task sequences

These tests were updated to provide pattern inputs in the new canonical
shape expected by the parser: a top-level mapping with a `patterns` key,
where each pattern is an object containing a `steps` list.
"""


class TestPatternThreadConstruction:
    """Test PatternThread initialization and setup"""

    def test_create_pattern_thread(self, sample_waypoints, sample_patterns):
        """Test creating a pattern thread"""
        thread = PatternThread(
            thread_id="test_thread",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )

        assert thread.thread_id == "test_thread"
        assert thread.priority == TaskPriority.NORMAL
        assert len(thread.waypoints) == len(sample_waypoints)

    def test_build_task_sequence(self, sample_waypoints, sample_patterns):
        """Test that task sequence is built correctly"""
        thread = PatternThread(
            thread_id="test_thread",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )

        PatternThreadHelper.build_task_sequence(thread,sample_patterns)

        # Should have tasks queued
        assert len(thread.task_queue) > 0

        # First task should be goto to first waypoint
        first_task = thread.task_queue[0]
        assert isinstance(first_task, GotoTask)
        assert first_task.target == (100, 64, 100)


class TestPatternThreadExpansion:
    """Test pattern expansion into tasks"""

    def test_simple_pattern_expansion(self):
        """Test expanding a simple pattern (provide new shape expected by parser)"""
        patterns = PatternsConfigParser.from_yaml({
            "patterns": {
                "simple": {"steps": ["~ ~ ~-5", "~ ~ ~-5"]}
            }
        })
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": ["simple"]},
        ]

        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread, patterns)

        # Should have: goto(100,64,100) + 2 pattern gotos
        assert len(thread.task_queue) == 3

        tasks = list(thread.task_queue)
        assert isinstance(tasks[0], GotoTask)
        assert tasks[0].target == (100, 64, 100)  # Waypoint

        assert isinstance(tasks[1], GotoTask)
        assert tasks[1].target == (100, 64, 95)  # Pattern step 1

        assert isinstance(tasks[2], GotoTask)
        assert tasks[2].target == (100, 64, 90)  # Pattern step 2

    def test_pattern_with_dwell(self):
        """Test that dwell steps are expanded correctly"""
        patterns = PatternsConfigParser.from_yaml({
            "patterns": {
                "with_dwell": {
                    "steps": [
                        "~ ~ ~-5",
                        {"type": "dwell", "period": "2s"},
                        "~ ~ ~-5",
                    ]
                }
            }
        })
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": ["with_dwell"]},
        ]

        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread, patterns)

        # Should have: goto(waypoint) + goto(pattern) + dwell + goto(pattern)
        assert len(thread.task_queue) == 4

        tasks = list(thread.task_queue)
        assert isinstance(tasks[0], GotoTask)
        assert isinstance(tasks[1], GotoTask)
        assert isinstance(tasks[2], DwellTask)
        assert isinstance(tasks[3], GotoTask)
        assert tasks[2].duration == 2.0

    def test_multiple_waypoints(self, sample_waypoints, sample_patterns):
        """Test that multiple waypoints are handled correctly"""
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread, sample_patterns)

        # Ensure tasks were generated for both waypoints
        assert len(thread.task_queue) > 1

        tasks = list(thread.task_queue)

        # First waypoint goto
        assert isinstance(tasks[0], GotoTask)
        assert tasks[0].target == (100, 64, 100)

        # Last task before final waypoint should be a goto to that waypoint
        assert isinstance(tasks[-2], GotoTask)
        assert tasks[-2].target == (150, 64, 100)

    def test_unknown_pattern_skipped(self):
        """Test that unknown patterns are skipped gracefully"""
        patterns = PatternsConfigParser.from_yaml({
            "patterns": {"known": {"steps": ["~ ~ ~-5"]}}
        })
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": ["unknown", "known"]},
        ]

        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread, patterns)

        # Should still build: goto(waypoint) + goto(known pattern)
        assert len(thread.task_queue) == 2


class TestPatternThreadSuspensionResumption:
    """Test suspension and resumption mechanics"""

    def test_thread_tracks_task_index(self, sample_waypoints, sample_patterns):
        """Test that thread tracks current task index"""
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread, sample_patterns)

        initial_index = thread.current_task_index
        assert initial_index == 0

        # Simulate advancing through tasks
        thread.current_task_index = 5
        assert thread.current_task_index == 5

    def test_rebuild_task_sequence_is_deterministic(self, sample_waypoints, sample_patterns):
        """Test that rebuilding sequence produces identical results"""
        thread1 = PatternThread(
            thread_id="test1",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread1, sample_patterns)
        seq1 = [(t.target if isinstance(t, GotoTask) else t.duration) for t in thread1.task_queue]

        thread2 = PatternThread(
            thread_id="test2",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread2, sample_patterns)
        seq2 = [(t.target if isinstance(t, GotoTask) else t.duration) for t in thread2.task_queue]

        # Sequences should be identical
        assert seq1 == seq2
        assert len(seq1) == len(seq2)


class TestPatternThreadNoPatterns:
    """Test edge cases with no patterns"""

    def test_waypoint_with_no_patterns(self):
        """Test waypoint that has no patterns"""
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": []},
        ]
        patterns = PatternsConfigParser.from_yaml({})

        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
        )
        PatternThreadHelper.build_task_sequence(thread,patterns)

        # Should just have the goto waypoint task
        assert len(thread.task_queue) == 1
        assert isinstance(thread.task_queue[0], GotoTask)
        assert thread.task_queue[0].target == (100, 64, 100)

    def test_empty_waypoints(self):
        """Test with no waypoints"""
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=[],
        )
        PatternThreadHelper.build_task_sequence(thread, PatternsConfigParser.from_yaml({}))

        # Should have empty task queue
        assert len(thread.task_queue) == 0
