package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

public interface ClientDisconnectListener extends Listener {
    void onClientDisconnect(ClientDisconnectEvent event);
    
    class ClientDisconnectEvent extends Event<ClientDisconnectListener> {
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
        public void fire(ArrayList<ClientDisconnectListener> listeners)
        {
            for(ClientDisconnectListener listener : listeners)
                listener.onClientDisconnect(this);
        }
        
        @Override
        public Class<ClientDisconnectListener> getListenerType()
        {
            return ClientDisconnectListener.class;
        }
    }
}
