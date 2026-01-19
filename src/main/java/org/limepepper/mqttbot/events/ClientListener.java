package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface ClientListener extends Listener {
    void onClientJoin(ClientJoinEvent event);
    
    void onClientDisconnect(ClientDisconnectEvent event);
    
    class ClientJoinEvent extends Event<ClientListener> {
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
        public void fire(ArrayList<ClientListener> listeners)
        {
            for(ClientListener listener : listeners)
                listener.onClientJoin(this);
        }
        
        @Override
        public Class<ClientListener> getListenerType()
        {
            return ClientListener.class;
        }
    }
    
    public static class ClientDisconnectEvent extends Event<ClientListener> {
        private final String playerName;
        
        public ClientDisconnectEvent(String playerName)
        {
            this.playerName = playerName;
        }
        
        public String getPlayerName()
        {
            return playerName;
        }
        
        @Override
        public void fire(ArrayList<ClientListener> listeners)
        {
            for(ClientListener listener : listeners)
                listener.onClientDisconnect(this);
        }
        
        @Override
        public Class<ClientListener> getListenerType()
        {
            return ClientListener.class;
        }
    }
}
