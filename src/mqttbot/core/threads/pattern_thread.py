from typing import Optional, Callable, Awaitable, Any

from mqttbot.core.task.task import TaskContext, TaskStatus, TaskPriority
from mqttbot.core.scheduler import Scheduler
from mqttbot.core.task.task import TaskPriority
from mqttbot.core.threads.pattern_expander import PatternExpander
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.tasks.dwell_task import DwellTask
from mqttbot.tasks.goto_task import GotoTask

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
            waypoints: list[dict[str, Any]],  # From config
            patterns: dict[str, list],  # Pattern definitions from config
            on_suspend: Optional[Callable[["TaskThread"], Awaitable[None]]] = None,
            on_resume: Optional[Callable[["TaskThread", TaskContext], Awaitable[None]]] = None,
    ) -> None:
        """Initialize a pattern-based thread

        Args:
            thread_id: Unique thread identifier
            priority: Task priority level
            waypoints: List of waypoint dicts with x, y, z, patterns
            patterns: Dict mapping pattern names to step definitions
            on_suspend: Optional callback when suspended
            on_resume: Optional callback when resumed

        Example waypoints:
            [
                {"x": 18, "y": 65, "z": -8, "patterns": ["cane_row_01"]},
                {"x": 21, "y": 65, "z": -110, "patterns": ["cane_row_02"]},
            ]

        Example patterns:
            {
                "cane_row_01": [
                    "~ ~ ~-5",
                    "~ ~ ~-16",
                    {"type": "dwell", "period": "4s"},
                    "~ ~ ~-10",
                ]
            }
        """
        super().__init__(thread_id, priority, on_suspend, on_resume)

        self.waypoints = waypoints  # Keep for rebuilding on resume
        self.patterns = patterns
        self.current_task_index = 0  # Track where we are in the sequence

    def build_task_sequence(self) -> None:
        """Build the full task sequence from waypoints and patterns

        This is deterministic - same input always produces same output.
        It's safe to call multiple times.
        """
        self.task_queue.clear()
        self.current_task_index = 0

        for waypoint in self.waypoints:
            x, y, z = waypoint["x"], waypoint["y"], waypoint["z"]
            base_pos = (x, y, z)

            # Add goto task to reach this waypoint
            goto_task = GotoTask(x, y, z)
            self.task_queue.append(goto_task)

            # Expand and add pattern tasks
            pattern_names = waypoint.get("patterns", [])
            for pattern_name in pattern_names:
                if pattern_name not in self.patterns:
                    print(f"[PatternThread] Unknown pattern: {pattern_name}")
                    continue

                pattern_def = self.patterns[pattern_name]
                expanded = PatternExpander.expand_pattern(pattern_def, base_pos)

                print(f"[PatternThread] Expanded pattern '{pattern_name}' from {base_pos}:")

                # Add expanded tasks to queue
                for task_type, params in expanded:
                    if task_type == "goto":
                        x, y, z = params
                        print(f"  → goto {params}")
                        task = GotoTask(x, y, z)
                        self.task_queue.append(task)
                        base_pos = params  # Update position for next pattern step

                    elif task_type == "dwell":
                        print(f"  → dwell {params}s")
                        task = DwellTask(params)
                        self.task_queue.append(task)

    async def suspend(self) -> TaskContext:
        """Suspend - save waypoint and task index for resumption"""
        print(f"[PatternThread] Suspending at task index {self.current_task_index}")
        ctx = await super().suspend()
        ctx.metadata["task_index"] = self.current_task_index
        ctx.metadata["total_tasks"] = len(self.waypoints)
        return ctx

    async def resume(self, ctx: TaskContext) -> None:
        """Resume - rebuild task sequence and skip to where we were

        This is the key property: patterns are fully deterministic from config,
        so we can safely rebuild and skip without any global state.
        """
        task_index = ctx.metadata.get("task_index", 0)

        print(f"[PatternThread] Resuming - rebuilding task sequence")

        # Rebuild the entire sequence (deterministic, same as startup)
        self.build_task_sequence()

        # Skip to the task we were on
        print(f"[PatternThread] Skipping {task_index} tasks to resume")
        for _ in range(task_index):
            if self.task_queue:
                self.task_queue.popleft()

        self.current_task_index = task_index

        await super().resume(ctx)

    async def step(self, ctx) -> bool:
        """Execute one step of the pattern sequence"""
        if not self.current_task:
            return True

        # Execute the task step
        status = self.current_task.step(ctx)

        if status == TaskStatus.SUCCESS or status == TaskStatus.FAILED:
            # Task completed, move to next
            self.current_task.exit(ctx, status)
            await self._advance_to_next_task()
            self.current_task_index += 1

        return self.current_task is None
