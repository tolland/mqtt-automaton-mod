from mqttbot.models.inventory_item import InventoryItem
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Callable, Any, Protocol
from abc import ABC, abstractmethod
import json

@dataclass
class InventoryState:
    main_items: dict[int, InventoryItem] = field(default_factory=dict)
    backpack_items: dict[int, InventoryItem] = field(default_factory=dict)
    open: bool = False
    current_container: str = "main"  # "main" or "backpack"
