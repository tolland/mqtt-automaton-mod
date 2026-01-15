package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface DeathListener extends Listener {
    public void onDeath();
    
    public static class DeathEvent extends Event<DeathListener> {
        public static final DeathEvent INSTANCE = new DeathEvent();
        
        @Override
        public void fire(ArrayList<DeathListener> listeners)
        {
            for(DeathListener listener : listeners)
                listener.onDeath();
        }
        
        @Override
        public Class<DeathListener> getListenerType()
        {
            return DeathListener.class;
        }
    }
}
