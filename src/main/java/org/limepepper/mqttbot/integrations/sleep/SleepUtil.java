package org.limepepper.mqttbot.integrations.sleep;

import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.wurstclient.WurstClient;
import net.wurstclient.util.BlockBreaker;
import net.wurstclient.util.InteractionSimulator;
import org.jetbrains.annotations.Nullable;
import org.jetbrains.annotations.UnknownNullability;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.limepepper.mqttbot.util.MqttBotLogger;

public final class SleepUtil {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(SleepUtil.class);
    
    public static final Minecraft MC = Minecraft.getInstance();
    
    // --- config ---
    private static final long DAY_TICKS = 24_000L;
    private static final long NIGHT_START = 13_000L; // adjust if you want
                                                     // earlier
    private static final long NIGHT_END = 23_000L;
    private static final int DEFAULT_RADIUS = 2; // scan nearest bed within N
                                                 // blocks
    private static final int MAX_INTERACT_DISTANCE_SQ =
        (int)Math.round(4.5 * 4.5); // ~4.5 blocks
    private static final int TRY_COOLDOWN_TICKS = 100; // 5 seconds @20TPS
    
    // --- state ---
    private static boolean enabled = false;
    private static String requestId = null;
    private static String correlationId = null;
    private static String identity = null;
    private static int scanRadius = DEFAULT_RADIUS;
    
    private static long lastTryGameTime = -1;
    @Nullable
    private static BlockPos bedPos = null;
    private static Phase phase = Phase.IDLE;
    
    private static final WurstClient WURST = WurstClient.INSTANCE;
    
    private enum Phase
    {
        IDLE,
        ARMED,
        WAIT_NIGHT,
        APPROACHING,
        INTERACTING,
        SLEEPING,
        DONE,
        FAILED
    }
    
    private SleepUtil()
    {}
    
    // Call once from your client initializer
    public static void init()
    {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if(!enabled)
                return;
            tick(client);
        });
        EventManager.INSTANCE.add(MqttMessageListener.class,
            SleepMessageHandler.INSTANCE);
    }
    
    // Your MQTT handler should call this when it receives {"cmd":"sleep",
    // "requestId":"...", "radius":N}
    public static void start(String reqId, @Nullable Integer radiusOverride)
    {
        start(reqId, null, null, radiusOverride);
    }
    
    /**
     * Start sleep with full correlation tracking
     */
    public static void start(String reqId, @Nullable String corrId,
        @Nullable String ident, @Nullable Integer radiusOverride)
    {
        Minecraft client = Minecraft.getInstance();
        enabled = true;
        requestId = reqId;
        correlationId = corrId;
        identity = (ident != null) ? ident : "mqttbot";
        scanRadius = (radiusOverride != null && radiusOverride > 0)
            ? radiusOverride : DEFAULT_RADIUS;
        bedPos = null;
        lastTryGameTime = -1;
        phase = Phase.ARMED;
        emit("sleep_armed", null);
        // immediate tick to reduce latency
        if(client != null)
            tick(client);
    }
    
    // Optional cancel/stop
    public static void stop(@Nullable String reason)
    {
        enabled = false;
        emit("sleep_stopped", reason);
        clearCorrelation();
        bedPos = null;
        phase = Phase.IDLE;
    }
    
    /**
     * Clear correlation tracking
     */
    private static void clearCorrelation()
    {
        requestId = null;
        correlationId = null;
        identity = null;
    }
    
    private static void tick(Minecraft client)
    {
        if(Minecraft.getInstance().level == null || client.player == null)
        {
            fail("no_client");
            return;
        }
        Level w = Minecraft.getInstance().level;
        
        switch(phase)
        {
            case ARMED ->
            {
                // Find nearest bed first; if none, fail early (controller can
                // decide what to do)
                bedPos = findNearestBed(client, scanRadius);
                if(bedPos == null)
                {
                    fail("no_bed_nearby");
                    return;
                }
                emit("sleep_bed_found", bedPosJson());
                // If it's night-ish, proceed; else wait
                if(isNightish(w))
                {
                    phase = Phase.APPROACHING;
                }else
                {
                    phase = Phase.WAIT_NIGHT;
                    emit("sleep_waiting_night", null);
                }
            }
            case WAIT_NIGHT ->
            {
                if(isNightish(w))
                {
                    phase = Phase.APPROACHING;
                }
            }
            case APPROACHING ->
            {
                // If we drifted, re-scan (e.g., moved radius away)
                if(bedPos == null || Minecraft.getInstance().level
                    .getBlockState(bedPos).isAir())
                {
                    bedPos = findNearestBed(client, scanRadius);
                    if(bedPos == null)
                    {
                        fail("bed_missing");
                        return;
                    }
                    emit("sleep_bed_found", bedPosJson());
                }
                // If too far to interact, ask controller to move us closer OR
                // you can auto-publish a #goto here.
                if(!withinInteractDistance(client, bedPos))
                {
                    emit("sleep_too_far", bedPosJson()); // controller can #goto
                                                         // bedPos
                    // stay in APPROACHING; controller will move us; we'll try
                    // again next tick
                    return;
                }
                phase = Phase.INTERACTING;
            }
            case INTERACTING ->
            {
                if(!isNightish(w))
                {
                    // still daylight or not storming: throttle messages; stay
                    // in INTERACTING until night or thunder
                    return;
                }
                long now = w.getGameTime();
                if(lastTryGameTime != -1
                    && (now - lastTryGameTime) < TRY_COOLDOWN_TICKS)
                {
                    return; // cooldown
                }
                // Try to sleep: right-click the bed
                rightClickBlockLegit(bedPos);
                var hit = new BlockHitResult(Vec3.atCenterOf(bedPos),
                    Direction.UP, bedPos, false);
                var res = client.gameMode.useItemOn(client.player,
                    InteractionHand.MAIN_HAND, hit);
                lastTryGameTime = now;
                emit("sleep_try", bedPosJson());
                // If the interaction succeeded, client will transition to
                // sleeping shortly.
                phase = Phase.SLEEPING;
            }
            case SLEEPING ->
            {
                // Wait until the client reports sleeping or we detect daybreak
                // (server advanced time)
                if(client.player.isSleeping())
                {
                    emit("sleep_started", null);
                    // We can stay here and watch for wake-up; but most servers
                    // skip to day quickly.
                }
                if(!isNightish(w))
                {
                    emit("sleep_done", null);
                    done();
                }
            }
            case DONE, FAILED, IDLE ->
            {
                // nothing
            }
        }
    }
    
    private static boolean rightClickBlockLegit(BlockPos pos)
    {
        // if breaking or riding, stop and don't try other blocks
        if(MC.player != null && MC.gameMode != null
            && (MC.gameMode.isDestroying() || MC.player.isHandsBusy()))
            return true;
        
        double range = 3;
        // if this block is unreachable, try the next one
        BlockBreaker.BlockBreakingParams params =
            BlockBreaker.getBlockBreakingParams(pos);
        if(params == null || params.distanceSq() > Mth.square(range)
            || !params.lineOfSight())
            return false;
        
        // face and right click the block
        MC.rightClickDelay = 4;
        WURST.getRotationFaker().faceVectorPacket(params.hitVec());
        InteractionSimulator.rightClickBlock(params.toHitResult());
        return true;
    }
    
    private static void done()
    {
        sendStandardResponse("success", "Sleep completed successfully", null);
        enabled = false;
        phase = Phase.DONE;
        clearCorrelation();
        bedPos = null;
    }
    
    private static void fail(String reason)
    {
        sendStandardResponse("failure", "Sleep failed", reason);
        enabled = false;
        phase = Phase.FAILED;
        clearCorrelation();
        bedPos = null;
    }
    
    // -------- helpers --------
    
    private static boolean isNightish(@UnknownNullability Level w)
    {
        if(w.dimension() != Level.OVERWORLD)
            return true; // be permissive in other dims
        if(!w.dimensionType().hasSkyLight() || w.dimensionType().hasFixedTime())
            return true;
        long tod = w.getDayTime() % DAY_TICKS;
        boolean nightByTime = (tod >= NIGHT_START && tod < NIGHT_END);
        return nightByTime || w.isThundering();
    }
    
    private static boolean withinInteractDistance(Minecraft client,
        BlockPos pos)
    {
        var p = client.player;
        double distSq = p.distanceToSqr(Vec3.atCenterOf(pos));
        return distSq <= MAX_INTERACT_DISTANCE_SQ;
    }
    
    @Nullable
    private static BlockPos findNearestBed(Minecraft client, int radius)
    {
        if(client.level == null || client.player == null)
            return null;
        BlockPos player = client.player.blockPosition();
        BlockPos best = null;
        double bestSq = Double.POSITIVE_INFINITY;
        
        int r = Math.max(1, radius);
        for(int dx = -r; dx <= r; dx++)
        {
            for(int dy = -1; dy <= 2; dy++)
            { // search a small vertical window
                for(int dz = -r; dz <= r; dz++)
                {
                    BlockPos bp = player.offset(dx, dy, dz);
                    BlockState st = client.level.getBlockState(bp);
                    if(!st.is(BlockTags.BEDS))
                        continue;
                    double d2 = bp.distSqr(player);
                    if(d2 < bestSq)
                    {
                        best = bp;
                        bestSq = d2;
                    }
                }
            }
        }
        return best;
    }
    
    private static String bedPosJson()
    {
        if(bedPos == null)
            return null;
        return "{\"x\":" + bedPos.getX() + ",\"y\":" + bedPos.getY() + ",\"z\":"
            + bedPos.getZ() + "}";
    }
    
    // Replace this with your actual MQTT publish; include requestId if present
    
    /**
     * Send standard success/failure response
     */
    private static void sendStandardResponse(String status, String message,
        String reason)
    {
        try
        {
            var mc = Minecraft.getInstance();
            String playerName =
                (mc.player != null) ? mc.getUser().getName() : "unknown";
            
            JsonObject response = new JsonObject();
            response.addProperty("status", status);
            response.addProperty("message", message);
            if(reason != null)
            {
                response.addProperty("reason", reason);
            }
            response.addProperty("player", playerName);
            
            if(bedPos != null)
            {
                response.addProperty("bedX", bedPos.getX());
                response.addProperty("bedY", bedPos.getY());
                response.addProperty("bedZ", bedPos.getZ());
            }
            
            // Use stored correlation info if available
            String reqId = (requestId != null) ? requestId
                : java.util.UUID.randomUUID().toString();
            String corrId = correlationId;
            String ident = (identity != null) ? identity : "mqttbot";
            
            EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName,
                new ServiceMessage("sleep", "start", reqId, corrId, null,
                    response,
                    ident, null)));
            
        }catch(Exception e)
        {
            System.err
                .println("Error sending sleep response: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Legacy emit method - kept for other notifications
     */
    private static void emit(String type, @Nullable String extraJson)
    {
        StringBuilder sb = new StringBuilder(128);
        sb.append("{\"type\":\"").append(type).append("\"");
        if(requestId != null)
            sb.append(",\"requestId\":\"").append(requestId).append("\"");
        if(bedPos != null)
        {
            sb.append(",\"bedX\":").append(bedPos.getX()).append(",\"bedY\":")
                .append(bedPos.getY()).append(",\"bedZ\":")
                .append(bedPos.getZ());
        }
        if(extraJson != null)
            sb.append(",\"extra\":").append(extraJson);
        sb.append('}');
        // Example: Mqtt.publish("baritone/"+clientId+"/event", sb.toString());
        LOGGER.debug("[Sleep] " + sb);
    }
}
