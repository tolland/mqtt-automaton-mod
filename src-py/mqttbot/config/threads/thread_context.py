from dataclasses import dataclass


@dataclass
class ThreadContext:
    """Context information for a TaskThread execution."""

    thread_id: str
    attempt: int = 1
