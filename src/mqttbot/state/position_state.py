
from dataclasses import dataclass, field

from mqttbot.state.entity_state import EntityState


@dataclass
class PositionState:
    player: EntityState
    nearby_entities: dict[str, EntityState] = field(default_factory=dict)
