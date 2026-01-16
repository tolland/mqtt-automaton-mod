from typing import Optional, Callable, Awaitable, Any, Generator

from rich.tree import Tree

from mqttbot.core.context import Context
from mqttbot.core.tasks.dwell_task import DwellTask
from mqttbot.core.tasks.goto_task import GotoTask
from mqttbot.core.tasks.task_priority import TaskPriority, TaskStatus
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.tasks.task import TaskFactory, Task, TaskCompiler
from mqttbot.core.patterns.patterns_config_parser import PatternsConfigParser

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
        patterns: PatternsConfig | dict,
        on_suspend: Optional[Callable[["TaskThread"], Awaitable[None]]] = None,
        on_resume: Optional[Callable[["TaskThread", Context], Awaitable[None]]] = None,
    ) -> None:
        """Initialize a pattern-based thread
        """
        super().__init__(thread_id, priority, on_suspend, on_resume)

        self.waypoints = waypoints

        # Normalize patterns input: accept raw dicts (as tests provide) or a
        # PatternsConfig instance produced by PatternsConfigParser
        if isinstance(patterns, PatternsConfig):
            self.patterns_config = patterns
        else:
            # If tests passed a dict in the old shape, parse into PatternsConfig
            # PatternsConfigParser expects the top-level YAML shape
            # Support both shapes: either {'patterns': {...}} or {'name': [...]} directly
            if isinstance(patterns, dict) and "patterns" not in patterns:
                patterns_input = {"patterns": patterns}
            else:
                patterns_input = patterns if isinstance(patterns, dict) else {}
            self.patterns_config = PatternsConfigParser.from_yaml(patterns_input)

        # Backwards-compatible convenience attribute used by older code/tests
        # that expect a dictionary-like or iterable of patterns.
        self.patterns = self.patterns_config

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
        """Build the full task sequence from waypoints and patterns
        """
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



    async def suspend(self) -> None:
        """Suspend - save waypoint and task index for resumption"""
        print(f"[PatternThread] Suspending at task index {self.current_task_index}")
        await super().suspend()
        if self.current_task:
            self.task_queue.appendleft(self.current_task)
            self.current_task.status = TaskStatus.READY
            self.current_task = None


    async def resume(self, ctx: Context) -> None:
        """Resume - rebuild task sequence and skip to where we were

        This is the key property: patterns are fully deterministic from config,
        so we can safely rebuild and skip without any global state.
        """

        print(f"[PatternThread] Resuming - rebuilding task sequence")

        # # Rebuild the entire sequence (deterministic, same as startup)
        # self.build_task_sequence()
        #
        # # Skip to the task we were on
        # print(f"[PatternThread] Skipping {task_index} tasks to resume")
        # for _ in range(task_index):
        #     if self.task_queue:
        #         self.task_queue.popleft()

        self.current_task_index = 0

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
                waypoint = self.waypoints[waypoint_idx] if waypoint_idx < len(self.waypoints) else None

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
