from dataclasses import dataclass
from dataclasses import dataclass, field
from enum import Enum, auto


class BaritoneStatus(Enum):
    IDLE = auto()
    PATHING = auto()
    PAUSED = auto()
    FAILED = auto()
    SUCCESS = auto()

@dataclass
class BaritoneSettings:
    allow_break: bool = True
    allow_break_anyway: list[str] = field(default_factory=list)

@dataclass
class BaritoneState:
    status: BaritoneStatus = BaritoneStatus.IDLE
    suspended: bool = False
    settings: BaritoneSettings = field(default_factory=BaritoneSettings)
