package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;
import org.limepepper.mqttbot.mixinterface.IClientPlayerEntity;

import java.util.ArrayList;

public interface PlayerMoveListener extends Listener
{
    public void onPlayerMove(IClientPlayerEntity player);

    public static class PlayerMoveEvent extends Event<PlayerMoveListener>
    {
        private final IClientPlayerEntity player;

        public PlayerMoveEvent(IClientPlayerEntity player)
        {
            this.player = player;
        }

        @Override
        public void fire(ArrayList<PlayerMoveListener> listeners)
        {
            for(PlayerMoveListener listener : listeners)
                listener.onPlayerMove(player);
        }

        @Override
        public Class<PlayerMoveListener> getListenerType()
        {
            return PlayerMoveListener.class;
        }
    }
}
