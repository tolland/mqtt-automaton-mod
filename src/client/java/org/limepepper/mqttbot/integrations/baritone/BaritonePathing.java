package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import baritone.api.behavior.IPathingBehavior;
import baritone.api.event.events.PathEvent;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.event.listener.IEventBus;
import baritone.api.pathing.goals.Goal;
import baritone.api.utils.BetterBlockPos;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.Objects;
import java.util.UUID;

/**
 *
 * This class handles both Baritone command execution and pathing event
 * tracking.
 * It maintains correlation between goto commands and their corresponding
 * pathing events
 * by storing requestId/correlationId when commands are received and including
 * them
 * in all pathing event responses.
 *
 */
public final class BaritonePathing extends Action
    implements MqttMessageListener {
    public static final BaritonePathing INSTANCE = new BaritonePathing();
    public static final Minecraft MC = Minecraft.getInstance();
    
    private static boolean pathActive = false;
    private static boolean announced = false;
    
    private static Goal oldGoal = null;
    private static Goal currentGoal = null;
    private static final int POS_PERIOD_TICKS = 100;
    private static int posTick = 0;
    private static BlockPos lastSentPos = null;
    private static IBaritone baritone = null;
    private static IPathingBehavior pathing = null;
    
    // Track correlation between goto commands and pathing events
    private static String activeRequestId = null;
    private static String activeCorrelationId = null;
    private static String activeIdentity = null;
    
    private BaritonePathing()
    {}
    
    /**
     * Initialize both command handling and pathing event tracking
     */
    public static void init()
    {
        // Register for MQTT command messages
        EventManager.INSTANCE.add(MqttMessageListener.class,
            BaritonePathing.INSTANCE);
        
        // Initialize pathing event tracking
        baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        pathing = baritone.getPathingBehavior();
        
        IEventBus bus = BaritoneAPI.getProvider().getPrimaryBaritone()
            .getGameEventHandler();
        
        bus.registerEventListener(new AbstractGameEventListener()
        {
            @Override
            public void onPathEvent(PathEvent e)
            {
                switch(e)
                {
                    case CALC_FINISHED_NOW_EXECUTING ->
                    {
                        pathActive = true;
                        announced = false;
                        currentGoal = pathing.getGoal();
                        mqttSend("CALC_FINISHED_NOW_EXECUTING");
                    }
                    // this never seems to fire
                    case AT_GOAL ->
                    {
                        mqttSend("AT_GOAL");
                        pathActive = false;
                        currentGoal = null;
                        announced = true; // prevent re-announcing
                        // Clear correlation tracking when goal is reached
                        clearActiveCorrelation();
                    }
                    case CALC_FAILED ->
                    {
                        Goal failedGoal = pathing.getGoal();
                        double heuristic = (failedGoal != null)
                            ? failedGoal.heuristic(
                                baritone.getPlayerContext().playerFeet())
                            : Double.NaN;
                        System.out.println("Goal pos heuristic: " + heuristic);
                        // we’ll still allow NEXT_* to try; don’t clear state
                        // yet.
                        mqttSend("CALC_FAILED", "initial");
                        if(heuristic < 4.0 && !announced)
                        {
                            // if we're close to the goal, announce it
                            BetterBlockPos feet =
                                baritone.getPlayerContext().playerFeet();
                            mqttSendSuccess("Goal reached (close enough)",
                                feet.x, feet.y, feet.z);
                            announced = true;
                        }else
                        {
                            // Send failure for calc failed
                            mqttSendFailure("Path calculation failed",
                                "Could not find path to goal");
                        }
                    }
                    case NEXT_CALC_FAILED ->
                    {
                        mqttSend("NEXT_CALC_FAILED", "next_segment");
                    }
                    case CANCELED ->
                    {
                        // Debounce: only consider "not pathing" if we *were*
                        // pathing recently
                        // (This avoids spurious cancel spam from your build.)
                        if(pathActive)
                        {
                            pathActive = false;
                            // Clear correlation tracking when canceled
                            clearActiveCorrelation();
                        }
                    }
                    default ->
                        {
                    }
                }
            }
        });
        
        // 2) Poll once per client tick for "in goal" (works even if AT_GOAL
        // never fires)
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if(client.player == null)
                return;
            if(pathing.getGoal() == null)
                return;
            
            currentGoal = pathing.getGoal();
            BetterBlockPos feet = baritone.getPlayerContext().playerFeet();
            
            boolean inGoal = currentGoal.isInGoal(feet);
            // System.out.println("BaritoneIntegration: feet=" + feet + ",
            // inGoal=" + inGoal + ", pathActive=" + pathActive + ",
            // currentGoal=" + currentGoal);
            
            if(inGoal && (oldGoal != currentGoal))
            {
                oldGoal = currentGoal;
                announced = true;
                // publish once
                mqttSendSuccess("Goal reached", feet.x, feet.y, feet.z);
                // optionally "reset" so a new goto can trigger again
                pathActive = false;
                currentGoal = null;
                // Clear correlation tracking when goal is reached
                clearActiveCorrelation();
            }
            
            if(++posTick >= POS_PERIOD_TICKS)
            {
                posTick = 0;
                
                // Use doubles for precise pos; you can also include yaw/pitch
                // if you like
                double x = client.player.getX();
                double y = client.player.getY();
                double z = client.player.getZ();
                
                // only send if moved at least one block (tweak threshold if
                // needed)
                BlockPos bp = client.player.blockPosition();
                if(!bp.equals(lastSentPos))
                {
                    mqttSend("{\"type\": \"pos\", \"x\":" + x + ",\"y\":" + y
                        + ",\"z\":" + z + "}");
                    lastSentPos = bp;
                }
                // String.format("baritone/%s/event", mc.getUser().getName()
            }
            
        });
        
    }
    
    // --- Command handling (from BaritoneCmds) ---
    
    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent)
    {
        if(MC.player == null)
            return;
        MessageData data = mqttMessageEvent.messageData;
        System.out.println("received message in baritone pathing");
        if(!mqttMessageEvent.messageData.getService().equals("baritone"))
            return;
        System.out.println("message for baritone");
        switch(mqttMessageEvent.messageData.getMethod())
        {
            case "goto":
            handleGotoCommand(data);
            break;
            case "pause":
            MC.getConnection().sendChat("#pause");
            break;
            case "resume":
            MC.getConnection().sendChat("#resume");
            break;
            case "cancel":
            MC.getConnection().sendChat("#cancel");
            // Clear correlation when explicitly canceled
            clearActiveCorrelation();
            break;
            case "chat":
            // Legacy support - will be removed soon
            String cmd = data.getParams().get("message").getAsString();
            System.out.println("Legacy chat cmd: " + cmd);
            if(MC.player != null)
            {
                MC.getConnection().sendChat(cmd);
            }
            break;
            default:
            System.out.println("Unknown method in baritone: "
                + mqttMessageEvent.messageData.getMethod());
        }
    }
    
    /**
     * Handle structured goto commands with x, y, z parameters
     * This is a temporary shim - will be replaced with direct Baritone API
     * calls
     */
    private void handleGotoCommand(MessageData data)
    {
        try
        {
            if(data.getParams() == null)
            {
                System.out.println("Error: goto command missing params");
                return;
            }
            
            // Store correlation information for this goto command
            activeRequestId = data.getRequestId();
            activeCorrelationId = data.getCorrelationId();
            activeIdentity = data.getIdentity();
            
            // Extract coordinates from params
            int x = data.getParams().get("x").getAsInt();
            int y = data.getParams().get("y").getAsInt();
            int z = data.getParams().get("z").getAsInt();
            
            // Build the goto command string (temporary shim)
            String gotoCmd = String.format("#goto %d %d %d", x, y, z);
            System.out.println("Executing goto command: " + gotoCmd);
            System.out.println("Tracking correlation: requestId="
                + activeRequestId + ", correlationId=" + activeCorrelationId);
            
            if(MC.player != null)
            {
                MC.getConnection().sendChat(gotoCmd);
            }else
            {
                System.out.println(
                    "Error: Player is null, cannot execute goto command");
                clearActiveCorrelation();
            }
            
        }catch(Exception e)
        {
            System.out
                .println("Error handling goto command: " + e.getMessage());
            e.printStackTrace();
            clearActiveCorrelation();
        }
    }
    
    /**
     * Clear the active correlation tracking
     */
    private static void clearActiveCorrelation()
    {
        activeRequestId = null;
        activeCorrelationId = null;
        activeIdentity = null;
    }
    
    // --- helpers ---
    
    private static boolean mqttSend(String payload)
    {
        return mqttSend(payload, null);
    }
    
    /**
     * Send standard success response
     */
    private static void mqttSendSuccess(String message, int x, int y, int z)
    {
        try
        {
            var mc = Minecraft.getInstance();
            
            JsonObject response = new JsonObject();
            response.addProperty("status", "success");
            response.addProperty("message", message);
            response.addProperty("x", x);
            response.addProperty("y", y);
            response.addProperty("z", z);
            response.addProperty("player", mc.getUser().getName());
            
            // Use stored correlation info if available, otherwise generate new
            String requestId = (activeRequestId != null) ? activeRequestId
                : UUID.randomUUID().toString();
            String correlationId = activeCorrelationId;
            String identity =
                (activeIdentity != null) ? activeIdentity : "mqttbot";
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(
                mc.getUser().getName(), new MessageData("baritone", "goto",
                    requestId, correlationId, null, response, identity, null)));
            
        }catch(Exception e)
        {
            e.printStackTrace();
        }
    }
    
    /**
     * Send standard failure response
     */
    private static void mqttSendFailure(String message, String reason)
    {
        try
        {
            var mc = Minecraft.getInstance();
            
            JsonObject response = new JsonObject();
            response.addProperty("status", "failure");
            response.addProperty("message", message);
            response.addProperty("reason", reason);
            response.addProperty("player", mc.getUser().getName());
            
            // Use stored correlation info if available, otherwise generate new
            String requestId = (activeRequestId != null) ? activeRequestId
                : UUID.randomUUID().toString();
            String correlationId = activeCorrelationId;
            String identity =
                (activeIdentity != null) ? activeIdentity : "mqttbot";
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(
                mc.getUser().getName(), new MessageData("baritone", "goto",
                    requestId, correlationId, null, response, identity, null)));
            
        }catch(Exception e)
        {
            e.printStackTrace();
        }
    }
    
    private static boolean mqttSend(String payload, String detail)
    {
        try
        {
            var mc = Minecraft.getInstance();
            
            // Create structured response data
            JsonObject responseData =
                createStructuredResponse(payload, pathing.getGoal(), detail);
            
            // Use stored correlation info if available, otherwise generate new
            String requestId = (activeRequestId != null) ? activeRequestId
                : UUID.randomUUID().toString();
            String correlationId = activeCorrelationId;
            String identity =
                (activeIdentity != null) ? activeIdentity : "mqttbot";
            
            EventManager.fire(
                new MqttReplyListener.MqttReplyEvent(mc.getUser().getName(),
                    new MessageData("baritone", "pathing", requestId,
                        correlationId, null, responseData, identity, null)));
            
        }catch(Exception e)
        {
            e.printStackTrace();
            return false;
        }
        return true;
    }
    
    /**
     * Create structured response data as JsonObject
     */
    private static JsonObject createStructuredResponse(String type, Goal goal,
        String detail)
    {
        var mc = Minecraft.getInstance();
        String player =
            (mc.player != null) ? mc.getUser().getName() : "unknown";
        
        JsonObject response = new JsonObject();
        response.addProperty("type", type);
        response.addProperty("player", player);
        
        if(detail != null)
        {
            response.addProperty("detail", detail);
        }
        
        GoalData gd = goalData(goal);
        if(gd != null)
        {
            if(gd.x != null)
                response.addProperty("goalX", gd.x);
            if(gd.y != null)
                response.addProperty("goalY", gd.y);
            if(gd.z != null)
                response.addProperty("goalZ", gd.z);
            response.addProperty("goalType", gd.kind);
        }
        
        return response;
    }
    
    // Try to surface coordinates for common Goal types without tying to
    // internals.
    private record GoalData(Integer x, Integer y, Integer z, String kind)
    {}
    
    private static GoalData goalData(Goal g)
    {
        if(g == null)
            return null;
        String kind = g.getClass().getSimpleName();
        
        // Avoid compile breaks if a type isn’t present: use string names not
        // direct imports in ‘instanceof’ if you prefer.
        try
        {
            if(Objects.equals(kind, "GoalBlock"))
            {
                // GoalBlock usually has a BlockPos accessor; reflect to avoid
                // hard coupling:
                var m = g.getClass().getMethod("getPos"); // or "pos()"
                                                          // depending on
                                                          // build
                Object pos = m.invoke(g);
                int x = (int)pos.getClass().getMethod("getX").invoke(pos);
                int y = (int)pos.getClass().getMethod("getY").invoke(pos);
                int z = (int)pos.getClass().getMethod("getZ").invoke(pos);
                return new GoalData(x, y, z, kind);
            }
            if(Objects.equals(kind, "GoalXZ"))
            {
                int x = (int)g.getClass().getMethod("getX").invoke(g);
                int z = (int)g.getClass().getMethod("getZ").invoke(g);
                return new GoalData(x, null, z, kind);
            }
            if(Objects.equals(kind, "GoalNear"))
            {
                int x = (int)g.getClass().getMethod("getX").invoke(g);
                int y = (int)g.getClass().getMethod("getY").invoke(g);
                int z = (int)g.getClass().getMethod("getZ").invoke(g);
                return new GoalData(x, y, z, kind);
            }
        }catch(Throwable ignore)
        { /* fall through */ }
        return new GoalData(null, null, null, kind);
    }
}
