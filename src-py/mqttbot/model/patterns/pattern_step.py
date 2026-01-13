
from dataclasses import dataclass
from typing import Optional
@dataclass
class PatternStep:
    """A single step in a pattern"""

    type: str  # "goto" or "dwell"
    relative_coords: Optional[tuple[int, int, int]] = None  # For goto steps
    dwell_seconds: Optional[float] = None  # For dwell steps
