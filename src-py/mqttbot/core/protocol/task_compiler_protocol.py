from typing import Protocol, Tuple, runtime_checkable, Iterator

from mqttbot.config.model.pattern.pattern_config import PatternsConfig
from mqttbot.config.model.step.pattern_step import PatternStep
from mqttbot.core.protocol.task import Task


@runtime_checkable
class TaskCompilerProtocol(Protocol):
    """Protocol describing the public surface of TaskCompiler."""

    patterns_lib: PatternsConfig
    current_pos: Tuple[float, float, float]

    def compile_pattern(
        self,
        p_name: str,
        anchor_pos: Tuple[float, float, float],
    ) -> Iterator[Task]: ...

    def compile_step(self, step_config: "Step") -> Iterator[Task]: ...

    def _calculate_relative(self, spec: PatternStep) -> Tuple[float, float, float]: ...


__all__ = ["TaskCompilerProtocol"]
