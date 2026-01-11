"""Pattern expansion - converts relative coordinates to absolute"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatternStep:
    """A single step in a pattern"""
    type: str  # "goto" or "dwell"
    relative_coords: Optional[tuple[int, int, int]] = None  # For goto steps
    dwell_seconds: Optional[float] = None  # For dwell steps


class PatternExpander:
    """Expands relative pattern coordinates into absolute ones"""

    @staticmethod
    def parse_pattern_step(step_def: str | dict) -> Optional[PatternStep]:
        """Parse a pattern step definition

        Examples:
            "~ ~ ~-5"  → relative(0, 0, -5)
            "~5 ~ ~"   → relative(5, 0, 0)
            {"type": "dwell", "period": "4s"}  → dwell
        """
        if isinstance(step_def, dict):
            if step_def.get("type") == "dwell":
                return PatternStep(
                    type="dwell",
                    dwell_seconds=PatternExpander._parse_dwell(step_def.get("period", "1s"))
                )
            return None

        if isinstance(step_def, str):
            # Parse "~5 ~-3 ~10" style coords
            tokens = step_def.split()
            if len(tokens) != 3:
                raise ValueError(f"Invalid pattern step: {step_def}")

            dx = PatternExpander._parse_axis(tokens[0])
            dy = PatternExpander._parse_axis(tokens[1])
            dz = PatternExpander._parse_axis(tokens[2])

            return PatternStep(
                type="goto",
                relative_coords=(dx, dy, dz)
            )

        return None

    @staticmethod
    def _parse_axis(token: str) -> int:
        """Parse a single axis like '~', '~5', '~-3', '0'"""
        token = token.strip()
        if token in ("~", "~0"):
            return 0
        if token.startswith("~"):
            return int(token[1:]) if token[1:] else 0
        return int(token)

    @staticmethod
    def _parse_dwell(period_str: str) -> float:
        """Parse dwell period like '4s', '500ms'"""
        period_str = period_str.strip().lower()
        if period_str.endswith("ms"):
            return float(period_str[:-2]) / 1000.0
        elif period_str.endswith("s"):
            return float(period_str[:-1])
        return float(period_str)

    @staticmethod
    def expand_pattern(
            pattern_steps: list[str | dict],
            base_position: tuple[int, int, int]
    ) -> list[tuple[str, tuple[int, int, int] | float]]:
        """Expand a pattern into absolute coordinates

        Args:
            pattern_steps: List of pattern step definitions (relative coords or dwell)
            base_position: The starting waypoint (absolute coords)

        Returns:
            List of (task_type, params) tuples
                ("goto", (x, y, z))
                ("dwell", seconds)

        Example:
            >>> expander = PatternExpander()
            >>> pattern = ["~ ~ ~-5", "~ ~ ~-10", {"type": "dwell", "period": "2s"}]
            >>> result = expander.expand_pattern(pattern, (100, 64, 100))
            >>> result
            [
                ("goto", (100, 64, 95)),
                ("goto", (100, 64, 85)),
                ("dwell", 2.0)
            ]
        """
        tasks = []
        current_pos = base_position

        for step_def in pattern_steps:
            step = PatternExpander.parse_pattern_step(step_def)
            if not step:
                continue

            if step.type == "goto":
                dx, dy, dz = step.relative_coords
                absolute = (
                    current_pos[0] + dx,
                    current_pos[1] + dy,
                    current_pos[2] + dz
                )
                tasks.append(("goto", absolute))
                current_pos = absolute

            elif step.type == "dwell":
                tasks.append(("dwell", step.dwell_seconds))

        return tasks
