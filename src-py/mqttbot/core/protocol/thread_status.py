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

    @property
    def is_active(self) -> bool:
        """Returns True if thread is actively processing."""
        return self in (
            ThreadStatus.RUNNING,
        )


class ThreadInternalStatus(Enum):
    """
    Internal thread state machine states.
    """
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SUSPENDING = auto()
    SUSPENDED = auto()
    RESUMING = auto()
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
            ThreadInternalStatus.CANCELING,
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
    def external(self) -> ThreadStatus:
        """Projects the internal state to the external API state."""
        mapping = {
            self.READY: ThreadStatus.READY,
            # All active transition states project to RUNNING
            self.RUNNING: ThreadStatus.RUNNING,
            self.SUSPENDING: ThreadStatus.RUNNING,
            self.RESUMING: ThreadStatus.RUNNING,
            self.CANCELING: ThreadStatus.RUNNING,
            # Paused state
            self.SUSPENDED: ThreadStatus.SUSPENDED,
            # Terminal states
            self.COMPLETED: ThreadStatus.COMPLETED,
            self.FAILED: ThreadStatus.COMPLETED,
            self.CANCELLED: ThreadStatus.COMPLETED,
        }
        return mapping[self]

    @property
    def _transition_map(self) -> dict:
        # Define valid "Current -> Next" mappings
        return {
            self.READY: [self.RUNNING, self.CANCELLED],
            self.RUNNING: [self.SUSPENDING, self.COMPLETED, self.FAILED, self.CANCELING],
            self.SUSPENDING: [self.SUSPENDED, self.FAILED],  # Enforces intermediate state
            self.SUSPENDED: [self.RESUMING, self.CANCELLED],
            self.RESUMING: [self.RUNNING, self.FAILED],
            # Terminal states typically transition to nothing
            self.COMPLETED: [],
            self.FAILED: [],
            self.CANCELLED: [],
            self.CANCELING: [self.CANCELLED, self.FAILED],
        }

    def can_transition_to(self, next_state: "ThreadInternalStatus") -> bool:
        return next_state in self._transition_map.get(self, [])

    def transition_to(self, next_state: "ThreadInternalStatus") -> "ThreadInternalStatus":
        if not self.can_transition_to(next_state):
            raise IllegalStateTransition(
                f"Invalid transition: {self.name} -> {next_state.name}"
            )
        return next_state
