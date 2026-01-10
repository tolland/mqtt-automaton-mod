from dataclasses import dataclass


# Position/entity state module
@dataclass
class EntityState:
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
