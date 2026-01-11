from dataclasses import dataclass

from dataclasses import dataclass
from typing import Optional, Any




@dataclass
class ThreadContext:
    """Context information for a TaskThread execution."""
    thread_id: str
    attempt: int = 1
