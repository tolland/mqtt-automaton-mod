package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import baritone.api.behavior.IPathingBehavior;
import com.google.gson.Gson;
import net.minecraft.world.item.Item;
import net.wurstclient.util.ItemUtils;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;

import java.util.ArrayList;
import java.util.List;

public final class BaritoneCollectHandler
    implements MessageHandler {
    private static final Gson gson = new Gson();
    private static IBaritone baritone;
    private static IPathingBehavior pathing;

    @Override
    public boolean canHandle(MessageData msg)
    {
        return "baritone".equals(msg.getService())
            && "collect".equals(msg.getMethod());
    }

    
    @Override
    public void handle(MessageData msg)
    {
        BaritoneCollectCommand cmd = gson.fromJson(msg.getParams(), BaritoneCollectCommand.class);

        baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        Item item = ItemUtils.getItemFromNameOrID(cmd.block);
        List<Item> items = new ArrayList<>();
        if(item != null)
        {
            items.add(item);
        }
        baritone.getCollectProcess().collect(items, cmd.range);
    }
    
    public record BaritoneCollectCommand(String block, int range)
    {}
}
