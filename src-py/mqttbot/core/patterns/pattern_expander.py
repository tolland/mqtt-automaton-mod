from typing import Optional

from mqttbot.model.patterns.pattern import PatternStep
from mqttbot.model.patterns.step import StepBase, TaskStep

"""Pattern expansion - converts relative coordinates to absolute"""


class PatternExpander:
    """Expands relative pattern coordinates into absolute ones"""

    @staticmethod
    def parse_pattern_step2(step_def: str | dict) -> Optional[StepBase]:
        """Parse a pattern step definition into either  relative coords or a concrete task step
        """
        if isinstance(step_def, dict):
            return TaskStep(**step_def)

        if isinstance(step_def, str):
            return PatternStep.from_string(step_def)

        raise ValueError(f"Invalid pattern step definition: {step_def}")
