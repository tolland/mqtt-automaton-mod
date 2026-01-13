from typing import Any

from mqttbot.core.patterns.pattern_expander import PatternExpander

from mqttbot.model.patterns.pattern_config import PatternConfig
from mqttbot.model.patterns.patterns_config import PatternsConfig


class PatternsConfigParser:
    """Parse YAML config and build pattern configs"""

    @staticmethod
    def from_yaml(yaml_data: dict[str, Any]) -> PatternsConfig:
        """
        Parse YAML config and return PatternConfig object.
        ```
        """
        patterns = []
        patterns_data = yaml_data.get("patterns", {})

        for pattern_id, pattern_data in patterns_data.items():
            step_defs = []
            for step_def in pattern_data.get("steps", []):
                step_defs.append(PatternExpander.parse_pattern_step2(step_def))

            # Build thread config
            pattern_config = PatternConfig(
                pattern_id=pattern_id,
                steps=step_defs,
                on_pattern_start_tasks=pattern_data.get("on_pattern_start", []),
                on_pattern_end_tasks=pattern_data.get("on_pattern_end", []),
                metadata=pattern_data.get("metadata", {}),
            )
            patterns.append(pattern_config)

        return PatternsConfig(
            patterns=patterns,
            on_patterns_start_tasks=yaml_data.get("on_patterns_start", []),
            on_patterns_end_tasks=yaml_data.get("on_patterns_end", []),
            metadata=yaml_data.get("metadata", {}),
        )
