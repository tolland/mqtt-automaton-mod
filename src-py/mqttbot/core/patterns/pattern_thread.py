from __future__ import annotations

from collections.abc import Callable
from collections.abc import Generator
from typing import Any

from loguru import logger
from rich.tree import Tree

from mqttbot.core.protocol.task import Task
from mqttbot.core.tasks.dwell_task import DwellTask
from mqttbot.core.tasks.goto_task import GotoTask
from mqttbot.core.tasks.task_priority import TaskPriority
from mqttbot.core.tasks.task_status import TaskStatus
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.task_thread_base import TaskThreadBase
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.patterns.step import TaskStep
from mqttbot.model.tasks.task import TaskCompiler, TaskFactory

"""PatternThread - expands waypoints and patterns into deterministic task sequences"""


class PatternThread(TaskThreadBase):
    """
    A thread that expands waypoints and patterns into task sequences.

    Patterns use relative coordinates that are resolved based on the previous
    position. This thread ensures deterministic expansion - the same sequence
    is always generated from the same config.

    Key property: resumable from any point because the expansion is fully
    deterministic. On resume, just rebuild the task sequence and skip to
    where we were.
    """

    def __init__(
        self,
        thread_id: str,
        priority: TaskPriority,
        waypoints: list[dict[str, Any]],
        patterns: PatternsConfig,
        on_suspend: Callable[["TaskThreadBase", "Context"], list[Task]] | None = None,
        on_resume: Callable[["TaskThreadBase", Context], list[Task]] | None = None,
        on_cancel: Callable[["TaskThreadBase", Context], list[Task]] | None = None,
        on_failed: Callable[["TaskThreadBase", Context], list[Task]] | None = None,
        on_waypoint_start: list[TaskStep] | None = None,
        on_waypoint_end: list[TaskStep] | None = None,
        on_waypoints_start: list[TaskStep] | None = None,
        on_waypoints_end: list[TaskStep] | None = None,
    ) -> None:
        """Initialize a pattern-based thread

        Args:
            thread_id: Unique identifier for this thread
            priority: Thread priority level
            waypoints: List of waypoint dictionaries with x, y, z, patterns
            patterns: PatternsConfig object containing pattern definitions
            on_suspend: Optional callback when thread is suspended
            on_resume: Optional callback when thread is resumed
            on_cancel: Optional callback when thread is cancelled
            on_failed: Optional callback when thread is failed
        """
        super().__init__(thread_id, priority, on_suspend, on_resume, on_cancel, on_failed)

        self.waypoints = waypoints
        self.patterns_config = patterns
        self.current_task_index = 0

    # async def step(self, ctx) -> ThreadStatus:
    #     """Execute one step of the pattern sequence"""
    #     self.current_task_index += 1
    #
    #     return await super().step(ctx)

    async def suspend(self, ctx: Context) -> None:
        """Suspend - save waypoint and task index for resumption"""
        logger.debug(f"[{self.thread_id}] Suspending at task index {self.current_task_index}")
        if self.current_task:
            self.task_queue.appendleft(self.current_task)
            self.current_task.suspend(ctx)
            self.current_task = None
        await super().suspend(ctx)

    async def resume(self, ctx: Context) -> None:
        """Resume - resume this thread from suspension point
        """
        logger.debug(f"[{self.thread_id}] Resuming")

        # So we rely on suspend to decide what to do with current_task
        #  which currently to put it back on the queue so it is re-executed
        if self.current_task and self.current_task.status == TaskStatus.SUSPENDED:
            raise RuntimeError(f"Thread {self.thread_id} has a suspended current task on resume.")
            # self.current_task.resume(ctx)

        self.current_task_index = 0

        await super().resume(ctx)

    def to_dict(self) -> dict:
        """Specific override for PatternThread state."""
        state = super().to_dict()
        state.update({
            "current_task_index": self.current_task_index,
            "waypoints_count": len(self.waypoints),
        })
        return state

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "correlation_id", self.correlation_id
        yield "priority", self.priority.name
        yield "state", self.state.name
        yield "_status", self._status.value
        yield "uninterruptible", self.uninterruptible
        yield "current_task", type(self.current_task).__name__ if self.current_task else None
        yield "task_queue_len", len(self.task_queue)
        yield "on_suspend", self._on_suspend
        yield "on_resume", self._on_resume
        yield "on_cancel", self._on_cancel
        yield "on_failed", self._on_failed

    def __rich__(self):
        """Rich representation showing expanded task sequence as a tree"""
        # Build tree of tasks organized by waypoint
        root = Tree(
            f"[bold cyan]{self.thread_id}[/bold cyan] "
            f"[yellow]({self.priority.name})[/yellow] "
            f"[dim]({len(self.task_queue)} tasks)[/dim]"
        )

        tasks = list(self.task_queue)
        waypoint_idx = 0
        waypoint_node = None

        for task in tasks:
            if isinstance(task, GotoTask):
                # Check if this is a waypoint goto
                waypoint = (
                    self.waypoints[waypoint_idx] if waypoint_idx < len(self.waypoints) else None
                )

                if waypoint and task.target == (waypoint["x"], waypoint["y"], waypoint["z"]):
                    # This is a waypoint goto - create new waypoint node
                    target_str = f"({waypoint['x']}, {waypoint['y']}, {waypoint['z']})"
                    patterns_str = ", ".join(waypoint.get("patterns", []))

                    wp_label = (
                        f"[bold magenta]Waypoint {waypoint_idx + 1}[/bold magenta] "
                        f"[cyan]{target_str}[/cyan]"
                    )
                    if patterns_str:
                        wp_label += f" [dim]→ {patterns_str}[/dim]"

                    waypoint_node = root.add(wp_label)
                    waypoint_idx += 1
                else:
                    # Pattern goto - add to current waypoint
                    target_str = f"({task.target[0]}, {task.target[1]}, {task.target[2]})"
                    waypoint_node.add(f"[green]goto[/green] {target_str}")

            elif isinstance(task, DwellTask):
                # Dwell task
                waypoint_node.add(f"[blue]dwell[/blue] {task.duration}s")

        return root



class PatternThreadHelper:
    @staticmethod
    def expand_pattern(pt: type[PatternThread], name: str, start_pos: tuple) -> Generator[Task, None, None]:
        if name not in pt.patterns_config:
            raise ValueError(f"Unknown pattern: {name}")

        pattern_def = pt.patterns_config.get(name)
        # Context persists across the whole pattern sequence
        context = {"pos": start_pos}

        # 1. Pre-tasks (e.g., toggle wurst ON)
        for step in pattern_def.get("on_pattern_start", []):
            yield from TaskFactory.from_config(step, context)

        # 2. Main Movement Steps
        for step in pattern_def.get("steps", []):
            yield from TaskFactory.from_config(step, context)

        # 3. Post-tasks (e.g., toggle wurst OFF)
        for step in pattern_def.get("on_pattern_end", []):
            yield from TaskFactory.from_config(step, context)

    @staticmethod
    def build_task_sequence(pt: "PatternThread") -> None:
        """Build the full task sequence from waypoints and patterns"""
        pt.task_queue.clear()
        compiler = TaskCompiler(pt.patterns_config)

        for wp in pt.waypoints:
            wp_pos = (wp["x"], wp["y"], wp["z"])

            # Use enqueue_task to properly inject correlation_id
            pt.enqueue_task(GotoTask.create(*wp_pos))

            # Expand and add pattern tasks
            pattern_names = wp.get("patterns", [])
            for p_name in pattern_names:
                for task in compiler.compile_pattern(p_name, wp_pos):
                    pt.enqueue_task(task)
                wp_pos = compiler.current_pos
