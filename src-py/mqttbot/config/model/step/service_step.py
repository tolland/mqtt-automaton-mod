from __future__ import annotations

from typing import Any, Literal

from mqttbot.config.model.step.step_base import StepBase


class ServiceStep(StepBase):
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
    type: Literal["oneshot", "command", "dwell", "commandtochat"] = "command"
    service: str = "none"
    method: str = "none"
    params: dict[str, Any] = {}
