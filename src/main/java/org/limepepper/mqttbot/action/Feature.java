package org.limepepper.mqttbot.action;

import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.event.EventManager;

public abstract class Feature {
    
    protected static final MqttCore CORE = MqttCore.INSTANCE;
    protected static final EventManager EVENTS = CORE.getEventManager();
    
    protected void onEnable()
    {
        
    }
    
    protected void onDisable()
    {
        
    }
}
