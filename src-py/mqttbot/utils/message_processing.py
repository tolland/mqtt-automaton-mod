def _get_current_position(self) -> tuple[float, float, float]:
    """Get current bot position"""
    return self._last_position or (0.0, 0.0, 0.0)
