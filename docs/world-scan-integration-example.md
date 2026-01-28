# World Scan Integration Example

This document shows how the ScanHandler (Java mod) and WorldStateCache (Python pybot) work together.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Java Mod (Agent)                          │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ScanHandler                                            │ │
│  │                                                         │ │
│  │ - Scans entities/blocks in radius                     │ │
│  │ - Serializes to JSON (raw data, no interpretation)    │ │
│  │ - Publishes to MQTT                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                     MQTT (JSON payload)
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                  Python Pybot (Controller)                    │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ WorldStateCache                                        │ │
│  │                                                         │ │
│  │ - Receives scan results                                │ │
│  │ - Stores raw entities/blocks                          │ │
│  │ - Interprets relationships (item frames → chests)     │ │
│  │ - Maintains spatial indices                           │ │
│  │ - Provides query API                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## 1. Request Scan from Python

```python
from mqttbot.core.services.message_service import MessageService
from mqttbot.model.messaging.service_message import ServiceMessage
import uuid

# Create message service
msg_service = MessageService(mqtt_client)

# Request container scan
request = ServiceMessage(
    service="scan",
    method="scan_containers",
    request_id=str(uuid.uuid4()),
    params={
        "radius": 128  # Scan 128 blocks around player
    }
)

# Send request and wait for response
response = await msg_service.send_and_wait(request, timeout=10.0)
print(f"Scan found {response.response['entity_count']} entities and {response.response['block_count']} blocks")
```

## 2. Mod Processes Request

The ScanHandler in Java:

```java
// ScanHandler receives the request via MQTT
// Scans entities and blocks within radius
// Returns raw JSON data

{
  "scan_type": "container_scan",
  "timestamp": 1706454000000,
  "center": [100.5, 64.0, -200.5],
  "radius": 128,
  "entities": [
    {
      "type": "minecraft:item_frame",
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "pos": [100.5, 65.5, -200.5],
      "extra": {
        "facing": "north",
        "rotation": 0,
        "item_id": "minecraft:sugar_cane",
        "item_count": 1
      }
    }
  ],
  "blocks": [
    {
      "type": "minecraft:chest",
      "pos": [100, 64, -200],
      "extra": {
        "slot_count": 27
      }
    }
  ],
  "entity_count": 1,
  "block_count": 1
}
```

## 3. Python Updates Cache

```python
from mqttbot.core.state.world_cache import WorldStateCache
from mqttbot.model.world import ScanResult

# Initialize cache
world_cache = WorldStateCache()

# Parse response into ScanResult
scan_result = ScanResult.from_dict(response.response)

# Update cache (interprets relationships automatically)
world_cache.update_from_scan(scan_result)

print(world_cache)
# Output: WorldStateCache(entities=1, blocks=1, containers=1, labeled=1)
```

## 4. Query the Cache

```python
# Find all containers for sugar cane
sugar_cane_chests = world_cache.find_containers_for_item("minecraft:sugar_cane")
for container in sugar_cane_chests:
    print(f"Sugar cane chest at {container.position}")
    print(f"  Label: {container.label.items}")
    print(f"  Last seen: {container.last_seen}")

# Find containers near a position
player_pos = (100, 64, -200)
nearby_containers = world_cache.find_containers_in_radius(player_pos, radius=64)
print(f"Found {len(nearby_containers)} containers nearby")

# Get specific container
chest = world_cache.get_container_at((100, 64, -200))
if chest and chest.label:
    print(f"Chest should contain: {chest.label.items}")
```

## 5. Integration with Task System

```python
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.state.blackboard import TypedBlackboard

class ChestScanTask(TaskBase):
    """Task to scan area for labeled chests"""

    def __init__(self, blackboard: TypedBlackboard, radius: int = 128):
        super().__init__()
        self.blackboard = blackboard
        self.radius = radius

    async def enter(self) -> None:
        """Send scan request when task starts"""
        request = ServiceMessage(
            service="scan",
            method="scan_containers",
            request_id=str(uuid.uuid4()),
            params={"radius": self.radius}
        )

        response = await self.message_service.send_and_wait(request, timeout=10.0)

        # Update world cache in blackboard
        world_module = self.blackboard.get_module("world")
        scan_result = ScanResult.from_dict(response.response)
        world_module.cache.update_from_scan(scan_result)

        self.logger.info(f"Scan complete: {world_module.cache}")

    async def step(self) -> TaskState:
        return TaskState.COMPLETED

# Use in scheduler
scan_task = ChestScanTask(blackboard, radius=128)
await scheduler.schedule(scan_task)

# Query results
world_cache = blackboard.get_module("world").cache
containers = world_cache.get_all_labeled_containers()
print(f"Found {len(containers)} labeled containers")
```

## 6. Example: Chest Sorting Workflow

```python
async def sort_chests_workflow(blackboard: TypedBlackboard):
    """Complete workflow for sorting chests"""

    # 1. Scan area for containers
    scan_task = ChestScanTask(blackboard, radius=128)
    await scheduler.schedule(scan_task)

    # 2. Get world cache
    world_cache = blackboard.get_module("world").cache

    # 3. For each labeled container, check its contents
    for container in world_cache.get_all_labeled_containers():
        # Navigate to container
        goto_task = GotoTask(container.position)
        await scheduler.schedule(goto_task)

        # Open and query contents
        # (This would use container service - not implemented in this example)

        # Identify misplaced items
        # Move items to correct containers
        # ...
```

## 7. Message Flow Diagram

```
Python Pybot                          Java Mod
     |                                    |
     |  MQTT: scan/scan_containers       |
     |  params: {radius: 128}            |
     |------------------------------------>|
     |                                    |
     |                         ScanHandler processes
     |                         - Iterate entities
     |                         - Iterate blocks
     |                         - Serialize to JSON
     |                                    |
     |  MQTT: response                   |
     |  {entities: [...], blocks: [...]} |
     |<------------------------------------|
     |                                    |
WorldStateCache.update_from_scan()      |
- Store raw data                        |
- Extract item frames                   |
- Interpret labels                      |
- Build indices                         |
     |                                    |
Query API available:                    |
- find_containers_for_item()            |
- find_containers_in_radius()           |
- get_container_at()                    |
     |                                    |
```

## 8. Testing the Integration

### In-game Test (Java Mod)

1. Place a chest at (100, 64, -200)
2. Place an item frame above it (100, 65, -200) with sugar cane
3. Enable the mod (should auto-start)
4. Send MQTT message:

```json
{
  "service": "scan",
  "method": "scan_containers",
  "request_id": "test-123",
  "params": {"radius": 64}
}
```

5. Observe response in MQTT topic `mqttbot/{player}/response`

### Python Test

```python
import asyncio
from mqttbot.core.state.world_cache import WorldStateCache
from mqttbot.model.world import ScanResult

# Mock scan result (from real mod response)
mock_data = {
    "scan_type": "container_scan",
    "timestamp": 1706454000000,
    "center": [100.0, 64.0, -200.0],
    "radius": 64,
    "entities": [
        {
            "type": "minecraft:item_frame",
            "uuid": "test-uuid",
            "pos": [100.5, 65.5, -200.5],
            "extra": {
                "facing": "down",
                "rotation": 0,
                "item_id": "minecraft:sugar_cane",
                "item_count": 1
            }
        }
    ],
    "blocks": [
        {
            "type": "minecraft:chest",
            "pos": [100, 64, -200],
            "extra": {"slot_count": 27}
        }
    ],
    "entity_count": 1,
    "block_count": 1
}

# Test cache
cache = WorldStateCache()
scan = ScanResult.from_dict(mock_data)
cache.update_from_scan(scan)

# Verify interpretation
assert len(cache.containers) == 1
assert len(cache.item_frames) == 1
assert len(cache.container_labels) == 1

# Check label extraction
chest_pos = (100, 64, -200)
label = cache.container_labels[chest_pos]
assert "minecraft:sugar_cane" in label.items

# Query API
containers = cache.find_containers_for_item("minecraft:sugar_cane")
assert len(containers) == 1
assert containers[0].position == chest_pos

print("✓ All tests passed")
```

## 9. Benefits of This Design

**Separation of Concerns:**
- Mod: Dumb sensor (reports what it sees)
- Pybot: Smart brain (interprets relationships)

**Flexibility:**
- Change label format (item frames → signs) without mod changes
- Experiment with different labeling schemes
- Add new query patterns easily

**Performance:**
- Mod scans are infrequent (on-demand)
- Python cache enables fast local queries
- No need to re-scan for every query

**Debugging:**
- Inspect raw scan data
- Test interpretation logic independently
- Easy to reproduce issues with mock data

## 10. Next Steps

1. **Add MessagePack encoding** for efficiency (optional)
2. **Implement container interaction** (open, query, transfer)
3. **Build sorting tasks** that use the cache
4. **Add persistence** (save cache to disk)
5. **Handle chunk updates** (detect removed chests)
