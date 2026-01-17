package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface HeartbeatListener extends Listener {
    void onHeartbeat();
    
    class HeaertbeatEvent extends Event<HeartbeatListener> {
        public static final HeaertbeatEvent INSTANCE = new HeaertbeatEvent();
        
        @Override
        public void fire(ArrayList<HeartbeatListener> listeners)
        {
            for(HeartbeatListener listener : listeners)
                listener.onHeartbeat();
        }
        
        @Override
        public Class<HeartbeatListener> getListenerType()
        {
            return HeartbeatListener.class;
        }
    }
}
