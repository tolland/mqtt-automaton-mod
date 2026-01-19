from enum import Enum


class TaskState(Enum):
    READY = "ready"
    INIT = "init"
    SENT = "sent"
    WAITING = "waiting"
    DONE = "done"
    SUSPENDED = "suspended"
