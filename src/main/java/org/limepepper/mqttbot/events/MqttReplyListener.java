package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;

import java.util.ArrayList;

/**
 * Listener to send replies or status to external modules.
 */
public interface MqttReplyListener extends Listener {
    
    void onReplyArrived(MqttReplyEvent mqttReplyEvent);
    
    class MqttReplyEvent extends Event<MqttReplyListener> {
        
        public String botId;
        public ServiceMessage serviceMessage;
        public String topic;
        
        public MqttReplyEvent(String botId, ServiceMessage serviceMessage)
        {
            this(botId, serviceMessage, "reply");
        }
        
        public MqttReplyEvent(String botId, ServiceMessage serviceMessage,
            String topic)
        {
            this.botId = botId;
            this.serviceMessage = serviceMessage;
            this.topic = topic;
        }
        
        @Override
        public void fire(ArrayList<MqttReplyListener> listeners)
        {
            for(MqttReplyListener listener : listeners)
                listener.onReplyArrived(this);
        }
        
        @Override
        public Class<MqttReplyListener> getListenerType()
        {
            return MqttReplyListener.class;
        }
    }
    
}
