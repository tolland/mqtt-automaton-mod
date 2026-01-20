from enum import Enum, IntEnum, auto


class TaskPriority(IntEnum):
    # Pillager attack, immediate threat
    CRITICAL = 0
    HIGH = 1  # Hunger
    NORMAL = 2  # Farming, travel
    LOW = 3  # Idle tasks


class TaskStatus(Enum):
    READY = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SUSPENDED = auto()
