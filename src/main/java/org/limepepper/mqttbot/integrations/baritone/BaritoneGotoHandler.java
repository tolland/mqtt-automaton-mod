package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.event.events.PathEvent;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.event.listener.IEventBus;
import baritone.api.pathing.goals.Goal;
import baritone.api.utils.BetterBlockPos;
import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.*;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.Set;

/**
 * This is a handler for '#goto x y z' style baritone commands.
 * In order to detect progress and completion, we listen to Baritone pathing events
 * and also use a tick handler to check for goal completion and send position
 * updates.
 */
public final class BaritoneGotoHandler extends Action
    implements MessageHandler, RequiresFeatures {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BaritoneGotoHandler.class);
    private static final Gson gson = new Gson();
    
    public BaritoneGotoHandler()
    {
        IEventBus bus = MqttCore.baritone.getGameEventHandler();
        /*
         * Register pathing event listener
         * Baritone is currently not sending an AT_GOAL event when reaching the
         * goal reliably. Need to find out why @TODO
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
        ClientTickEvents.END_CLIENT_TICK.register(this::handleTick);
    }
    
    public static BaritoneGotoHandler create()
    {
        return new BaritoneGotoHandler();
    }
    
    @Override
    public boolean canHandle(MessageData msg)
    {
        return "baritone".equals(msg.getService())
            && "goto".equals(msg.getMethod());
    }
    
    @Override
    public void handle(MessageData msg)
    {
        requiredFeatures().forEach(CORE.features()::enable);

        // Extract and validate correlation IDs - fail fast if invalid
        CorrelationIds ids = CorrelationIds.fromMessage(msg);

        JsonElement paramsEl = msg.getParams();
        BaritoneGotoCommand cmd;
        cmd = gson.fromJson(paramsEl, BaritoneGotoCommand.class);
        MqttCore.INSTANCE.setBotState(MqttCore.BotState.BUSY);
        PathingState.INSTANCE.reset();

        // Store correlation IDs in PathingState for response tracking
        PathingState.INSTANCE.setCorrelationIds(ids);
        PathingState.INSTANCE.setPos(cmd.x, cmd.y, cmd.z);
        String gotoCmd =
            String.format("#goto %.2f %.2f %.2f", cmd.x, cmd.y, cmd.z);
        CORE.sendChat(gotoCmd);
    }
    
    /**
     * Handles pathing events from Baritone
     */
    private void handlePathEvent(PathEvent event)
    {
        if(!CORE.features().isEnabled(BaritonePathingFeature.class))
        {
            return;
        }
        switch(event)
        {
            case CALC_FINISHED_NOW_EXECUTING ->
            {
                PathingState.INSTANCE.setPathActive(true);
                PathingState.INSTANCE.setAnnounced(false);
                PathingState.INSTANCE.setGoal(MqttCore.pathing.getGoal());
                ResponseBuilder.sendPathingEvent("CALC_FINISHED_NOW_EXECUTING",
                    null);
            }
            case AT_GOAL ->
            {
                ResponseBuilder.sendPathingEvent("AT_GOAL", null);
                PathingState.INSTANCE.setPathActive(false);
                PathingState.INSTANCE.setAnnounced(true);
                PathingState.INSTANCE.updateGoal(null);
                // Correlation IDs cleared by PathingState lifecycle methods
            }
            case CALC_FAILED -> handleCalcFailed();
            case NEXT_CALC_FAILED ->
            {
                ResponseBuilder.sendPathingEvent("NEXT_CALC_FAILED",
                    "next_segment");
            }
            case CANCELED ->
            {
                // @TODO how to handle this on the client?
                // do we need to notify the client it was canceled?
                if(PathingState.INSTANCE.isPathActive())
                {
                    PathingState.INSTANCE.setPathActive(false);

                }
                // Correlation IDs cleared by PathingState lifecycle methods
                requiredFeatures().forEach(CORE.features()::disable);
            }
            default ->
            {
                // No action needed
            }
        }
    }
    
    /**
     * Baritone frequently fails to calculate a path to the goal. Despite being
     * standing in the goal block. MqttBot is not picky, near is good enough.
     */
    private void handleCalcFailed()
    {
        Goal failedGoal = MqttCore.pathing.getGoal();
        double heuristic =
            (failedGoal != null)
                ? failedGoal.heuristic(
                    MqttCore.baritone.getPlayerContext().playerFeet())
                : Double.NaN;
        
        LOGGER.debug("Goal pos heuristic: " + heuristic);
        ResponseBuilder.sendPathingEvent("CALC_FAILED", "initial");
        
        if(heuristic < Constants.CLOSE_ENOUGH_HEURISTIC
            && !PathingState.INSTANCE.isAnnounced())
        {
            // Close enough to goal, announce success
            BetterBlockPos feet =
                MqttCore.baritone.getPlayerContext().playerFeet();
            ResponseBuilder.sendGotoSuccess("Goal reached (close enough)",
                feet.x, feet.y, feet.z);
            PathingState.INSTANCE.setAnnounced(true);
        }else
        {
            // Too far, send failure
            ResponseBuilder.sendGotoFailure("Path calculation failed",
                "Could not find path to goal");
        }
        requiredFeatures().forEach(CORE.features()::disable);
    }
    
    /**
     * Handles client tick events for goal checking and position updates
     */
    private void handleTick(net.minecraft.client.Minecraft client)
    {
        // LOGGER.debug("Tick handler called");
        var player = client.player;
        var goal = MqttCore.pathing.getGoal();
        boolean pathingEnabled =
            CORE.features().isEnabled(BaritonePathingFeature.class);
        if(player == null || goal == null)
        {
            return;
        }
        // LOGGER.debug("Tick handler called2");
        
        /*
         * This is debounce code to prevent multiple goal reached announcements
         * if the AT_GOAL event is not sent by Baritone.
         * It's very temperamental and should not be refactored without careful
         * testing.
         */
        // Check if goal reached
        Goal tmpGoal = MqttCore.pathing.getGoal();
        Goal oldGoal = PathingState.INSTANCE.getOldGoal();
        PathingState.INSTANCE.setGoal(tmpGoal);
        BetterBlockPos feet = MqttCore.baritone.getPlayerContext().playerFeet();
        boolean inGoal = PathingState.INSTANCE.isInGoal(feet);
        boolean hasGoalChanged = PathingState.INSTANCE.changed();
        
        // LOGGER.debug("tmpGoal = " + tmpGoal);
        // LOGGER.debug("oldGoal = " + oldGoal);
        // System.out.printf("Goal status: inGoal=%b, hasGoalChanged=%b%n",
        // inGoal,
        // hasGoalChanged);
        
        if(inGoal && hasGoalChanged)
        {
            PathingState.INSTANCE.setAnnounced(true);
            ResponseBuilder.sendGotoSuccess("Goal reached", feet.x, feet.y,
                feet.z);
            PathingState.INSTANCE.done(); // Clears correlation IDs
            LOGGER.debug("Goal reached, disabling features");
            requiredFeatures().forEach(CORE.features()::disable);
        }
        
        /*
         * // End debounce code - see above note
         */
        
        // Send position updates periodically
        if(PathingState.INSTANCE.shouldSendPosition())
        {
            double x = client.player.getX();
            double y = client.player.getY();
            double z = client.player.getZ();
            BlockPos bp = client.player.blockPosition();
            
            if(PathingState.INSTANCE.hasPositionChanged(bp))
            {
                JsonObject pos = new JsonObject();
                pos.addProperty("x", x);
                pos.addProperty("y", y);
                pos.addProperty("z", z);
                ResponseBuilder.sendPathingEventWithPayload("pos", pos);
            }
        }
    }
    
    @Override
    public Set<Class<? extends Feature>> requiredFeatures()
    {
        return Set.of(InventoryFullFeature.class, BaritonePathingFeature.class);
    }
    
    public record BaritoneGotoCommand(float x, float y, float z)
    {}
    
}
