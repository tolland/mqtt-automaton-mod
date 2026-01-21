# Client Readiness State Architecture

## State Machine

### ClientReadiness Enum
```java
public enum ClientReadiness {
    // Not connected to any world
    DISCONNECTED,

    // In main menu, server list, etc (no world loaded)
    IN_MENU,

    // Connecting to a world (between menu and in-world)
    CONNECTING,

    // In world, alive, no GUI - READY FOR TASKS
    IN_WORLD_READY,

    // In world but dead (respawn screen)
    IN_WORLD_DEAD,

    // In world but GUI open (inventory, chest, etc)
    IN_WORLD_GUI,

    // Unknown state
    UNKNOWN;

    public boolean canAcceptTasks() {
        return this == IN_WORLD_READY;
    }

    public boolean isInWorld() {
        return this == IN_WORLD_READY
            || this == IN_WORLD_DEAD
            || this == IN_WORLD_GUI;
    }
}
```

### ClientReadinessState (Singleton)
```java
public enum ClientReadinessState {
    INSTANCE;

    private ClientReadiness currentState = ClientReadiness.UNKNOWN;
    private String currentWorldName = null;
    private Instant stateChangeTime = Instant.now();

    void transitionTo(ClientReadiness newState, String reason) {
        if (currentState != newState) {
            ClientReadiness oldState = currentState;
            currentState = newState;
            stateChangeTime = Instant.now();

            // Publish state change event via MQTT
            publishStateChange(oldState, newState, reason);
        }
    }

    private void publishStateChange(ClientReadiness from, ClientReadiness to, String reason) {
        JsonObject event = new JsonObject();
        event.addProperty("from", from.toString());
        event.addProperty("to", to.toString());
        event.addProperty("reason", reason);
        event.addProperty("canAcceptTasks", to.canAcceptTasks());
        event.addProperty("worldName", currentWorldName);
        event.addProperty("timestamp", stateChangeTime.toString());

        // Publish to MQTT topic: client/state
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(
            playerName,
            new MessageData("client", "state_change",
                UUID.randomUUID().toString(), null, null, event, playerName),
            "events"
        ));
    }
}
```

## Event Handlers

### Enhanced ClientListener
```java
public interface ClientListener extends Listener {
    // Existing
    void onClientJoin();
    void onClientDisconnect();

    // New events
    void onPlayerDeath();
    void onPlayerRespawn();
    void onScreenOpen(Screen screen);
    void onScreenClose();
}
```

### Enhanced PlayerEventWatcher
```java
public class PlayerEventWatcher {
    public static void init() {
        // World join/disconnect
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            String worldName = client.level != null
                ? client.level.dimension().location().toString()
                : "unknown";
            ClientReadinessState.INSTANCE.setWorldName(worldName);
            ClientReadinessState.INSTANCE.transitionTo(
                ClientReadiness.IN_WORLD_READY,
                "joined_world:" + worldName
            );
            EventManager.fire(ClientListener.ClientJoinEvent.INSTANCE);
        });

        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            ClientReadinessState.INSTANCE.transitionTo(
                ClientReadiness.DISCONNECTED,
                "disconnected"
            );
            EventManager.fire(ClientListener.ClientDisconnectEvent.INSTANCE);
        });

        // Player death
        // Note: This requires server-side event forwarding or client-side detection
        // Option 1: Poll player health in tick handler
        // Option 2: Listen to damage events and check for death

        // Screen open/close
        ScreenEvents.AFTER_INIT.register((client, screen, width, height) -> {
            if (screen != null) {
                ClientReadinessState.INSTANCE.transitionTo(
                    ClientReadiness.IN_WORLD_GUI,
                    "screen_opened:" + screen.getClass().getSimpleName()
                );
            }
        });

        ScreenEvents.REMOVE.register((screen) -> {
            // Check if back to in-game
            Minecraft mc = Minecraft.getInstance();
            if (mc.screen == null && mc.level != null && mc.player != null) {
                if (mc.player.isDeadOrDying()) {
                    ClientReadinessState.INSTANCE.transitionTo(
                        ClientReadiness.IN_WORLD_DEAD,
                        "screen_closed_but_dead"
                    );
                } else {
                    ClientReadinessState.INSTANCE.transitionTo(
                        ClientReadiness.IN_WORLD_READY,
                        "screen_closed"
                    );
                }
            }
        });
    }
}
```

### Tick-based State Monitoring
For states that can't be detected via events alone (e.g., death detection), use a tick handler:

```java
public class ReadinessTickHandler {
    private static boolean wasDeadLastTick = false;

    public static void onClientTick(Minecraft client) {
        if (client.player == null) return;

        boolean isDead = client.player.isDeadOrDying();

        // Death transition
        if (isDead && !wasDeadLastTick) {
            ClientReadinessState.INSTANCE.transitionTo(
                ClientReadiness.IN_WORLD_DEAD,
                "player_died"
            );
        }

        // Respawn transition
        if (!isDead && wasDeadLastTick) {
            ClientReadinessState.INSTANCE.transitionTo(
                ClientReadiness.IN_WORLD_READY,
                "player_respawned"
            );
        }

        wasDeadLastTick = isDead;
    }
}
```

## Python Client Integration

### Event Subscription
```python
class ModularBotClient:
    def __init__(self):
        self._client_state = ClientReadiness.UNKNOWN
        self._state_change_callbacks = []

    def _on_client_state_change(self, event: Dict[str, Any]):
        """Handle client state change events from mod"""
        old_state = event.get("from")
        new_state = event.get("to")
        can_accept_tasks = event.get("canAcceptTasks", False)
        reason = event.get("reason", "")

        logger.info(f"[client] State change: {old_state} → {new_state} ({reason})")

        self._client_state = new_state

        # Cancel active tasks if no longer ready
        if not can_accept_tasks and self._has_active_tasks():
            logger.warning("[client] State changed to not ready, canceling active tasks")
            await self._cancel_all_tasks()

        # Notify callbacks
        for callback in self._state_change_callbacks:
            callback(old_state, new_state, reason)

    def subscribe_to_mqtt(self):
        # Subscribe to state changes
        self.mqtt_client.subscribe(f"mqttbot/{self.player_name}/events")
        self.mqtt_client.message_callback_add(
            f"mqttbot/{self.player_name}/events",
            self._on_mqtt_event
        )

    def _on_mqtt_event(self, client, userdata, msg):
        event = json.loads(msg.payload)
        if event.get("service") == "client" and event.get("method") == "state_change":
            asyncio.create_task(self._on_client_state_change(event["response"]))
```

### Startup Wait
```python
async def _wait_for_ready(self, timeout: float = 60.0):
    """Wait for client to be in IN_WORLD_READY state"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Query current state
        response = await self.send_command("client", "get_state", {}, timeout=5.0)
        state = response.get("state")
        can_accept_tasks = response.get("canAcceptTasks", False)

        if can_accept_tasks:
            logger.info(f"[bot] Client ready in state: {state}")
            return

        logger.debug(f"[bot] Waiting for ready state, currently: {state}")
        await asyncio.sleep(1.0)

    raise TimeoutError(f"Client did not become ready within {timeout}s")
```

## Benefits

1. **Event-Driven**: State changes published immediately, no polling needed
2. **Comprehensive**: Covers all 6+ states you mentioned
3. **Python Integration**: Client can reactively handle state changes
4. **Task Safety**: Automatically cancel tasks when state becomes not-ready
5. **Debugging**: Full state transition history with reasons
6. **Extensible**: Easy to add new states (e.g., AFK detection, low health)

## Implementation Notes

- Death detection requires tick handler (no direct event in Fabric for client-side death)
- Bungee lobby detection: track world name changes on reconnect
- Screen events available via Fabric's `ScreenEvents` API
- All state changes logged with timestamps and reasons for debugging
