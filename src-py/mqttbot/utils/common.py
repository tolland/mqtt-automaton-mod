from typing import Any

# @staticmethod
# def _parse_dwell(period_str: str) -> float:
#     """Parse dwell period like '4s', '500ms'"""
#     period_str = period_str.strip().lower()
#     if period_str.endswith("ms"):
#         return float(period_str[:-2]) / 1000.0
#     elif period_str.endswith("s"):
#         return float(period_str[:-1])
#     return float(period_str)


def parse_dwell(dwell_spec: Any) -> float:
    """Parse dwell period (e.g., '5s', '500ms', or float)"""
    if isinstance(dwell_spec, (int, float)):
        return float(dwell_spec)

    if isinstance(dwell_spec, str):
        dwell_spec = dwell_spec.strip().lower()
        if dwell_spec.endswith("ms"):
            return float(dwell_spec[:-2]) / 1000.0
        elif dwell_spec.endswith("s"):
            return float(dwell_spec[:-1])
        else:
            return float(dwell_spec)

    return 0.0


def resolve_coordinates(step: str, base_xyz: tuple[float, float, float]) -> tuple[int, int, int]:
    """
    Parse a pattern step "a b c" → absolute target from current (x,y,z)

    Args:
        step: Coordinate string like "~ ~ ~2" or "100 64 -200"
        base_xyz: Base coordinates to resolve relative to

    Returns:
        Tuple of absolute coordinates (x, y, z)
    """
    tok = step.split()
    if len(tok) != 3:
        raise ValueError(f"pattern step must have 3 tokens: {step}")
    bx, by, bz = base_xyz

    def resolve_axis(t: str, base: float) -> float:
        t = t.strip()
        if t == "~" or t == "~0" or t == "0":
            return base
        if t.startswith("~"):
            # relative delta (may be like "~-5" or "~10")
            delta = float(t[1:]) if t[1:] else 0.0
            return base + delta
        # else absolute world coord
        return float(t)

    ax = resolve_axis(tok[0], bx)
    ay = resolve_axis(tok[1], by)
    az = resolve_axis(tok[2], bz)
    # use block coords (Baritone #goto typically takes ints)
    return int(round(ax)), int(round(ay)), int(round(az))
