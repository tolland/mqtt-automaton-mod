package org.limepepper.mqttbot.integrations.inventory;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.HashMap;
import java.util.Map;

/**
 * Handles incoming MQTT commands for inventory queries
 */
public final class InventoryQueryHandler extends Action
    implements MqttMessageListener {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(InventoryQueryHandler.class);
    
    public static final Minecraft MC = Minecraft.getInstance();
    
    public static void init()
    {
        EventManager.INSTANCE.add(MqttMessageListener.class,
            new InventoryQueryHandler());
    }
    
    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent)
    {
        ServiceMessage data = mqttMessageEvent.serviceMessage;
        
        if(!data.getService().equals("inventory"))
        {
            return;
        }
        
        System.out
            .println("[InventoryQueryHandler] Received inventory command: "
                + data.getMethod());
        
        switch(data.getMethod())
        {
            case "query":
            case "query_inventory":
            handleQueryInventory(data);
            break;
            
            case "get_item_count":
            handleGetItemCount(data);
            break;
            
            case "check_capacity":
            handleCheckCapacity(data);
            break;
            
            default:
            LOGGER.debug(
                "[InventoryQueryHandler] Unknown method: " + data.getMethod());
        }
    }
    
    /**
     * Return full inventory state
     */
    private void handleQueryInventory(ServiceMessage data)
    {
        if(MC.player == null)
        {
            sendErrorResponse(data, "Player not available");
            return;
        }
        
        Inventory inventory = MC.player.getInventory();
        Map<String, Integer> itemCounts = new HashMap<>();
        int emptySlots = 0;
        int fullSlots = 0;
        
        // Scan all inventory slots
        for(int i = 0; i < inventory.getNonEquipmentItems().size(); i++)
        {
            ItemStack stack = inventory.getNonEquipmentItems().get(i);
            
            if(stack.isEmpty())
            {
                emptySlots++;
            }else
            {
                fullSlots++;
                String itemId =
                    BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
                itemCounts.merge(itemId, stack.getCount(), Integer::sum);
            }
        }
        
        // Build response
        JsonObject responseData = new JsonObject();
        responseData.addProperty("emptySlots", emptySlots);
        responseData.addProperty("fullSlots", fullSlots);
        responseData.addProperty("totalSlots", emptySlots + fullSlots);
        
        JsonObject itemCountsJson = new JsonObject();
        for(Map.Entry<String, Integer> entry : itemCounts.entrySet())
        {
            itemCountsJson.addProperty(entry.getKey(), entry.getValue());
        }
        responseData.add("itemCounts", itemCountsJson);
        
        sendResponse(data, responseData);
    }
    
    /**
     * Return count of a specific item
     */
    private void handleGetItemCount(ServiceMessage data)
    {
        if(MC.player == null)
        {
            sendErrorResponse(data, "Player not available");
            return;
        }
        
        JsonElement paramsEl = data.getParams();
        if(paramsEl == null || !paramsEl.isJsonObject()
            || !paramsEl.getAsJsonObject().has("itemId"))
        {
            sendErrorResponse(data, "Missing 'itemId' parameter");
            return;
        }
        
        String targetItemId =
            paramsEl.getAsJsonObject().get("itemId").getAsString();
        Inventory inventory = MC.player.getInventory();
        int totalCount = 0;
        
        // Count the specific item
        for(int i = 0; i < inventory.getNonEquipmentItems().size(); i++)
        {
            ItemStack stack = inventory.getNonEquipmentItems().get(i);
            
            if(!stack.isEmpty())
            {
                String itemId =
                    BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
                if(itemId.equals(targetItemId))
                {
                    totalCount += stack.getCount();
                }
            }
        }
        
        JsonObject responseData = new JsonObject();
        responseData.addProperty("itemId", targetItemId);
        responseData.addProperty("count", totalCount);
        
        sendResponse(data, responseData);
    }
    
    /**
     * Check if inventory has space
     */
    private void handleCheckCapacity(ServiceMessage data)
    {
        if(MC.player == null)
        {
            sendErrorResponse(data, "Player not available");
            return;
        }
        
        Inventory inventory = MC.player.getInventory();
        int emptySlots = 0;
        
        for(int i = 0; i < inventory.getNonEquipmentItems().size(); i++)
        {
            if(inventory.getNonEquipmentItems().get(i).isEmpty())
            {
                emptySlots++;
            }
        }
        
        boolean isFull = (emptySlots == 0);
        
        JsonObject responseData = new JsonObject();
        responseData.addProperty("emptySlots", emptySlots);
        responseData.addProperty("isFull", isFull);
        responseData.addProperty("hasSpace", !isFull);
        
        sendResponse(data, responseData);
    }
    
    private void sendResponse(ServiceMessage originalData,
        JsonObject responseData)
    {
        String playerName = MC.getUser().getName();
        
        // Preserve the original requestId - don't create a new one!
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName,
            new ServiceMessage("inventory", originalData.getMethod(),
                originalData.getRequestId(), originalData.getCorrelationId(),
                null, responseData, "mqttbot", null)));
    }
    
    private void sendErrorResponse(ServiceMessage originalData, String error)
    {
        JsonObject responseData = new JsonObject();
        responseData.addProperty("error", error);
        sendResponse(originalData, responseData);
    }
}
