package org.limepepper.mqttbot.actions;

import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ChatMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.limepepper.mqttbot.util.MsgUtils;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * Handles generic chat and command messages. It is also used to handle
 * messages that are directly inserted into the chat box by other mods, such as
 * Baritone and Wurst.
 * Filters for completion messages and sends them as MQTT events.
 */
public class ChatMessageAction extends Action implements ChatMessageListener {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(ChatMessageAction.class);
    
    // Message patterns to watch for
    private static final List<MessagePattern> MESSAGE_PATTERNS =
        new ArrayList<>();
    
    static
    {
        // Baritone completion messages
        MESSAGE_PATTERNS.add(
            new MessagePattern(Pattern.compile("\\[Baritone\\] Done building"),
                "baritone", "building_complete"));
        MESSAGE_PATTERNS.add(
            new MessagePattern(Pattern.compile("\\[Baritone\\] Goal reached"),
                "baritone", "goal_reached"));
        MESSAGE_PATTERNS.add(
            new MessagePattern(Pattern.compile("\\[Baritone\\] .* completed"),
                "baritone", "task_complete"));
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile("\\[Baritone\\] .* No more items to collect"),
            "baritone", "collect_complete"));
        
        // Wurst completion messages (strip color codes for matching)
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile("\\[Wurst\\].*AutoShopGUI completed successfully!"),
            "wurst", "autoshop_complete"));
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile("\\[Wurst\\].*All items sold successfully!"),
            "wurst", "items_sold"));
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile("\\[Wurst\\].*completed successfully!"), "wurst",
            "task_complete"));
        
        // Server restart messages
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile("The server will restart in \\d+ minute"), "server",
            "restart_warning"));
        MESSAGE_PATTERNS
            .add(new MessagePattern(Pattern.compile("Server is restarting"),
                "server", "restart_imminent"));
    }
    
    @Override
    public void onChatMessage(ChatMessageEvent event)
    {
        String message = event.getMessage();
        
        // Strip Minecraft color codes for pattern matching
        String cleanMessage = MsgUtils.stripColorCodes(message);
        
        // Check each pattern
        for(MessagePattern pattern : MESSAGE_PATTERNS)
        {
            if(pattern.matches(cleanMessage))
            {
                LOGGER.info("Matched chat pattern: {} - {}", pattern.source,
                    pattern.eventType);
                sendChatEvent(pattern.source, pattern.eventType, message,
                    cleanMessage);
                // Only match the first pattern
                break;
            }
        }
    }
    
    /**
     * Send a chat event via MQTT
     */
    private void sendChatEvent(String source, String eventType,
        String rawMessage, String cleanMessage)
    {
        try
        {
            var mc = Minecraft.getInstance();
            String playerName =
                (mc.player != null) ? mc.getUser().getName() : "unknown";
            
            // Create structured response data
            JsonObject resp = new JsonObject();
            resp.addProperty("source", source);
            resp.addProperty("event_type", eventType);
            resp.addProperty("raw_message", rawMessage);
            resp.addProperty("clean_message", cleanMessage);
            resp.addProperty("player", playerName);
            // timestamp is provided at the ServiceMessage level; don't
            // duplicate
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName,
                new ServiceMessage("events", "chat_message",
                    UUID.randomUUID().toString(), null, null, resp, "mqttbot",
                    null)));
            
            LOGGER.debug("Sent chat event: {} / {}", source, eventType);
            
        }catch(Exception e)
        {
            LOGGER.error("Error sending chat event: {}", e.getMessage(), e);
        }
    }
    
    /**
     * Helper class to store message patterns
     */
    private static class MessagePattern {
        final Pattern pattern;
        final String source;
        final String eventType;
        
        MessagePattern(Pattern pattern, String source, String eventType)
        {
            this.pattern = pattern;
            this.source = source;
            this.eventType = eventType;
        }
        
        boolean matches(String message)
        {
            return pattern.matcher(message).find();
        }
    }
}
