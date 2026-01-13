from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

# Core primitives
T = TypeVar("T")


class StateModule(ABC, Generic[T]):
    """Base for extensible state domains"""

    @abstractmethod
    def handle_event(self, event: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_state(self) -> T:
        pass

    @abstractmethod
    def reset_state(self) -> None:
        pass
