package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.event.events.PathEvent;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.event.listener.IEventBus;
import baritone.api.pathing.goals.Goal;
import baritone.api.pathing.goals.GoalBlock;
import baritone.api.utils.BetterBlockPos;
import com.google.gson.Gson;
import com.google.gson.JsonElement;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.Vec3;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.*;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.Set;

/**
 * Handler for Baritone goto commands using direct Baritone API integration.
 * This implementation uses a proper state machine (PathingState) to track
 * request lifecycle, includes stuck detection with auto-nudge, and maintains
 * full event history for debugging.
 *
 * <p>
 * Key improvements over legacy version:
 * <ul>
 * <li>Uses Baritone API directly instead of chat commands</li>
 * <li>Proper state machine with PathingPhase tracking</li>
 * <li>Stuck detection with configurable auto-nudge</li>
 * <li>Request history for debugging</li>
 * <li>Timeout handling for calculation and pathing</li>
 * <li>Event timeline logging</li>
 * </ul>
 * </p>
 */
public final class BaritoneGotoHandler extends Action
    implements MessageHandler, RequiresFeatures {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BaritoneGotoHandler.class);
    private static final Gson gson = new Gson();
    
    public BaritoneGotoHandler()
    {
        IEventBus bus = MqttCore.baritone.getGameEventHandler();
        
        // Register Baritone path event listener
        bus.registerEventListener(new AbstractGameEventListener()
        {
            @Override
            public void onPathEvent(PathEvent event)
            {
                handlePathEvent(event);
            }
        });
        
        // Register tick handler for stuck detection and goal completion
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
        try
        {
            // Enable required features
            requiredFeatures().forEach(CORE.features()::enable);
            
            // Extract and validate correlation IDs - fail fast if invalid
            CorrelationIds ids = CorrelationIds.fromMessage(msg);
            
            // Parse command parameters
            JsonElement paramsEl = msg.getParams();
            BaritoneGotoCommand cmd;
            cmd = gson.fromJson(paramsEl, BaritoneGotoCommand.class);
            
            // Create target BlockPos from command
            BlockPos targetPos =
                new BlockPos((int)cmd.x, (int)cmd.y, (int)cmd.z);
            
            // Start new pathing request (cancels any existing request)
            PathingState.INSTANCE.startRequest(ids, targetPos);
            PathingState.INSTANCE.transitionTo(PathingPhase.CALCULATING);
            
            // Set bot state
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.BUSY);
            
            // Use Baritone API directly instead of chat command
            Goal goal = new GoalBlock(targetPos);
            PathingState.INSTANCE.setBaritoneGoal(goal);
            MqttCore.baritone.getCustomGoalProcess().setGoalAndPath(goal);
            
            PathingState.INSTANCE.logEvent("GOTO_COMMAND_SENT",
                String.format("Using Baritone API: GoalBlock(%d, %d, %d)",
                    targetPos.getX(), targetPos.getY(), targetPos.getZ()));
            
            LOGGER.info("Sent goto command to Baritone: {}", targetPos);
            
        }catch(Exception e)
        {
            LOGGER.error("Error handling goto command: {}", e.getMessage(), e);
            LOGGER.error("Request history:\n{}",
                RequestHistory.INSTANCE.dumpHistory());
            throw new RuntimeException("Failed to handle goto command", e);
        }
    }
    
    /**
     * Handles pathing events from Baritone
     */
    private void handlePathEvent(PathEvent event)
    {
        if(!PathingState.INSTANCE.hasActiveRequest())
        {
            return; // Ignore events when no active request
        }
        
        PathingState.INSTANCE.logEvent("BARITONE_EVENT", event.toString());
        
        switch(event)
        {
            case CALC_FINISHED_NOW_EXECUTING ->
            {
                PathingState.INSTANCE.transitionTo(PathingPhase.PATHING);
                PathingState.INSTANCE.logEvent("CALC_FINISHED",
                    "Path calculated, starting movement");
                ResponseBuilder.sendPathingEvent("CALC_FINISHED_NOW_EXECUTING",
                    null);
            }
            case AT_GOAL ->
            {
                BetterBlockPos feet =
                    MqttCore.baritone.getPlayerContext().playerFeet();
                ResponseBuilder.sendGotoSuccess("Goal reached", feet.x, feet.y,
                    feet.z);
                PathingState.INSTANCE.completeSuccess();
                MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
                requiredFeatures().forEach(CORE.features()::disable);
            }
            case CALC_FAILED -> handleCalcFailed();
            case NEXT_CALC_FAILED ->
            {
                PathingState.INSTANCE.logEvent("NEXT_CALC_FAILED",
                    "Failed to calculate next segment");
                ResponseBuilder.sendPathingEvent("NEXT_CALC_FAILED",
                    "next_segment");
            }
            case CANCELED ->
            {
                // @TODO how to handle this on the client?
                PathingState.INSTANCE.logEvent("BARITONE_CANCELED",
                    "Baritone canceled the path");
                PathingState.INSTANCE.completeFailed("Baritone canceled");
                MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
                requiredFeatures().forEach(CORE.features()::disable);
            }
            default ->
            {
                // No action needed for other events
            }
        }
    }
    
    /**
     * Handles path calculation failure. Checks if we're "close enough" to the
     * goal and succeeds if so.
     */
    private void handleCalcFailed()
    {
        Goal failedGoal = PathingState.INSTANCE.getBaritoneGoal();
        BetterBlockPos feet = MqttCore.baritone.getPlayerContext().playerFeet();
        
        double heuristic =
            (failedGoal != null)
                ? failedGoal.heuristic(feet)
                : Double.NaN;
        
        LOGGER.debug("CALC_FAILED - Goal heuristic: {}", heuristic);
        PathingState.INSTANCE.logEvent("CALC_FAILED",
            String.format("Heuristic: %.2f", heuristic));
        
        double threshold =
            BaritoneConfig.getInstance().getCloseEnoughHeuristic();
        
        if(heuristic < threshold)
        {
            // Close enough to goal, consider it a success
            LOGGER.info("Close enough to goal (heuristic: {} < {})", heuristic,
                threshold);
            ResponseBuilder.sendGotoSuccess("Goal reached (close enough)",
                feet.x, feet.y, feet.z);
            PathingState.INSTANCE.completeSuccess();
        }else
        {
            // Too far, it's a failure
            String reason = String.format(
                "Path calculation failed (heuristic: %.2f >= %.2f)", heuristic,
                threshold);
            LOGGER.warn(reason);
            ResponseBuilder.sendGotoFailure("Path calculation failed", reason);
            PathingState.INSTANCE.completeFailed(reason);
        }
        
        MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
        requiredFeatures().forEach(CORE.features()::disable);
    }
    
    /**
     * Tick handler for stuck detection, timeout detection, and goal completion
     * checking (backup for unreliable Baritone AT_GOAL events)
     */
    private void handleTick(net.minecraft.client.Minecraft client)
    {
        if(!PathingState.INSTANCE.hasActiveRequest())
        {
            return; // Nothing to do
        }
        
        if(client.player == null)
        {
            return;
        }
        
        BlockPos currentPos = client.player.blockPosition();
        PathingPhase phase = PathingState.INSTANCE.getPhase();
        
        // Update position for stuck detection
        PathingState.INSTANCE.updatePosition(currentPos);
        
        // Check for calculation timeout
        if(PathingState.INSTANCE.hasCalculationTimedOut())
        {
            LOGGER.warn("Calculation phase timed out");
            String reason = String.format(
                "Calculation timed out after %d seconds",
                BaritoneConfig.getInstance().getMaxCalculationTimeSeconds());
            ResponseBuilder.sendGotoFailure("Calculation timeout", reason);
            PathingState.INSTANCE.completeFailed(reason);
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
            requiredFeatures().forEach(CORE.features()::disable);
            return;
        }
        
        // Check for pathing timeout
        if(PathingState.INSTANCE.hasPathingTimedOut())
        {
            LOGGER.warn("Pathing phase timed out");
            String reason = String.format("Pathing timed out after %d seconds",
                BaritoneConfig.getInstance().getMaxPathingTimeSeconds());
            ResponseBuilder.sendGotoFailure("Pathing timeout", reason);
            PathingState.INSTANCE.completeFailed(reason);
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
            requiredFeatures().forEach(CORE.features()::disable);
            return;
        }
        
        // Check for stuck (only during PATHING phase)
        if(phase == PathingPhase.PATHING
            && PathingState.INSTANCE.isStuck(currentPos))
        {
            LOGGER.warn("Bot appears to be stuck!");
            PathingState.INSTANCE.transitionTo(PathingPhase.STUCK);
            PathingState.INSTANCE.logEvent("STUCK_DETECTED",
                String.format("Position unchanged at %s", currentPos));
            
            // Auto-nudge if enabled
            if(BaritoneConfig.getInstance().isAutoNudgeWhenStuck())
            {
                nudgeForward(client);
                PathingState.INSTANCE.logEvent("AUTO_NUDGE", "Nudged forward");
                PathingState.INSTANCE.transitionTo(PathingPhase.PATHING);
            }
        }
        
        // Backup goal completion check (in case AT_GOAL event doesn't fire)
        if(phase == PathingPhase.PATHING || phase == PathingPhase.STUCK)
        {
            BetterBlockPos feet =
                MqttCore.baritone.getPlayerContext().playerFeet();
            if(PathingState.INSTANCE.isInGoal(feet))
            {
                LOGGER.info("Goal reached detected in tick handler");
                ResponseBuilder.sendGotoSuccess("Goal reached", feet.x, feet.y,
                    feet.z);
                PathingState.INSTANCE.completeSuccess();
                MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);
                requiredFeatures().forEach(CORE.features()::disable);
            }
        }
    }
    
    /**
     * Nudge the player forward slightly to help unstick
     */
    private void nudgeForward(net.minecraft.client.Minecraft client)
    {
        if(client.player == null)
        {
            return;
        }
        
        // Get player's look direction
        Vec3 lookVec = client.player.getLookAngle();
        
        // Nudge forward by 0.5 blocks
        double nudgeDistance = 0.5;
        Vec3 newPos = client.player.position()
            .add(lookVec.x * nudgeDistance, 0, lookVec.z * nudgeDistance);
        
        // Teleport to new position (this is a client-side nudge)
        client.player.setPos(newPos.x, newPos.y, newPos.z);
        
        LOGGER.debug("Nudged player forward by {} blocks", nudgeDistance);
    }
    
    @Override
    public Set<Class<? extends Feature>> requiredFeatures()
    {
        return Set.of(InventoryFullFeature.class, BaritonePathingFeature.class);
    }
    
    public record BaritoneGotoCommand(float x, float y, float z)
    {}
    
}
