from dataclasses import dataclass, field

from mqttbot.core.models.inventory_item import InventoryItem


@dataclass
class InventoryState:
    main_items: dict[int, InventoryItem] = field(default_factory=dict)
    open: bool = False
    current_container: str = "main"
