package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;

import java.util.ArrayList;

/**
 * modules that have an interest in incoming messages, such as
 * baritone or wurst implement this listener
 */
public interface MqttMessageListener extends Listener {
    
    void onMessageArrived(MqttMessageEvent mqttMessageEvent);
    
    public static class MqttMessageEvent extends Event<MqttMessageListener> {
        
        public String receiver;
        public ServiceMessage serviceMessage;
        
        public MqttMessageEvent(String receiver, ServiceMessage serviceMessage)
        {
            this.receiver = receiver;
            this.serviceMessage = serviceMessage;
        }
        
        @Override
        public void fire(ArrayList<MqttMessageListener> listeners)
        {
            for(MqttMessageListener listener : listeners)
                listener.onMessageArrived(this);
        }
        
        @Override
        public Class<MqttMessageListener> getListenerType()
        {
            return MqttMessageListener.class;
        }
    }
    
}
