"""Tests for Scheduler - thread preemption and management"""
import pytest
from mqttbot.core.scheduler import Scheduler
from mqttbot.core.task.task import TaskPriority
from mqttbot.core.threads.task_thread import TaskThread


class TestSchedulerRegistration:
    """Test thread registration and enqueueing"""
    
    def test_register_thread(self, scheduler):
        """Test registering a thread at startup"""
        thread = TaskThread("test_thread", TaskPriority.NORMAL)
        scheduler.register_thread(thread)
        
        # Thread should be in ready queue
        assert len(scheduler.ready_threads) == 1
    
    def test_enqueue_thread(self, scheduler):
        """Test enqueueing a thread (after startup)"""
        thread = TaskThread("test_thread", TaskPriority.NORMAL)
        result = scheduler.enqueue_thread(thread)
        
        assert result is True
        assert len(scheduler.ready_threads) == 1
    
    def test_enqueue_multiple_threads(self, scheduler):
        """Test enqueueing multiple threads"""
        thread1 = TaskThread("thread1", TaskPriority.NORMAL)
        thread2 = TaskThread("thread2", TaskPriority.HIGH)
        
        scheduler.enqueue_thread(thread1)
        scheduler.enqueue_thread(thread2)
        
        assert len(scheduler.ready_threads) == 2


class TestSchedulerSingleton:
    """Test singleton mode to prevent duplicate threads"""
    
    def test_singleton_prevents_duplicate(self, scheduler):
        """Test that singleton=True prevents enqueueing duplicate thread"""
        thread1 = TaskThread("evasion", TaskPriority.CRITICAL)
        thread2 = TaskThread("evasion", TaskPriority.CRITICAL)
        
        result1 = scheduler.enqueue_thread(thread1, singleton=True)
        result2 = scheduler.enqueue_thread(thread2, singleton=True)
        
        assert result1 is True
        assert result2 is False  # Second one blocked
        assert len(scheduler.ready_threads) == 1
    
    def test_singleton_allows_different_threads(self, scheduler):
        """Test that singleton doesn't block different thread IDs"""
        thread1 = TaskThread("evasion", TaskPriority.CRITICAL)
        thread2 = TaskThread("sleep", TaskPriority.HIGH)
        
        result1 = scheduler.enqueue_thread(thread1, singleton=True)
        result2 = scheduler.enqueue_thread(thread2, singleton=True)
        
        assert result1 is True
        assert result2 is True
        assert len(scheduler.ready_threads) == 2
    
    def test_singleton_detects_in_current_thread(self, scheduler):
        """Test that singleton detects thread in current slot"""
        thread1 = TaskThread("farming", TaskPriority.NORMAL)
        scheduler.current_thread = thread1
        
        thread2 = TaskThread("farming", TaskPriority.NORMAL)
        result = scheduler.enqueue_thread(thread2, singleton=True)
        
        assert result is False
    
    def test_singleton_detects_in_suspended(self, scheduler):
        """Test that singleton detects thread in suspended stack"""
        thread1 = TaskThread("farming", TaskPriority.NORMAL)
        scheduler.suspended_stack.append(thread1)
        
        thread2 = TaskThread("farming", TaskPriority.NORMAL)
        result = scheduler.enqueue_thread(thread2, singleton=True)
        
        assert result is False


class TestSchedulerThreadIdTracking:
    """Test thread ID existence checking"""
    
    def test_thread_id_exists_in_ready_queue(self, scheduler):
        """Test detecting thread ID in ready queue"""
        thread = TaskThread("test_thread", TaskPriority.NORMAL)
        scheduler.ready_threads.append(thread)
        
        exists = scheduler._thread_id_exists("test_thread")
        assert exists is True
    
    def test_thread_id_not_exists(self, scheduler):
        """Test detecting non-existent thread ID"""
        exists = scheduler._thread_id_exists("nonexistent")
        assert exists is False
    
    def test_has_active_thread_public_api(self, scheduler):
        """Test public has_active_thread method"""
        thread = TaskThread("farming", TaskPriority.NORMAL)
        scheduler.current_thread = thread
        
        assert scheduler.has_active_thread("farming") is True
        assert scheduler.has_active_thread("other") is False


class TestSchedulerPriority:
    """Test thread priority ordering"""
    
    def test_threads_ordered_by_priority(self, scheduler):
        """Test that threads are ordered by priority in heap"""
        normal_thread = TaskThread("normal", TaskPriority.NORMAL)
        high_thread = TaskThread("high", TaskPriority.HIGH)
        critical_thread = TaskThread("critical", TaskPriority.CRITICAL)
        
        # Add in random order
        scheduler.enqueue_thread(normal_thread)
        scheduler.enqueue_thread(critical_thread)
        scheduler.enqueue_thread(high_thread)
        
        # Highest priority should be first
        assert scheduler.ready_threads[0].priority == TaskPriority.CRITICAL
    
    def test_priority_comparison(self):
        """Test that priority comparison works"""
        normal = TaskThread("normal", TaskPriority.NORMAL)
        high = TaskThread("high", TaskPriority.HIGH)
        
        # High priority should be "less than" normal (for min-heap)
        assert high < normal


class TestSchedulerThreadStateTracking:
    """Test tracking thread state"""
    
    def test_clear_ready_threads(self, scheduler):
        """Test clearing ready threads"""
        thread1 = TaskThread("thread1", TaskPriority.NORMAL)
        thread2 = TaskThread("thread2", TaskPriority.NORMAL)
        
        scheduler.enqueue_thread(thread1)
        scheduler.enqueue_thread(thread2)
        
        assert len(scheduler.ready_threads) == 2
        
        # Clear (would normally be done at test cleanup)
        scheduler.ready_threads.clear()
        assert len(scheduler.ready_threads) == 0
    
    def test_suspended_stack_lifo(self, scheduler):
        """Test that suspended stack is LIFO"""
        thread1 = TaskThread("thread1", TaskPriority.NORMAL)
        thread2 = TaskThread("thread2", TaskPriority.NORMAL)
        
        scheduler.suspended_stack.append(thread1)
        scheduler.suspended_stack.append(thread2)
        
        # Should pop in reverse order
        popped = scheduler.suspended_stack.pop()
        assert popped.thread_id == "thread2"


class TestSchedulerEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_enqueue_thread_without_singleton(self, scheduler):
        """Test that without singleton, duplicates are allowed"""
        thread1 = TaskThread("farming", TaskPriority.NORMAL)
        thread2 = TaskThread("farming", TaskPriority.NORMAL)
        
        result1 = scheduler.enqueue_thread(thread1, singleton=False)
        result2 = scheduler.enqueue_thread(thread2, singleton=False)
        
        assert result1 is True
        assert result2 is True
        assert len(scheduler.ready_threads) == 2
    
    def test_singleton_default_is_false(self, scheduler):
        """Test that singleton defaults to False"""
        thread1 = TaskThread("test", TaskPriority.NORMAL)
        thread2 = TaskThread("test", TaskPriority.NORMAL)
        
        result1 = scheduler.enqueue_thread(thread1)  # No singleton param
        result2 = scheduler.enqueue_thread(thread2)  # No singleton param
        
        assert result1 is True
        assert result2 is True  # Both allowed without singleton
    
    def test_empty_scheduler(self, scheduler):
        """Test operations on empty scheduler"""
        assert len(scheduler.ready_threads) == 0
        assert scheduler.current_thread is None
        assert len(scheduler.suspended_stack) == 0
        assert scheduler._thread_id_exists("any") is False
