package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;

/**
 * Listener for chat messages intercepted from the chat HUD.
 * This includes messages from mods (Wurst, Baritone) and server messages.
 */
public interface ChatMessageListener extends Listener {

    void onChatMessage(ChatMessageEvent chatMessageEvent);

    public static class ChatMessageEvent extends Event<ChatMessageListener> {

        private final String message;
        private final long timestamp;

        public ChatMessageEvent(String message)
        {
            this.message = message;
            this.timestamp = System.currentTimeMillis();
        }

        public String getMessage()
        {
            return message;
        }

        public long getTimestamp()
        {
            return timestamp;
        }

        @Override
        public void fire(ArrayList<ChatMessageListener> listeners)
        {
            for(ChatMessageListener listener : listeners)
                listener.onChatMessage(this);
        }

        @Override
        public Class<ChatMessageListener> getListenerType()
        {
            return ChatMessageListener.class;
        }
    }
}
