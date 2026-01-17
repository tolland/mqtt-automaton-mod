package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.time.Duration;
import java.time.Instant;

/**
 * Proper state machine for Baritone pathing requests. Tracks the current
 * request, phase transitions, and delegates to PathingRequest for detailed
 * tracking.
 *
 * <p>
 * This singleton manages ONE active request at a time. New requests preempt
 * existing ones (cancelling the old request and starting fresh).
 * </p>
 */
enum PathingState
{
    INSTANCE;

    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(PathingState.class);

    private PathingRequest currentRequest = null;

    // ========== Request Lifecycle ==========

    /**
     * Start a new pathing request. If there's an existing active request, it
     * will be cancelled.
     *
     * @param ids
     *            Correlation IDs from the incoming MQTT message
     * @param targetPos
     *            Target BlockPos from the request params
     */
    void startRequest(CorrelationIds ids, BlockPos targetPos)
    {
        // Cancel existing request if present
        if(currentRequest != null && currentRequest.getPhase().isActive())
        {
            LOGGER.warn("New request received while {} is active - cancelling old request",
                currentRequest.getPhase());
            currentRequest.transitionTo(PathingPhase.CANCELLED);
            currentRequest.logEvent("PREEMPTED", "New request received");
            RequestHistory.INSTANCE.recordRequest(currentRequest);
        }

        // Create new request
        currentRequest = new PathingRequest(ids, targetPos);
        LOGGER.info("Started new pathing request: {}", currentRequest);
    }

    /**
     * Transition current request to a new phase
     *
     * @param newPhase
     *            The phase to transition to
     */
    void transitionTo(PathingPhase newPhase)
    {
        if(currentRequest == null)
        {
            LOGGER.warn("Attempted to transition to {} but no active request",
                newPhase);
            return;
        }

        PathingPhase oldPhase = currentRequest.getPhase();
        currentRequest.transitionTo(newPhase);
        LOGGER.debug("Phase transition: {} -> {}", oldPhase, newPhase);

        // If reached terminal state, record to history
        if(newPhase.isTerminal())
        {
            RequestHistory.INSTANCE.recordRequest(currentRequest);
            if(newPhase == PathingPhase.IDLE)
            {
                currentRequest = null;
            }
        }
    }

    /**
     * Complete the current request successfully
     */
    void completeSuccess()
    {
        if(currentRequest != null)
        {
            transitionTo(PathingPhase.GOAL_REACHED);
            currentRequest = null; // Clear after recording
        }
    }

    /**
     * Fail the current request with a reason
     *
     * @param reason
     *            Why the request failed
     */
    void completeFailed(String reason)
    {
        if(currentRequest != null)
        {
            currentRequest.setFailureReason(reason);
            transitionTo(PathingPhase.FAILED);
            currentRequest = null; // Clear after recording
        }
    }

    // ========== State Queries ==========

    /**
     * Check if there's an active request
     *
     * @return true if a request is currently active
     */
    boolean hasActiveRequest()
    {
        return currentRequest != null && currentRequest.getPhase().isActive();
    }

    /**
     * Get current phase, or IDLE if no request
     *
     * @return current PathingPhase
     */
    PathingPhase getPhase()
    {
        return (currentRequest != null) ? currentRequest.getPhase()
            : PathingPhase.IDLE;
    }

    /**
     * Get the current request
     *
     * @return PathingRequest or null if none active
     */
    PathingRequest getCurrentRequest()
    {
        return currentRequest;
    }

    /**
     * Require that a request is active, throw if not
     *
     * @return The current PathingRequest
     * @throws IllegalStateException
     *             if no active request
     */
    PathingRequest requireActiveRequest()
    {
        if(currentRequest == null)
        {
            throw new IllegalStateException(
                "No active pathing request - cannot perform this operation");
        }
        return currentRequest;
    }

    /**
     * Get correlation IDs for the current request
     *
     * @return CorrelationIds or null if no active request
     */
    CorrelationIds getCorrelationIds()
    {
        return (currentRequest != null)
            ? currentRequest.getCorrelationIds()
            : null;
    }

    /**
     * Require correlation IDs, throw if not available
     *
     * @return CorrelationIds
     * @throws IllegalStateException
     *             if no active request
     */
    CorrelationIds requireCorrelationIds()
    {
        return requireActiveRequest().getCorrelationIds();
    }

    // ========== Baritone Goal Tracking ==========

    /**
     * Set the Baritone Goal object for tracking (nullable)
     *
     * @param goal
     *            The Goal from Baritone, or null
     */
    void setBaritoneGoal(Goal goal)
    {
        if(currentRequest != null)
        {
            currentRequest.setBaritoneGoal(goal);
        }
    }

    /**
     * Get the Baritone Goal object
     *
     * @return Goal or null
     */
    Goal getBaritoneGoal()
    {
        return (currentRequest != null) ? currentRequest.getBaritoneGoal()
            : null;
    }

    /**
     * Check if player is in the Baritone goal
     *
     * @param pos
     *            Player position
     * @return true if in goal
     */
    boolean isInGoal(BlockPos pos)
    {
        Goal goal = getBaritoneGoal();
        return goal != null && goal.isInGoal(pos);
    }

    // ========== Event Logging ==========

    /**
     * Log an event to the current request's timeline
     *
     * @param eventType
     *            Type of event
     * @param details
     *            Event details
     */
    void logEvent(String eventType, String details)
    {
        if(currentRequest != null)
        {
            currentRequest.logEvent(eventType, details);
        }
    }

    // ========== Stuck Detection ==========

    /**
     * Update player position for stuck detection
     *
     * @param currentPos
     *            Current player position
     */
    void updatePosition(BlockPos currentPos)
    {
        if(currentRequest != null)
        {
            currentRequest.updatePosition(currentPos);
        }
    }

    /**
     * Check if the bot appears to be stuck
     *
     * @param currentPos
     *            Current player position
     * @return true if stuck
     */
    boolean isStuck(BlockPos currentPos)
    {
        if(currentRequest == null)
        {
            return false;
        }

        int threshold =
            BaritoneConfig.getInstance().getStuckDetectionThresholdSeconds();
        return currentRequest.isStuck(currentPos, threshold);
    }

    // ========== Timeout Detection ==========

    /**
     * Check if current request has exceeded calculation timeout
     *
     * @return true if timed out
     */
    boolean hasCalculationTimedOut()
    {
        if(currentRequest == null
            || currentRequest.getPhase() != PathingPhase.CALCULATING)
        {
            return false;
        }

        long elapsed = currentRequest.getElapsedTime().getSeconds();
        int timeout =
            BaritoneConfig.getInstance().getMaxCalculationTimeSeconds();
        return elapsed > timeout;
    }

    /**
     * Check if current request has exceeded pathing timeout
     *
     * @return true if timed out
     */
    boolean hasPathingTimedOut()
    {
        if(currentRequest == null
            || currentRequest.getPhase() != PathingPhase.PATHING)
        {
            return false;
        }

        long elapsed = currentRequest.getElapsedTime().getSeconds();
        int timeout = BaritoneConfig.getInstance().getMaxPathingTimeSeconds();
        return elapsed > timeout;
    }

    // ========== JSON Serialization ==========

    /**
     * Serialize current state to JSON for MQTT transmission
     *
     * @return JsonObject representing current state
     */
    public JsonObject toJson()
    {
        JsonObject json = new JsonObject();
        json.addProperty("stateType", "pathingState");

        if(currentRequest != null)
        {
            json.addProperty("hasActiveRequest", true);
            json.addProperty("phase", currentRequest.getPhase().toString());
            json.addProperty("requestId",
                currentRequest.getCorrelationIds().requestId());
            json.addProperty("correlationId",
                currentRequest.getCorrelationIds().correlationId());

            BlockPos target = currentRequest.getTargetPos();
            json.addProperty("targetX", target.getX());
            json.addProperty("targetY", target.getY());
            json.addProperty("targetZ", target.getZ());

            json.addProperty("elapsedSeconds",
                currentRequest.getElapsedTime().getSeconds());

            // Include Baritone goal data if available
            Goal goal = currentRequest.getBaritoneGoal();
            if(goal != null)
            {
                GoalDataExtractor.GoalData goalData =
                    GoalDataExtractor.extract(goal);
                if(goalData != null)
                {
                    if(goalData.x() != null)
                        json.addProperty("baritoneGoalX", goalData.x());
                    if(goalData.y() != null)
                        json.addProperty("baritoneGoalY", goalData.y());
                    if(goalData.z() != null)
                        json.addProperty("baritoneGoalZ", goalData.z());
                    json.addProperty("baritoneGoalType", goalData.kind());
                }
            }

            // Include last known position if available
            BlockPos lastPos = currentRequest.getLastKnownPosition();
            if(lastPos != null)
            {
                json.addProperty("lastX", lastPos.getX());
                json.addProperty("lastY", lastPos.getY());
                json.addProperty("lastZ", lastPos.getZ());
            }
        }else
        {
            json.addProperty("hasActiveRequest", false);
            json.addProperty("phase", PathingPhase.IDLE.toString());
        }

        // Include history statistics
        json.add("historyStats", RequestHistory.INSTANCE.getStatistics());

        return json;
    }
}
