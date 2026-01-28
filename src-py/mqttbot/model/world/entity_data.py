"""
Entity data models for world state.
Raw entity data from mod scans.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EntityData:
    """Raw entity data from mod scan."""

    type: str  # e.g. "minecraft:item_frame"
    uuid: str
    pos: tuple[float, float, float]
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "EntityData":
        """Deserialize from JSON/dict"""
        return cls(
            type=data["type"],
            uuid=data["uuid"],
            pos=tuple(data["pos"]),
            extra=data.get("extra", {}),
        )

    def to_dict(self) -> dict:
        """Serialize to dict for JSON"""
        return {
            "type": self.type,
            "uuid": self.uuid,
            "pos": list(self.pos),
            "extra": self.extra,
        }


@dataclass
class ItemFrameData:
    """
    Interpreted item frame data.
    Extracted from EntityData with type=minecraft:item_frame
    """

    uuid: str
    pos: tuple[float, float, float]
    facing: str  # "north", "south", "east", "west", "up", "down"
    rotation: int  # 0-7
    item_id: Optional[str] = None  # e.g. "minecraft:sugar_cane"
    item_count: int = 0

    @classmethod
    def from_entity_data(cls, entity: EntityData) -> Optional["ItemFrameData"]:
        """Extract item frame data from generic entity data"""
        if entity.type != "minecraft:item_frame":
            return None

        return cls(
            uuid=entity.uuid,
            pos=entity.pos,
            facing=entity.extra.get("facing", "north"),
            rotation=entity.extra.get("rotation", 0),
            item_id=entity.extra.get("item_id"),
            item_count=entity.extra.get("item_count", 0),
        )

    def attached_block_pos(self) -> tuple[int, int, int]:
        """
        Calculate the position of the block this frame is attached to.
        Item frames attach to the block behind them (opposite of facing direction).
        """
        x, y, z = self.pos

        # Offset based on facing direction (opposite direction)
        offsets = {
            "north": (0, 0, 1),  # Frame facing north, attached to block to south
            "south": (0, 0, -1),
            "east": (-1, 0, 0),
            "west": (1, 0, 0),
            "up": (0, -1, 0),
            "down": (0, 1, 0),
        }

        offset = offsets.get(self.facing, (0, 0, 0))
        return (int(x + offset[0]), int(y + offset[1]), int(z + offset[2]))
