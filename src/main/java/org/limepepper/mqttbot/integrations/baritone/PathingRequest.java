package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * Represents a single Baritone pathing request with complete lifecycle
 * tracking. This class owns all data related to a goto command: correlation
 * IDs, target position, timing, current phase, and event history.
 *
 * <p>
 * Immutable after construction except for phase transitions and event logging.
 * </p>
 */
public final class PathingRequest
{
    private final CorrelationIds correlationIds;
    private final BlockPos targetPos;
    private final Instant startTime;
    private final List<String> eventTimeline;

    private PathingPhase phase;
    private Goal baritoneGoal;
    private String failureReason;
    private Instant completionTime;
    private BlockPos lastKnownPosition;
    private Instant lastPositionUpdateTime;

    /**
     * Creates a new pathing request
     *
     * @param correlationIds
     *            The correlation IDs from the incoming MQTT request
     * @param targetPos
     *            The target BlockPos from the request params (not from
     *            Baritone Goal)
     */
    public PathingRequest(CorrelationIds correlationIds, BlockPos targetPos)
    {
        this.correlationIds = java.util.Objects.requireNonNull(correlationIds,
            "correlationIds cannot be null");
        this.targetPos = java.util.Objects.requireNonNull(targetPos,
            "targetPos cannot be null");
        this.startTime = Instant.now();
        this.phase = PathingPhase.IDLE;
        this.eventTimeline = new ArrayList<>();
        this.lastPositionUpdateTime = Instant.now();

        logEvent("REQUEST_CREATED", String.format("Target: %s", targetPos));
    }

    // ========== Phase Management ==========

    public void transitionTo(PathingPhase newPhase)
    {
        PathingPhase oldPhase = this.phase;
        this.phase = newPhase;
        logEvent("PHASE_TRANSITION",
            String.format("%s -> %s", oldPhase, newPhase));

        if(newPhase.isTerminal())
        {
            this.completionTime = Instant.now();
        }
    }

    public PathingPhase getPhase()
    {
        return phase;
    }

    // ========== Event Timeline ==========

    public void logEvent(String eventType, String details)
    {
        Instant now = Instant.now();
        Duration elapsed = Duration.between(startTime, now);
        String entry = String.format("[+%.3fs] %s: %s",
            elapsed.toMillis() / 1000.0, eventType, details);
        eventTimeline.add(entry);
    }

    public List<String> getEventTimeline()
    {
        return new ArrayList<>(eventTimeline);
    }

    // ========== Baritone Goal Tracking ==========

    public void setBaritoneGoal(Goal goal)
    {
        this.baritoneGoal = goal;
        if(goal != null)
        {
            logEvent("BARITONE_GOAL_SET", goal.toString());
        }else
        {
            logEvent("BARITONE_GOAL_CLEARED", "");
        }
    }

    public Goal getBaritoneGoal()
    {
        return baritoneGoal;
    }

    // ========== Position Tracking for Stuck Detection ==========

    public void updatePosition(BlockPos currentPos)
    {
        this.lastKnownPosition = currentPos;
        this.lastPositionUpdateTime = Instant.now();
    }

    public BlockPos getLastKnownPosition()
    {
        return lastKnownPosition;
    }

    public Instant getLastPositionUpdateTime()
    {
        return lastPositionUpdateTime;
    }

    /**
     * Check if position hasn't changed for a certain duration
     *
     * @param currentPos
     *            Current player position
     * @param stuckThresholdSeconds
     *            How long without movement to consider stuck
     * @return true if stuck
     */
    public boolean isStuck(BlockPos currentPos, int stuckThresholdSeconds)
    {
        if(lastKnownPosition == null)
        {
            return false;
        }

        // If position changed, we're not stuck
        if(!currentPos.equals(lastKnownPosition))
        {
            return false;
        }

        // Position hasn't changed - check how long
        Duration timeSinceLastUpdate =
            Duration.between(lastPositionUpdateTime, Instant.now());
        return timeSinceLastUpdate.getSeconds() >= stuckThresholdSeconds;
    }

    // ========== Failure Tracking ==========

    public void setFailureReason(String reason)
    {
        this.failureReason = reason;
        logEvent("FAILURE", reason);
    }

    public String getFailureReason()
    {
        return failureReason;
    }

    // ========== Getters ==========

    public CorrelationIds getCorrelationIds()
    {
        return correlationIds;
    }

    public BlockPos getTargetPos()
    {
        return targetPos;
    }

    public Instant getStartTime()
    {
        return startTime;
    }

    public Instant getCompletionTime()
    {
        return completionTime;
    }

    public Duration getElapsedTime()
    {
        Instant end = (completionTime != null) ? completionTime : Instant.now();
        return Duration.between(startTime, end);
    }

    // ========== Serialization ==========

    public JsonObject toJson()
    {
        JsonObject json = new JsonObject();
        json.addProperty("requestId",
            correlationIds.requestId());
        json.addProperty("correlationId",
            correlationIds.correlationId());
        json.addProperty("targetX", targetPos.getX());
        json.addProperty("targetY", targetPos.getY());
        json.addProperty("targetZ", targetPos.getZ());
        json.addProperty("phase", phase.toString());
        json.addProperty("startTime", startTime.toString());
        json.addProperty("elapsedSeconds", getElapsedTime().getSeconds());

        if(completionTime != null)
        {
            json.addProperty("completionTime", completionTime.toString());
            json.addProperty("durationSeconds",
                Duration.between(startTime, completionTime).getSeconds());
        }

        if(failureReason != null)
        {
            json.addProperty("failureReason", failureReason);
        }

        if(lastKnownPosition != null)
        {
            json.addProperty("lastX", lastKnownPosition.getX());
            json.addProperty("lastY", lastKnownPosition.getY());
            json.addProperty("lastZ", lastKnownPosition.getZ());
        }

        return json;
    }

    @Override
    public String toString()
    {
        return String.format(
            "PathingRequest{requestId=%s, target=%s, phase=%s, elapsed=%.1fs}",
            correlationIds.requestId(), targetPos, phase,
            getElapsedTime().toMillis() / 1000.0);
    }
}
