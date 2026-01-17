package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;
import org.limepepper.mqttbot.util.MsgUtils;

import java.util.ArrayList;

/**
 * Listener for client or game originated chat messages.
 * These are messages that the player
 */
public interface ChatMessageSentListener extends Listener {
    
    void onChatMessageSent(ChatMessageSentEvent chatMessageSentEvent);
    
    class ChatMessageSentEvent extends Event<ChatMessageSentListener> {
        
        private final String message;
        private final long timestamp;
        
        public ChatMessageSentEvent(String message)
        {
            this.message = MsgUtils.stripColorCodes(message);
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
        public void fire(ArrayList<ChatMessageSentListener> listeners)
        {
            for(ChatMessageSentListener listener : listeners)
                listener.onChatMessageSent(this);
        }
        
        @Override
        public Class<ChatMessageSentListener> getListenerType()
        {
            return ChatMessageSentListener.class;
        }
    }
}
