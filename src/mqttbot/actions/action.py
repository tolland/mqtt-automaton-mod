from abc import ABC, abstractmethod


class Action(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

    @abstractmethod
    def can_start(self) -> bool:
        pass

    @abstractmethod
    def is_complete(self) -> bool:
        pass

    @abstractmethod
    def reset(self):
        pass

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for this pattern execution
        Used to track and correlate actions and replies across the system.
        """
        self.correlation_id = correlation_id
