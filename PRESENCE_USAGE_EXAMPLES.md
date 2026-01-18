# Device Presence Library - Usage Examples

## Java Mod Side

### Basic Setup

```java
import org.limepepper.mqttbot.presence.*;
import org.eclipse.paho.client.mqttv3.*;

public class MqttBotMod {
    private DevicePresence presence;
    private MqttClient mqttClient;
    private String playerName;

    public void initializeMqtt() throws MqttException {
        playerName = Minecraft.getInstance().getUser().getName();

        // Create MQTT client
        mqttClient = new MqttClient("tcp://localhost:1883", "mqttbot_" + playerName);

        // Create presence manager
        presence = new DevicePresence(playerName, mqttClient);

        // Connect with LWT (Last Will and Testament)
        MqttConnectOptions options = presence.createConnectionOptions();
        options.setUserName("mqttbot");
        options.setPassword("secret".toCharArray());

        mqttClient.connect(options);

        // Immediately announce we're online
        String connectionId = UUID.randomUUID().toString();
        presence.announceOnline(connectionId);

        // Publish device configuration
        publishDeviceConfig();
    }

    private void publishDeviceConfig() throws MqttException {
        DeviceConfig config = new DeviceConfig(
            playerName,
            playerName,  // name
            "MinecraftClient",  // model
            "mqttbot-mod",  // manufacturer
            "1.0.0",  // sw_version
            List.of(
                "baritone.goto",
                "baritone.cancel",
                "inventory.query",
                "inventory.drop"
            ),
            Map.of(
                "max_concurrent_tasks", 1,
                "supports_correlation_ids", true,
                "baritone_version", "1.21.8"
            ),
            Map.of(
                "command", "mqttbot/" + playerName + "/command",
                "events", "mqttbot/" + playerName + "/events",
                "availability", presence.getAvailabilityTopic(),
                "readiness", presence.getReadinessTopic()
            )
        );

        presence.publishConfig(config);
    }

    public void shutdown() throws MqttException {
        // Gracefully announce offline before disconnecting
        presence.announceOffline();
        mqttClient.disconnect();
    }
}
```

### Publishing Readiness State

Hook into existing `ClientListener` events:

```java
public class ClientAction extends Action implements ClientListener {

    private DevicePresence presence;

    @Override
    public void onClientJoin() {
        try {
            // Player joined world - now ready
            JsonObject additionalData = new JsonObject();
            additionalData.addProperty("world",
                Minecraft.getInstance().level.dimension().location().toString());

            BetterBlockPos pos = MqttCore.baritone.getPlayerContext().playerFeet();
            JsonObject position = new JsonObject();
            position.addProperty("x", pos.x);
            position.addProperty("y", pos.y);
            position.addProperty("z", pos.z);
            additionalData.add("position", position);

            additionalData.addProperty("health",
                Minecraft.getInstance().player.getHealth());

            ReadinessState state = ReadinessState.ready(
                "IN_WORLD_READY",
                "player_joined_world",
                additionalData
            );

            presence.publishReadiness(state);

        } catch (MqttException e) {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }

    @Override
    public void onClientDisconnect() {
        try {
            // Player disconnected - not ready
            ReadinessState state = ReadinessState.notReady(
                "DISCONNECTED",
                "player_left_world",
                null
            );

            presence.publishReadiness(state);

        } catch (MqttException e) {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }

    // New method for death detection
    public void onPlayerDeath() {
        try {
            ReadinessState state = ReadinessState.notReady(
                "IN_WORLD_DEAD",
                "player_died",
                null
            );

            presence.publishReadiness(state);

        } catch (MqttException e) {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }

    // New method for respawn
    public void onPlayerRespawn() {
        try {
            JsonObject additionalData = new JsonObject();
            BetterBlockPos pos = MqttCore.baritone.getPlayerContext().playerFeet();
            JsonObject position = new JsonObject();
            position.addProperty("x", pos.x);
            position.addProperty("y", pos.y);
            position.addProperty("z", pos.z);
            additionalData.add("position", position);

            ReadinessState state = ReadinessState.ready(
                "IN_WORLD_READY",
                "player_respawned",
                additionalData
            );

            presence.publishReadiness(state);

        } catch (MqttException e) {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }
}
```

### Optional: Heartbeat for Fast Detection

```java
public class HeartbeatPublisher {
    private final ScheduledExecutorService scheduler;
    private final DevicePresence presence;
    private long sequenceNumber = 0;

    public HeartbeatPublisher(DevicePresence presence) {
        this.presence = presence;
        this.scheduler = Executors.newScheduledThreadPool(1);
    }

    public void start() {
        // Publish heartbeat every 500ms
        scheduler.scheduleAtFixedRate(() -> {
            try {
                presence.publishHeartbeat(sequenceNumber++);
            } catch (MqttException e) {
                LOGGER.error("Failed to publish heartbeat: {}", e.getMessage());
            }
        }, 0, 500, TimeUnit.MILLISECONDS);
    }

    public void stop() {
        scheduler.shutdown();
    }
}
```

## Python Client Side

### Basic Setup

```python
import asyncio
import paho.mqtt.client as mqtt
from mqttbot.device_presence import DevicePresenceMonitor

class MqttBotClient:
    def __init__(self, player_name: str):
        self.player_name = player_name
        self.mqtt_client = mqtt.Client()
        self.device_monitor = DevicePresenceMonitor(player_name, self.mqtt_client)

        # Setup MQTT callbacks
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        print(f"[mqtt] Connected with result code {rc}")

        # Subscribe to device presence topics
        self.device_monitor.subscribe()

    def _on_mqtt_disconnect(self, client, userdata, rc):
        print(f"[mqtt] Disconnected with result code {rc}")

    async def connect_and_wait_ready(self):
        """Connect to MQTT and wait for mod to be ready"""

        # Connect to broker
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.loop_start()

        print(f"[bot] Waiting for {self.player_name} to be available...")

        # Wait for mod to announce it's online
        available = await self.device_monitor.wait_for_available(timeout=30.0)
        if not available:
            raise TimeoutError("Mod did not come online")

        print(f"[bot] Mod is available!")

        # Get device config (capabilities)
        config = await self.device_monitor.wait_for_config(timeout=10.0)
        if config:
            print(f"[bot] Device config: {config.name} v{config.sw_version}")
            print(f"[bot] Services: {', '.join(config.services)}")

        # Wait for mod to be ready (in world, not dead, etc)
        print(f"[bot] Waiting for {self.player_name} to be ready...")
        ready = await self.device_monitor.wait_for_ready(timeout=60.0)

        if not ready:
            raise TimeoutError("Mod did not become ready")

        print(f"[bot] Mod is ready! State: {self.device_monitor.readiness.state}")

    async def run(self):
        """Main bot loop"""
        try:
            # Wait for mod to be available and ready
            await self.connect_and_wait_ready()

            # Subscribe to state changes
            self.device_monitor.on_availability_change(self._on_availability_change)
            self.device_monitor.on_readiness_change(self._on_readiness_change)

            # Optional: Start heartbeat monitoring for fast detection
            await self.device_monitor.start_heartbeat_monitoring()

            # Now safe to send commands
            print("[bot] Starting bot operations...")
            await self.bot_loop()

        finally:
            await self.device_monitor.stop_heartbeat_monitoring()
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

    def _on_availability_change(self, availability):
        """Called when device goes online/offline"""
        print(f"[bot] Device availability changed: {availability.value}")

        if availability.value == "offline":
            print("[bot] Mod went offline! Pausing operations...")
            # Cancel active tasks, wait for reconnect, etc

    def _on_readiness_change(self, readiness):
        """Called when device readiness changes"""
        print(f"[bot] Device readiness changed: {readiness.state} "
              f"(can_accept_tasks={readiness.can_accept_tasks})")

        if not readiness.can_accept_tasks:
            print(f"[bot] Device not ready: {readiness.reason}")
            # Pause task scheduling

    async def bot_loop(self):
        """Main bot logic"""
        while True:
            # Check if still ready before sending command
            if not self.device_monitor.is_ready:
                print("[bot] Waiting for device to be ready again...")
                await self.device_monitor.wait_for_ready(timeout=60.0)

            # Send command...
            await self.send_goto_command(x=100, y=64, z=200)

            await asyncio.sleep(5.0)


# Usage
async def main():
    client = MqttBotClient(player_name="SandyFire")
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Handling State Changes Reactively

```python
class FarmingBot:
    def __init__(self, device_monitor: DevicePresenceMonitor):
        self.monitor = device_monitor
        self.active_task = None

        # Subscribe to state changes
        self.monitor.on_readiness_change(self._on_readiness_change)

    def _on_readiness_change(self, readiness):
        """React to readiness changes"""

        if not readiness.can_accept_tasks and self.active_task:
            # Device no longer ready - cancel active task
            print(f"[farming] Device not ready ({readiness.reason}), canceling task")
            self.active_task.cancel()
            self.active_task = None

        elif readiness.can_accept_tasks and not self.active_task:
            # Device became ready - resume operations
            print(f"[farming] Device ready ({readiness.state}), resuming")
            self.active_task = asyncio.create_task(self.farming_loop())

    async def farming_loop(self):
        """Main farming logic"""
        try:
            while True:
                # Check position from readiness message
                if self.monitor.readiness:
                    pos = self.monitor.readiness.additional_data.get("position", {})
                    print(f"[farming] Current position: {pos}")

                # Farm...
                await asyncio.sleep(10.0)

        except asyncio.CancelledError:
            print("[farming] Task cancelled")
```

### Using Heartbeat for Fast Detection

```python
async def main():
    client = MqttBotClient(player_name="SandyFire")

    # Connect and subscribe
    client.mqtt_client.connect("localhost", 1883, 60)
    client.mqtt_client.loop_start()
    client.device_monitor.subscribe()

    # Start heartbeat monitoring (500ms heartbeats, 1.5s timeout)
    await client.device_monitor.start_heartbeat_monitoring()

    # Heartbeat monitor will detect crashes within 1.5 seconds
    # (vs. 20-30 seconds with just MQTT keepalive)

    # Run bot...
    await client.run()
```

## Integration with Existing Code

### Replace `_wait_for_player_join()`

**Before**:
```python
async def _wait_for_player_join(self, timeout: float = 60.0) -> None:
    # Poll blackboard state...
    while time.time() - start_time < timeout:
        events_module = self.blackboard.get_module("events")
        if events_module:
            events_state = events_module.get_state()
            if events_state and events_state.player_joined:
                return
        await asyncio.sleep(0.1)
```

**After**:
```python
async def _wait_for_ready(self, timeout: float = 60.0) -> None:
    """Wait for device to be available and ready"""

    # Wait for availability (online)
    if not await self.device_monitor.wait_for_available(timeout=30.0):
        raise TimeoutError("Device did not come online")

    # Wait for readiness (can accept tasks)
    if not await self.device_monitor.wait_for_ready(timeout=timeout):
        raise TimeoutError("Device did not become ready")
```

### Benefits

1. **No polling** - Event-driven via MQTT broker push
2. **Fast detection** - Sub-second with heartbeat, <1 minute with LWT
3. **Reliable** - MQTT broker guarantees LWT delivery
4. **Generic** - Library works for any MQTT device, not just Minecraft
5. **Debuggable** - Can use MQTT Explorer to see all state transitions
6. **Extensible** - Easy to add new readiness states
