package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.ArrayList;

/**
 * Listener to send replies or status to external modules.
 */
public interface MqttReplyListener extends Listener {

    void onReplyArrived(MqttReplyEvent mqttReplyEvent);

    public static class MqttReplyEvent extends Event<MqttReplyListener> {


        public String botId;
        public MessageData messageData;

        public MqttReplyEvent(String botId, MessageData messageData) {
            this.botId = botId;
            this.messageData = messageData;
        }

        @Override
        public void fire(ArrayList<MqttReplyListener> listeners) {
            for (MqttReplyListener listener : listeners)
                listener.onReplyArrived(this);
        }

        @Override
        public Class<MqttReplyListener> getListenerType() {
            return MqttReplyListener.class;
        }
    }

}
