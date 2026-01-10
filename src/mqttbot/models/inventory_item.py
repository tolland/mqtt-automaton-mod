from dataclasses import dataclass


# Inventory state module
@dataclass
class InventoryItem:
    name: str
    count: int
    slot: int
