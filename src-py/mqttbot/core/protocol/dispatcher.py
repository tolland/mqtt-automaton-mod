from typing import Protocol, runtime_checkable, Optional, TYPE_CHECKING, List, Any

from mqttbot.core.protocol.thread import ThreadInterface

if TYPE_CHECKING:
    # Import only for type checking to avoid circular imports at runtime
    from mqttbot.core.threads.scheduler_context import Context


@runtime_checkable
class DispatcherInterface(Protocol):
    """Protocol that describes the public surface of the Dispatcher.

    This focuses on the attributes and methods that consumers/tests use:
      - queues (ready/done) and the current_thread
      - the async ``step`` method used by the scheduler loop
      - a small utility method ``is_complete`` used for completion checks

    The goal is to allow tests or alternate implementations to be passed
    where a Dispatcher is required without importing the concrete class.
    """

    ready_queue: List[ThreadInterface]
    done_queue: List[ThreadInterface]
    current_thread: Optional[ThreadInterface]

    async def step(self, ctx: "Context") -> bool:  # pragma: no cover - simple protocol
        """Run one dispatcher tick; returns True when no work remains."""

    def is_complete(self) -> bool:  # pragma: no cover - simple protocol
        """Return True when dispatcher has no ready threads and no current thread."""

    def __rich_repr__(self) -> Any:  # pragma: no cover - optional pretty repr
        ...
