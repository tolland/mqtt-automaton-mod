"""Tests for Scheduler - thread preemption and management"""

from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.threads.thread_base import TaskThreadBase


class TestSchedulerRegistration:
    """Test thread registration and enqueueing"""

    def test_register_thread(self, mock_scheduler):
        """Test registering a thread at startup"""
        thread = TaskThreadBase("test_thread", ThreadPriority.NORMAL)
        mock_scheduler.register_thread(thread)

        # Thread should be in ready queue
        assert len(mock_scheduler.ready_threads) == 1

    def test_enqueue_thread(self, mock_scheduler):
        """Test enqueueing a thread (after startup)"""
        thread = TaskThreadBase("test_thread", ThreadPriority.NORMAL)
        result = mock_scheduler.enqueue_thread(thread)

        assert result is True
        assert len(mock_scheduler.ready_threads) == 1

    def test_enqueue_multiple_threads(self, mock_scheduler):
        """Test enqueueing multiple threads"""
        thread1 = TaskThreadBase("thread1", ThreadPriority.NORMAL)
        thread2 = TaskThreadBase("thread2", ThreadPriority.HIGH)

        mock_scheduler.enqueue_thread(thread1)
        mock_scheduler.enqueue_thread(thread2)

        assert len(mock_scheduler.ready_threads) == 2


class TestSchedulerSingleton:
    """Test singleton mode to prevent duplicate threads"""

    def test_singleton_prevents_duplicate(self, mock_scheduler):
        """Test that singleton=True prevents enqueueing duplicate thread"""
        thread1 = TaskThreadBase("evasion", ThreadPriority.CRITICAL)
        thread2 = TaskThreadBase("evasion", ThreadPriority.CRITICAL)

        result1 = mock_scheduler.enqueue_thread(thread1, singleton=True)
        result2 = mock_scheduler.enqueue_thread(thread2, singleton=True)

        assert result1 is True
        assert result2 is False  # Second one blocked
        assert len(mock_scheduler.ready_threads) == 1

    def test_singleton_allows_different_threads(self, mock_scheduler):
        """Test that singleton doesn't block different thread IDs"""
        thread1 = TaskThreadBase("evasion", ThreadPriority.CRITICAL)
        thread2 = TaskThreadBase("sleep", ThreadPriority.HIGH)

        result1 = mock_scheduler.enqueue_thread(thread1, singleton=True)
        result2 = mock_scheduler.enqueue_thread(thread2, singleton=True)

        assert result1 is True
        assert result2 is True
        assert len(mock_scheduler.ready_threads) == 2

    def test_singleton_detects_in_current_thread(self, mock_scheduler):
        """Test that singleton detects thread in current slot"""
        thread1 = TaskThreadBase("farming", ThreadPriority.NORMAL)
        mock_scheduler.current_thread = thread1

        thread2 = TaskThreadBase("farming", ThreadPriority.NORMAL)
        result = mock_scheduler.enqueue_thread(thread2, singleton=True)

        assert result is False


class TestSchedulerThreadIdTracking:
    """Test thread ID existence checking"""

    def test_thread_id_exists_in_ready_queue(self, mock_scheduler):
        """Test detecting thread ID in ready queue"""
        thread = TaskThreadBase("test_thread", ThreadPriority.NORMAL)
        mock_scheduler.ready_threads.append(thread)

        exists = mock_scheduler._thread_id_exists("test_thread")
        assert exists is True

    def test_thread_id_not_exists(self, mock_scheduler):
        """Test detecting non-existent thread ID"""
        exists = mock_scheduler._thread_id_exists("nonexistent")
        assert exists is False

    def test_has_active_thread_public_api(self, mock_scheduler):
        """Test public has_active_thread method"""
        thread = TaskThreadBase("farming", ThreadPriority.NORMAL)
        mock_scheduler.current_thread = thread

        assert mock_scheduler.has_active_thread("farming") is True
        assert mock_scheduler.has_active_thread("other") is False


class TestSchedulerPriority:
    """Test thread priority ordering"""

    def test_threads_ordered_by_priority(self, mock_scheduler):
        """Test that threads are ordered by priority in heap"""
        normal_thread = TaskThreadBase("normal", ThreadPriority.NORMAL)
        high_thread = TaskThreadBase("high", ThreadPriority.HIGH)
        critical_thread = TaskThreadBase("critical", ThreadPriority.CRITICAL)

        # Add in random order
        mock_scheduler.enqueue_thread(normal_thread)
        mock_scheduler.enqueue_thread(critical_thread)
        mock_scheduler.enqueue_thread(high_thread)

        # Highest priority should be first
        assert mock_scheduler.ready_threads[0].priority == ThreadPriority.CRITICAL

    def test_priority_comparison(self):
        """Test that priority comparison works"""
        normal = TaskThreadBase("normal", ThreadPriority.NORMAL)
        high = TaskThreadBase("high", ThreadPriority.HIGH)

        # High priority should be "less than" normal (for min-heap)
        assert high < normal


class TestSchedulerThreadStateTracking:
    """Test tracking thread state"""

    def test_clear_ready_threads(self, mock_scheduler):
        """Test clearing ready threads"""
        thread1 = TaskThreadBase("thread1", ThreadPriority.NORMAL)
        thread2 = TaskThreadBase("thread2", ThreadPriority.NORMAL)

        mock_scheduler.enqueue_thread(thread1)
        mock_scheduler.enqueue_thread(thread2)

        assert len(mock_scheduler.ready_threads) == 2

        # Clear (would normally be done at test cleanup)
        mock_scheduler.ready_threads.clear()
        assert len(mock_scheduler.ready_threads) == 0

    def test_done_queue_lifo(self, mock_scheduler):
        """Test that done_queue stack is LIFO"""
        thread1 = TaskThreadBase("thread1", ThreadPriority.NORMAL)
        thread2 = TaskThreadBase("thread2", ThreadPriority.NORMAL)

        mock_scheduler.done_threads.append(thread1)
        mock_scheduler.done_threads.append(thread2)

        # Should pop in reverse order
        popped = mock_scheduler.done_threads.pop()
        assert popped.thread_id == "thread2"


class TestSchedulerEdgeCases:
    """Test edge cases and error conditions"""

    def test_enqueue_thread_without_singleton(self, mock_scheduler):
        """Test that without singleton, duplicates are allowed"""
        thread1 = TaskThreadBase("farming", ThreadPriority.NORMAL)
        thread2 = TaskThreadBase("farming", ThreadPriority.NORMAL)

        result1 = mock_scheduler.enqueue_thread(thread1, singleton=False)
        result2 = mock_scheduler.enqueue_thread(thread2, singleton=False)

        assert result1 is True
        assert result2 is True
        assert len(mock_scheduler.ready_threads) == 2

    def test_singleton_default_is_false(self, mock_scheduler):
        """Test that singleton defaults to False"""
        thread1 = TaskThreadBase("test", ThreadPriority.NORMAL)
        thread2 = TaskThreadBase("test", ThreadPriority.NORMAL)

        result1 = mock_scheduler.enqueue_thread(thread1)  # No singleton param
        result2 = mock_scheduler.enqueue_thread(thread2)  # No singleton param

        assert result1 is True
        assert result2 is True  # Both allowed without singleton

    def test_empty_scheduler(self, mock_scheduler):
        """Test operations on empty scheduler"""
        assert len(mock_scheduler.ready_threads) == 0
        assert mock_scheduler.current_thread is None
        assert len(mock_scheduler.done_threads) == 0
        assert mock_scheduler._thread_id_exists("any") is False


class TestSchedulerUninterruptible:
    """Test uninterruptible thread behavior"""

    def test_normal_thread_can_be_preempted(self, mock_scheduler):
        """Test that normal threads can be preempted by higher priority"""
        # Start with a normal priority thread running
        normal_thread = TaskThreadBase("farming", ThreadPriority.NORMAL)
        mock_scheduler.current_thread = normal_thread

        # Enqueue a high priority thread
        high_thread = TaskThreadBase("combat", ThreadPriority.HIGH)
        mock_scheduler.enqueue_thread(high_thread)

        # Should preempt (HIGH < NORMAL in priority value)
        assert mock_scheduler._should_preempt() is True

    def test_uninterruptible_thread_cannot_be_preempted(self, mock_scheduler):
        """Test that uninterruptible threads CANNOT be preempted"""
        # Start with an uninterruptible cleanup thread running
        cleanup_thread = TaskThreadBase(
            "cleanup",
            ThreadPriority.NORMAL,
            uninterruptible=True
        )
        mock_scheduler.current_thread = cleanup_thread

        # Try to preempt with even higher priority
        critical_thread = TaskThreadBase("panic", ThreadPriority.CRITICAL)
        mock_scheduler.enqueue_thread(critical_thread)

        # Should NOT preempt - cleanup must finish
        assert mock_scheduler._should_preempt() is False

    def test_uninterruptible_flag_in_thread_repr(self):
        """Test that uninterruptible flag shows in thread repr"""
        thread = TaskThreadBase(
            "test",
            ThreadPriority.NORMAL,
            uninterruptible=True
        )

        assert thread.uninterruptible is True

    def test_uninterruptible_defaults_to_false(self):
        """Test that uninterruptible defaults to False"""
        thread = TaskThreadBase("test", ThreadPriority.NORMAL)

        assert thread.uninterruptible is False

    def test_priority_still_applies_when_not_uninterruptible(self, mock_scheduler):
        """Test that priority-based preemption still works normally"""
        # Normal interruptible thread
        normal_thread = TaskThreadBase("farming", ThreadPriority.NORMAL)
        mock_scheduler.current_thread = normal_thread

        # Higher priority should preempt
        high_thread = TaskThreadBase("event", ThreadPriority.HIGH)
        mock_scheduler.enqueue_thread(high_thread)

        assert mock_scheduler._should_preempt() is True

        # Lower priority should NOT preempt
        mock_scheduler.ready_threads.clear()
        low_thread = TaskThreadBase("background", ThreadPriority.LOW)
        mock_scheduler.enqueue_thread(low_thread)

        assert mock_scheduler._should_preempt() is False
