from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


class StepBase(ABC):
    """
    Base class for pattern steps

    The base class for steps. A step represents the config item, which is later used
    to create tasks to be executed.

    Attributes:

    """

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
    """
    A task step represents the config
    object used to create a task that will be executed by a service/method on
    the bot mod.

    This class is used to define a task step with specific attributes such as
    the service name, the method to be executed, the type of step, and any
    parameters needed for execution.

    :ivar service: The name of the service associated with this task step. Defaults to "none".
    :type service: str
    :ivar method: The method to be executed in the service. Defaults to "none".
    :type method: str
    :ivar type: The type of this step, typically indicating its role (e.g., "command"). Defaults to "command".
    :type type: str
    :ivar params: A dictionary of parameters required for executing the step. Defaults to None.
    :type params: dict[str, Any]
    """

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
