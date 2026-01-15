package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface DamageListener extends Listener {
    public void onDamage();
    
    public static class DamageEvent extends Event<DamageListener> {
        public static final DamageEvent INSTANCE = new DamageEvent();
        
        @Override
        public void fire(ArrayList<DamageListener> listeners)
        {
            for(DamageListener listener : listeners)
                listener.onDamage();
        }
        
        @Override
        public Class<DamageListener> getListenerType()
        {
            return DamageListener.class;
        }
    }
}
