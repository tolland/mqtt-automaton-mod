from dataclasses import dataclass

from enum import Enum
from enum import Enum, auto


@dataclass
class TaskContext:
    """Captures resumable state for a task"""
    step_index: int
    metadata: dict[str, object]  # Task-specific state


class TaskPriority(Enum):
    CRITICAL = 0  # Pillager attack, immediate threat
    HIGH = 1  # Hunger
    NORMAL = 2  # Farming, travel
    LOW = 3  # Idle tasks

class TaskStatus(Enum):
    READY = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SUSPENDED = auto()
