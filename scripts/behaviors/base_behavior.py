"""
Base behavior class for modular bot behaviors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import time


class BehaviorState(Enum):
    """States a behavior can be in"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"  # For emergency situations


class BaseBehavior(ABC):
    """
    Base class for all bot behaviors.

    Behaviors are modular units that can be combined to create complex bot activities.
    Each behavior has a lifecycle: initialize -> execute -> cleanup
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.state = BehaviorState.IDLE
        self.priority = self.config.get("priority", 5)  # 1-10, lower = higher priority
        self.interruptible = self.config.get("interruptible", True)
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None

    @abstractmethod
    def can_start(self, context: Dict[str, Any]) -> bool:
        """
        Check if this behavior can start given the current context.

        Args:
            context: Current bot state and environment info

        Returns:
            bool: True if behavior can start
        """
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Execute the behavior.

        Args:
            context: Current bot state and environment info

        Returns:
            bool: True if behavior completed successfully
        """
        pass

    @abstractmethod
    def cleanup(self, context: Dict[str, Any]) -> None:
        """
        Clean up after behavior execution.

        Args:
            context: Current bot state and environment info
        """
        pass

    def start(self, context: Dict[str, Any]) -> bool:
        """Start the behavior"""
        if not self.can_start(context):
            return False

        self.state = BehaviorState.RUNNING
        self.started_at = time.time()
        return True

    def pause(self) -> None:
        """Pause the behavior"""
        if self.state == BehaviorState.RUNNING:
            self.state = BehaviorState.PAUSED

    def resume(self) -> None:
        """Resume a paused behavior"""
        if self.state == BehaviorState.PAUSED:
            self.state = BehaviorState.RUNNING

    def suspend(self) -> None:
        """Suspend behavior (for emergencies)"""
        self.state = BehaviorState.SUSPENDED

    def complete(self, success: bool = True) -> None:
        """Mark behavior as completed"""
        self.state = BehaviorState.COMPLETED if success else BehaviorState.FAILED
        self.completed_at = time.time()

    def get_duration(self) -> Optional[float]:
        """Get behavior execution duration in seconds"""
        if self.started_at is None:
            return None
        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    def is_active(self) -> bool:
        """Check if behavior is currently active"""
        return self.state in [BehaviorState.RUNNING, BehaviorState.PAUSED]

    def can_be_interrupted(self) -> bool:
        """Check if behavior can be interrupted"""
        return self.interruptible and self.state == BehaviorState.RUNNING

    def get_status(self) -> Dict[str, Any]:
        """Get current behavior status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "priority": self.priority,
            "interruptible": self.interruptible,
            "duration": self.get_duration(),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
