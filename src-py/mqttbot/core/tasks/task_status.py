from enum import Enum, auto


class TaskInternalState(Enum):
    READY = "ready"
    INIT = "init"
    SENT = "sent"
    WAITING = "waiting"
    DONE = "done"
    SUSPEND = "suspend"
    RESUME = "resume"
    SUSPENDED = "suspended"


class TaskStatus(Enum):
    READY = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SUSPENDED = auto()
