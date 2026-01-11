from dataclasses import dataclass


@dataclass
class PositionState:
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
