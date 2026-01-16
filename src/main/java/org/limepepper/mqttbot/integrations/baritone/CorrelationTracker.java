package org.limepepper.mqttbot.integrations.baritone;

import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.UUID;

/**
 * Tracks correlation information (requestId, correlationId, identity)
 */
public class CorrelationTracker {
    private String requestId;
    private String correlationId;
    private String identity;
    
    void setFrom(MessageData data)
    {
        this.requestId = data.getRequestId();
        this.correlationId = data.getCorrelationId();
        this.identity = data.getIdentity();
    }
    
    void clear()
    {
        this.requestId = null;
        this.correlationId = null;
        this.identity = null;
    }
    
    public String getRequestId()
    {
        return requestId != null ? requestId : UUID.randomUUID().toString();
    }
    
    public String getCorrelationId()
    {
        return correlationId;
    }
    
    String getIdentity()
    {
        return identity != null ? identity : BaritonePathing.DEFAULT_IDENTITY;
    }
}
