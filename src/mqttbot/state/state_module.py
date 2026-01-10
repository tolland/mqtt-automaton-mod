from dataclasses import dataclass, field
from typing import TypeVar, Generic, Callable, Any, Protocol
from abc import ABC, abstractmethod
import json

# Core primitives
T = TypeVar('T')


class StateModule(ABC, Generic[T]):
    """Base for extensible state domains"""

    @abstractmethod
    def handle_event(self, event: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_state(self) -> T:
        pass
