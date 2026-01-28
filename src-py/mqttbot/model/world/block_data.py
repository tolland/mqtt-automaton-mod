"""
Block data models for world state.
Raw block data from mod scans.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BlockData:
    """Raw block data from mod scan."""

    type: str  # e.g. "minecraft:chest"
    pos: tuple[int, int, int]
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "BlockData":
        """Deserialize from JSON/dict"""
        return cls(
            type=data["type"], pos=tuple(data["pos"]), extra=data.get("extra", {})
        )

    def to_dict(self) -> dict:
        """Serialize to dict for JSON"""
        return {"type": self.type, "pos": list(self.pos), "extra": self.extra}


@dataclass
class ChestLabel:
    """
    Label for a chest/container.
    Defines what items should be stored in this container.
    """

    items: list[str]  # List of item IDs, e.g. ["minecraft:sugar_cane", "minecraft:bamboo"]
    mode: str = "inclusive"  # "inclusive" or "exclusive"
    source: str = "item_frame"  # "item_frame" or "sign"

    def to_dict(self) -> dict:
        return {"items": self.items, "mode": self.mode, "source": self.source}

    @classmethod
    def from_dict(cls, data: dict) -> "ChestLabel":
        return cls(
            items=data["items"],
            mode=data.get("mode", "inclusive"),
            source=data.get("source", "item_frame"),
        )


@dataclass
class ContainerInfo:
    """
    Container block with interpreted metadata.
    Combines raw block data with labels and other interpreted info.
    """

    position: tuple[int, int, int]
    type: str  # "minecraft:chest", "minecraft:barrel", etc.
    label: Optional[ChestLabel] = None
    last_seen: float = 0.0
    dimension: str = "minecraft:overworld"
    slot_count: int = 27  # Default chest size

    def to_dict(self) -> dict:
        return {
            "position": list(self.position),
            "type": self.type,
            "label": self.label.to_dict() if self.label else None,
            "last_seen": self.last_seen,
            "dimension": self.dimension,
            "slot_count": self.slot_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContainerInfo":
        label_data = data.get("label")
        return cls(
            position=tuple(data["position"]),
            type=data["type"],
            label=ChestLabel.from_dict(label_data) if label_data else None,
            last_seen=data.get("last_seen", 0.0),
            dimension=data.get("dimension", "minecraft:overworld"),
            slot_count=data.get("slot_count", 27),
        )


@dataclass
class SignData:
    """Sign block with text."""

    position: tuple[int, int, int]
    lines: list[str]  # 4 lines of text

    @classmethod
    def from_block_data(cls, block: BlockData) -> Optional["SignData"]:
        """Extract sign data from generic block data"""
        if "sign" not in block.type:
            return None

        lines = block.extra.get("lines", [])
        return cls(position=block.pos, lines=lines)

    def is_sort_label(self) -> bool:
        """Check if this sign is a [SORT] label"""
        return len(self.lines) > 0 and "[SORT]" in self.lines[0]

    def extract_item_ids(self) -> list[str]:
        """Extract item IDs from sign lines (lines 1-3)"""
        items = []
        for line in self.lines[1:4]:
            if line and line.strip():
                items.append(line.strip())
        return items
