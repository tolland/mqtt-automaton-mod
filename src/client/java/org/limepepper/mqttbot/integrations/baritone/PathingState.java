package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import net.minecraft.core.BlockPos;

/**
 * Manages pathing state (active status, goals, announcements)
 */
class PathingState {
    private boolean pathActive = false;
    private boolean announced = false;
    
    private Goal oldGoal = null;
    private Goal currentGoal = null;
    private int posTick = 0;
    private BlockPos lastSentPos = null;
    
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
        if(++posTick >= BaritonePathing.POSITION_UPDATE_PERIOD_TICKS)
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
}
