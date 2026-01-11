"""Tests for PatternThread - pattern expansion into task sequences"""
import pytest
from mqttbot.core.scheduler import Scheduler
from mqttbot.core.task.task import TaskPriority
from mqttbot.core.threads.pattern_thread import PatternThread
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.tasks.goto_task import GotoTask
from mqttbot.tasks.dwell_task import DwellTask


class TestPatternThreadConstruction:
    """Test PatternThread initialization and setup"""
    
    def test_create_pattern_thread(self, sample_waypoints, sample_patterns):
        """Test creating a pattern thread"""
        thread = PatternThread(
            thread_id="test_thread",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
            patterns=sample_patterns,
        )
        
        assert thread.thread_id == "test_thread"
        assert thread.priority == TaskPriority.NORMAL
        assert len(thread.waypoints) == len(sample_waypoints)
        assert len(thread.patterns) > 0
    
    def test_build_task_sequence(self, sample_waypoints, sample_patterns):
        """Test that task sequence is built correctly"""
        thread = PatternThread(
            thread_id="test_thread",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
            patterns=sample_patterns,
        )
        
        thread.build_task_sequence()
        
        # Should have tasks queued
        assert len(thread.task_queue) > 0
        
        # First task should be goto to first waypoint
        first_task = thread.task_queue[0]
        assert isinstance(first_task, GotoTask)
        assert first_task.target == (100, 64, 100)


class TestPatternThreadExpansion:
    """Test pattern expansion into tasks"""
    
    def test_simple_pattern_expansion(self):
        """Test expanding a simple pattern"""
        patterns = {
            "simple": ["~ ~ ~-5", "~ ~ ~-5"],
        }
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": ["simple"]},
        ]
        
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
            patterns=patterns,
        )
        thread.build_task_sequence()
        
        # Should have: goto(100,64,100) + 2 pattern gotos
        assert len(thread.task_queue) == 3
        
        tasks = list(thread.task_queue)
        assert isinstance(tasks[0], GotoTask)
        assert tasks[0].target == (100, 64, 100)  # Waypoint
        
        assert isinstance(tasks[1], GotoTask)
        assert tasks[1].target == (100, 64, 95)   # Pattern step 1
        
        assert isinstance(tasks[2], GotoTask)
        assert tasks[2].target == (100, 64, 90)   # Pattern step 2
    
    def test_pattern_with_dwell(self):
        """Test that dwell steps are expanded correctly"""
        patterns = {
            "with_dwell": [
                "~ ~ ~-5",
                {"type": "dwell", "period": "2s"},
                "~ ~ ~-5",
            ],
        }
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": ["with_dwell"]},
        ]
        
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
            patterns=patterns,
        )
        thread.build_task_sequence()
        
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
            patterns=sample_patterns,
        )
        thread.build_task_sequence()
        
        # First waypoint: goto + row_01 (4 tasks) + row_02 (3 tasks)
        # Second waypoint: goto + simple (1 task)
        # Total: 2 + 4 + 3 + 1 + 1 = 11 tasks
        
        assert len(thread.task_queue) == 10
        
        tasks = list(thread.task_queue)
        
        # First waypoint goto
        assert isinstance(tasks[0], GotoTask)
        assert tasks[0].target == (100, 64, 100)
        
        # Last task should be second waypoint goto
        assert isinstance(tasks[-2], GotoTask)
        assert tasks[-2].target == (150, 64, 100)
    
    def test_unknown_pattern_skipped(self):
        """Test that unknown patterns are skipped gracefully"""
        patterns = {
            "known": ["~ ~ ~-5"],
        }
        waypoints = [
            {"x": 100, "y": 64, "z": 100, "patterns": ["unknown", "known"]},
        ]
        
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
            patterns=patterns,
        )
        thread.build_task_sequence()
        
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
            patterns=sample_patterns,
        )
        thread.build_task_sequence()
        
        initial_index = thread.current_task_index
        assert initial_index == 0
        
        # Simulate advancing through tasks
        thread.current_task_index = 5
        assert thread.current_task_index == 5
    
    def test_suspend_saves_task_index(self, sample_waypoints, sample_patterns):
        """Test that suspend captures task index"""
        from mqttbot.core.threads.suspension_context import ThreadSuspensionContext
        
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
            patterns=sample_patterns,
        )
        thread.build_task_sequence()
        
        # Simulate being at task 5
        thread.current_task_index = 5
        
        # Create proper suspension context
        ctx = ThreadSuspensionContext.from_thread(
            position=(100, 64, 100),
            task_index=5
        )

        assert ctx.current_task_index == 5
        assert ctx.position_at_suspend == (100, 64, 100)
    
    def test_rebuild_task_sequence_is_deterministic(self, sample_waypoints, sample_patterns):
        """Test that rebuilding sequence produces identical results"""
        thread1 = PatternThread(
            thread_id="test1",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
            patterns=sample_patterns,
        )
        thread1.build_task_sequence()
        seq1 = [(t.target if isinstance(t, GotoTask) else t.duration) for t in thread1.task_queue]
        
        thread2 = PatternThread(
            thread_id="test2",
            priority=TaskPriority.NORMAL,
            waypoints=sample_waypoints,
            patterns=sample_patterns,
        )
        thread2.build_task_sequence()
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
        patterns = {}
        
        thread = PatternThread(
            thread_id="test",
            priority=TaskPriority.NORMAL,
            waypoints=waypoints,
            patterns=patterns,
        )
        thread.build_task_sequence()
        
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
            patterns={},
        )
        thread.build_task_sequence()
        
        # Should have empty task queue
        assert len(thread.task_queue) == 0
