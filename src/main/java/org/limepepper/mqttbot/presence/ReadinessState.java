package org.limepepper.mqttbot.presence;

import com.google.gson.JsonObject;

import java.time.Instant;
import java.util.Objects;

/**
 * Device readiness state - whether device can currently accept tasks/commands.
 *
 * <p>
 * Examples:
 * <ul>
 * <li>Minecraft: IN_WORLD_READY (can accept goto commands)</li>
 * <li>Minecraft: IN_WORLD_DEAD (cannot accept commands)</li>
 * <li>IoT device: READY (can execute commands)</li>
 * <li>IoT device: UPDATING (firmware update in progress)</li>
 * </ul>
 * </p>
 */
public class ReadinessState
{
    private final boolean ready;
    private final String state;
    private final boolean canAcceptTasks;
    private final String reason;
    private final JsonObject additionalData;
    private final Instant timestamp;

    public ReadinessState(boolean ready, String state, boolean canAcceptTasks,
        String reason, JsonObject additionalData)
    {
        this.ready = ready;
        this.state = Objects.requireNonNull(state, "state cannot be null");
        this.canAcceptTasks = canAcceptTasks;
        this.reason = reason;
        this.additionalData = additionalData;
        this.timestamp = Instant.now();
    }

    /**
     * Create a ready state
     */
    public static ReadinessState ready(String state, String reason,
        JsonObject additionalData)
    {
        return new ReadinessState(true, state, true, reason, additionalData);
    }

    /**
     * Create a not-ready state
     */
    public static ReadinessState notReady(String state, String reason,
        JsonObject additionalData)
    {
        return new ReadinessState(false, state, false, reason, additionalData);
    }

    /**
     * Convert to JSON for MQTT publication
     */
    public JsonObject toJson()
    {
        JsonObject json = new JsonObject();
        json.addProperty("ready", ready);
        json.addProperty("state", state);
        json.addProperty("can_accept_tasks", canAcceptTasks);
        json.addProperty("reason", reason);
        json.addProperty("timestamp", timestamp.toString());

        if(additionalData != null)
        {
            // Merge additional data into root
            additionalData.entrySet().forEach(
                entry -> json.add(entry.getKey(), entry.getValue()));
        }

        return json;
    }

    // Getters

    public boolean isReady()
    {
        return ready;
    }

    public String getState()
    {
        return state;
    }

    public boolean canAcceptTasks()
    {
        return canAcceptTasks;
    }

    public String getReason()
    {
        return reason;
    }

    public Instant getTimestamp()
    {
        return timestamp;
    }

    @Override
    public String toString()
    {
        return String.format("ReadinessState{state=%s, ready=%s, reason=%s}",
            state, ready, reason);
    }
}
