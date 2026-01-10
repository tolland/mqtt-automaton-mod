package org.limepepper.mqttbot.action;

import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.event.EventManager;

public abstract class Feature {
    
    protected static final MqttCore MQTT_BOT_CLIENT = MqttCore.INSTANCE;
    protected static final EventManager EVENTS =
        MQTT_BOT_CLIENT.getEventManager();
}
