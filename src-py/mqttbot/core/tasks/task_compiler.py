import importlib
from typing import Iterator

import mqttbot.core.tasks as _tasks  # noqa: F401
from mqttbot.config.model.pattern.pattern_config import PatternsConfig
from mqttbot.config.model.step.pattern_step import PatternStep
from mqttbot.config.model.step.service_step import ServiceStep
from mqttbot.config.model.step.steps_discriminator import Step
from mqttbot.core.tasks.task_base import TaskFactory
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_compiler_protocol import TaskCompilerProtocol

inspect = importlib.import_module("rich").inspect

class TaskCompiler(TaskCompilerProtocol):
    """Stateful compiler that tracks coordinate drift during generation."""

    def __init__(self,
                 patterns_lib: PatternsConfig,
                 ):
        self.patterns_lib: PatternsConfig = patterns_lib
        self.current_pos = (0.0, 0.0, 0.0)  # The 'expected' state

    def compile_pattern(
        self,
        p_name: str,
        anchor_pos: tuple[float, float, float],
    ) -> Iterator[Task]:
        self.current_pos = anchor_pos
        pattern = self.patterns_lib.get(p_name)
        if pattern is None:
            raise ValueError(f"Pattern '{p_name}' not found in library")

        for step in pattern.steps:
            yield from self.compile_step(step)

    def compile_step(self, step_config: "Step") -> Iterator[Task]:
        """Compile a single step into one or more tasks, updating internal state as needed."""
        try:
            # inspect(step_config, title="Compiling Step")
            config_def = step_config.to_dict()
            # Update internal state if it's a movement task
            if isinstance(step_config, ServiceStep) and step_config.type == "goto":
                p = step_config.params["target"]
                self.current_pos = (p["x"], p["y"], p["z"])
            elif isinstance(step_config, PatternStep) and step_config.type == "pattern":
                coords = step_config.coords.resolve(self.current_pos)
                self.current_pos = coords
                config_def.update(
                    {
                        "params": {
                            "target": {
                                "x": coords[0],
                                "y": coords[1],
                                "z": coords[2],
                            }
                        }
                    }
                )

            yield TaskFactory.create(config_def)
        except:
            inspect(step_config)
            raise
