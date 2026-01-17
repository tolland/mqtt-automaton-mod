package org.limepepper.mqttbot.integrations.baritone;

/**
 * Represents the current phase of a Baritone pathing request. This tracks the
 * lifecycle of a goto command from initial request through completion or
 * failure.
 */
public enum PathingPhase
{
    /**
     * No active pathing request
     */
    IDLE,

    /**
     * Baritone is calculating a path to the goal
     */
    CALCULATING,

    /**
     * Baritone is actively moving along the calculated path
     */
    PATHING,

    /**
     * Player has reached the goal (or close enough)
     */
    GOAL_REACHED,

    /**
     * Pathing failed (path calculation failed, unreachable, etc.)
     */
    FAILED,

    /**
     * Baritone appears to be stuck (not making progress)
     */
    STUCK,

    /**
     * Request was cancelled (by user or by new request)
     */
    CANCELLED;

    /**
     * Check if this phase represents an active request (not terminal)
     *
     * @return true if request is still in progress
     */
    public boolean isActive()
    {
        return this == CALCULATING || this == PATHING || this == STUCK;
    }

    /**
     * Check if this phase represents a completed request (terminal state)
     *
     * @return true if request has reached a final state
     */
    public boolean isTerminal()
    {
        return this == GOAL_REACHED || this == FAILED || this == CANCELLED
            || this == IDLE;
    }
}
