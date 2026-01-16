from typing import Protocol, Generator

from rich import inspect

from mqttbot.config.tasks.task_registry import TaskRegistry
from mqttbot.core.context import Context
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.model.patterns.pattern import PatternStep
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.patterns.step import StepBase, TaskStep


class Task(Protocol):
    status: TaskStatus

    def enter(self, ctx: Context) -> None: ...

    def step(self, ctx: Context) -> TaskStatus: ...

    def suspend(self) -> None: ...

    def resume(self, ctx: Context) -> None: ...

    def exit(self, ctx: Context, status: TaskStatus) -> None: ...


class TaskCompiler:
    """Stateful compiler that tracks coordinate drift during generation."""

    def __init__(self, patterns_lib: PatternsConfig):
        self.patterns_lib: PatternsConfig = patterns_lib
        self.current_pos = (0.0, 0.0, 0.0)  # The 'expected' state

    def compile_pattern(self, p_name: str, anchor_pos: tuple) -> Generator[Task, None, None]:
        self.current_pos = anchor_pos
        pattern = self.patterns_lib[p_name]
        if pattern is None:
            # Unknown pattern - nothing to yield
            return

        for step in pattern:
            yield from self.compile_step(step)

    def compile_step(self, step_config: StepBase) -> Generator[Task, None, None]:
        # # 1. Handle String Shorthand (~ ~ ~)
        # if isinstance(config, str):
        #     self.current_pos = self._calculate_relative(config)
        #     yield GotoTask.create(*self.current_pos)
        #     return
        try:
            for step_item in step_config:
                config_def = step_config.to_dict()
                # Update internal state if it's a movement task
                if isinstance(step_item, TaskStep) and step_config.type == "goto":
                    p = step_config["params"]["target"]
                    self.current_pos = (p["x"], p["y"], p["z"])
                elif isinstance(step_item, PatternStep) and step_config.type == "goto":
                    coords = step_item.coords.resolve(self.current_pos)
                    self.current_pos = coords
                    config_def.update({
                        "params": {
                            "target": {
                                "x": coords[0],
                                "y": coords[1],
                                "z": coords[2],
                            }
                        }
                    })

                yield TaskFactory.create(config_def)
        except:
            inspect(step_item)
            raise

    def _calculate_relative(self, spec: PatternStep) -> tuple[float, float, float]:
        cx, cy, cz = self.current_pos
        parts = spec.relative_coords

        def resolve(val, current):
            if val.startswith("~"):
                return current + (float(val[1:]) if len(val) > 1 else 0)
            return float(val)

        return resolve(parts[0], cx), resolve(parts[1], cy), resolve(parts[2], cz)


class TaskFactory:
    @staticmethod
    def create(data: dict) -> Task:
        data = dict(data)
        task_type = data.pop("type")
        task_cls = TaskRegistry.get(task_type)
        return task_cls(**data)
