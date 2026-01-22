from enum import Enum, auto


class IllegalStateTransition(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class ThreadStatus(Enum):
    """
    External thread state machine states.
    """
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SUSPENDED = auto()
    CANCELLED = auto()


class ThreadInternalStatus(Enum):
    """
    Internal thread state machine states.
    """
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SUSPENDING = auto()
    RESUMING = auto()
    SUSPENDED = auto()
    RESUME = auto()
    CANCELING = auto()
    CANCELLED = auto()

    @property
    def is_active(self) -> bool:
        """Returns True if thread is actively processing."""
        return self in (
            ThreadInternalStatus.RUNNING,
            ThreadInternalStatus.SUSPENDING,
            ThreadInternalStatus.RESUMING,
        )

    @property
    def is_terminal(self) -> bool:
        """Returns True if thread has finished."""
        return self in (
            ThreadInternalStatus.COMPLETED,
            ThreadInternalStatus.FAILED,
            ThreadInternalStatus.CANCELLED,
        )

    @property
    def _transition_map(self) -> dict:
        # Define valid "Current -> Next" mappings
        return {
            self.READY: [self.RUNNING, self.CANCELLED],
            self.RUNNING: [self.SUSPENDING, self.COMPLETED, self.FAILED, self.CANCELING, self.RUNNING],
            self.SUSPENDING: [self.SUSPENDED, self.FAILED],  # Enforces intermediate state
            self.SUSPENDED: [self.RESUMING, self.CANCELLED],
            self.RESUMING: [self.RUNNING, self.FAILED],
            # Terminal states typically transition to nothing
            self.COMPLETED: [],
            self.FAILED: [],
            self.CANCELLED: [],
        }

    def can_transition_to(self, next_state: "ThreadInternalStatus") -> bool:
        return next_state in self._transition_map.get(self, [])

    def transition_to(self, next_state: "ThreadInternalStatus") -> "ThreadInternalStatus":
        if not self.can_transition_to(next_state):
            raise IllegalStateTransition(
                f"Invalid transition: {self.name} -> {next_state.name}"
            )
        return next_state
