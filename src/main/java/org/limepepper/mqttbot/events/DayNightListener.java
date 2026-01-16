package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface DayNightListener extends Listener {
    void onNightStart();
    
    void onDayStart();
    
    class NightStartEvent extends Event<DayNightListener> {
        public static final NightStartEvent INSTANCE = new NightStartEvent();
        
        @Override
        public void fire(ArrayList<DayNightListener> listeners)
        {
            for(DayNightListener listener : listeners)
                listener.onNightStart();
        }
        
        @Override
        public Class<DayNightListener> getListenerType()
        {
            return DayNightListener.class;
        }
    }
    
    class DayStartEvent extends Event<DayNightListener> {
        public static final DayStartEvent INSTANCE = new DayStartEvent();
        
        @Override
        public void fire(ArrayList<DayNightListener> listeners)
        {
            for(DayNightListener listener : listeners)
                listener.onDayStart();
        }
        
        @Override
        public Class<DayNightListener> getListenerType()
        {
            return DayNightListener.class;
        }
    }
}
