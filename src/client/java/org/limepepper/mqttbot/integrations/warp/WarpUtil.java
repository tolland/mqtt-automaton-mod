package org.limepepper.mqttbot.integrations.warp;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import net.minecraft.client.Minecraft;
import net.minecraft.util.math.Vec3d;
import com.google.gson.JsonObject;

/**
 * Warp utility for handling server-side teleport commands with position-based completion detection.
 * Similar to SleepUtil but for warp/teleport operations.
 */
public final class WarpUtil {
    
    private static boolean enabled = false;
    private static String requestId = null;
    private static Vec3d targetPos = null;
    private static int radius = 5;
    private static String warpName = null;
    private static long startTime = 0;
    private static final int MAX_WAIT_TICKS = 300; // 15 seconds at 20 TPS
    private static int waitTicks = 0;
    
    private enum Phase {
        IDLE,
        WAITING_FOR_TELEPORT,
        COMPLETED,
        FAILED
    }
    
    private static Phase phase = Phase.IDLE;
    
    static {
        // Register tick handler
        ClientTickEvents.END_CLIENT_TICK.register(WarpUtil::tick);
    }
    
    /**
     * Start a warp operation
     * @param reqId Request ID for tracking
     * @param name Warp destination name
     * @param targetX Expected destination X coordinate
     * @param targetY Expected destination Y coordinate  
     * @param targetZ Expected destination Z coordinate
     * @param radiusOverride Optional radius override (default 5 blocks)
     */
    public static void start(String reqId, String name, double targetX, double targetY, double targetZ, Integer radiusOverride) {
        enabled = true;
        requestId = reqId;
        warpName = name;
        targetPos = new Vec3d(targetX, targetY, targetZ);
        radius = (radiusOverride != null && radiusOverride > 0) ? radiusOverride : 5;
        startTime = System.currentTimeMillis();
        waitTicks = 0;
        phase = Phase.WAITING_FOR_TELEPORT;
        
        System.out.println("[WarpUtil] Starting warp to '" + name + "' at " + targetPos + " (radius: " + radius + ")");
    }
    
    /**
     * Stop the current warp operation
     */
    public static void stop() {
        enabled = false;
        requestId = null;
        targetPos = null;
        warpName = null;
        phase = Phase.IDLE;
        waitTicks = 0;
    }
    
    /**
     * Check if warp utility is currently active
     */
    public static boolean isActive() {
        return enabled && phase == Phase.WAITING_FOR_TELEPORT;
    }
    
    /**
     * Main tick handler - checks player position against target
     */
    private static void tick(Minecraft client) {
        if (!enabled || phase != Phase.WAITING_FOR_TELEPORT || client.player == null) {
            return;
        }
        
        waitTicks++;
        
        // Check for timeout
        if (waitTicks >= MAX_WAIT_TICKS) {
            fail("Warp timeout - took longer than " + (MAX_WAIT_TICKS / 20) + " seconds");
            return;
        }
        
        // Get current player position
        Vec3d playerPos = client.player.getPos();
        double distance = playerPos.distanceTo(targetPos);
        
        // Check if player is within target radius
        if (distance <= radius) {
            success("Warp completed - arrived at " + warpName);
            return;
        }
        
        // Debug logging every 2 seconds
        if (waitTicks % 40 == 0) {
            System.out.println("[WarpUtil] Waiting for warp... Distance to target: " + String.format("%.1f", distance) + " blocks");
        }
    }
    
    /**
     * Handle successful warp completion
     */
    private static void success(String message) {
        sendStandardResponse("success", message, null);
        phase = Phase.COMPLETED;
        enabled = false;
        System.out.println("[WarpUtil] " + message);
    }
    
    /**
     * Handle warp failure
     */
    private static void fail(String reason) {
        sendStandardResponse("failure", "Warp failed", reason);
        phase = Phase.FAILED;
        enabled = false;
        System.out.println("[WarpUtil] Warp failed: " + reason);
    }
    
    /**
     * Send standard success/failure response
     */
    private static void sendStandardResponse(String status, String message, String reason) {
        try {
            var mc = Minecraft.getInstance();
            String playerName = (mc.player != null) ? mc.getUser().getName() : "unknown";
            
            JsonObject response = new JsonObject();
            response.addProperty("status", status);
            response.addProperty("message", message);
            if (reason != null) {
                response.addProperty("reason", reason);
            }
            response.addProperty("player", playerName);
            
            if (targetPos != null) {
                response.addProperty("targetX", targetPos.x);
                response.addProperty("targetY", targetPos.y);
                response.addProperty("targetZ", targetPos.z);
            }
            
            if (warpName != null) {
                response.addProperty("warpName", warpName);
            }
            
            // Include current player position
            if (mc.player != null) {
                Vec3d pos = mc.player.getPos();
                response.addProperty("x", pos.x);
                response.addProperty("y", pos.y);
                response.addProperty("z", pos.z);
            }
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName, new MessageData(
                    "warp",
                    "teleport",
                    requestId,  // Use the original request ID from the command
                    null,
                    null,
                    response,
                    "mqttbot",
                    null)
            ));
            
        } catch (Exception e) {
            System.err.println("Error sending warp response: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
