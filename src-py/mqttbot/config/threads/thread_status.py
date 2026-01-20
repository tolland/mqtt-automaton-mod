from enum import Enum, auto


class ThreadStatus(Enum):
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SUSPENDED = auto()
    CANCELLED = auto()
