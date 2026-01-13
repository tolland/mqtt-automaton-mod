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
