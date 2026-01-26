package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface ClientJoinListener extends Listener {
    void onClientJoin(ClientJoinEvent event);
    
    class ClientJoinEvent extends Event<ClientJoinListener> {
        private final String playerName;
        private final String world;
        
        public ClientJoinEvent(String playerName, String world)
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
        public void fire(ArrayList<ClientJoinListener> listeners)
        {
            for(ClientJoinListener listener : listeners)
                listener.onClientJoin(this);
        }
        
        @Override
        public Class<ClientJoinListener> getListenerType()
        {
            return ClientJoinListener.class;
        }
    }
}
