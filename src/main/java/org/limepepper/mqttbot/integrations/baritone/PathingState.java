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
    }
    
    void done()
    {
        oldGoal = currentGoal;
        pathActive = false;
        announced = false;
        currentGoal = null;
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
