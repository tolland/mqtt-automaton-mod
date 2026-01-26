import logging
from enum import Enum, auto

from mqttbot.core.protocol.thread_status import IllegalStateTransition

logger = logging.getLogger("mqttbot.task_status")


class TaskStatus(Enum):
    READY = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SUSPENDED = auto()
    CANCELLED = auto()


class TaskInternalState(Enum):
    """Internal task state machine states.
    protected by transition_to map.
    """
    INITIAL = auto()
    "Task constructed but not yet started. tasks params are set."
    ENQUEUED = auto()
    "Task has been enqueued by thread. e.g. it has a correlation id."
    READY = auto()
    "Task has been selected as current_task. enter() was called."
    SENT = auto()
    WAITING = auto()
    "Task is waiting for external response."
    DONE = auto()
    """Task completed successfully or did not require a response.
    If a non-resumable task is suspended, it will transition to DONE.
    """
    FAILED = auto()
    RESUMING = auto()
    RESUMED = auto()
    SUSPENDING = auto()
    SUSPENDED = auto()
    CANCELING = auto()
    CANCELLED = auto()

    @property
    def is_active(self) -> bool:
        """Returns True if task is actively processing."""
        return self in (
            TaskInternalState.INITIAL,
            TaskInternalState.ENQUEUED,
            TaskInternalState.READY,
            TaskInternalState.SENT,
            TaskInternalState.WAITING,
            TaskInternalState.SUSPENDING,
            TaskInternalState.RESUMING,
            TaskInternalState.CANCELING,
        )

    @property
    def is_terminal(self) -> bool:
        """Returns True if task has finished."""
        return self in (
            TaskInternalState.DONE,
            TaskInternalState.FAILED,
            TaskInternalState.CANCELLED,
        )

    @property
    def external(self) -> TaskStatus:
        """Projects the internal state to the external API state."""
        mapping = {
            self.INITIAL: TaskStatus.READY,
            self.ENQUEUED: TaskStatus.READY,
            # Active / transient states project to RUNNING
            self.READY: TaskStatus.RUNNING,
            self.SENT: TaskStatus.RUNNING,
            self.WAITING: TaskStatus.RUNNING,
            self.SUSPENDING: TaskStatus.RUNNING,
            self.RESUMING: TaskStatus.RUNNING,
            self.RESUMED: TaskStatus.RUNNING,
            self.CANCELING: TaskStatus.RUNNING,
            # Paused state
            self.SUSPENDED: TaskStatus.SUSPENDED,
            # Completed outcome
            self.DONE: TaskStatus.SUCCESS,
            self.FAILED: TaskStatus.FAILED,
            self.CANCELLED: TaskStatus.CANCELLED,
        }
        return mapping[self]

    @property
    def _transition_map(self) -> dict:
        return {
            self.INITIAL: [self.ENQUEUED, self.SUSPENDED, self.CANCELING, self.RESUMING],
            self.ENQUEUED: [self.READY, self.FAILED, self.SUSPENDING, self.CANCELING],
            self.READY: [self.SENT, self.WAITING, self.SUSPENDING, self.CANCELING, self.RESUMING],
            self.SENT: [
                self.SUSPENDING,
                self.CANCELING,
                self.FAILED,
                self.CANCELING,
                self.WAITING,
            ],
            # Allow suspension requests from active states
            self.SUSPENDING: [self.SUSPENDED, self.FAILED, self.DONE],
            self.WAITING: [
                self.DONE,
                self.FAILED,
                self.SUSPENDING,
                self.CANCELING,
            ],
            self.SUSPENDED: [self.READY, self.RESUMING, self.CANCELLED],
            self.RESUMING: [self.RESUMED, self.FAILED, self.CANCELING, self.READY],
            # canceling is uninterruptible, so we should only go to
            # CANCELLED or FAILED from there
            self.CANCELING: [self.CANCELLED, self.FAILED],
            # Terminal states transition to nothing
            self.DONE: [],
            self.FAILED: [],
            self.CANCELLED: [],
        }

    def can_transition_to(self, next_state: "TaskInternalState") -> bool:
        allowed = self._transition_map.get(self, [])
        return next_state in allowed

    def transition_to(self, next_state: "TaskInternalState") -> "TaskInternalState":
        if not self.can_transition_to(next_state):
            raise IllegalStateTransition(f"Invalid transition: {self.name} -> {next_state.name}")
        return next_state
