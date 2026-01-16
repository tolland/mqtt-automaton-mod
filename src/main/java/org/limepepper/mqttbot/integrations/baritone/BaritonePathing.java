package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import baritone.api.behavior.IPathingBehavior;
import baritone.api.event.events.PathEvent;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.event.listener.IEventBus;
import baritone.api.pathing.goals.Goal;
import baritone.api.utils.BetterBlockPos;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;

import java.util.ArrayList;
import java.util.List;

/**
 * Handles Baritone command execution and pathing event tracking.
 * Maintains correlation between goto commands and their corresponding pathing
 * events.
 */
public final class BaritonePathing extends Action
    implements MqttMessageListener {
    
    public static final BaritonePathing INSTANCE = new BaritonePathing();
    
    private static final MqttCore mqttCore = MqttCore.INSTANCE;
    
    private final List<MessageHandler> handlers = new ArrayList<>();
    
    // Constants
    static final int POSITION_UPDATE_PERIOD_TICKS = 100;
    private static final double CLOSE_ENOUGH_HEURISTIC = 4.0;
    static final String SERVICE_NAME = "baritone";
    static final String DEFAULT_IDENTITY = "mqttbot";
    
    // Baritone API references
    private static IBaritone baritone;
    static IPathingBehavior pathing;
    
    // State management
    private static final PathingState pathingState = new PathingState();
    static final CorrelationTracker correlationTracker =
        new CorrelationTracker();
    private static final ResponseBuilder responseBuilder =
        new ResponseBuilder();
    
    private BaritonePathing()
    {
        handlers.add(BaritoneCollectHandler.create());
        // handlers.add(new BaritoneMineHandler());
        // handlers.add(new BaritoneCancelHandler());
    }
    
    /**
     * Initialize command handling and pathing event tracking
     */
    public static void init()
    {
        // Register for incoming MQTT command messages
        EventManager.INSTANCE.add(MqttMessageListener.class, INSTANCE);
        
        // Initialize Baritone API
        baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        pathing = baritone.getPathingBehavior();
        
        IEventBus bus = baritone.getGameEventHandler();
        /*
         * Register pathing event listener
         * Baritone is currently not sending an AT_GOAL event when reaching the
         * goal
         * so we also check for goal completion in the tick handler,
         * However, it does send CALC_FAILED when it cannot find a path
         */
        bus.registerEventListener(new AbstractGameEventListener()
        {
            @Override
            public void onPathEvent(PathEvent event)
            {
                handlePathEvent(event);
            }
        });
        
        // Register tick handler for goal checking and position updates
        ClientTickEvents.END_CLIENT_TICK.register(BaritonePathing::handleTick);
    }
    
    @Override
    public void onMessageArrived(MqttMessageListener.MqttMessageEvent event)
    {
        if(mqttCore.getPlayer() == null)
        {
            return;
        }
        
        MessageData data = event.messageData;
        
        for(MessageHandler handler : handlers)
        {
            if(handler.canHandle(data))
            {
                try
                {
                    handler.handle(data);
                }catch(Exception ex)
                {
                    System.out.printf("Failed to handle message %s %s%n", data,
                        ex);
                }
            }
        }
        
        if(!SERVICE_NAME.equals(data.getService()))
        {
            return;
        }
        
        handleCommand(data.getMethod(), data);
    }
    
    private void handleCommand(String method, MessageData data)
    {
        switch(method)
        {
            case "goto" -> handleGotoCommand(data);
            case "pause" -> mqttCore.sendChat("#pause");
            case "resume" -> mqttCore.sendChat("#resume");
            case "cancel" ->
            {
                mqttCore.sendChat("#cancel");
                correlationTracker.clear();
            }
            case "chat" -> handleLegacyChatCommand(data);
            default -> System.out
                .println("Unknown method in baritone: " + method);
        }
    }
    
    private void handleGotoCommand(MessageData data)
    {
        try
        {
            JsonElement paramsEl = data.getParams();
            if(paramsEl == null || paramsEl.isJsonNull()
                || !paramsEl.isJsonObject())
            {
                System.out.println("Error: goto command missing params");
                return;
            }
            JsonObject params = paramsEl.getAsJsonObject();
            
            // Store correlation information
            correlationTracker.setFrom(data);
            
            // Extract coordinates
            int x = params.get("x").getAsInt();
            int y = params.get("y").getAsInt();
            int z = params.get("z").getAsInt();
            
            // Execute goto command
            String gotoCmd = String.format("#goto %d %d %d", x, y, z);
            System.out.println("Executing goto command: " + gotoCmd);
            System.out.println("Tracking correlation: requestId="
                + correlationTracker.getRequestId() + ", correlationId="
                + correlationTracker.getCorrelationId());
            
            if(mqttCore.getPlayer() != null)
            {
                mqttCore.sendChat(gotoCmd);
            }else
            {
                System.out.println(
                    "Error: Player is null, cannot execute goto command");
                correlationTracker.clear();
            }
        }catch(Exception e)
        {
            System.out
                .println("Error handling goto command: " + e.getMessage());
            e.printStackTrace();
            correlationTracker.clear();
        }
    }
    
    private void handleLegacyChatCommand(MessageData data)
    {
        // Legacy support - will be removed soon
        JsonElement paramsEl = data.getParams();
        String cmd = null;
        if(paramsEl != null && paramsEl.isJsonObject())
        {
            JsonObject params = paramsEl.getAsJsonObject();
            if(params.has("message"))
                cmd = params.get("message").getAsString();
        }
        System.out.println("Legacy chat cmd: " + cmd);
        if(mqttCore.getPlayer() != null && cmd != null)
        {
            mqttCore.sendChat(cmd);
        }
    }
    
    /**
     * Handles pathing events from Baritone
     */
    private static void handlePathEvent(PathEvent event)
    {
        switch(event)
        {
            case CALC_FINISHED_NOW_EXECUTING ->
            {
                pathingState.setPathActive(true);
                pathingState.setAnnounced(false);
                pathingState.setGoal(pathing.getGoal());
                responseBuilder.sendPathingEvent("CALC_FINISHED_NOW_EXECUTING",
                    null);
            }
            case AT_GOAL ->
            {
                responseBuilder.sendPathingEvent("AT_GOAL", null);
                pathingState.setPathActive(false);
                pathingState.setAnnounced(true);
                pathingState.updateGoal(null);
                correlationTracker.clear();
            }
            case CALC_FAILED -> handleCalcFailed();
            case NEXT_CALC_FAILED ->
            {
                responseBuilder.sendPathingEvent("NEXT_CALC_FAILED",
                    "next_segment");
            }
            case CANCELED ->
            {
                if(pathingState.isPathActive())
                {
                    pathingState.setPathActive(false);
                    correlationTracker.clear();
                }
            }
            default ->
            {
                // No action needed
            }
        }
    }
    
    private static void handleCalcFailed()
    {
        Goal failedGoal = pathing.getGoal();
        double heuristic = (failedGoal != null)
            ? failedGoal.heuristic(baritone.getPlayerContext().playerFeet())
            : Double.NaN;
        
        System.out.println("Goal pos heuristic: " + heuristic);
        responseBuilder.sendPathingEvent("CALC_FAILED", "initial");
        
        if(heuristic < CLOSE_ENOUGH_HEURISTIC && !pathingState.isAnnounced())
        {
            // Close enough to goal, announce success
            BetterBlockPos feet = baritone.getPlayerContext().playerFeet();
            responseBuilder.sendGotoSuccess("Goal reached (close enough)",
                feet.x, feet.y, feet.z);
            pathingState.setAnnounced(true);
        }else
        {
            // Too far, send failure
            responseBuilder.sendGotoFailure("Path calculation failed",
                "Could not find path to goal");
        }
    }
    
    /**
     * Handles client tick events for goal checking and position updates
     */
    private static void handleTick(net.minecraft.client.Minecraft client)
    {
        if(client.player == null || pathing.getGoal() == null)
        {
            return;
        }
        
        /*
         * This is debounce code to prevent multiple goal reached announcements
         * if the AT_GOAL event is not sent by Baritone.
         * It's very temperamental and should not be refactored without careful
         * testing.
         */
        // Check if goal reached
        Goal tmpGoal = pathing.getGoal();
        Goal oldGoal = pathingState.getOldGoal();
        pathingState.setGoal(tmpGoal);
        BetterBlockPos feet = baritone.getPlayerContext().playerFeet();
        boolean inGoal = pathingState.isInGoal(feet);
        boolean hasGoalChanged = pathingState.changed();
        
        // System.out.println("tmpGoal = " + tmpGoal);
        // System.out.println("oldGoal = " + oldGoal);
        // System.out.printf("Goal status: inGoal=%b, hasGoalChanged=%b%n",
        // inGoal,
        // hasGoalChanged);
        
        if(inGoal && hasGoalChanged)
        {
            pathingState.setAnnounced(true);
            responseBuilder.sendGotoSuccess("Goal reached", feet.x, feet.y,
                feet.z);
            pathingState.done();
            correlationTracker.clear();
        }
        
        /*
         * // End debounce code - see above note
         */
        
        // Send position updates periodically
        if(pathingState.shouldSendPosition())
        {
            double x = client.player.getX();
            double y = client.player.getY();
            double z = client.player.getZ();
            BlockPos bp = client.player.blockPosition();
            
            if(pathingState.hasPositionChanged(bp))
            {
                JsonObject pos = new JsonObject();
                pos.addProperty("x", x);
                pos.addProperty("y", y);
                pos.addProperty("z", z);
                responseBuilder.sendPathingEventWithPayload("pos", pos);
            }
        }
    }
    
}
