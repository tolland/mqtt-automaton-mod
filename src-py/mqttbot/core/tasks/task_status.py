from enum import Enum


class TaskState(Enum):
    INIT = "init"
    SENT = "sent"
    WAITING = "waiting"
    DONE = "done"
