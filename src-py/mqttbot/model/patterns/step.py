from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, Iterator


class StepBase(ABC):
    """Base class for pattern steps"""

    pass

    def __iter__(self) -> Iterator["StepBase"]:
        yield self

    def __len__(self) -> int:
        return 1

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        pass


@dataclass
class TaskStep(StepBase):
    """A task config expressed for an event handler step"""

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
