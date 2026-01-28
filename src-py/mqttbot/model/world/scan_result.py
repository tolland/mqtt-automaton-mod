"""
Scan result models.
Represents the output from mod scan operations.
"""

from dataclasses import dataclass, field
from typing import Literal

from mqttbot.model.world.block_data import BlockData
from mqttbot.model.world.entity_data import EntityData


@dataclass
class ScanResult:
    """Result from a mod scan operation."""

    scan_type: Literal["area_scan", "container_scan", "entity_scan"]
    timestamp: float
    center: tuple[float, float, float]
    radius: int

    # World identity (for cache organization)
    server: str  # Server address or world name
    dimension: str  # e.g., "minecraft:overworld", "minecraft:the_nether"
    seed: int = 0  # World seed for disambiguation

    entities: list[EntityData] = field(default_factory=list)
    blocks: list[BlockData] = field(default_factory=list)

    entity_count: int = 0
    block_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "ScanResult":
        """Deserialize from JSON response"""
        entities = [EntityData.from_dict(e) for e in data.get("entities", [])]
        blocks = [BlockData.from_dict(b) for b in data.get("blocks", [])]

        return cls(
            scan_type=data["scan_type"],
            timestamp=data["timestamp"],
            center=tuple(data["center"]),
            radius=data["radius"],
            server=data.get("server", "unknown"),
            dimension=data.get("dimension", "minecraft:overworld"),
            seed=data.get("seed", 0),
            entities=entities,
            blocks=blocks,
            entity_count=data.get("entity_count", len(entities)),
            block_count=data.get("block_count", len(blocks)),
        )

    def to_dict(self) -> dict:
        """Serialize to dict"""
        return {
            "scan_type": self.scan_type,
            "timestamp": self.timestamp,
            "center": list(self.center),
            "radius": self.radius,
            "server": self.server,
            "dimension": self.dimension,
            "seed": self.seed,
            "entities": [e.to_dict() for e in self.entities],
            "blocks": [b.to_dict() for b in self.blocks],
            "entity_count": self.entity_count,
            "block_count": self.block_count,
        }
