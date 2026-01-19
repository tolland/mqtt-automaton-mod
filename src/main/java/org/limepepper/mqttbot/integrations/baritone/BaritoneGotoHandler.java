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
import org.limepepper.mqttbot.mqtt.ServiceMessage;
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
    public boolean canHandle(ServiceMessage msg)
    {
        return "baritone".equals(msg.getService())
            && "goto".equals(msg.getMethod());
    }
    
    @Override
    public void handle(ServiceMessage msg)
    {
        LOGGER.trace("=== HANDLE GOTO START ===");
        LOGGER.trace("Message: {}", msg.toString());
        
        try
        {
            // Enable required features
            requiredFeatures().forEach(CORE.features()::enable);
            LOGGER.trace("Features enabled");
            
            // Extract and validate correlation IDs - fail fast if invalid
            CorrelationIds ids = CorrelationIds.fromMessage(msg);
            LOGGER.trace(
                "Extracted correlation IDs: requestId={}, correlationId={}",
                ids.requestId(), ids.correlationId());
            
            // Parse command parameters
            JsonElement paramsEl = msg.getParams();
            BaritoneGotoCommand cmd;
            cmd = gson.fromJson(paramsEl, BaritoneGotoCommand.class);
            LOGGER.trace("Parsed command: x={}, y={}, z={}", cmd.x, cmd.y,
                cmd.z);
            
            // Create target BlockPos from command
            BlockPos targetPos =
                new BlockPos((int)cmd.x, (int)cmd.y, (int)cmd.z);
            LOGGER.trace("Target BlockPos: {}", targetPos);
            
            // Check current state before canceling
            LOGGER.trace("hasActiveRequest BEFORE cancel: {}",
                PathingState.INSTANCE.hasActiveRequest());
            
            // CRITICAL: Cancel Baritone BEFORE creating the request
            // If we cancel after, Baritone fires CANCELED event which our
            // handler treats as a failure since there's now an active request
            try
            {
                LOGGER.trace("Calling cancelEverything()...");
                MqttCore.baritone.getPathingBehavior().cancelEverything();
                LOGGER.trace("cancelEverything() returned successfully");
            }catch(Exception e)
            {
                LOGGER.warn("Error calling Baritone cancelEverything(): {}",
                    e.getMessage());
            }
            
            // Give Baritone a moment to process the cancel
            LOGGER.trace("Waiting 50ms for Baritone to process cancel...");
            Thread.sleep(50);
            
            // Check state after cancel and sleep
            LOGGER.trace("hasActiveRequest AFTER cancel+sleep: {}",
                PathingState.INSTANCE.hasActiveRequest());
            
            // Now create the request (after Baritone is clean)
            LOGGER.trace("Creating new PathingRequest...");
            PathingState.INSTANCE.startRequest(ids, targetPos);
            LOGGER.trace(
                "PathingRequest created, transitioning to CALCULATING...");
            PathingState.INSTANCE.transitionTo(PathingPhase.CALCULATING);
            LOGGER.trace("Phase transition complete");
            
            // Set bot state
            MqttCore.INSTANCE.setBotState(MqttCore.BotState.BUSY);
            LOGGER.trace("Bot state set to BUSY");
            
            // Use Baritone API directly instead of chat command
            Goal goal = new GoalBlock(targetPos);
            PathingState.INSTANCE.setBaritoneGoal(goal);
            LOGGER.trace("Calling setGoalAndPath with {}", goal);
            MqttCore.baritone.getCustomGoalProcess().setGoalAndPath(goal);
            LOGGER.trace("setGoalAndPath returned");
            
            PathingState.INSTANCE.logEvent("GOTO_COMMAND_SENT",
                String.format("Using Baritone API: GoalBlock(%d, %d, %d)",
                    targetPos.getX(), targetPos.getY(), targetPos.getZ()));
            
            LOGGER.info("Sent goto command to Baritone: {}", targetPos);
            LOGGER.trace("=== HANDLE GOTO END ===");
            
        }catch(Exception e)
        {
            LOGGER.error("=== HANDLE GOTO ERROR ===");
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
        LOGGER.trace(">>> PATH EVENT: {} (hasActiveRequest={})", event,
            PathingState.INSTANCE.hasActiveRequest());
        
        if(!PathingState.INSTANCE.hasActiveRequest())
        {
            LOGGER.trace("    Ignoring event - no active request");
            return; // Ignore events when no active request
        }
        
        LOGGER.trace("    Processing event for active request");
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
            case CANCELED -> handleCanceled();
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
     * Handles Baritone CANCELED event. Checks if player is at/near goal and
     * sends appropriate success or failure response.
     */
    private void handleCanceled()
    {
        Goal canceledGoal = PathingState.INSTANCE.getBaritoneGoal();
        BetterBlockPos feet = MqttCore.baritone.getPlayerContext().playerFeet();
        
        double heuristic =
            (canceledGoal != null)
                ? canceledGoal.heuristic(feet)
                : Double.NaN;
        
        LOGGER.debug("CANCELED - Goal heuristic: {}", heuristic);
        PathingState.INSTANCE.logEvent("BARITONE_CANCELED",
            String.format("Heuristic: %.2f", heuristic));
        
        double threshold =
            BaritoneConfig.getInstance().getCloseEnoughHeuristic();
        
        if(heuristic < threshold)
        {
            // Already at goal - Baritone canceled because no pathing needed
            LOGGER.info("Already at goal (heuristic: {} < {})", heuristic,
                threshold);
            ResponseBuilder.sendGotoSuccess("Already at goal",
                feet.x, feet.y, feet.z);
            PathingState.INSTANCE.completeSuccess();
        }else
        {
            // Canceled for other reason (actual failure)
            String reason = String.format(
                "Baritone canceled (heuristic: %.2f >= %.2f)", heuristic,
                threshold);
            LOGGER.warn(reason);
            ResponseBuilder.sendGotoFailure("Baritone canceled", reason);
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
