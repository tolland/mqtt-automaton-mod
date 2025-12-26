package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import baritone.api.behavior.IPathingBehavior;
import baritone.api.event.events.PathEvent;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.event.listener.IEventBus;
import baritone.api.pathing.goals.Goal;
import baritone.api.utils.BetterBlockPos;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import net.minecraft.client.Minecraft;
import net.minecraft.util.math.BlockPos;

import java.util.Objects;
import java.util.UUID;
import com.google.gson.JsonObject;

/**
 *
 * This class is designed to handle integration with Baritone's pathing
 * events in order to notify the client of state changes and completion
 * states such as goal reached and failure.
 *
 */
public final class BaritonePathing {


    private static boolean pathActive = false;
    private static boolean announced = false;

    private static Goal oldGoal = null;
    private static Goal currentGoal = null;
    private static final int POS_PERIOD_TICKS = 100;
    private static int posTick = 0;
    private static BlockPos lastSentPos = null;
    private static IBaritone baritone = null;
    private static IPathingBehavior pathing = null;

    /**
     *
     *
     */
    public static void init() {


        baritone = BaritoneAPI.getProvider().getPrimaryBaritone();
        pathing = baritone.getPathingBehavior();

        IEventBus bus = BaritoneAPI.getProvider()
                .getPrimaryBaritone()
                .getGameEventHandler();

        bus.registerEventListener(new AbstractGameEventListener() {
            @Override
            public void onPathEvent(PathEvent e) {
                switch (e) {
                    case CALC_FINISHED_NOW_EXECUTING -> {
                        pathActive = true;
                        announced = false;
                        currentGoal = pathing.getGoal();
                        //   mqtt.publish("baritone/event", payload("CALC_FINISHED_NOW_EXECUTING", pathing.getGoal(), null));
                        mqttSend("CALC_FINISHED_NOW_EXECUTING");
                    }
                    // this never seems to fire
                    case AT_GOAL -> {
                        // publish goal reached
                        //     mqtt.publish("baritone/event", payload("AT_GOAL", pathing.getGoal(), null));

                        mqttSend("AT_GOAL");
                        pathActive = false;
                        currentGoal = null;
                        announced = true; // prevent re-announcing
                    }
                    case CALC_FAILED -> {
                        Goal failedGoal = pathing.getGoal();
                        double heuristic = (failedGoal != null) ? failedGoal.heuristic(baritone.getPlayerContext().playerFeet()) : Double.NaN;
                        System.out.println("Goal pos heuristic: " + heuristic);
                        // we’ll still allow NEXT_* to try; don’t clear state yet.
                        mqttSend(
                                "CALC_FAILED",
                                "initial"
                        );
                        if (heuristic < 4.0 && !announced) {
                            // if we're close to the goal, announce it
                            BetterBlockPos feet = baritone.getPlayerContext().playerFeet();
                            mqttSendSuccess("Goal reached (close enough)", feet.x, feet.y, feet.z);
                            announced = true;
                        } else {
                            // Send failure for calc failed
                            mqttSendFailure("Path calculation failed", "Could not find path to goal");
                        }
                    }
                    case NEXT_CALC_FAILED -> {
                        mqttSend(
                                "NEXT_CALC_FAILED",
                                "next_segment"
                        );
                    }
                    case CANCELED -> {
                        // Debounce: only consider "not pathing" if we *were* pathing recently
                        // (This avoids spurious cancel spam from your build.)
                        if (pathActive) {
                            pathActive = false;
                        }
                    }
                    default -> {
                    }
                }
            }
        });

        // 2) Poll once per client tick for "in goal" (works even if AT_GOAL never fires)
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client.player == null) return;
            if (pathing.getGoal() == null) return;

            currentGoal = pathing.getGoal();
            BetterBlockPos feet = baritone.getPlayerContext().playerFeet();

            boolean inGoal = currentGoal.isInGoal(feet);
            //System.out.println("BaritoneIntegration: feet=" + feet + ", inGoal=" + inGoal + ", pathActive=" + pathActive + ", currentGoal=" + currentGoal);

            if (inGoal && (oldGoal != currentGoal)) {
                oldGoal = currentGoal;
                announced = true;
                // publish once
                mqttSendSuccess("Goal reached", feet.x, feet.y, feet.z);
                // optionally "reset" so a new goto can trigger again
                pathActive = false;
                currentGoal = null;
            }

            if (++posTick >= POS_PERIOD_TICKS) {
                posTick = 0;

                // Use doubles for precise pos; you can also include yaw/pitch if you like
                double x = client.player.getX();
                double y = client.player.getY();
                double z = client.player.getZ();

                // only send if moved at least one block (tweak threshold if needed)
                BlockPos bp = client.player.blockPosition();
                if (!bp.equals(lastSentPos)) {
                    mqttSend("{\"type\": \"pos\", \"x\":" + x + ",\"y\":" + y + ",\"z\":" + z + "}");
                    lastSentPos = bp;
                }
                // String.format("baritone/%s/event", mc.getUser().getName()
            }

        });

    }


    // --- helpers ---

    private static boolean mqttSend(String payload) {
        return mqttSend(payload, null);
    }
    
    /**
     * Send standard success response
     */
    private static void mqttSendSuccess(String message, int x, int y, int z) {
        try {
            var mc = Minecraft.getInstance();
            
            JsonObject response = new JsonObject();
            response.addProperty("status", "success");
            response.addProperty("message", message);
            response.addProperty("x", x);
            response.addProperty("y", y);
            response.addProperty("z", z);
            response.addProperty("player", mc.getUser().getName());
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(mc.getUser().getName(), new MessageData(
                            "baritone",
                            "goto",
                            UUID.randomUUID().toString(),
                            null,
                            null,
                            response,
                            "mqttbot",
                            null)
                    )
            );
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * Send standard failure response
     */
    private static void mqttSendFailure(String message, String reason) {
        try {
            var mc = Minecraft.getInstance();
            
            JsonObject response = new JsonObject();
            response.addProperty("status", "failure");
            response.addProperty("message", message);
            response.addProperty("reason", reason);
            response.addProperty("player", mc.getUser().getName());
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(mc.getUser().getName(), new MessageData(
                            "baritone",
                            "goto",
                            UUID.randomUUID().toString(),
                            null,
                            null,
                            response,
                            "mqttbot",
                            null)
                    )
            );
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static boolean mqttSend(String payload, String detail) {
        try {
            var mc = Minecraft.getInstance();
            
            // Create structured response data
            JsonObject responseData = createStructuredResponse(payload, pathing.getGoal(), detail);
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(mc.getUser().getName(), new MessageData(
                            "baritone",
                            "pathing",
                            UUID.randomUUID().toString(),
                            null,
                            null,
                            responseData,
                            "mqttbot",
                            null)  // No longer using message field for structured data
                    )
            );

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
        return true;
    }

    /**
     * Create structured response data as JsonObject
     */
    private static JsonObject createStructuredResponse(String type, Goal goal, String detail) {
        var mc = Minecraft.getInstance();
        String player = (mc.player != null) ? mc.getUser().getName() : "unknown";

        JsonObject response = new JsonObject();
        response.addProperty("type", type);
        response.addProperty("player", player);
        
        if (detail != null) {
            response.addProperty("detail", detail);
        }

        GoalData gd = goalData(goal);
        if (gd != null) {
            if (gd.x != null) response.addProperty("goalX", gd.x);
            if (gd.y != null) response.addProperty("goalY", gd.y);
            if (gd.z != null) response.addProperty("goalZ", gd.z);
            response.addProperty("goalType", gd.kind);
        }
        
        return response;
    }



    // Try to surface coordinates for common Goal types without tying to internals.
    private record GoalData(Integer x, Integer y, Integer z, String kind) {
    }

    private static GoalData goalData(Goal g) {
        if (g == null) return null;
        String kind = g.getClass().getSimpleName();

        // Avoid compile breaks if a type isn’t present: use string names not direct imports in ‘instanceof’ if you prefer.
        try {
            if (Objects.equals(kind, "GoalBlock")) {
                // GoalBlock usually has a BlockPos accessor; reflect to avoid hard coupling:
                var m = g.getClass().getMethod("getPos"); // or "pos()" depending on build
                Object pos = m.invoke(g);
                int x = (int) pos.getClass().getMethod("getX").invoke(pos);
                int y = (int) pos.getClass().getMethod("getY").invoke(pos);
                int z = (int) pos.getClass().getMethod("getZ").invoke(pos);
                return new GoalData(x, y, z, kind);
            }
            if (Objects.equals(kind, "GoalXZ")) {
                int x = (int) g.getClass().getMethod("getX").invoke(g);
                int z = (int) g.getClass().getMethod("getZ").invoke(g);
                return new GoalData(x, null, z, kind);
            }
            if (Objects.equals(kind, "GoalNear")) {
                int x = (int) g.getClass().getMethod("getX").invoke(g);
                int y = (int) g.getClass().getMethod("getY").invoke(g);
                int z = (int) g.getClass().getMethod("getZ").invoke(g);
                return new GoalData(x, y, z, kind);
            }
        } catch (Throwable ignore) { /* fall through */ }
        return new GoalData(null, null, null, kind);
    }

    private BaritonePathing() {
    }
}
