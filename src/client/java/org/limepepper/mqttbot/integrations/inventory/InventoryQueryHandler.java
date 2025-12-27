package org.limepepper.mqttbot.integrations.inventory;

import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.core.registries.BuiltInRegistries;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Handles incoming MQTT commands for inventory queries
 */
public final class InventoryQueryHandler extends Action implements MqttMessageListener {

    public static final Minecraft MC = Minecraft.getInstance();

    public static void init() {
        EventManager.INSTANCE.add(MqttMessageListener.class, new InventoryQueryHandler());
    }

    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent) {
        MessageData data = mqttMessageEvent.messageData;

        if (!data.getService().equals("inventory")) {
            return;
        }

        System.out.println("[InventoryQueryHandler] Received inventory command: " + data.getMethod());

        switch (data.getMethod()) {
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
                System.out.println("[InventoryQueryHandler] Unknown method: " + data.getMethod());
        }
    }

    /**
     * Return full inventory state
     */
    private void handleQueryInventory(MessageData data) {
        if (MC.player == null) {
            sendErrorResponse(data, "Player not available");
            return;
        }

        Inventory inventory = MC.player.getInventory();
        Map<String, Integer> itemCounts = new HashMap<>();
        int emptySlots = 0;
        int fullSlots = 0;

        // Scan all inventory slots
        for (int i = 0; i < inventory.getNonEquipmentItems().size(); i++) {
            ItemStack stack = inventory.getNonEquipmentItems().get(i);

            if (stack.isEmpty()) {
                emptySlots++;
            } else {
                fullSlots++;
                String itemId = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
                itemCounts.merge(itemId, stack.getCount(), Integer::sum);
            }
        }

        // Build response
        JsonObject responseData = new JsonObject();
        responseData.addProperty("emptySlots", emptySlots);
        responseData.addProperty("fullSlots", fullSlots);
        responseData.addProperty("totalSlots", emptySlots + fullSlots);

        JsonObject itemCountsJson = new JsonObject();
        for (Map.Entry<String, Integer> entry : itemCounts.entrySet()) {
            itemCountsJson.addProperty(entry.getKey(), entry.getValue());
        }
        responseData.add("itemCounts", itemCountsJson);

        sendResponse(data, responseData);
    }

    /**
     * Return count of a specific item
     */
    private void handleGetItemCount(MessageData data) {
        if (MC.player == null) {
            sendErrorResponse(data, "Player not available");
            return;
        }

        if (data.getParams() == null || !data.getParams().has("itemId")) {
            sendErrorResponse(data, "Missing 'itemId' parameter");
            return;
        }

        String targetItemId = data.getParams().get("itemId").getAsString();
        Inventory inventory = MC.player.getInventory();
        int totalCount = 0;

        // Count the specific item
        for (int i = 0; i < inventory.getNonEquipmentItems().size(); i++) {
            ItemStack stack = inventory.getNonEquipmentItems().get(i);

            if (!stack.isEmpty()) {
                String itemId = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
                if (itemId.equals(targetItemId)) {
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
    private void handleCheckCapacity(MessageData data) {
        if (MC.player == null) {
            sendErrorResponse(data, "Player not available");
            return;
        }

        Inventory inventory = MC.player.getInventory();
        int emptySlots = 0;

        for (int i = 0; i < inventory.getNonEquipmentItems().size(); i++) {
            if (inventory.getNonEquipmentItems().get(i).isEmpty()) {
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

    private void sendResponse(MessageData originalData, JsonObject responseData) {
        String playerName = MC.getUser().getName();

        EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName, new MessageData(
                "inventory",
                originalData.getMethod(),
                UUID.randomUUID().toString(),
                originalData.getCorrelationId(),
                null,
                responseData,
                "mqttbot",
                null)
        ));
    }

    private void sendErrorResponse(MessageData originalData, String error) {
        JsonObject responseData = new JsonObject();
        responseData.addProperty("error", error);
        sendResponse(originalData, responseData);
    }
}
