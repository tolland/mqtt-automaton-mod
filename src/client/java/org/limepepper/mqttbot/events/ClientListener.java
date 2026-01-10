package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface ClientListener extends Listener {
    public void onClientJoin();
    
    public static class ClientJoinEvent extends Event<ClientListener> {
        
        public static final ClientListener.ClientJoinEvent INSTANCE =
            new ClientListener.ClientJoinEvent();
        
        @Override
        public void fire(ArrayList<ClientListener> listeners)
        {
            for(ClientListener listener : listeners)
                listener.onClientJoin();
        }
        
        @Override
        public Class<ClientListener> getListenerType()
        {
            return ClientListener.class;
        }
    }
}
