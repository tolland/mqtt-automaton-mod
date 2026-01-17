package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * Manages pathing state (active status, goals, announcements)
 */
enum PathingState
{
    INSTANCE;
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(PathingState.class);
    
    private boolean pathActive = false;
    private boolean announced = false;

    /**
     * Correlation IDs for the current pathing task. Set when a goto command is
     * received and cleared when the task completes or fails. This allows
     * responses to include the proper requestId and correlationId without
     * relying on fragile global state.
     */
    private CorrelationIds correlationIds = null;

    private Goal oldGoal = null;
    private Goal currentGoal = null;
    private int posTick = 0;
    private BlockPos lastSentPos = null;
    private float poxX = Float.NaN;
    private float poxY = Float.NaN;
    private float poxZ = Float.NaN;
    
    public void setPos(float x, float y, float z)
    {
        this.poxX = x;
        this.poxY = y;
        this.poxZ = z;
    }
    
    public Coords getPos()
    {
        return new Coords(poxX, poxY, poxZ);
    }

    /**
     * Sets the correlation IDs for the current pathing task. Should be called
     * when a goto command is received.
     *
     * @param ids
     *            The validated correlation IDs from the incoming request
     * @throws NullPointerException
     *             if ids is null
     */
    void setCorrelationIds(CorrelationIds ids)
    {
        this.correlationIds =
            java.util.Objects.requireNonNull(ids, "CorrelationIds cannot be null");
    }

    /**
     * Gets the correlation IDs for the current pathing task.
     *
     * @return The correlation IDs, or null if no task is active
     */
    CorrelationIds getCorrelationIds()
    {
        return correlationIds;
    }

    /**
     * Gets the correlation IDs for the current pathing task, throwing an
     * exception if not set. Use this when you expect IDs to be present and
     * want to fail fast if they're missing.
     *
     * @return The correlation IDs
     * @throws IllegalStateException
     *             if correlation IDs are not set
     */
    CorrelationIds requireCorrelationIds()
    {
        if(correlationIds == null)
        {
            throw new IllegalStateException(
                "CorrelationIds not set - this indicates a bug in the pathing state machine");
        }
        return correlationIds;
    }
    
    void setPathActive(boolean active)
    {
        this.pathActive = active;
    }
    
    boolean isPathActive()
    {
        return pathActive;
    }
    
    void setAnnounced(boolean announced)
    {
        this.announced = announced;
    }
    
    boolean isAnnounced()
    {
        return announced;
    }
    
    /**
     * This is the methd to call to indicate you have arrived, but
     * before process the don actions, this acts as a debounce flag
     *
     * @param goal
     *            Current pathing Goal from Baritone
     */
    void updateGoal(Goal goal)
    {
        this.oldGoal = this.currentGoal;
        this.currentGoal = goal;
    }
    
    void setGoal(Goal goal)
    {
        this.currentGoal = goal;
    }
    
    Goal getCurrentGoal()
    {
        return currentGoal;
    }
    
    public Goal getOldGoal()
    {
        return oldGoal;
    }
    
    boolean isInGoal(BlockPos pos)
    {
        return currentGoal != null && currentGoal.isInGoal(pos);
    }
    
    boolean hasGoalChanged()
    {
        return oldGoal != currentGoal;
    }
    
    boolean changed()
    {
        return hasGoalChanged();
    }
    
    void reset()
    {
        LOGGER.debug("Resetting pathing state");
        oldGoal = null;
        pathActive = false;
        announced = false;
        currentGoal = null;
        correlationIds = null;
    }
    
    void done()
    {
        oldGoal = currentGoal;
        pathActive = false;
        announced = false;
        currentGoal = null;
        correlationIds = null;
    }
    
    boolean shouldSendPosition()
    {
        if(++posTick >= Constants.POSITION_UPDATE_PERIOD_TICKS)
        {
            posTick = 0;
            return true;
        }
        return false;
    }
    
    boolean hasPositionChanged(BlockPos newPos)
    {
        if(!newPos.equals(lastSentPos))
        {
            lastSentPos = newPos;
            return true;
        }
        return false;
    }
    
    public JsonObject toJson()
    {
        JsonObject json = new JsonObject();
        json.addProperty("stateType", "pathingState");
        json.addProperty("pathActive", pathActive);
        json.addProperty("announced", announced);
        if(currentGoal != null)
        {
            GoalDataExtractor.GoalData goalData =
                GoalDataExtractor.extract(currentGoal);
            if(goalData != null)
            {
                if(goalData.x() != null)
                    json.addProperty("goalX", goalData.x());
                if(goalData.y() != null)
                    json.addProperty("goalY", goalData.y());
                if(goalData.z() != null)
                    json.addProperty("goalZ", goalData.z());
                json.addProperty("goalType", goalData.kind());
                json.addProperty("goalDetails", goalData.details());
            }
        }else
        {
            json.addProperty("goalType", (String)null);
        }
        
        json.add("coords", getPos().toJson());
        
        return json;
    }
}
