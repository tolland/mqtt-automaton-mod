from __future__ import annotations

from typing import Union

from mqttbot.config.model.step.pattern_step import PatternStep
from mqttbot.config.model.step.goto_step import GotoStep
from mqttbot.config.model.step.service_step import ServiceStep

# This Union is the "Registry"
Step = Union[ServiceStep, PatternStep, GotoStep]

__all__ = ["Step","ServiceStep", "PatternStep", "GotoStep"]
