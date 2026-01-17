package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;

import java.util.Objects;

/**
 * Extracts coordinate data from Baritone Goal objects using reflection
 */
class GoalDataExtractor {
    record GoalData(Integer x, Integer y, Integer z, String kind,
        String details)
    {
        GoalData(Integer x, Integer y, Integer z, String kind, String details)
        {
            this.x = x;
            this.y = y;
            this.z = z;
            this.kind = kind;
            this.details = details;
        }
    }
    
    static GoalData extract(Goal goal)
    {
        if(goal == null)
        {
            return null;
        }
        
        String kind = goal.getClass().getSimpleName();
        
        try
        {
            if(Objects.equals(kind, "GoalBlock"))
            {
                return extractGoalBlock(goal);
            }else if(Objects.equals(kind, "GoalXZ"))
            {
                return extractGoalXZ(goal);
            }else if(Objects.equals(kind, "GoalNear"))
            {
                return extractGoalNear(goal);
            }
        }catch(Throwable ignore)
        {
            // Reflection failed, return basic info
        }
        
        return new GoalData(null, null, null, kind, "");
    }
    
    private static GoalData extractGoalBlock(Goal goal) throws Exception
    {
        var method = goal.getClass().getMethod("getPos");
        Object pos = method.invoke(goal);
        int x = (int)pos.getClass().getMethod("getX").invoke(pos);
        int y = (int)pos.getClass().getMethod("getY").invoke(pos);
        int z = (int)pos.getClass().getMethod("getZ").invoke(pos);
        return new GoalData(x, y, z, "GoalBlock", goal.toString());
    }
    
    private static GoalData extractGoalXZ(Goal goal) throws Exception
    {
        int x = (int)goal.getClass().getMethod("getX").invoke(goal);
        int z = (int)goal.getClass().getMethod("getZ").invoke(goal);
        return new GoalData(x, null, z, "GoalXZ", goal.toString());
    }
    
    private static GoalData extractGoalNear(Goal goal) throws Exception
    {
        int x = (int)goal.getClass().getMethod("getX").invoke(goal);
        int y = (int)goal.getClass().getMethod("getY").invoke(goal);
        int z = (int)goal.getClass().getMethod("getZ").invoke(goal);
        return new GoalData(x, y, z, "GoalNear", goal.toString());
    }
}
