from dataclasses import dataclass
from typing import Any


@dataclass
class TaskStepConfig:
    """A tasl config expressed for an event handler step"""

    service: str = "none"
    method: str = "none"
    type: str = "command"
    params: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "service": self.service,
            "method": self.method,
            "type": self.type,
            "params": self.params or {},
        }
