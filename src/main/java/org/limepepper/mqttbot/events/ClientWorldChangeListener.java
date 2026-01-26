package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface ClientWorldChangeListener extends Listener {
    void onClientWorldChange(ClientWorldChangeEvent event);
    
    class ClientWorldChangeEvent extends Event<ClientWorldChangeListener> {
        private final String playerName;
        private final String world;
        
        public ClientWorldChangeEvent(String playerName, String world)
        {
            this.playerName = playerName;
            this.world = world;
        }
        
        public String getPlayerName()
        {
            return playerName;
        }
        
        public String getWorld()
        {
            return world;
        }
        
        @Override
        public void fire(ArrayList<ClientWorldChangeListener> listeners)
        {
            for(ClientWorldChangeListener listener : listeners)
                listener.onClientWorldChange(this);
        }
        
        @Override
        public Class<ClientWorldChangeListener> getListenerType()
        {
            return ClientWorldChangeListener.class;
        }
    }
}
