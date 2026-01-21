import json
from dataclasses import dataclass
from typing import Optional

from loguru import logger


@dataclass
class Inventory:
    """Python equivalent of the Minecraft Inventory class for representing inventory items."""

    item_id: str
    name: str
    quantity: int
    location: str | None = None
    description: str | None = None

    def to_json(self) -> str:
        """Convert to JSON string matching Java Inventory format."""
        data = {
            "itemId": self.item_id,
            "name": self.name,
            "quantity": self.quantity,
            "location": self.location,
            "description": self.description,
        }
        # Remove None values to keep JSON clean
        return json.dumps({k: v for k, v in data.items() if v is not None})

    @classmethod
    def from_json(cls, json_str: str) -> Optional["Inventory"]:
        """Parse JSON string into an Inventory object."""
        try:
            data = json.loads(json_str)
            return cls(
                item_id=data.get("itemId"),
                name=data.get("name"),
                quantity=data.get("quantity", 0),
                location=data.get("location"),
                description=data.get("description"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse Inventory from JSON: {e}")
            return None
