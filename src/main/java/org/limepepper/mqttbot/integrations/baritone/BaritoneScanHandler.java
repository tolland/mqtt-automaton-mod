package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.wurstclient.util.BlockUtils;
import net.wurstclient.util.ItemUtils;
import org.jetbrains.annotations.Nullable;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.action.Feature;
import org.limepepper.mqttbot.action.InventoryFullFeature;
import org.limepepper.mqttbot.action.RequiresFeatures;
import org.limepepper.mqttbot.mqtt.MessageHandler;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.limepepper.mqttbot.util.BlockLists;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

/**
 */
public final class BaritoneScanHandler extends Action
    implements MessageHandler, RequiresFeatures {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BaritoneScanHandler.class);
    private static final Gson gson =
        new GsonBuilder().create();
    
    private CorrelationIds correlationIds = null;
    
    private BaritoneScanHandler()
    {
        
    }
    
    public static BaritoneScanHandler create()
    {
        return new BaritoneScanHandler();
    }
    
    @Override
    public boolean canHandle(ServiceMessage msg)
    {
        return "baritone".equals(msg.getService())
            && "scan".equals(msg.getMethod());
    }
    
    @Override
    public void handle(ServiceMessage msg)
    {
        requiredFeatures().forEach(CORE.features()::enable);
        
        // Extract and validate correlation IDs - fail fast if invalid
        this.correlationIds = CorrelationIds.fromMessage(msg);
        
        MqttCore.INSTANCE.setBotState(MqttCore.BotState.BUSY);
        
        JsonElement paramsEl = msg.getParams();
        if(paramsEl == null || paramsEl.isJsonNull())
        {
            LOGGER.warn(
                "Missing params for baritone scan request (requestId={})",
                msg.getRequestId());
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
            this.correlationIds = null;
            return;
        }
        
        BaritoneScanEntityCommand cmd;
        try
        {
            cmd = gson.fromJson(paramsEl, BaritoneScanEntityCommand.class);
        }catch(JsonParseException | NumberFormatException e)
        {
            LOGGER.error("Failed to parse BaritoneScanEntityCommand: {}",
                e.getMessage(), e);
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
            this.correlationIds = null;
            return;
        }
        
        IBaritone baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        Item item_param = ItemUtils.getItemFromNameOrID("minecraft:item_frame");
        List<Item> itemsToCollect = new ArrayList<>();
        if(item_param != null)
        {
            itemsToCollect.add(item_param);
        }
        
        int range = 5;
        BlockPos startPosition =
            MqttCore.baritone.getPlayerContext().player().blockPosition();
        
        for(Entity entity : MqttCore.baritone.getPlayerContext().entities())
        {
            if(entity instanceof ItemFrame itemFrame)
            {
                BlockPos attachedPos = itemFrame.getPos()
                    .relative(itemFrame.getDirection().getOpposite());
                Block block = BlockUtils.getBlock(attachedPos);
                
                if(BlockLists.CONTAINER_BLOCKS.contains(block))
                {
                    Item frameItem = itemFrame.getItem().getItem();
                    System.out.println("Container at " + attachedPos
                        + " has frame with: " + frameItem);
                    System.out.println(
                        "Block is: " + BlockUtils.getName(attachedPos));
                    
                }
            }
        }
    }
    
    @Override
    public Set<Class<? extends Feature>> requiredFeatures()
    {
        return Set.of(InventoryFullFeature.class);
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
    
    public record Coords(
        int x,
        int y,
        int z)
    {}
    
    public record BaritoneScanEntityCommand(String block,
        int range,
        @Nullable Coords origin)
    {}
    
}
