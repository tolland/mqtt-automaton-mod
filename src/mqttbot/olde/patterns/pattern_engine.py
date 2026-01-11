"""
Pattern execution engine for reusable movement and action patterns
"""

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Union, Callable


@dataclass
class PatternStep:
    """Represents a single step in a pattern"""

    step_type: str  # "move", "dwell", "action", "condition"
    data: Dict[str, Any]
    step_id: str = None

    def __post_init__(self):
        if self.step_id is None:
            self.step_id = str(uuid.uuid4())[:8]


class PatternEngine:
    """
    Executes patterns of movements and actions.

    Patterns can contain:
    - Movement steps: "~ ~ ~2" (relative coordinates)
    - Dwell steps: {"type": "dwell", "period": "3s"}
    - Action steps: {"type": "action", "action": "harvest"}
    - Condition steps: {"type": "condition", "check": "inventory_full"}
    """

    def __init__(
            self,
            message_sender: Callable[[str], None],
            position_tracker: Callable[[], Tuple[float, float, float]],
    ):
        """
        Initialize pattern engine.

        Args:
            message_sender: Function to send MQTT messages
            position_tracker: Function to get current bot position
        """
        self.message_sender = message_sender
        self.position_tracker = position_tracker
        self.current_position = (0.0, 0.0, 0.0)
        self.correlation_id = None
        self.arrival_event = threading.Event()
        self.arrival_timeout = 60  # Default timeout in seconds
        self.cancelled = False  # Flag to cancel ongoing pattern execution

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for this pattern execution"""
        self.correlation_id = correlation_id

    def signal_arrival(self) -> None:
        """Signal that the bot has arrived at the target location"""
        self.arrival_event.set()

    def cancel(self) -> None:
        """Cancel the currently executing pattern"""
        print(f"[pattern] Cancelling pattern execution")
        self.cancelled = True
        self.arrival_event.set()  # Unblock any waiting arrivals

    def reset(self) -> None:
        """Reset cancellation flag for new pattern execution"""
        self.cancelled = False

    def wait_for_arrival(self, timeout: int = None) -> bool:
        """
        Wait for the bot to arrive at the target location.

        Args:
            timeout: Timeout in seconds (uses self.arrival_timeout if not specified)

        Returns:
            bool: True if arrival was signaled, False if timeout or cancelled
        """
        if timeout is None:
            timeout = self.arrival_timeout

        self.arrival_event.clear()  # Clear before waiting
        arrived = self.arrival_event.wait(timeout=timeout)

        # If cancelled, return False
        if self.cancelled:
            print(f"[pattern] Arrival wait cancelled")
            return False

        return arrived

    def parse_dwell_period(self, period_str: str) -> float:
        """Parse dwell period string like '3s', '1.5s', '500ms' into seconds"""
        period_str = period_str.strip().lower()
        if period_str.endswith("ms"):
            return float(period_str[:-2]) / 1000.0
        elif period_str.endswith("s"):
            return float(period_str[:-1])
        else:
            # Assume seconds if no unit specified
            return float(period_str)

    def execute_dwell(self, dwell_config: Dict[str, Any]) -> bool:
        """Execute a dwell/pause step"""
        period_str = dwell_config.get("period", "1s")
        try:
            period_seconds = self.parse_dwell_period(period_str)
            print(f"[pattern] Dwell: pausing for {period_seconds}s ({period_str})")
            time.sleep(period_seconds)
            print(f"[pattern] Dwell completed")
            return True
        except (ValueError, TypeError) as e:
            print(f"[pattern] Error parsing dwell period '{period_str}': {e}")
            return False



    def execute_action(self, action_config: Dict[str, Any]) -> bool:
        """Execute an action step"""
        action_type = action_config.get("action", "unknown")
        params = action_config.get("params", {})

        print(f"[pattern] Action: {action_type} with params {params}")

        # Create appropriate message based on action type
        if action_type == "harvest":
            message_data = {
                "service": "wurst",
                "method": "command",
                "correlationId": self.correlation_id,
                "params": {"command": "t", "args": ["autofarm", "on"]},
            }
        elif action_type == "stop_harvest":
            message_data = {
                "service": "wurst",
                "method": "command",
                "correlationId": self.correlation_id,
                "params": {"command": "t", "args": ["autofarm", "off"]},
            }
        else:
            print(f"[pattern] Unknown action type: {action_type}")
            return False

        cmd = str(message_data).replace("'", '"')
        self.message_sender(cmd)
        return True

    def check_condition(self, condition_config: Dict[str, Any]) -> bool:
        """Check a condition step"""
        condition_type = condition_config.get("check", "unknown")

        print(f"[pattern] Condition: checking {condition_type}")

        # For now, just return True - this would be expanded based on needs
        if condition_type == "inventory_full":
            # Would check actual inventory status
            return False  # Placeholder
        elif condition_type == "night_time":
            # Would check actual time
            return False  # Placeholder

        return True

    def execute_pattern(
            self,
            pattern_name: str,
            pattern_steps: List[Union[str, Dict[str, Any]]],
            start_position: Tuple[float, float, float] = None,
    ) -> bool:
        """
        Execute a complete pattern.

        Args:
            pattern_name: Name of the pattern for logging
            pattern_steps: List of pattern steps (strings or dicts)
            start_position: Starting position for the pattern

        Returns:
            bool: True if pattern completed successfully
        """
        # Reset cancellation flag at start of pattern
        self.reset()

        if start_position is None:
            start_position = self.position_tracker()

        print(
            f"[pattern] Executing pattern '{pattern_name}' with {len(pattern_steps)} steps"
        )
        current_pos = start_position

        for step_idx, step in enumerate(pattern_steps, 1):
            # Check for cancellation
            if self.cancelled:
                print(f"[pattern] Pattern '{pattern_name}' cancelled at step {step_idx}")
                return False

            print(f"[pattern] Step {step_idx}/{len(pattern_steps)}: {step}")

            # Handle different step types
            if isinstance(step, dict):
                step_type = step.get("type", "unknown")

                if step_type == "dwell":
                    if not self.execute_dwell(step):
                        print(f"[pattern] Dwell step {step_idx} failed")
                        return False
                elif step_type == "action":
                    if not self.execute_action(step):
                        print(f"[pattern] Action step {step_idx} failed")
                        return False
                elif step_type == "condition":
                    if not self.check_condition(step):
                        print(f"[pattern] Condition step {step_idx} failed")
                        return False
                else:
                    print(f"[pattern] Unknown step type: {step_type}")
                    return False

            elif isinstance(step, str):
                # Movement step
                try:
                    target_coords = self.resolve_coordinates(step, current_pos)
                    if not self.execute_movement(target_coords):
                        print(f"[pattern] Movement step {step_idx} failed")
                        return False
                    current_pos = (
                        float(target_coords[0]),
                        float(target_coords[1]),
                        float(target_coords[2]),
                    )
                except ValueError as e:
                    print(f"[pattern] Error in movement step {step_idx}: {e}")
                    return False
            else:
                print(f"[pattern] Invalid step type: {type(step)}")
                return False

        print(f"[pattern] Pattern '{pattern_name}' completed successfully")
        return True
