# Chest/Container Sorting System Design

## Overview

A distributed sorting system where the bot automatically organizes items by:
1. Scanning the environment for labeled chests (via signs)
2. Building a registry of chest locations and their designated contents
3. Identifying "wrong" items in chests
4. Moving items from source chests to their designated destination chests

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Python MQTT Task System                    │
│                                                               │
│  ┌──────────────────┐      ┌─────────────────────────────┐  │
│  │ ChestRegistry    │      │ ChestSortingTask            │  │
│  │                  │      │                             │  │
│  │ - chest_map      │◄─────┤ 1. Scan for chests         │  │
│  │ - item_rules     │      │ 2. Read sign labels        │  │
│  │ - last_scan      │      │ 3. Query chest contents    │  │
│  └──────────────────┘      │ 4. Identify misplaced items│  │
│                            │ 5. Move items to dest      │  │
│                            └─────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │ MQTT ServiceMessages
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    Fabric Mod (Java)                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Container Service (NEW)                              │   │
│  │                                                       │   │
│  │ Methods:                                             │   │
│  │  - scan_nearby_blocks   (uses Baritone/Wurst)      │   │
│  │  - read_sign_text       (read sign contents)        │   │
│  │  - open_container       (interact with chest)       │   │
│  │  - query_container      (get contents)              │   │
│  │  - transfer_items       (move items between invs)   │   │
│  │  - close_container      (close screen)              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Baritone Integration (EXISTING)                      │   │
│  │  - Block search API                                  │   │
│  │  - Pathfinding to locations                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Wurst Integration (EXISTING)                         │   │
│  │  - ChestESP for chest location finding              │   │
│  │  - Block search capabilities                         │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Chest Labeling Mechanism

**Sign Format:**
```
Line 1: [SORT]          (marker to identify sorting chests)
Line 2: minecraft:sugar_cane
Line 3: minecraft:bamboo
Line 4: <optional additional item or metadata>
```

**Alternative Format (for exclusion):**
```
Line 1: [SORT-EXCLUDE]  (chest to ignore during sorting)
```

**Chest Registry Data Structure:**
```python
@dataclass
class ChestLabel:
    """Represents a labeled chest and its sorting rules"""
    position: tuple[int, int, int]  # World coordinates
    items: list[str]                # List of item IDs this chest should contain
    mode: str = "inclusive"         # "inclusive" or "exclusive"
    last_accessed: float = 0.0      # Timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "items": self.items,
            "mode": self.mode,
            "last_accessed": self.last_accessed
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChestLabel":
        return cls(
            position=tuple(data["position"]),
            items=data["items"],
            mode=data.get("mode", "inclusive"),
            last_accessed=data.get("last_accessed", 0.0)
        )

@dataclass
class ChestRegistry:
    """Registry of all known labeled chests"""
    chests: dict[tuple[int, int, int], ChestLabel]  # pos -> label
    item_to_chests: dict[str, list[tuple[int, int, int]]]  # item_id -> positions
    last_full_scan: float = 0.0

    def add_chest(self, label: ChestLabel) -> None:
        """Add or update a chest in the registry"""
        self.chests[label.position] = label
        for item_id in label.items:
            if item_id not in self.item_to_chests:
                self.item_to_chests[item_id] = []
            if label.position not in self.item_to_chests[item_id]:
                self.item_to_chests[item_id].append(label.position)

    def find_destination_for_item(self, item_id: str) -> list[tuple[int, int, int]]:
        """Find all chests that should contain this item"""
        return self.item_to_chests.get(item_id, [])
```

### 2. New Mod Features (Java - Fabric Mod)

#### A. ContainerHandler (`org.limepepper.mqttbot.integrations.container.ContainerHandler`)

**Service Name:** `"container"`

**Methods to Implement:**

##### `scan_nearby_blocks`
```java
/**
 * Scan for nearby blocks of specific types within a radius
 * Uses Baritone's block search or Wurst's ESP features
 *
 * Request params:
 *   - block_types: String[] (e.g., ["minecraft:chest", "minecraft:barrel"])
 *   - radius: int (search radius in blocks)
 *   - include_signs: boolean (also find adjacent signs)
 *
 * Response:
 *   - blocks: List<BlockInfo>
 *     - position: {x, y, z}
 *     - type: String
 *     - has_adjacent_sign: boolean
 */
```

##### `read_sign_text`
```java
/**
 * Read the text content of a sign at a given position
 *
 * Request params:
 *   - position: {x, y, z}
 *
 * Response:
 *   - lines: String[4] (four lines of sign text)
 *   - success: boolean
 */
```

##### `open_container`
```java
/**
 * Open a container (chest, barrel, etc.) at the specified position
 * Bot must be within interaction range (~4 blocks)
 *
 * Request params:
 *   - position: {x, y, z}
 *   - timeout_ms: int (default 5000)
 *
 * Response:
 *   - success: boolean
 *   - container_type: String (e.g., "minecraft:chest")
 *   - slot_count: int (number of slots in container)
 */
```

##### `query_container`
```java
/**
 * Query the contents of the currently open container
 * Extends existing InventoryQueryHandler to support containers
 *
 * Request params:
 *   - (none - uses currently open container)
 *
 * Response:
 *   - container_type: String
 *   - total_slots: int
 *   - items: List<ItemStack>
 *     - slot: int
 *     - item_id: String
 *     - count: int
 *     - nbt: Object (optional)
 *   - empty_slots: int
 */
```

##### `transfer_items`
```java
/**
 * Transfer items between player inventory and open container
 *
 * Request params:
 *   - operation: String ("deposit_all" | "withdraw_all" | "deposit_item" | "withdraw_item")
 *   - item_id: String (for deposit_item/withdraw_item)
 *   - quantity: int (max amount to transfer, -1 for all)
 *   - from_container: boolean (true = container->inventory, false = inventory->container)
 *
 * Response:
 *   - success: boolean
 *   - transferred_count: int
 *   - item_id: String
 */
```

##### `close_container`
```java
/**
 * Close the currently open container screen
 *
 * Response:
 *   - success: boolean
 */
```

#### B. ContainerWatcher (`org.limepepper.mqttbot.watchers.ContainerWatcher`)

**Events to Fire:**
- `ContainerOpenedEvent` - when a container screen opens
- `ContainerClosedEvent` - when a container screen closes
- `ContainerContentChangeEvent` - when container contents change

**State to Track:**
- Currently open container position
- Container type
- Last known contents

#### C. Extensions to Existing Components

**InventoryQueryHandler Enhancement:**
- Detect if a container screen is open (already partially done in InventoryWatcher:48)
- Query container slots in addition to player inventory
- Return both player and container inventory in single response

**BaritoneGotoHandler Enhancement:**
- Add method parameter to specify precision (e.g., for chest interaction, need ~3 block range)
- Current goto likely gets close enough, but may need fine-tuning

### 3. New MQTT Message Types

All messages use the existing `ServiceMessage` protocol with `service: "container"`

#### Scan for Chests
```json
{
  "service": "container",
  "method": "scan_nearby_blocks",
  "request_id": "uuid",
  "params": {
    "block_types": ["minecraft:chest", "minecraft:barrel", "minecraft:trapped_chest"],
    "radius": 64,
    "include_signs": true
  }
}
```

#### Read Sign
```json
{
  "service": "container",
  "method": "read_sign_text",
  "request_id": "uuid",
  "params": {
    "position": {"x": 100, "y": 64, "z": -200}
  }
}
```

#### Open Container
```json
{
  "service": "container",
  "method": "open_container",
  "request_id": "uuid",
  "params": {
    "position": {"x": 100, "y": 64, "z": -200},
    "timeout_ms": 5000
  }
}
```

#### Query Container Contents
```json
{
  "service": "container",
  "method": "query_container",
  "request_id": "uuid",
  "params": {}
}
```

#### Transfer Items
```json
{
  "service": "container",
  "method": "transfer_items",
  "request_id": "uuid",
  "params": {
    "operation": "withdraw_item",
    "item_id": "minecraft:sugar_cane",
    "quantity": 64,
    "from_container": true
  }
}
```

#### Close Container
```json
{
  "service": "container",
  "method": "close_container",
  "request_id": "uuid",
  "params": {}
}
```

### 4. Python Task Implementation

#### ChestScanTask
```python
class ChestScanTask(TaskBase):
    """
    Scan area for labeled chests and update registry

    Steps:
    1. Use Baritone/Wurst to find all chests in radius
    2. For each chest, check for adjacent signs
    3. Read sign text and parse labels
    4. Update ChestRegistry
    """

    def __init__(self, radius: int = 64):
        super().__init__()
        self.radius = radius
        self.found_chests = []
        self.current_chest_idx = 0

    async def enter(self) -> None:
        # Send scan request
        msg = self.create_service_message(
            service="container",
            method="scan_nearby_blocks",
            params={
                "block_types": ["minecraft:chest", "minecraft:barrel"],
                "radius": self.radius,
                "include_signs": True
            }
        )
        await self.send_message(msg)

    async def step(self) -> TaskState:
        # Process scan results, read signs, update registry
        ...
```

#### ChestSortTask
```python
class ChestSortTask(TaskBase):
    """
    Main sorting task that orchestrates the sorting process

    High-level algorithm:
    1. Ensure ChestRegistry is up to date (run ChestScanTask if needed)
    2. For each labeled chest:
       a. Navigate to chest (GotoTask)
       b. Open chest
       c. Query contents
       d. Identify items that don't belong
       e. For each misplaced item:
          i.  Find destination chest
          ii. Plan multi-step move if needed
    3. Transfer items to correct chests
    """

    def __init__(self, registry: ChestRegistry):
        super().__init__()
        self.registry = registry
        self.work_queue = []  # List of (item_id, source_pos, dest_pos, quantity)
```

#### ItemTransferTask
```python
class ItemTransferTask(TaskBase):
    """
    Transfer specific items from one chest to another

    Steps:
    1. Navigate to source chest
    2. Open source chest
    3. Withdraw items to inventory
    4. Close chest
    5. Navigate to destination chest
    6. Open destination chest
    7. Deposit items
    8. Close chest
    """

    def __init__(
        self,
        item_id: str,
        source_pos: tuple[int, int, int],
        dest_pos: tuple[int, int, int],
        quantity: int = -1
    ):
        super().__init__()
        self.item_id = item_id
        self.source_pos = source_pos
        self.dest_pos = dest_pos
        self.quantity = quantity
        self.state_machine = StateMachine([
            "GOTO_SOURCE",
            "OPEN_SOURCE",
            "WITHDRAW",
            "CLOSE_SOURCE",
            "GOTO_DEST",
            "OPEN_DEST",
            "DEPOSIT",
            "CLOSE_DEST",
            "COMPLETE"
        ])
```

### 5. Sorting Algorithm

```python
def plan_sorting_operations(registry: ChestRegistry) -> list[TransferOperation]:
    """
    Analyze all chests and plan optimal sorting operations

    Returns:
        List of transfer operations to execute
    """
    operations = []

    # For each chest in registry
    for chest_pos, chest_label in registry.chests.items():
        # Get current contents
        contents = query_chest_contents(chest_pos)

        # Find items that don't belong
        for item_slot in contents.items:
            item_id = item_slot.item_id

            # Check if item belongs in this chest
            if item_id not in chest_label.items:
                # Find destination chest(s) for this item
                dest_positions = registry.find_destination_for_item(item_id)

                if dest_positions:
                    # Pick closest destination
                    closest_dest = find_closest_position(chest_pos, dest_positions)

                    operations.append(TransferOperation(
                        item_id=item_id,
                        source=chest_pos,
                        destination=closest_dest,
                        quantity=item_slot.count
                    ))
                else:
                    # No destination found - log warning or use overflow chest
                    logger.warning(f"No destination for {item_id} at {chest_pos}")

    # Optimize order (e.g., group by source chest, minimize travel)
    return optimize_transfer_order(operations)
```

### 6. Integration Points

#### Python Side (src-py/mqttbot/)

**New Files:**
- `src-py/mqttbot/core/tasks/chest_scan_task.py`
- `src-py/mqttbot/core/tasks/chest_sort_task.py`
- `src-py/mqttbot/core/tasks/item_transfer_task.py`
- `src-py/mqttbot/core/state/chest_registry.py`
- `src-py/mqttbot/model/chest_label.py`

**Modified Files:**
- `src-py/mqttbot/core/state/typed_blackboard.py` - Add ChestRegistryModule
- `src-py/mqttbot/core/modular_bot_client.py` - Register new tasks

#### Java Side (src/main/java/org/limepepper/mqttbot/)

**New Files:**
- `integrations/container/ContainerHandler.java`
- `integrations/container/ContainerOpenAction.java`
- `integrations/container/ContainerQueryHandler.java`
- `integrations/container/ContainerTransferHandler.java`
- `integrations/container/SignReader.java`
- `integrations/container/BlockScanner.java`
- `watchers/ContainerWatcher.java`
- `events/ContainerOpenedEvent.java`
- `events/ContainerClosedEvent.java`

**Modified Files:**
- `MqttBotClientModInitializer.java` - Register ContainerHandler and ContainerWatcher
- `integrations/inventory/InventoryQueryHandler.java` - Extend to support container queries

### 7. Usage Example

```python
# In Python MQTT task client

# Initial setup: Scan for labeled chests
scan_task = ChestScanTask(radius=128)
await scheduler.schedule(scan_task)

# Get registry from blackboard
registry = blackboard.get_module("chest_registry")

# Run sorting process
sort_task = ChestSortTask(registry)
await scheduler.schedule(sort_task)

# Or manually transfer specific items
transfer_task = ItemTransferTask(
    item_id="minecraft:sugar_cane",
    source_pos=(100, 64, -200),
    dest_pos=(150, 65, -180),
    quantity=64
)
await scheduler.schedule(transfer_task)
```

## Advanced Features (Future Enhancements)

### 1. Smart Inventory Management
- Track chest fill levels
- Route items to least-full chest when multiple destinations exist
- Warn when destination chests are full

### 2. Chest Network Visualization
- Export chest map as graph
- Visualize item flow paths
- Identify orphaned items (no destination)

### 3. Multi-Item Labels
- Support wildcards (e.g., `minecraft:*_ore` for all ores)
- Support tags (e.g., `#minecraft:logs`)
- Support metadata/NBT filtering

### 4. Sorting Modes
- **Continuous Mode**: Constantly monitor and sort
- **One-Shot Mode**: Sort once and stop
- **Scheduled Mode**: Sort at specific intervals

### 5. Priority System
- High-priority items sorted first
- Critical chests (e.g., farms) checked more frequently

### 6. Conflict Resolution
- Handle items that match multiple chest labels
- Define precedence rules
- Support for "overflow" chests

## Testing Strategy

### Unit Tests
- ChestLabel parsing from sign text
- ChestRegistry lookup operations
- Transfer operation planning algorithm

### Integration Tests
- Scan → Read Signs → Update Registry flow
- Complete item transfer (source → dest) flow
- Error handling (chest destroyed, full inventory, etc.)

### Manual Tests
- Set up test world with labeled chests
- Run sorting on small set (5-10 chests)
- Verify items end up in correct locations
- Test edge cases (double chests, trapped chests, barrels)

## Implementation Order

1. **Phase 1: Basic Container Interaction** (Java mod)
   - Implement `open_container`, `close_container`
   - Implement `query_container`
   - Test manual container opening/querying

2. **Phase 2: Sign Reading** (Java mod)
   - Implement `read_sign_text`
   - Implement `scan_nearby_blocks` with sign detection
   - Test sign reading accuracy

3. **Phase 3: Item Transfer** (Java mod)
   - Implement `transfer_items` with all operations
   - Test deposit/withdraw flows
   - Handle edge cases (full inventory, full chest)

4. **Phase 4: Python Registry** (Python)
   - Implement ChestLabel and ChestRegistry
   - Implement ChestScanTask
   - Test registry building from sign data

5. **Phase 5: Sorting Logic** (Python)
   - Implement ItemTransferTask
   - Implement ChestSortTask
   - Test end-to-end sorting

6. **Phase 6: Optimization & Polish**
   - Optimize pathfinding between chests
   - Add error recovery
   - Add logging and monitoring

## Performance Considerations

- **Scanning**: Limit radius to prevent lag; scan incrementally
- **Pathfinding**: Cache paths between frequently used chests
- **Container Access**: Batch operations when possible
- **State Synchronization**: Only update registry when changes detected

## Security & Safety

- **Validation**: Verify sign format before parsing
- **Rate Limiting**: Prevent spam clicking on containers
- **Bounds Checking**: Ensure slot indices are valid
- **Timeout Handling**: Don't get stuck waiting for container to open
- **Graceful Degradation**: Continue sorting even if some chests are inaccessible
