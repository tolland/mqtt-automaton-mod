from typing import Any

from mqttbot.core.patterns.pattern_expander import PatternExpander
from mqttbot.model.patterns.pattern import Pattern
from mqttbot.model.patterns.patterns_config import PatternsConfig


class PatternsConfigParser:
    """
    Parse YAML config and build pattern configs
    on_patterns_start/end are a list of tasks that are inserted to run after
    the goto of the waypoint and before each waypoint respectively.
    1. on_patterns_start - runs once before all patterns at a waypoint
    2. on_patterns_end - runs once after all patterns at a waypoint
    3. on_pattern_start - runs before each individual pattern
    4. on_pattern_end - runs after each individual pattern

    currently on_patterns_start/end is a top level key
    @TODO move under the patterns key, but then need to move the list of patterns
    under a dedicated patterns list key as well to avoid confusion.
    """

    @staticmethod
    def from_yaml(yaml_data: dict[str, Any]) -> PatternsConfig:
        """
        Parse YAML config and return PatternConfig object.
        ```
        """
        patterns_data = yaml_data.get("patterns", {})
        patterns = PatternsConfigParser.from_pattern_yaml(patterns_data)
        on_failed = yaml_data.get("on_failed", [])
        on_patterns_start = yaml_data.get("on_patterns_start", [])
        on_patterns_end = yaml_data.get("on_patterns_end", [])
        on_pattern_start = yaml_data.get("on_pattern_start", [])
        on_pattern_end = yaml_data.get("on_pattern_end", [])
        return PatternsConfig(
            patterns=patterns,
            on_pattern_start_tasks=[PatternExpander.parse_pattern_step(x) for x in on_pattern_start],
            on_pattern_end_tasks=[PatternExpander.parse_pattern_step(x) for x in on_pattern_end],
            on_patterns_start_tasks=[PatternExpander.parse_pattern_step(x) for x in on_patterns_start],
            on_patterns_end_tasks=[PatternExpander.parse_pattern_step(x) for x in on_patterns_end],
            on_failed_tasks=[PatternExpander.parse_pattern_step(x) for x in on_failed],
            metadata=yaml_data.get("metadata", {}),
        )

    @staticmethod
    def from_pattern_yaml(patterns_data: dict[str, Any]) -> list[Pattern]:
        patterns = []
        for pattern_id, pattern_data in patterns_data.items():
            step_defs = []
            steps_list = pattern_data.get("steps", [])
            on_start = pattern_data.get("on_pattern_start", [])
            on_end = pattern_data.get("on_pattern_end", [])
            metadata = pattern_data.get("metadata", {})
            for step_def in steps_list:
                step_defs.append(PatternExpander.parse_pattern_step(step_def))

            # Build thread config
            pattern_config = Pattern(
                pattern_id=pattern_id,
                steps=step_defs,
                on_pattern_start_tasks=[PatternExpander.parse_pattern_step(x) for x in on_start],
                on_pattern_end_tasks=[PatternExpander.parse_pattern_step(x) for x in on_end],
                metadata=metadata,
            )
            patterns.append(pattern_config)
        return patterns
