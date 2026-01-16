package org.limepepper.mqttbot.integrations.baritone;

public enum Constants
{
    INSTANCE;
    
    // Constants
    static final int POSITION_UPDATE_PERIOD_TICKS = 100;
    static final double CLOSE_ENOUGH_HEURISTIC = 4.0;
    static final String SERVICE_NAME = "baritone";
    static final String DEFAULT_IDENTITY = "mqttbot";
}
