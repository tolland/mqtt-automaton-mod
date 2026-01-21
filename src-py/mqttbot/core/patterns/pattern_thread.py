from collections.abc import Awaitable, Callable, Generator
from typing import Any

from loguru import logger
from rich.tree import Tree

from mqttbot.core.context import Context
from mqttbot.core.tasks.dwell_task import DwellTask
from mqttbot.core.tasks.goto_task import GotoTask
from mqttbot.core.tasks.task_priority import TaskPriority, TaskStatus
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.tasks.task import Task, TaskCompiler, TaskFactory

"""PatternThread - expands waypoints and patterns into deterministic task sequences"""


class PatternThread(TaskThread):
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
        on_suspend: Callable[["TaskThread", Context], Awaitable[None]] | None = None,
        on_resume: Callable[["TaskThread", Context], Awaitable[None]] | None = None,
        on_cancel: Callable[["TaskThread", Context], Awaitable[None]] | None = None,
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
        """
        super().__init__(thread_id, priority, on_suspend, on_resume, on_cancel)

        self.waypoints = waypoints
        self.patterns_config = patterns
        self.current_task_index = 0

    def expand_pattern(self, name: str, start_pos: tuple) -> Generator[Task, None, None]:
        if name not in self.patterns_config:
            raise ValueError(f"Unknown pattern: {name}")

        pattern_def = self.patterns_config.get(name)
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

    def build_task_sequence(self) -> None:
        """Build the full task sequence from waypoints and patterns"""
        self.task_queue.clear()
        compiler = TaskCompiler(self.patterns_config)

        for wp in self.waypoints:
            wp_pos = (wp["x"], wp["y"], wp["z"])

            # Use enqueue_task to properly inject correlation_id
            self.enqueue_task(GotoTask.create(*wp_pos))

            # Expand and add pattern tasks
            pattern_names = wp.get("patterns", [])
            for p_name in pattern_names:
                for task in compiler.compile_pattern(p_name, wp_pos):
                    self.enqueue_task(task)
                wp_pos = compiler.current_pos

    async def suspend(self, ctx: Context) -> None:
        """Suspend - save waypoint and task index for resumption"""
        logger.debug(f"[{self.thread_id}] Suspending at task index {self.current_task_index}")
        await super().suspend(ctx)
        if self.current_task:
            self.task_queue.appendleft(self.current_task)
            self.current_task.status = TaskStatus.READY
            self.current_task = None

    async def resume(self, ctx: Context) -> None:
        """Resume - resume this thread from suspension point
        """
        logger.debug(f"[{self.thread_id}] Resuming")

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

    async def step(self, ctx) -> bool:
        """Execute one step of the pattern sequence"""
        if not self.current_task:
            return True

        # Execute the task step
        status = self.current_task.step(ctx)

        if status == TaskStatus.SUCCESS or status == TaskStatus.FAILED:
            # Task completed, move to next
            self.current_task.exit(ctx, status)
            await self._advance_to_next_task(ctx)
            self.current_task_index += 1

        return self.current_task is None

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
