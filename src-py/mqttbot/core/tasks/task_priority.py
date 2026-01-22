from enum import IntEnum


class TaskPriority(IntEnum):
    # Pillager attack, immediate threat
    CRITICAL = 0
    HIGH = 1  # Hunger
    NORMAL = 2  # Farming, travel
    LOW = 3  # Idle tasks
