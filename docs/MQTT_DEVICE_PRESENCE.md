# MQTT Device Presence Protocol

Based on Home Assistant's MQTT discovery pattern, adapted for generic device liveness/readiness.

## Overview

Fast (<500ms) detection of device availability and readiness using MQTT retained messages, Last Will and Testament (LWT), and state topics.

## Topic Structure

For a device with ID `{device_id}` (e.g., player name "SandyFire"):

```
mqttbot/{device_id}/availability    - Liveness (online/offline) - RETAINED + LWT
mqttbot/{device_id}/config           - Device capabilities - RETAINED
mqttbot/{device_id}/readiness        - Operational readiness - NOT RETAINED
mqttbot/{device_id}/state            - Current state detail - NOT RETAINED
```

## Message Formats

### 1. Availability (Liveness)

**Topic**: `mqttbot/{device_id}/availability`
**Retained**: YES
**QoS**: 1

```json
{
  "state": "online",
  "timestamp": "2026-01-18T12:34:56.789Z",
  "connection_id": "conn_abc123"
}
```

**Offline** (published by MQTT broker via LWT):
```json
{
  "state": "offline",
  "timestamp": "2026-01-18T12:34:56.789Z"
}
```

### 2. Config (Capabilities)

**Topic**: `mqttbot/{device_id}/config`
**Retained**: YES
**QoS**: 1

```json
{
  "device": {
    "identifiers": ["mqttbot_SandyFire"],
    "name": "SandyFire",
    "model": "MinecraftClient",
    "manufacturer": "mqttbot-mod",
    "sw_version": "1.0.0"
  },
  "services": [
    "baritone.goto",
    "baritone.cancel",
    "inventory.query",
    "inventory.drop"
  ],
  "capabilities": {
    "max_concurrent_tasks": 1,
    "supports_correlation_ids": true,
    "baritone_version": "1.21.8"
  },
  "topics": {
    "command": "mqttbot/{device_id}/command",
    "events": "mqttbot/{device_id}/events",
    "availability": "mqttbot/{device_id}/availability",
    "readiness": "mqttbot/{device_id}/readiness"
  }
}
```

### 3. Readiness (Operational State)

**Topic**: `mqttbot/{device_id}/readiness`
**Retained**: NO
**QoS**: 1

```json
{
  "ready": true,
  "state": "IN_WORLD_READY",
  "can_accept_tasks": true,
  "reason": "player_joined_world",
  "world": "minecraft:overworld",
  "position": {"x": 18, "y": 65, "z": -8},
  "health": 20.0,
  "timestamp": "2026-01-18T12:34:56.789Z"
}
```

**Not Ready** states:
```json
{
  "ready": false,
  "state": "IN_WORLD_DEAD",
  "can_accept_tasks": false,
  "reason": "player_died",
  "timestamp": "2026-01-18T12:34:56.789Z"
}
```

### 4. State (Detailed Runtime State)

**Topic**: `mqttbot/{device_id}/state`
**Retained**: NO
**QoS**: 0 (fire-and-forget for frequent updates)

```json
{
  "state_type": "full_state",
  "readiness": {
    "state": "IN_WORLD_READY",
    "can_accept_tasks": true
  },
  "active_tasks": [
    {
      "type": "baritone.goto",
      "request_id": "req_123",
      "correlation_id": "corr_456",
      "phase": "PATHING"
    }
  ],
  "player": {
    "health": 20.0,
    "food": 20,
    "position": {"x": 18, "y": 65, "z": -8}
  },
  "timestamp": "2026-01-18T12:34:56.789Z"
}
```

## MQTT Connection Setup

### Java Mod Side

When connecting to MQTT broker:

```java
MqttConnectOptions options = new MqttConnectOptions();
options.setCleanSession(false); // Persistent session
options.setAutomaticReconnect(true);
options.setKeepAliveInterval(20); // 20 second keepalive
options.setConnectionTimeout(10);

// CRITICAL: Set Last Will and Testament
String availabilityTopic = "mqttbot/" + playerName + "/availability";
JsonObject lwt = new JsonObject();
lwt.addProperty("state", "offline");
lwt.addProperty("timestamp", Instant.now().toString());

options.setWill(
    availabilityTopic,
    lwt.toString().getBytes(StandardCharsets.UTF_8),
    1,  // QoS 1
    true // Retained
);

client.connect(options);

// Immediately publish online status (overwrites LWT)
publishAvailability("online");
publishConfig();
```

### Python Client Side

```python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    # Subscribe to all device topics
    client.subscribe(f"mqttbot/{device_id}/availability", qos=1)
    client.subscribe(f"mqttbot/{device_id}/config", qos=1)
    client.subscribe(f"mqttbot/{device_id}/readiness", qos=1)

    # Will immediately receive retained messages for availability & config

def on_message(client, userdata, msg):
    if msg.topic.endswith("/availability"):
        handle_availability_change(msg.payload)
    elif msg.topic.endswith("/readiness"):
        handle_readiness_change(msg.payload)
```

## Detection Timing

### Liveness Detection (Availability)

**Scenario 1: Mod crashes**
- MQTT broker detects TCP connection loss
- Broker publishes LWT to `availability` topic
- Client receives within: **keepalive interval + network latency**
- Typical: **20-30 seconds** (depends on keepalive setting)

**Faster detection** (5-10 seconds):
- Reduce keepalive to 5 seconds
- Trade-off: more network traffic

**Sub-second detection**:
- Use heartbeat pattern (see below)

### Readiness Detection (State Changes)

**Scenario: Player dies**
- Tick handler detects death (20ms per tick)
- Publishes readiness change immediately
- Client receives within: **network latency**
- Typical: **50-200ms**

**Scenario: Player joins world**
- Fabric event fires immediately
- Publishes readiness change
- Client receives within: **50-200ms**

## Fast Detection Pattern (Heartbeat + LWT)

For sub-second liveness detection, combine heartbeat with LWT:

### Mod Side
```java
// Publish heartbeat every 500ms
ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
scheduler.scheduleAtFixedRate(() -> {
    JsonObject heartbeat = new JsonObject();
    heartbeat.addProperty("timestamp", Instant.now().toString());
    heartbeat.addProperty("sequence", sequenceNumber++);

    publish("mqttbot/" + playerName + "/heartbeat", heartbeat, 0, false);
}, 0, 500, TimeUnit.MILLISECONDS);
```

### Python Client Side
```python
class HeartbeatMonitor:
    def __init__(self, timeout: float = 1.0):
        self._last_heartbeat = None
        self._timeout = timeout
        self._is_alive = False

    def on_heartbeat(self, timestamp: str):
        self._last_heartbeat = time.time()
        if not self._is_alive:
            self._is_alive = True
            self._on_device_alive()

    async def monitor(self):
        while True:
            await asyncio.sleep(0.1)  # Check every 100ms

            if self._last_heartbeat is None:
                continue

            elapsed = time.time() - self._last_heartbeat
            if elapsed > self._timeout and self._is_alive:
                self._is_alive = False
                self._on_device_dead()
```

**Detection time**: **timeout + check_interval** (e.g., 1.0s + 0.1s = 1.1s max)

## Complete State Machine

```
Client Startup:
1. Connect to MQTT
2. Subscribe to mqttbot/{device_id}/availability (retained)
   → Immediately learn if device is online/offline
3. Subscribe to mqttbot/{device_id}/config (retained)
   → Immediately learn device capabilities
4. If available, subscribe to readiness topic
5. Wait for readiness state with can_accept_tasks=true
6. Begin sending commands

State Transitions:
- availability: online → offline
  → Cancel all active tasks
  → Enter "waiting for reconnect" state

- availability: offline → online
  → Re-read config (may have changed after update)
  → Wait for readiness before resuming

- readiness: can_accept_tasks true → false
  → Cancel active tasks (or pause if task supports it)

- readiness: can_accept_tasks false → true
  → Resume operations
```

## Implementation Notes

### MQTT Broker Requirements
- Support for retained messages (all major brokers)
- Support for LWT (all major brokers)
- Recommend: Mosquitto, EMQX, HiveMQ

### QoS Recommendations
- **Availability**: QoS 1 (at-least-once) + retained
- **Config**: QoS 1 + retained
- **Readiness**: QoS 1 (important state changes)
- **State**: QoS 0 (frequent updates, loss acceptable)
- **Heartbeat**: QoS 0 (fire-and-forget)

### Security
- Use TLS for production
- Authenticate devices with username/password or certificates
- Use MQTT ACLs to restrict topic access:
  - Device can only publish to `mqttbot/{device_id}/*`
  - Client can subscribe to `mqttbot/{device_id}/*`

## Benefits Over Current Approach

1. **Immediate Discovery**: Client gets device state on subscribe (retained messages)
2. **Fast Crash Detection**: LWT provides guaranteed offline notification
3. **No Polling**: Event-driven, broker pushes changes
4. **Standard Pattern**: Follows Home Assistant model, well-tested
5. **Generic**: Works for any MQTT-based system, not specific to Minecraft
6. **Debuggable**: Can use MQTT explorer to see all messages
7. **Scalable**: Multiple clients can monitor same device

## Migration Path

**Phase 1**: Add availability topic with LWT
**Phase 2**: Add config topic with capabilities
**Phase 3**: Migrate readiness to use new format
**Phase 4**: Add optional heartbeat for sub-second detection
**Phase 5**: Extract into standalone library
