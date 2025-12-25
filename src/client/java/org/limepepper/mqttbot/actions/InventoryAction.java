package org.limepepper.mqttbot.actions;

import com.google.gson.JsonObject;
import net.minecraft.client.MinecraftClient;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.InventoryListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.Map;
import java.util.UUID;

/**
 * Converts inventory events into MQTT messages
 */
public class InventoryAction extends Action implements InventoryListener {

    @Override
    public void onInventoryChange(Map<String, Integer> itemCounts, int emptySlots, int fullSlots) {
        sendInventoryEvent("inventory_change", itemCounts, emptySlots, fullSlots);
    }

    @Override
    public void onInventoryFull(Map<String, Integer> itemCounts) {
        sendInventoryEvent("inventory_full", itemCounts, 0, itemCounts.size());
    }

    @Override
    public void onItemCountChange(String itemId, int oldCount, int newCount, int totalCount) {
        sendItemCountEvent(itemId, oldCount, newCount, totalCount);
    }

    private void sendInventoryEvent(String eventType, Map<String, Integer> itemCounts,
                                    int emptySlots, int fullSlots) {
        try {
            var mc = MinecraftClient.getInstance();
            String playerName = (mc.player != null) ? mc.getSession().getUsername() : "unknown";

            // Create structured response data
            JsonObject responseData = new JsonObject();
            responseData.addProperty("event", eventType);
            responseData.addProperty("emptySlots", emptySlots);
            responseData.addProperty("fullSlots", fullSlots);
            responseData.addProperty("totalSlots", emptySlots + fullSlots);
            responseData.addProperty("player", playerName);
            responseData.addProperty("timestamp", System.currentTimeMillis());

            // Add item counts
            JsonObject itemCountsJson = new JsonObject();
            for (Map.Entry<String, Integer> entry : itemCounts.entrySet()) {
                itemCountsJson.addProperty(entry.getKey(), entry.getValue());
            }
            responseData.add("itemCounts", itemCountsJson);

            EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName, new MessageData(
                    "inventory",
                    eventType,
                    UUID.randomUUID().toString(),
                    null,
                    null,
                    responseData,
                    "mqttbot",
                    null)
            ));

            System.out.println("[InventoryAction] Sent " + eventType + " event: "
                + fullSlots + " full slots, " + emptySlots + " empty slots");

        } catch (Exception e) {
            System.err.println("Error sending inventory event: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void sendItemCountEvent(String itemId, int oldCount, int newCount, int totalCount) {
        try {
            var mc = MinecraftClient.getInstance();
            String playerName = (mc.player != null) ? mc.getSession().getUsername() : "unknown";

            // Create structured response data
            JsonObject responseData = new JsonObject();
            responseData.addProperty("event", "item_count_change");
            responseData.addProperty("itemId", itemId);
            responseData.addProperty("oldCount", oldCount);
            responseData.addProperty("newCount", newCount);
            responseData.addProperty("totalCount", totalCount);
            responseData.addProperty("delta", newCount - oldCount);
            responseData.addProperty("player", playerName);
            responseData.addProperty("timestamp", System.currentTimeMillis());

            EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName, new MessageData(
                    "inventory",
                    "item_count_change",
                    UUID.randomUUID().toString(),
                    null,
                    null,
                    responseData,
                    "mqttbot",
                    null)
            ));

            System.out.println("[InventoryAction] Item count change: " + itemId
                + " (" + oldCount + " -> " + newCount + ")");

        } catch (Exception e) {
            System.err.println("Error sending item count event: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
