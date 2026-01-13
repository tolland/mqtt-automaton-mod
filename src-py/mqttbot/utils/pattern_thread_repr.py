"""Rich representation for PatternThread - visual task sequence"""

from typing import Optional

from rich.console import Console
from rich.tree import Tree

from mqttbot.core.patterns.pattern_thread import PatternThread


def render_pattern_thread(thread: PatternThread, console: Optional[Console] = None) -> None:
    """
    Render PatternThread task sequence as a rich tree.

    Shows the complete expanded task sequence in a readable hierarchy.

    Example output:

    PatternThread: canes_farming_1 (NORMAL)
    ├── Waypoint 1: (100, 64, 100)
    │   ├── GotoTask → (100, 64, 100)
    │   ├── Pattern: row_01
    │   │   ├── GotoTask → (100, 64, 95)
    │   │   ├── GotoTask → (100, 64, 85)
    │   │   ├── DwellTask 2.0s
    │   │   └── GotoTask → (100, 64, 90)
    │   └── Pattern: row_02
    │       ├── GotoTask → (105, 64, 90)
    │       ├── GotoTask → (115, 64, 90)
    │       └── GotoTask → (100, 64, 90)
    └── Waypoint 2: (150, 64, 100)
        ├── GotoTask → (150, 64, 100)
        └── Pattern: simple
            └── GotoTask → (150, 64, 110)
    """
    if console is None:
        console = Console()

    # Root node
    root = Tree(
        f"[bold cyan]PatternThread[/bold cyan]: {thread.thread_id} "
        f"([yellow]{thread.priority.name}[/yellow]) "
        f"– {len(thread.task_queue)} tasks"
    )

    # Group tasks by waypoint
    current_waypoint_idx = 0
    current_pattern = None
    pattern_node = None
    waypoint_idx = 0
    task_idx = 0

    tasks = list(thread.task_queue)

    for task_num, task in enumerate(tasks):
        if isinstance(task, GotoTask):
            # Check if this is a waypoint goto (starts with a waypoint goto)
            waypoint = (
                thread.waypoints[waypoint_idx] if waypoint_idx < len(thread.waypoints) else None
            )

            if waypoint and task.target == (waypoint["x"], waypoint["y"], waypoint["z"]):
                # This is a waypoint goto
                wp_label = (
                    f"[bold magenta]Waypoint {waypoint_idx + 1}[/bold magenta]: "
                    f"({waypoint['x']}, {waypoint['y']}, {waypoint['z']})"
                )
                waypoint_node = root.add(wp_label)

                # Add the waypoint goto task
                target_str = f"({task.target[0]}, {task.target[1]}, {task.target[2]})"
                waypoint_node.add(f"[green]GotoTask[/green] → [cyan]{target_str}[/cyan]")

                current_pattern = None
                waypoint_idx += 1
            else:
                # This is a pattern goto
                target_str = f"({task.target[0]}, {task.target[1]}, {task.target[2]})"
                waypoint_node.add(f"[green]GotoTask[/green] → [cyan]{target_str}[/cyan]")

        elif isinstance(task, DwellTask):
            # Dwell task
            waypoint_node.add(f"[blue]DwellTask[/blue] [yellow]{task.duration}s[/yellow]")

    console.print(root)


def format_task_sequence_summary(thread: PatternThread) -> str:
    """
    Format a text summary of the task sequence.

    Returns a multi-line string showing the sequence.
    """
    tasks = list(thread.task_queue)
    lines = [
        f"PatternThread: {thread.thread_id} ({thread.priority.name})",
        f"Total tasks: {len(tasks)}",
        "",
        "Task sequence:",
    ]

    for i, task in enumerate(tasks, 1):
        if isinstance(task, GotoTask):
            target_str = f"({task.target[0]}, {task.target[1]}, {task.target[2]})"
            lines.append(f"  {i:2d}. GotoTask → {target_str}")
        elif isinstance(task, DwellTask):
            lines.append(f"  {i:2d}. DwellTask {task.duration}s")
        else:
            lines.append(f"  {i:2d}. {type(task).__name__}")

    return "\n".join(lines)


# Example usage in ModularBotClient:
"""
def _create_thread_from_config(self, config: ThreadConfig) -> TaskThread:
    '''Create a PatternThread from config and display it'''
    
    patterns = self.threads_config.get("patterns", {})
    waypoint_dicts = [...]
    
    thread = PatternThread(
        thread_id=config.thread_id,
        priority=config.priority,
        waypoints=waypoint_dicts,
        patterns=patterns,
    )
    
    thread.build_task_sequence()
    
    # Display the task sequence
    from rich.console import Console
    console = Console()
    console.print()
    render_pattern_thread(thread, console)
    console.print()
    
    return thread
"""
