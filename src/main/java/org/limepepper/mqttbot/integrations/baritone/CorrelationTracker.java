package org.limepepper.mqttbot.integrations.baritone;

import org.jetbrains.annotations.NotNull;
import org.limepepper.mqttbot.mqtt.MessageData;

/**
 * Tracks correlation information (requestId, correlationId, identity)
 */
public enum CorrelationTracker
{
    INSTANCE;
    
    private String requestId;
    private String correlationId;
    
    void setFrom(@NotNull MessageData data)
    {
        this.requestId = data.getRequestId();
        this.correlationId = data.getCorrelationId();
    }
    
    void clear()
    {
        this.requestId = null;
        this.correlationId = null;
    }
    
    public String getRequestId()
    {
        return requestId;
    }
    
    public String getCorrelationId()
    {
        return correlationId;
    }
    
}
