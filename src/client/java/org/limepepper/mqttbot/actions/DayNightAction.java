package org.limepepper.mqttbot.actions;

import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DayNightListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.UUID;

public class DayNightAction extends Action implements DayNightListener {
    
    @Override
    public void onNightStart()
    {
        sendTimeEvent("night_start", "Night has started");
    }
    
    @Override
    public void onDayStart()
    {
        sendTimeEvent("day_start", "Day has started");
    }
    
    private void sendTimeEvent(String eventType, String message)
    {
        try
        {
            var mc = Minecraft.getInstance();
            String playerName =
                (mc.player != null) ? mc.getUser().getName() : "unknown";
            
            // Create structured response data
            JsonObject responseData = new JsonObject();
            responseData.addProperty("event", eventType);
            responseData.addProperty("message", message);
            responseData.addProperty("player", playerName);
            responseData.addProperty("timestamp", System.currentTimeMillis());
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName,
                new MessageData("day_night", eventType,
                    UUID.randomUUID().toString(), null, null, responseData,
                    "mqttbot", null)));
            
        }catch(Exception e)
        {
            System.err.println("Error sending time event: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
