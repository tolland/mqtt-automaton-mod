from enum import Enum, auto

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
