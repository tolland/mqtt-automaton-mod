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
import net.minecraft.core.BlockPos;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

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
    private static final String SERVICE_NAME = "baritone";
    static final String DEFAULT_IDENTITY = "mqttbot";

    // Baritone API references
    private static IBaritone baritone;
    private static IPathingBehavior pathing;

    // State management
    private static final PathingState pathingState = new PathingState();
    private static final CorrelationTracker correlationTracker =
            new CorrelationTracker();
    private static final ResponseBuilder responseBuilder =
            new ResponseBuilder();

    private BaritonePathing() {
        handlers.add(new BaritoneCollectHandler());
        // handlers.add(new BaritoneMineHandler());
        // handlers.add(new BaritoneCancelHandler());
    }

    /**
     * Initialize command handling and pathing event tracking
     */
    public static void init() {
        // Register for incoming MQTT command messages
        EventManager.INSTANCE.add(MqttMessageListener.class, INSTANCE);

        // Initialize Baritone API
        baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        pathing = baritone.getPathingBehavior();

        IEventBus bus = baritone.getGameEventHandler();
        /*
         * Register pathing event listener
         * Baritone is currently not sending an AT_GOAL event when reaching the goal
         * so we also check for goal completion in the tick handler,
         * However, it does send CALC_FAILED when it cannot find a path
         */
        bus.registerEventListener(new AbstractGameEventListener() {
            @Override
            public void onPathEvent(PathEvent event) {
                handlePathEvent(event);
            }
        });

        // Register tick handler for goal checking and position updates
        ClientTickEvents.END_CLIENT_TICK.register(BaritonePathing::handleTick);
    }

    @Override
    public void onMessageArrived(MqttMessageListener.MqttMessageEvent event) {
        if (mqttCore.getPlayer() == null) {
            return;
        }

        MessageData data = event.messageData;

        for (MessageHandler handler : handlers) {
            if (handler.canHandle(data)) {
                try {
                    handler.handle(data);
                } catch (Exception ex) {
                    System.out.printf("Failed to handle message %s %s%n", data, ex);
                }
            }
        }

        if (!SERVICE_NAME.equals(data.getService())) {
            return;
        }

        handleCommand(data.getMethod(), data);
    }

    private void handleCommand(String method, MessageData data) {
        switch (method) {
            case "goto" -> handleGotoCommand(data);
            case "pause" -> mqttCore.sendChat("#pause");
            case "resume" -> mqttCore.sendChat("#resume");
            case "cancel" -> {
                mqttCore.sendChat("#cancel");
                correlationTracker.clear();
            }
            case "chat" -> handleLegacyChatCommand(data);
            default -> System.out
                    .println("Unknown method in baritone: " + method);
        }
    }

    private void handleGotoCommand(MessageData data) {
        try {
            if (data.getParams() == null) {
                System.out.println("Error: goto command missing params");
                return;
            }

            // Store correlation information
            correlationTracker.setFrom(data);

            // Extract coordinates
            int x = data.getParams().get("x").getAsInt();
            int y = data.getParams().get("y").getAsInt();
            int z = data.getParams().get("z").getAsInt();

            // Execute goto command
            String gotoCmd = String.format("#goto %d %d %d", x, y, z);
            System.out.println("Executing goto command: " + gotoCmd);
            System.out.println("Tracking correlation: requestId="
                    + correlationTracker.getRequestId() + ", correlationId="
                    + correlationTracker.getCorrelationId());

            if (mqttCore.getPlayer() != null) {
                mqttCore.sendChat(gotoCmd);
            } else {
                System.out.println(
                        "Error: Player is null, cannot execute goto command");
                correlationTracker.clear();
            }
        } catch (Exception e) {
            System.out
                    .println("Error handling goto command: " + e.getMessage());
            e.printStackTrace();
            correlationTracker.clear();
        }
    }

    private void handleLegacyChatCommand(MessageData data) {
        // Legacy support - will be removed soon
        String cmd = data.getParams().get("message").getAsString();
        System.out.println("Legacy chat cmd: " + cmd);
        if (mqttCore.getPlayer() != null) {
            mqttCore.sendChat(cmd);
        }
    }

    /**
     * Builds and sends MQTT responses
     */
    private static class ResponseBuilder {

        void sendSuccess(String message, int x, int y, int z) {
            JsonObject response = new JsonObject();
            response.addProperty("status", "success");
            response.addProperty("message", message);
            response.addProperty("x", x);
            response.addProperty("y", y);
            response.addProperty("z", z);
            response.addProperty("player", getPlayerName());

            sendResponse("goto", response);
        }

        void sendFailure(String message, String reason) {
            JsonObject response = new JsonObject();
            response.addProperty("status", "failure");
            response.addProperty("message", message);
            response.addProperty("reason", reason);
            response.addProperty("player", getPlayerName());

            sendResponse("goto", response);
        }

        void sendPathingEvent(String type, String detail) {
            JsonObject response =
                    createPathingResponse(type, pathing.getGoal(), detail);
            sendResponse("pathing", response);
        }

        void sendPathingEventWithPayload(String type, JsonObject payload) {
            sendResponse(type, payload);
        }

        private void sendResponse(String method, JsonObject response) {
            try {
                String playerName = getPlayerName();
                MessageData messageData = new MessageData(SERVICE_NAME, method,
                        correlationTracker.getRequestId(),
                        correlationTracker.getCorrelationId(), null, response,
                        correlationTracker.getIdentity(), null);

                EventManager.fire(new MqttReplyListener.MqttReplyEvent(
                        playerName, messageData));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        private JsonObject createPathingResponse(String type, Goal goal,
                                                 String detail) {
            JsonObject response = new JsonObject();
            response.addProperty("type", type);
            response.addProperty("player", getPlayerName());

            if (detail != null) {
                response.addProperty("detail", detail);
            }

            GoalDataExtractor.GoalData goalData =
                    GoalDataExtractor.extract(goal);
            if (goalData != null) {
                if (goalData.x != null)
                    response.addProperty("goalX", goalData.x);
                if (goalData.y != null)
                    response.addProperty("goalY", goalData.y);
                if (goalData.z != null)
                    response.addProperty("goalZ", goalData.z);
                response.addProperty("goalType", goalData.kind);
            }

            return response;
        }

        private String getPlayerName() {
            return mqttCore.getPlayerName();
        }
    }

    /**
     * Handles pathing events from Baritone
     */
    private static void handlePathEvent(PathEvent event) {
        switch (event) {
            case CALC_FINISHED_NOW_EXECUTING -> {
                pathingState.setPathActive(true);
                pathingState.setAnnounced(false);
                pathingState.setGoal(pathing.getGoal());
                responseBuilder.sendPathingEvent("CALC_FINISHED_NOW_EXECUTING",
                        null);
            }
            case AT_GOAL -> {
                responseBuilder.sendPathingEvent("AT_GOAL", null);
                pathingState.setPathActive(false);
                pathingState.setAnnounced(true);
                pathingState.updateGoal(null);
                correlationTracker.clear();
            }
            case CALC_FAILED -> handleCalcFailed();
            case NEXT_CALC_FAILED -> {
                responseBuilder.sendPathingEvent("NEXT_CALC_FAILED",
                        "next_segment");
            }
            case CANCELED -> {
                if (pathingState.isPathActive()) {
                    pathingState.setPathActive(false);
                    correlationTracker.clear();
                }
            }
            default -> {
                // No action needed
            }
        }
    }

    private static void handleCalcFailed() {
        Goal failedGoal = pathing.getGoal();
        double heuristic = (failedGoal != null)
                ? failedGoal.heuristic(baritone.getPlayerContext().playerFeet())
                : Double.NaN;

        System.out.println("Goal pos heuristic: " + heuristic);
        responseBuilder.sendPathingEvent("CALC_FAILED", "initial");

        if (heuristic < CLOSE_ENOUGH_HEURISTIC && !pathingState.isAnnounced()) {
            // Close enough to goal, announce success
            BetterBlockPos feet = baritone.getPlayerContext().playerFeet();
            responseBuilder.sendSuccess("Goal reached (close enough)", feet.x,
                    feet.y, feet.z);
            pathingState.setAnnounced(true);
        } else {
            // Too far, send failure
            responseBuilder.sendFailure("Path calculation failed",
                    "Could not find path to goal");
        }
    }

    /**
     * Handles client tick events for goal checking and position updates
     */
    private static void handleTick(net.minecraft.client.Minecraft client) {
        if (client.player == null || pathing.getGoal() == null) {
            return;
        }

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

        if (inGoal && hasGoalChanged) {
            pathingState.setAnnounced(true);
            responseBuilder.sendSuccess("Goal reached", feet.x, feet.y, feet.z);
            pathingState.done();
            correlationTracker.clear();
        }

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
                responseBuilder.sendPathingEventWithPayload("pos", pos);
            }
        }
    }

    /**
     * Extracts coordinate data from Baritone Goal objects using reflection
     */
    private static class GoalDataExtractor {
        private record GoalData(Integer x, Integer y, Integer z, String kind) {
        }

        static GoalData extract(Goal goal) {
            if (goal == null) {
                return null;
            }

            String kind = goal.getClass().getSimpleName();

            try {
                if (Objects.equals(kind, "GoalBlock")) {
                    return extractGoalBlock(goal);
                } else if (Objects.equals(kind, "GoalXZ")) {
                    return extractGoalXZ(goal);
                } else if (Objects.equals(kind, "GoalNear")) {
                    return extractGoalNear(goal);
                }
            } catch (Throwable ignore) {
                // Reflection failed, return basic info
            }

            return new GoalData(null, null, null, kind);
        }

        private static GoalData extractGoalBlock(Goal goal) throws Exception {
            var method = goal.getClass().getMethod("getPos");
            Object pos = method.invoke(goal);
            int x = (int) pos.getClass().getMethod("getX").invoke(pos);
            int y = (int) pos.getClass().getMethod("getY").invoke(pos);
            int z = (int) pos.getClass().getMethod("getZ").invoke(pos);
            return new GoalData(x, y, z, "GoalBlock");
        }

        private static GoalData extractGoalXZ(Goal goal) throws Exception {
            int x = (int) goal.getClass().getMethod("getX").invoke(goal);
            int z = (int) goal.getClass().getMethod("getZ").invoke(goal);
            return new GoalData(x, null, z, "GoalXZ");
        }

        private static GoalData extractGoalNear(Goal goal) throws Exception {
            int x = (int) goal.getClass().getMethod("getX").invoke(goal);
            int y = (int) goal.getClass().getMethod("getY").invoke(goal);
            int z = (int) goal.getClass().getMethod("getZ").invoke(goal);
            return new GoalData(x, y, z, "GoalNear");
        }
    }
}
