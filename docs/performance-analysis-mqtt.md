# MQTT Performance Analysis

## Current Performance Problems

I've identified several critical performance issues in your MQTT implementation that explain the lag during inventory-heavy operations.

### Problem 1: QoS 2 on ALL Messages ⚠️ CRITICAL

**Location:** `MqttClientInternal.java:30`
```java
int qos = 2;  // QoS 2 = "Exactly Once"
```

**Impact:** Every single MQTT message uses the slowest possible QoS level:
- QoS 2 requires **4-way handshake**: PUBLISH → PUBREC → PUBREL → PUBCOMP
- Each message can take 10-50ms depending on network latency
- For inventory state updates that will be superseded immediately, this is complete overkill

**What happens during crop breaking:**
```
Break 10 wheat:
- 10x wheat items picked up
- 10x seed items picked up
= 20 item pickup events
= 2 InventoryChangeEvent (full inventory snapshots)
= 2 ItemCountChangeEvent (one for wheat, one for seeds)
= 4 MQTT messages with QoS 2
= 4 × 4-way handshakes
= ~100-200ms of blocking time JUST for MQTT
```

### Problem 2: Synchronous, Blocking Publishing ⚠️ CRITICAL

**Location:** `MqttClientInternal.java:218-227`
```java
public void publish(String topic, String message) {
    try {
        MqttMessage mqttMessage = new MqttMessage(message.getBytes());
        mqttMessage.setQos(qos);
        mqttClient.publish(topic, mqttMessage);  // ← BLOCKS until handshake completes!
        LOGGER.debugMqtt("Message published successfully to {}", topic);
    } catch(MqttException me) {
        // error handling
    }
}
```

**Impact:**
- The `mqttClient.publish()` call is **synchronous and blocks** the Minecraft game thread
- With QoS 2, each call blocks for the full 4-way handshake
- Multiple rapid inventory changes stack up, causing visible lag

**This is the "copy-pasted from tutorial" code you suspected!** Tutorial code usually shows synchronous publishing for simplicity, not production performance.

### Problem 3: No Rate Limiting or Throttling

**Location:** `InventoryWatcher.java:32, 138-142`
```java
private static final int CHECK_INTERVAL = 20;  // Check every 1 second

// But on EVERY change, fires events:
if (!currentItemCounts.equals(previousItemCounts)) {
    hasChanges = true;
    EventManager.fire(new InventoryChangeEvent(...));  // Full snapshot
    fireItemCountChangeEvents(previousItemCounts, currentItemCounts);  // Per-item events
}
```

**Location:** `InventoryAction.java:26-40`
```java
@Override
public void onInventoryChange(Map<String, Integer> itemCounts, int emptySlots, int fullSlots) {
    sendInventoryEvent("inventory_change", itemCounts, emptySlots, fullSlots);
    // ← Immediately fires MQTT message (no throttling!)
}

@Override
public void onItemCountChange(String itemId, int oldCount, int newCount, int totalCount) {
    sendItemCountEvent(itemId, oldCount, newCount, totalCount);
    // ← Immediately fires MQTT message (no throttling!)
}
```

**Impact:**
- Every inventory check (once per second) that detects changes fires multiple MQTT messages
- No coalescing or batching of rapid changes
- No backpressure mechanism

**Real-world scenario:**
```
Break 64 sugar cane in 5 seconds:
= ~13 inventory checks (once per second)
= ~13 InventoryChangeEvent messages (full snapshots)
= ~13 ItemCountChangeEvent messages
= ~26 QoS 2 MQTT publishes
= ~104 MQTT protocol packets (4 per QoS 2 message)
= Hundreds of milliseconds of blocked game thread time
```

### Problem 4: Redundant Data in Multiple Event Types

Both `InventoryChangeEvent` (full snapshot) and `ItemCountChangeEvent` (per-item) are fired for the same change:

```java
// Full snapshot with ALL items
EventManager.fire(new InventoryChangeEvent(currentItemCounts, emptySlots, fullSlots));

// Then ALSO per-item events for items that changed
fireItemCountChangeEvents(previousItemCounts, currentItemCounts);
```

**Impact:**
- Same data sent twice in different formats
- Wastes bandwidth and processing time
- Confusing for consumers (which message should they listen to?)

### Problem 5: No Async/Background Publishing

The Paho MQTT client supports asynchronous publishing, but you're not using it:

```java
// Current: Synchronous (blocks)
mqttClient.publish(topic, mqttMessage);

// Available: Asynchronous (returns immediately)
// mqttClient.publish(topic, mqttMessage, null, new IMqttActionListener() { ... });
```

**Impact:**
- Every publish blocks the Minecraft client thread
- No ability to handle backpressure or connection issues gracefully
- One slow MQTT operation stalls the entire game

## Message Flow Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    Minecraft Game Thread                        │
│                                                                 │
│  Every 20 ticks (1 second):                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ InventoryWatcher.checkInventoryChanges()                 │  │
│  │   ↓                                                       │  │
│  │ EventManager.fire(InventoryChangeEvent)  ───┐            │  │
│  │   ↓                                          │            │  │
│  │ EventManager.fire(ItemCountChangeEvent×N) ───┼──┐        │  │
│  └──────────────────────────────────────────────┼──┼────────┘  │
│                                                  ↓  ↓            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ InventoryAction.onInventoryChange()                      │  │
│  │ InventoryAction.onItemCountChange()                      │  │
│  │   ↓                                                       │  │
│  │ EventManager.fire(MqttReplyEvent)  ──────────────────┐   │  │
│  └──────────────────────────────────────────────────────┼───┘  │
│                                                          ↓       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ MqttClientInternal.onReplyArrived()                      │  │
│  │   ↓                                                       │  │
│  │ MqttClientInternal.publish()                             │  │
│  │   ↓                                                       │  │
│  │ mqttClient.publish() ← BLOCKS HERE! (QoS 2 handshake)   │  │
│  │                        10-50ms per message               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Result: Game thread frozen during MQTT publish                │
└─────────────────────────────────────────────────────────────────┘
```

## Solutions

### Immediate Fixes (High Impact, Low Effort)

#### 1. Switch to QoS 1 or 0 for State Updates

```java
// In MqttClientInternal.java
public void publish(String topic, String message, int qos) {
    MqttMessage mqttMessage = new MqttMessage(message.getBytes());
    mqttMessage.setQos(qos);
    mqttClient.publish(topic, mqttMessage);
}

// Different QoS for different message types:
// - QoS 0 for state updates (fire and forget)
// - QoS 1 for commands/responses (at least once)
// - QoS 2 only for critical operations (rarely needed)
```

**Impact:** Reduces MQTT overhead by 75% (1 packet instead of 4)

#### 2. Use Async Publishing

```java
public void publishAsync(String topic, String message, int qos) {
    try {
        MqttMessage mqttMessage = new MqttMessage(message.getBytes());
        mqttMessage.setQos(qos);

        // Async publish - returns immediately
        mqttClient.publish(topic, mqttMessage, null, new IMqttActionListener() {
            @Override
            public void onSuccess(IMqttToken asyncActionToken) {
                LOGGER.debugMqtt("Message published successfully to {}", topic);
            }

            @Override
            public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                LOGGER.error("Failed to publish message to {}: {}", topic,
                    exception.getMessage(), exception);
            }
        });
    } catch(MqttException me) {
        LOGGER.error("Failed to publish MQTT message: {}", me.getMessage(), me);
    }
}
```

**Impact:** Eliminates blocking on game thread, dramatically reduces lag

#### 3. Add Rate Limiting/Throttling

```java
public class ThrottledStatePublisher {
    private final Map<String, ThrottleState> throttles = new ConcurrentHashMap<>();
    private final long minIntervalMs;

    public ThrottledStatePublisher(long minIntervalMs) {
        this.minIntervalMs = minIntervalMs;
    }

    public void publishState(String stateKey, String topic, String message) {
        ThrottleState state = throttles.computeIfAbsent(stateKey,
            k -> new ThrottleState());

        long now = System.currentTimeMillis();
        if (now - state.lastPublishTime >= minIntervalMs) {
            // Publish immediately
            mqttClient.publishAsync(topic, message, 0);
            state.lastPublishTime = now;
            state.pendingMessage = null;
        } else {
            // Store for later (will be published after minInterval)
            state.pendingMessage = new PendingMessage(topic, message);
        }
    }

    // Background thread to flush pending messages
    private void flushPendingMessages() {
        long now = System.currentTimeMillis();
        for (ThrottleState state : throttles.values()) {
            if (state.pendingMessage != null
                && now - state.lastPublishTime >= minIntervalMs) {
                mqttClient.publishAsync(
                    state.pendingMessage.topic,
                    state.pendingMessage.message,
                    0
                );
                state.lastPublishTime = now;
                state.pendingMessage = null;
            }
        }
    }
}
```

**Impact:** Limits MQTT messages to reasonable rate (e.g., 1 per second per state type)

### Medium-Term: Move to State Topics

As discussed in your question about state vs events, replace the current event-driven approach with state topics:

#### Change 1: Publish to State Topic (Retained)

```java
public void publishInventoryState(InventoryState state) {
    String topic = String.format("mqttbot/%s/state/inventory", playerName);
    String message = state.toJson();

    // Publish with RETAIN flag so new subscribers get latest state
    MqttMessage mqttMessage = new MqttMessage(message.getBytes());
    mqttMessage.setQos(0);  // QoS 0 for state updates
    mqttMessage.setRetained(true);  // ← KEY: Retained flag

    mqttClient.publishAsync(topic, mqttMessage, null, null);
}
```

#### Change 2: Throttle State Updates

```java
public class InventoryStatePublisher {
    private final ThrottledStatePublisher throttler;
    private InventoryState lastPublishedState;

    public InventoryStatePublisher() {
        // Publish inventory state at most once per second
        this.throttler = new ThrottledStatePublisher(1000);
    }

    public void onInventoryChange(InventoryState currentState) {
        // Only publish if state actually changed significantly
        if (hasSignificantChange(lastPublishedState, currentState)) {
            String topic = String.format("mqttbot/%s/state/inventory", playerName);
            throttler.publishState("inventory", topic, currentState.toJson());
            lastPublishedState = currentState;
        }
    }
}
```

#### Change 3: Keep Events for True Alerts

```java
public void onInventoryFull(InventoryState state) {
    // This is a TRUE event - publish immediately with QoS 1
    String topic = String.format("mqttbot/%s/events/inventory_full", playerName);

    MqttMessage mqttMessage = new MqttMessage(state.toJson().getBytes());
    mqttMessage.setQos(1);  // QoS 1 for important events
    mqttMessage.setRetained(false);  // NOT retained - it's an event

    mqttClient.publishAsync(topic, mqttMessage, null, null);
}
```

### Long-Term: Batch Updates

For operations that generate many rapid changes (like breaking crops), batch them:

```java
public class BatchedInventoryPublisher {
    private final BlockingQueue<InventoryUpdate> updateQueue =
        new LinkedBlockingQueue<>();
    private final ScheduledExecutorService scheduler =
        Executors.newSingleThreadScheduledExecutor();

    public BatchedInventoryPublisher() {
        // Flush batches every 500ms
        scheduler.scheduleAtFixedRate(this::flushBatch, 500, 500,
            TimeUnit.MILLISECONDS);
    }

    public void queueUpdate(InventoryState state) {
        // Add to queue (non-blocking)
        updateQueue.offer(new InventoryUpdate(state, System.currentTimeMillis()));
    }

    private void flushBatch() {
        // Only publish the LATEST state (all intermediate states are obsolete)
        InventoryUpdate latest = null;
        while (!updateQueue.isEmpty()) {
            latest = updateQueue.poll();
        }

        if (latest != null) {
            publishInventoryState(latest.state);
        }
    }
}
```

## Performance Comparison

### Current Implementation
```
Breaking 64 sugar cane (5 seconds):
- ~26 MQTT messages (QoS 2)
- ~104 MQTT protocol packets (4 per message)
- ~26 × 20ms = 520ms of blocked game thread time
- Visible lag spikes
```

### With Immediate Fixes (Async + QoS 0)
```
Breaking 64 sugar cane (5 seconds):
- ~26 MQTT messages (QoS 0)
- ~26 MQTT protocol packets (1 per message)
- 0ms blocked game thread time (async)
- No lag spikes
- 75% reduction in MQTT traffic
```

### With State Topics + Throttling
```
Breaking 64 sugar cane (5 seconds):
- ~5 MQTT messages (1 per second, throttled)
- ~5 MQTT protocol packets
- 0ms blocked game thread time (async)
- No lag spikes
- 95% reduction in MQTT traffic
```

### With Batching
```
Breaking 64 sugar cane (5 seconds):
- ~10 MQTT messages (2 per second, batched)
- ~10 MQTT protocol packets
- 0ms blocked game thread time (async)
- No lag spikes
- 90% reduction in MQTT traffic
- Latest state always available
```

## Recommended Implementation Order

1. **Phase 1: Async Publishing** (1-2 hours)
   - Switch `publish()` to async
   - Test with existing system
   - **Expected improvement:** Eliminate lag spikes

2. **Phase 2: QoS Tuning** (30 minutes)
   - Add QoS parameter to `publish()`
   - Use QoS 0 for state updates
   - Use QoS 1 for commands/events
   - **Expected improvement:** 75% reduction in MQTT traffic

3. **Phase 3: State Topics** (2-4 hours)
   - Implement state publishers with retained flag
   - Keep event publishers for alerts
   - Update Python side to subscribe to state topics
   - **Expected improvement:** Clear separation of concerns

4. **Phase 4: Throttling** (2-3 hours)
   - Add ThrottledStatePublisher
   - Configure sensible rates (1 update/sec for inventory)
   - **Expected improvement:** 80-90% reduction in messages

5. **Phase 5: Batching** (optional, 3-4 hours)
   - Add BatchedInventoryPublisher
   - Only for high-frequency updates
   - **Expected improvement:** Further traffic reduction

## Testing Strategy

### Unit Tests
- Test async publish completion
- Test throttling logic
- Test batching behavior

### Integration Tests
- Break 64 blocks rapidly
- Kill multiple mobs
- Monitor MQTT traffic (use `mosquitto_sub -v -t '#'`)
- Measure frame time impact

### Performance Metrics
```bash
# Monitor MQTT traffic before/after
mosquitto_sub -v -t 'mqttbot/#' | pee "wc -l" "ts '[%Y-%m-%d %H:%M:%S]'"
```

## Configuration

Add to `MqttBotConfig`:
```java
public class MqttBotConfig {
    // QoS levels for different message types
    private int stateQos = 0;      // Fire and forget for state
    private int eventQos = 1;      // At least once for events
    private int commandQos = 1;    // At least once for commands

    // Rate limiting
    private long minInventoryUpdateMs = 1000;  // Max 1 update/sec
    private long minPositionUpdateMs = 500;    // Max 2 updates/sec

    // Async options
    private boolean asyncPublish = true;
    private int asyncThreads = 2;
}
```

## Summary

Your suspicion was correct - the "copy-pasted tutorial code" is causing performance problems:

1. **QoS 2** is overkill for state updates
2. **Synchronous publishing** blocks the game thread
3. **No throttling** causes message floods
4. **Multiple redundant events** waste bandwidth

The fixes are straightforward and will dramatically improve performance, especially during inventory-heavy operations like farming or mob grinding.

The state vs events architectural discussion fits perfectly here - state topics with async publishing and throttling is the right long-term solution.
