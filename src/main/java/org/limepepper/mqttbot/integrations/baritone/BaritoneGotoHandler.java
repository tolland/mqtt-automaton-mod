package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.event.events.PathEvent;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.event.listener.IEventBus;
import baritone.api.pathing.goals.Goal;
import baritone.api.utils.BetterBlockPos;
import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.*;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.Set;

public final class BaritoneGotoHandler extends Action
        implements MessageHandler, RequiresFeatures {
    private static final MqttBotLogger LOGGER =
            new MqttBotLogger(BaritoneGotoHandler.class);
    private static final Gson gson = new Gson();

    /*
     * Correlation tracker for matching requests and responses
     * TODO so we are tracking this in various places, but as the bot
     * is one task only, its not entirely clear whether we need
     * multiple trackers or a single shared one would suffice
     */
    static final CorrelationTracker correlationTracker =
            new CorrelationTracker();
    private static final PathingState pathingState = new PathingState();

    public BaritoneGotoHandler() {
        IEventBus bus = MqttCore.baritone.getGameEventHandler();
        /*
         * Register pathing event listener
         * Baritone is currently not sending an AT_GOAL event when reaching the
         * goal
         * so we also check for goal completion in the tick handler,
         * However, it does send CALC_FAILED when it cannot find a path
         */
        bus.registerEventListener(new AbstractGameEventListener() {
            @Override
            public void onPathEvent(PathEvent event) {
                handlePathEvent(event);
            }
        });
    }

    public static BaritoneGotoHandler create() {
        return new BaritoneGotoHandler();
    }

    @Override
    public boolean canHandle(MessageData msg) {
        return "baritone".equals(msg.getService())
                && "goto".equals(msg.getMethod());
    }

    @Override
    public void handle(MessageData msg) {
        requiredFeatures().forEach(CORE.features()::enable);
        correlationTracker.setFrom(msg);
        MqttCore.INSTANCE.setBotState(MqttCore.BotState.BUSY);

        JsonElement paramsEl = msg.getParams();
        BaritoneGotoCommand cmd;
        cmd = gson.fromJson(paramsEl, BaritoneGotoCommand.class);
        String gotoCmd = String.format("#goto %f %f %f", cmd.x, cmd.y, cmd.z);
        CORE.sendChat(gotoCmd);
    }

    /**
     * Handles pathing events from Baritone
     */
    private void handlePathEvent(PathEvent event) {
        if (!CORE.features().isEnabled(BaritonePathingFeature.class)) {
            return;
        }
        switch (event) {
            case CALC_FINISHED_NOW_EXECUTING -> {
                pathingState.setPathActive(true);
                pathingState.setAnnounced(false);
                pathingState.setGoal(MqttCore.pathing.getGoal());
                ResponseBuilder.sendPathingEvent("CALC_FINISHED_NOW_EXECUTING",
                        null);
            }
            case AT_GOAL -> {
                ResponseBuilder.sendPathingEvent("AT_GOAL", null);
                pathingState.setPathActive(false);
                pathingState.setAnnounced(true);
                pathingState.updateGoal(null);
                correlationTracker.clear();
            }
            case CALC_FAILED -> handleCalcFailed();
            case NEXT_CALC_FAILED -> {
                ResponseBuilder.sendPathingEvent("NEXT_CALC_FAILED",
                        "next_segment");
            }
            case CANCELED -> {
                // @TODO how to handle this on the client?
                // do we need to notify the client it was canceled?
                if (pathingState.isPathActive()) {
                    pathingState.setPathActive(false);
                    correlationTracker.clear();
                }
                requiredFeatures().forEach(CORE.features()::disable);
            }
            default -> {
                // No action needed
            }
        }
    }

    /**
     * Baritone frequently fails to calculate a path to the goal. Despite being
     * standing in the goal block. MqttBot is not picky, near is good enough.
     */
    private void handleCalcFailed() {
        Goal failedGoal = MqttCore.pathing.getGoal();
        double heuristic =
                (failedGoal != null)
                        ? failedGoal.heuristic(
                        MqttCore.baritone.getPlayerContext().playerFeet())
                        : Double.NaN;

        System.out.println("Goal pos heuristic: " + heuristic);
        ResponseBuilder.sendPathingEvent("CALC_FAILED", "initial");

        if (heuristic < Constants.CLOSE_ENOUGH_HEURISTIC
                && !pathingState.isAnnounced()) {
            // Close enough to goal, announce success
            BetterBlockPos feet =
                    MqttCore.baritone.getPlayerContext().playerFeet();
            ResponseBuilder.sendGotoSuccess("Goal reached (close enough)",
                    feet.x, feet.y, feet.z);
            pathingState.setAnnounced(true);
        } else {
            // Too far, send failure
            ResponseBuilder.sendGotoFailure("Path calculation failed",
                    "Could not find path to goal");
        }
        requiredFeatures().forEach(CORE.features()::disable);
    }

    /**
     * Handles client tick events for goal checking and position updates
     */
    private void handleTick(net.minecraft.client.Minecraft client) {
        if (client.player == null || MqttCore.pathing.getGoal() == null
                || (!CORE.features().isEnabled(BaritonePathingFeature.class))) {
            return;
        }

        /*
         * This is debounce code to prevent multiple goal reached announcements
         * if the AT_GOAL event is not sent by Baritone.
         * It's very temperamental and should not be refactored without careful
         * testing.
         */
        // Check if goal reached
        Goal tmpGoal = MqttCore.pathing.getGoal();
        Goal oldGoal = pathingState.getOldGoal();
        pathingState.setGoal(tmpGoal);
        BetterBlockPos feet = MqttCore.baritone.getPlayerContext().playerFeet();
        boolean inGoal = pathingState.isInGoal(feet);
        boolean hasGoalChanged = pathingState.changed();

        // System.out.println("tmpGoal = " + tmpGoal);
        // System.out.println("oldGoal = " + oldGoal);
        // System.out.printf("Goal status: inGoal=%b, hasGoalChanged=%b%n",
        // inGoal,
        // hasGoalChanged);

        if (inGoal && hasGoalChanged) {
            pathingState.setAnnounced(true);
            ResponseBuilder.sendGotoSuccess("Goal reached", feet.x, feet.y,
                    feet.z);
            pathingState.done();
            correlationTracker.clear();
            requiredFeatures().forEach(CORE.features()::disable);
        }

        /*
         * // End debounce code - see above note
         */

        // Send position updates periodically
        if (pathingState.shouldSendPosition()) {
            double x = client.player.getX();
            double y = client.player.getY();
            double z = client.player.getZ();
            BlockPos bp = client.player.blockPosition();

            if (pathingState.hasPositionChanged(bp)) {
                JsonObject pos = new JsonObject();
                pos.addProperty("x", x);
                pos.addProperty("y", y);
                pos.addProperty("z", z);
                ResponseBuilder.sendPathingEventWithPayload("pos", pos);
            }
        }
    }

    @Override
    public Set<Class<? extends Feature>> requiredFeatures() {
        return Set.of(InventoryFullFeature.class);
    }

    public record BaritoneGotoCommand(float x, float y, float z) {
    }

}
