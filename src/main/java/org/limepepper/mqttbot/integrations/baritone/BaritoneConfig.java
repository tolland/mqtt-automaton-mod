package org.limepepper.mqttbot.integrations.baritone;

/**
 * Configuration settings for Baritone integration. This will be populated from
 * main config parsing in the future.
 */
public final class BaritoneConfig
{
    private static BaritoneConfig instance;

    // History settings
    private int maxHistorySize = 20;

    // Stuck detection settings
    private int stuckDetectionThresholdSeconds = 30;
    private boolean autoNudgeWhenStuck = true;

    // Timeout settings
    private int maxCalculationTimeSeconds = 60;
    private int maxPathingTimeSeconds = 300; // 5 minutes

    // "Close enough" heuristic for goal completion
    private double closeEnoughHeuristic = Constants.CLOSE_ENOUGH_HEURISTIC;

    private BaritoneConfig()
    {
        // Private constructor for singleton
    }

    public static synchronized BaritoneConfig getInstance()
    {
        if(instance == null)
        {
            instance = new BaritoneConfig();
        }
        return instance;
    }

    // ========== Getters and Setters ==========

    public int getMaxHistorySize()
    {
        return maxHistorySize;
    }

    public void setMaxHistorySize(int maxHistorySize)
    {
        this.maxHistorySize = Math.max(1, maxHistorySize);
        RequestHistory.INSTANCE.setMaxHistorySize(this.maxHistorySize);
    }

    public int getStuckDetectionThresholdSeconds()
    {
        return stuckDetectionThresholdSeconds;
    }

    public void setStuckDetectionThresholdSeconds(
        int stuckDetectionThresholdSeconds)
    {
        this.stuckDetectionThresholdSeconds =
            Math.max(5, stuckDetectionThresholdSeconds);
    }

    public boolean isAutoNudgeWhenStuck()
    {
        return autoNudgeWhenStuck;
    }

    public void setAutoNudgeWhenStuck(boolean autoNudgeWhenStuck)
    {
        this.autoNudgeWhenStuck = autoNudgeWhenStuck;
    }

    public int getMaxCalculationTimeSeconds()
    {
        return maxCalculationTimeSeconds;
    }

    public void setMaxCalculationTimeSeconds(int maxCalculationTimeSeconds)
    {
        this.maxCalculationTimeSeconds =
            Math.max(10, maxCalculationTimeSeconds);
    }

    public int getMaxPathingTimeSeconds()
    {
        return maxPathingTimeSeconds;
    }

    public void setMaxPathingTimeSeconds(int maxPathingTimeSeconds)
    {
        this.maxPathingTimeSeconds = Math.max(30, maxPathingTimeSeconds);
    }

    public double getCloseEnoughHeuristic()
    {
        return closeEnoughHeuristic;
    }

    public void setCloseEnoughHeuristic(double closeEnoughHeuristic)
    {
        this.closeEnoughHeuristic = Math.max(0, closeEnoughHeuristic);
    }
}
