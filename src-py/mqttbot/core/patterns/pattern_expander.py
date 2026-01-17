from typing import Optional, List, Tuple

from mqttbot.model.patterns.pattern import PatternStep, Coords, CoordAxis
from mqttbot.model.patterns.step import StepBase, TaskStep

"""Pattern expansion - converts relative coordinates to absolute"""


class PatternExpander:
    """Expands relative pattern coordinates into absolute ones"""

    @staticmethod
    def _parse_axis(token: str) -> int:
        """Parse a single axis token like '~', '~5', '0', '100', '~+5', '~-2'"""
        if token.startswith("~"):
            body = token[1:]
            if body == "":
                return 0
            # allow explicit + sign
            return int(body.replace("+", ""))
        return int(token)

    @staticmethod
    def parse_pattern_step(step_def: str | dict) -> Optional[StepBase]:
        """Parse a pattern step definition into either relative coords or a concrete task step"""
        if isinstance(step_def, dict):
            # Support dwell shorthands either at top level or inside params
            t = step_def.get("type")
            params = step_def.get("params", {})
            if t == "dwell" or (not t and "period" in step_def) or ("period" in params):
                period = step_def.get("period") or params.get("period")
                # Parse period like '4s' or '500ms'
                if isinstance(period, str) and period.endswith("ms"):
                    seconds = float(period[:-2]) / 1000.0
                elif isinstance(period, str) and period.endswith("s"):
                    seconds = float(period[:-1])
                else:
                    # fallback assume seconds as float/int
                    seconds = float(period)
                # Represent dwell as a standalone TaskStep (handled by DwellTask)
                return TaskStep(type="dwell", params={"period": seconds})

            # Otherwise treat as a generic TaskStep (may raise if keys mismatch)
            return TaskStep(**step_def)

        if isinstance(step_def, str):
            return PatternStep.from_string(step_def)

        raise ValueError(f"Invalid pattern step definition: {step_def}")

    @staticmethod
    def expand_pattern(pattern: List[str | dict], anchor: Tuple[float, float, float]):
        """Expand a raw pattern list (strings and dicts) into tuples of ('goto', (x,y,z)) or ('dwell', seconds)"""
        result = []
        cx, cy, cz = anchor
        for step in pattern:
            if isinstance(step, str):
                tokens = step.split()
                if len(tokens) != 3:
                    raise ValueError(f"Invalid pattern step string: {step}")
                dx = PatternExpander._parse_axis(tokens[0])
                dy = PatternExpander._parse_axis(tokens[1])
                dz = PatternExpander._parse_axis(tokens[2])

                # tokens starting with ~ are relative offsets
                def resolve(tok, d, cur):
                    if tok.startswith("~"):
                        return cur + d
                    return d

                nx = resolve(tokens[0], dx, cx)
                ny = resolve(tokens[1], dy, cy)
                nz = resolve(tokens[2], dz, cz)
                result.append(("goto", (nx, ny, nz)))
                cx, cy, cz = nx, ny, nz
            elif isinstance(step, dict):
                t = step.get("type")
                params = step.get("params", {})
                period = step.get("period") or params.get("period")
                if t == "dwell" or (period is not None):
                    if isinstance(period, str) and period.endswith("ms"):
                        seconds = float(period[:-2]) / 1000.0
                    elif isinstance(period, str) and period.endswith("s"):
                        seconds = float(period[:-1])
                    else:
                        seconds = float(period)
                    result.append(("dwell", seconds))
                else:
                    # Unknown dict step - attempt to parse as TaskStep
                    ts = TaskStep(**step)
                    result.append((ts.type, ts.params))
            else:
                raise ValueError(f"Unsupported step type: {step}")
        return result
