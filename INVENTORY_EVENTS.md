# Inventory Event Handling

This mod now includes comprehensive inventory event monitoring and MQTT integration.

## Overview

The inventory event system monitors the player's inventory in real-time and publishes MQTT messages when changes occur. This enables automation scripts to respond to inventory conditions like:

- Inventory becoming full
- Collecting specific items
- Item count reaching thresholds
- General inventory changes

## Architecture

The system consists of four main components:

### 1. InventoryWatcher
- Monitors inventory every 10 ticks (0.5 seconds)
- Compares current inventory state with previous state
- Fires events when changes are detected
- Skips monitoring when container/inventory screens are open
- Location: `org.limepepper.mqttbot.watchers.InventoryWatcher`

### 2. InventoryListener Interface
- Defines event callbacks for inventory changes
- Events:
  - `onInventoryChange()` - any inventory change detected
  - `onInventoryFull()` - inventory has no empty slots
  - `onItemCountChange()` - specific item count changed
- Location: `org.limepepper.mqttbot.events.InventoryListener`

### 3. InventoryAction
- Listens for inventory events
- Converts events to MQTT messages
- Publishes to topic: `mqttbot/{botId}/reply`
- Location: `org.limepepper.mqttbot.actions.InventoryAction`

### 4. InventoryQueryHandler
- Handles incoming MQTT commands for inventory queries
- Supports commands:
  - `query_inventory` - get full inventory state
  - `get_item_count` - get count of specific item
  - `check_capacity` - check available space
- Location: `org.limepepper.mqttbot.integrations.inventory.InventoryQueryHandler`

## MQTT Message Formats

### Outgoing Events (Published by mod)

#### Inventory Change Event
```json
{
  "service": "inventory",
  "method": "inventory_change",
  "requestId": "uuid",
  "response": {
    "event": "inventory_change",
    "emptySlots": 5,
    "fullSlots": 31,
    "totalSlots": 36,
    "player": "PlayerName",
    "timestamp": 1234567890,
    "itemCounts": {
      "minecraft:sugar_cane": 576,
      "minecraft:wheat": 128
    }
  }
}
```

#### Inventory Full Event
```json
{
  "service": "inventory",
  "method": "inventory_full",
  "requestId": "uuid",
  "response": {
    "event": "inventory_full",
    "emptySlots": 0,
    "fullSlots": 36,
    "totalSlots": 36,
    "player": "PlayerName",
    "timestamp": 1234567890,
    "itemCounts": {
      "minecraft:sugar_cane": 2304
    }
  }
}
```

#### Item Count Change Event
```json
{
  "service": "inventory",
  "method": "item_count_change",
  "requestId": "uuid",
  "response": {
    "event": "item_count_change",
    "itemId": "minecraft:sugar_cane",
    "oldCount": 512,
    "newCount": 576,
    "totalCount": 576,
    "delta": 64,
    "player": "PlayerName",
    "timestamp": 1234567890
  }
}
```

### Incoming Commands (Send to bot)

Topic: `mqttbot/{botId}/command` or `mqttbot/bots/command`

#### Query Full Inventory
```json
{
  "service": "inventory",
  "method": "query_inventory"
}
```

Response:
```json
{
  "service": "inventory",
  "method": "query_inventory",
  "response": {
    "emptySlots": 5,
    "fullSlots": 31,
    "totalSlots": 36,
    "itemCounts": {
      "minecraft:sugar_cane": 576
    }
  }
}
```

#### Get Specific Item Count
```json
{
  "service": "inventory",
  "method": "get_item_count",
  "params": {
    "itemId": "minecraft:sugar_cane"
  }
}
```

Response:
```json
{
  "service": "inventory",
  "method": "get_item_count",
  "response": {
    "itemId": "minecraft:sugar_cane",
    "count": 576
  }
}
```

#### Check Inventory Capacity
```json
{
  "service": "inventory",
  "method": "check_capacity"
}
```

Response:
```json
{
  "service": "inventory",
  "method": "check_capacity",
  "response": {
    "emptySlots": 5,
    "isFull": false,
    "hasSpace": true
  }
}
```

## Configuration Example

Add to your YAML configuration file:

```yaml
services:
  inventory:
    # No specific configuration needed yet
    # Future: thresholds, filters, etc.

events:
  inventory_full:
    enabled: true
    steps:
      - service: baritone
        method: pause
        description: "Stop current activity"

      - service: warp
        method: teleport
        description: "Return to base"
        params:
          name: "home"
          radius: 5
          command_template: "warp {name}"
          target:
            x: 345
            y: 64
            z: -2493

      - service: commands
        method: sendCommand
        params:
          message: "Inventory full - returning to base"

  inventory_change:
    enabled: false  # Usually too noisy, enable for debugging
    steps:
      - service: commands
        method: sendCommand
        params:
          message: "Inventory changed"
```

## Use Case: Sugar Cane Farming

When farming sugar cane, you want to know when inventory is full so you can:
1. Stop farming
2. Return to base
3. Deposit items
4. Resume farming

### Example Automation Script (Python)

```python
import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)

    if data.get('service') == 'inventory':
        if data.get('method') == 'inventory_full':
            print("Inventory is full!")
            item_counts = data['response']['itemCounts']
            print(f"Items: {item_counts}")

            # Send command to stop farming
            client.publish(f"mqttbot/{bot_id}/command", json.dumps({
                "service": "baritone",
                "method": "pause"
            }))

            # Warp home
            client.publish(f"mqttbot/{bot_id}/command", json.dumps({
                "service": "warp",
                "method": "teleport",
                "params": {"name": "home"}
            }))

client = mqtt.Client()
client.on_message = on_message
client.connect("mosquitto.lan", 1883)
client.subscribe("mqttbot/+/reply")
client.loop_forever()
```

## Performance Considerations

- **Check Interval**: Inventory is checked every 10 ticks (0.5 seconds) to balance responsiveness with performance
- **Container Screen Detection**: Monitoring pauses when inventory/container screens are open to avoid conflicts
- **Event Filtering**: Only fires events when actual changes are detected
- **Item Count Changes**: Individual item count change events are fired for each item type that changed

## Future Enhancements

Potential additions based on the reference implementations:

1. **Threshold Configuration**: Define thresholds in config for specific items
   ```yaml
   inventory:
     thresholds:
       - item: "minecraft:sugar_cane"
         fullThreshold: 576
       - item: "minecraft:wheat"
         lowThreshold: 10
   ```

2. **Ignore Lists**: Filter out common items from events
   ```yaml
   inventory:
     ignoreItems:
       - "minecraft:dirt"
       - "minecraft:cobblestone"
   ```

3. **Slot-Level Tracking**: Track specific inventory slots and movements

4. **Hotbar Monitoring**: Special handling for hotbar slots (similar to tweakeroo's hand restock)

5. **Durability Tracking**: Monitor tool durability and alert before breaking

## Technical Notes

- Uses Fabric's `ClientTickEvents.END_CLIENT_TICK` for tick-based monitoring
- Inventory snapshot comparison uses `HashMap` for efficient diffing
- All 36 main inventory slots are monitored (0-8 hotbar, 9-35 main)
- Armor and offhand slots are not currently monitored (can be added if needed)
