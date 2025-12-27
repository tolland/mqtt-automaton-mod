package org.limepepper.mqttbot.integrations.warp;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import net.minecraft.client.Minecraft;
import com.google.gson.JsonObject;

/**
 * Message handler for warp/teleport commands
 * Processes MQTT messages for the warp service
 */
public final class WarpMessageHandler extends Action implements MqttMessageListener {

    public static final WarpMessageHandler INSTANCE = new WarpMessageHandler();
    public static final Minecraft MC = Minecraft.getInstance();

    private WarpMessageHandler() {
    }

    /**
     * Initialize the warp message handler
     */
    public static void init() {
        EventManager.INSTANCE.add(MqttMessageListener.class, WarpMessageHandler.INSTANCE);
        System.out.println("WarpMessageHandler initialized");
    }

    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent) {
        MessageData data = mqttMessageEvent.messageData;
        System.out.println("Received message in warp handler");
        
        if (!data.getService().equals("warp")) {
            return;
        }
        
        System.out.println("Message for warp service: " + data.getMethod());
        
        switch (data.getMethod()) {
            case "teleport":
                handleTeleportCommand(data);
                break;
            default:
                System.out.println("Unknown method in warp service: " + data.getMethod());
        }
    }
    
    /**
     * Handle teleport command
     */
    private void handleTeleportCommand(MessageData data) {
        try {
            if (MC.player == null) {
                System.out.println("Error: Player is null, cannot execute warp command");
                return;
            }
            
            JsonObject params = data.getParams();
            if (params == null) {
                System.out.println("Error: warp teleport command missing params");
                return;
            }
            
            // Extract parameters
            String warpName = params.has("name") ? params.get("name").getAsString() : null;
            Integer radius = params.has("radius") ? params.get("radius").getAsInt() : 5;
            String commandTemplate = params.has("command_template") ? params.get("command_template").getAsString() : "warp {name}";
            
            // Extract target coordinates
            JsonObject target = params.has("target") ? params.getAsJsonObject("target") : null;
            if (target == null || !target.has("x") || !target.has("y") || !target.has("z")) {
                System.out.println("Error: warp teleport command missing target coordinates");
                return;
            }
            
            double targetX = target.get("x").getAsDouble();
            double targetY = target.get("y").getAsDouble();
            double targetZ = target.get("z").getAsDouble();
            
            if (warpName == null || warpName.trim().isEmpty()) {
                System.out.println("Error: warp teleport command missing name");
                return;
            }
            
            // Build warp command using template from params (supports different server plugins)
            // Examples: "warp {name}", "home tp {name}", "/warp {name}", "/home {name}"
            String warpCommand = commandTemplate.replace("{name}", warpName);
            System.out.println("Executing warp command: " + warpCommand);

            // Send the warp command
            MC.getConnection().sendCommand(warpCommand);
            
            // Start position monitoring
            WarpUtil.start(data.getRequestId(), warpName, targetX, targetY, targetZ, radius);
            
        } catch (Exception e) {
            System.out.println("Error handling warp teleport command: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
