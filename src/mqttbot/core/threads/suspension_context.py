
from dataclasses import dataclass

from dataclasses import dataclass
from typing import Optional, Any





@dataclass
class EventHandlerContext:
    """
    Typed context for event handler execution.

    Passed to event handlers so they know what triggered them.
    """

    # The message that triggered this event
    service: str
    method: str

    # Current bot position (at time of event)
    position: tuple[int, int, int]

    # Event-specific data
    response_data: dict[str, Any]


@dataclass
class TaskSuspensionContext:
    """
    Typed context for task suspension/resumption.

    Used when a task is suspended and needs to resume later.
    Tasks are responsible for saving their own state.
    """

    # Position where the task was suspended
    position: tuple[int, int, int]

    # Task-specific state (task decides what to save)
    metadata: dict[str, Any]

    @classmethod
    def for_position(
            cls,
            position: tuple[int, int, int],
            **metadata
    ) -> "TaskSuspensionContext":
        """Convenience constructor"""
        return cls(position=position, metadata=metadata)


@dataclass
class ThreadSuspensionContext:
    """
    Typed context for thread suspension/resumption.

    Saved when a thread is preempted and needs to resume later.
    Contains minimal state - the thread object itself persists.
    """

    # Position where the thread was suspended
    position_at_suspend: tuple[int, int, int]

    # Which task in the sequence we were on
    current_task_index: int

    # Thread-specific metadata (thread decides what to save)
    metadata: dict[str, Any]

    @classmethod
    def from_thread(
            cls,
            position: tuple[int, int, int],
            task_index: int,
            **metadata
    ) -> "ThreadSuspensionContext":
        """Convenience constructor"""
        return cls(
            position_at_suspend=position,
            current_task_index=task_index,
            metadata=metadata
        )

    def check_fatal_consistency(
            self,
            current_position: tuple[int, int, int],
            max_safe_distance: int = 200
    ) -> None:
        """
        Check if resumption would be safe.

        Raises RuntimeError if bot has been teleported too far away.
        This is a fatal consistency check - if it fails, the thread cannot resume.

        Args:
            current_position: Bot's current position
            max_safe_distance: Maximum allowed distance (in blocks)

        Raises:
            RuntimeError: If bot is too far from suspension point
        """
        distance = self._euclidean_distance(self.position_at_suspend, current_position)

        if distance > max_safe_distance:
            raise RuntimeError(
                f"Bot has moved {distance:.1f} blocks from suspension point "
                f"({self.position_at_suspend} → {current_position}). "
                f"This is beyond the safe resumption distance ({max_safe_distance}). "
                f"Resuming would be unsafe - thread cannot continue."
            )

    @staticmethod
    def _euclidean_distance(
            pos1: tuple[int, int, int],
            pos2: tuple[int, int, int]
    ) -> float:
        """Calculate 3D Euclidean distance between two positions"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        dz = pos2[2] - pos1[2]
        return (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
