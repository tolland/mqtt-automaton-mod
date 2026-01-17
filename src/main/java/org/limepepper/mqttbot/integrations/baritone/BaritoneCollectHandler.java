package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import com.google.gson.*;
import net.minecraft.world.item.Item;
import net.wurstclient.util.ItemUtils;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.action.Feature;
import org.limepepper.mqttbot.action.InventoryFullFeature;
import org.limepepper.mqttbot.action.RequiresFeatures;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ChatMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.limepepper.mqttbot.util.MsgUtils;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * BaritoneCollectHandler implements handler for '#collect <block> <range>'
 * command.
 * Baritone does not send an event at the end, so we look for various chat
 * messages that correspond to succes, failure, or inventory full.
 */
public final class BaritoneCollectHandler extends Action
    implements MessageHandler, ChatMessageListener, RequiresFeatures {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BaritoneCollectHandler.class);
    private static final Gson gson =
        new GsonBuilder().registerTypeAdapter(BaritoneCollectCommand.class,
            new BaritoneCollectCommandDeserializer()).create();
    
    // Message patterns that we are looking for
    private static final List<MessagePattern> MESSAGE_PATTERNS =
        new ArrayList<>();
    
    private BaritoneCollectHandler()
    {
        EventManager.INSTANCE.add(ChatMessageListener.class, this);
    }
    
    public static BaritoneCollectHandler create()
    {
        return new BaritoneCollectHandler();
    }
    
    @Override
    public boolean canHandle(MessageData msg)
    {
        return "baritone".equals(msg.getService())
            && "collect".equals(msg.getMethod());
    }
    
    @Override
    public void handle(MessageData msg)
    {
        requiredFeatures().forEach(CORE.features()::enable);
        CorrelationTracker.INSTANCE.setFrom(msg);
        MqttCore.INSTANCE.setBotState(MqttCore.BotState.BUSY);
        
        JsonElement paramsEl = msg.getParams();
        if(paramsEl == null || paramsEl.isJsonNull())
        {
            LOGGER.warn(
                "Missing params for baritone collect request (requestId={})",
                msg.getRequestId());
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
            CorrelationTracker.INSTANCE.clear();
            return;
        }
        
        BaritoneCollectCommand cmd;
        try
        {
            cmd = gson.fromJson(paramsEl, BaritoneCollectCommand.class);
        }catch(JsonParseException | NumberFormatException e)
        {
            LOGGER.error("Failed to parse BaritoneCollectCommand: {}",
                e.getMessage(), e);
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
            CorrelationTracker.INSTANCE.clear();
            return;
        }
        
        IBaritone baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        Item item = ItemUtils.getItemFromNameOrID(cmd.block);
        List<Item> items = new ArrayList<>();
        if(item != null)
        {
            items.add(item);
        }
        baritone.getCollectProcess().collect(items, cmd.range);
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
                LOGGER.debug("Matched chat pattern: {} - {}", pattern.source,
                    pattern.eventType);
                MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
                
                EventManager.fire(new MqttReplyListener.MqttReplyEvent(
                    MqttCore.INSTANCE.getPlayerName(),
                    MsgUtils.ctSuccess(CorrelationTracker.INSTANCE, "baritone",
                        "collect", pattern.eventType, message)));
                
                CorrelationTracker.INSTANCE.clear();
                requiredFeatures().forEach(CORE.features()::disable);
                break;
            }
        }
    }
    
    @Override
    public Set<Class<? extends Feature>> requiredFeatures()
    {
        return Set.of(InventoryFullFeature.class);
    }
    
    public record BaritoneCollectCommand(String block, int range)
    {}
    
    static
    {
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile("\\[Baritone\\] No more items to collect"),
            "baritone", "success"));
        MESSAGE_PATTERNS.add(new MessagePattern(
            Pattern.compile(
                "\\[Baritone\\] Collect failed - unable to path to items"),
            "baritone", "success"));
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
    
    static class BaritoneCollectCommandDeserializer
        implements JsonDeserializer<BaritoneCollectCommand> {
        
        @Override
        public BaritoneCollectCommand deserialize(JsonElement json,
            Type typeOfT, JsonDeserializationContext context)
            throws JsonParseException
        {
            if(json == null || json.isJsonNull())
            {
                throw new JsonParseException(
                    "Expected object for BaritoneCollectCommand but got null");
            }
            JsonObject obj = json.getAsJsonObject();
            
            JsonElement blockEl = obj.get("block");
            if(blockEl == null || blockEl.isJsonNull())
            {
                throw new JsonParseException("Missing required field: block");
            }
            String block = blockEl.getAsString();
            
            JsonElement rangeEl = obj.get("range");
            if(rangeEl == null || rangeEl.isJsonNull())
            {
                throw new JsonParseException("Missing required field: range");
            }
            int range = coerceToInt(rangeEl);
            
            return new BaritoneCollectCommand(block, range);
        }
        
        private int coerceToInt(JsonElement element)
        {
            if(element == null || element.isJsonNull())
            {
                throw new JsonParseException("Cannot coerce null to int");
            }
            
            if(element.isJsonPrimitive())
            {
                JsonPrimitive prim = element.getAsJsonPrimitive();
                if(prim.isNumber())
                {
                    return prim.getAsInt();
                }else if(prim.isString())
                {
                    return Integer.parseInt(prim.getAsString());
                }
            }
            throw new JsonParseException("Cannot coerce to int: " + element);
        }
    }
}
