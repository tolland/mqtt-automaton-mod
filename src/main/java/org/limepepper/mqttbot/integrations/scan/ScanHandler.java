package org.limepepper.mqttbot.integrations.scan;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.entity.SignBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.limepepper.mqttbot.util.BlockLists;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.HashSet;
import java.util.Set;

/**
 * Handles world scanning requests - dumps raw entity and block data
 * for interpretation by pybot.
 *
 * Scans entities (item frames, etc.) and blocks (chests, signs, etc.)
 * within a specified radius and returns raw serialized data.
 */
public final class ScanHandler extends Action implements MqttMessageListener {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(ScanHandler.class);
    private static final Minecraft MC = Minecraft.getInstance();
    
    // Default scan radius in blocks
    private static final int DEFAULT_RADIUS = 64;
    
    // Maximum allowed radius to prevent performance issues
    private static final int MAX_RADIUS = 256;
    
    public static void init()
    {
        EventManager.INSTANCE.add(MqttMessageListener.class, new ScanHandler());
        LOGGER.info("ScanHandler initialized");
    }
    
    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent)
    {
        ServiceMessage data = mqttMessageEvent.serviceMessage;
        
        if(!"scan".equals(data.getService()))
        {
            return;
        }
        
        LOGGER.debug("Received scan command: {}", data.getMethod());
        
        switch(data.getMethod())
        {
            case "scan_area":
            handleScanArea(data);
            break;
            
            case "scan_containers":
            handleScanContainers(data);
            break;
            
            case "scan_entities":
            handleScanEntities(data);
            break;
            
            default:
            LOGGER.debug("Unknown scan method: {}", data.getMethod());
            sendErrorResponse(data, "Unknown method: " + data.getMethod());
        }
    }
    
    /**
     * Scan everything in area - entities and blocks
     */
    private void handleScanArea(ServiceMessage data)
    {
        if(MC.player == null || MC.level == null)
        {
            sendErrorResponse(data, "Player or level not available");
            return;
        }
        
        int radius = extractRadius(data);
        Vec3 center = MC.player.position();
        
        LOGGER.debug("Scanning area with radius {} around {}", radius, center);
        
        JsonObject result = new JsonObject();
        result.addProperty("scan_type", "area_scan");
        result.addProperty("timestamp", System.currentTimeMillis());
        
        // Add world identity
        addWorldIdentity(result);
        
        // Add center position
        JsonArray centerPos = new JsonArray();
        centerPos.add(center.x);
        centerPos.add(center.y);
        centerPos.add(center.z);
        result.add("center", centerPos);
        result.addProperty("radius", radius);
        
        // Scan entities
        JsonArray entities = scanEntities(center, radius);
        result.add("entities", entities);
        
        // Scan blocks (containers and signs)
        JsonArray blocks = scanBlocks(center, radius);
        result.add("blocks", blocks);
        
        // Add metadata
        result.addProperty("entity_count", entities.size());
        result.addProperty("block_count", blocks.size());
        
        sendResponse(data, result);
    }
    
    /**
     * Scan only containers and their associated item frames
     */
    private void handleScanContainers(ServiceMessage data)
    {
        if(MC.player == null || MC.level == null)
        {
            sendErrorResponse(data, "Player or level not available");
            return;
        }
        
        int radius = extractRadius(data);
        Vec3 center = MC.player.position();
        
        LOGGER.debug("Scanning containers with radius {} around {}", radius,
            center);
        
        JsonObject result = new JsonObject();
        result.addProperty("scan_type", "container_scan");
        result.addProperty("timestamp", System.currentTimeMillis());
        
        // Add world identity
        addWorldIdentity(result);
        
        JsonArray centerPos = new JsonArray();
        centerPos.add(center.x);
        centerPos.add(center.y);
        centerPos.add(center.z);
        result.add("center", centerPos);
        result.addProperty("radius", radius);
        
        // Scan for item frames (for labeling)
        JsonArray itemFrames = new JsonArray();
        for(Entity entity : MC.level.entitiesForRendering())
        {
            if(entity instanceof ItemFrame
                && isWithinRadius(entity.position(), center, radius))
            {
                itemFrames.add(serializeItemFrame((ItemFrame)entity));
            }
        }
        result.add("entities", itemFrames);
        
        // Scan for container blocks
        JsonArray containers = scanContainerBlocks(center, radius);
        result.add("blocks", containers);
        
        result.addProperty("entity_count", itemFrames.size());
        result.addProperty("block_count", containers.size());
        
        sendResponse(data, result);
    }
    
    /**
     * Scan only entities
     */
    private void handleScanEntities(ServiceMessage data)
    {
        if(MC.player == null || MC.level == null)
        {
            sendErrorResponse(data, "Player or level not available");
            return;
        }
        
        int radius = extractRadius(data);
        Vec3 center = MC.player.position();
        
        JsonObject result = new JsonObject();
        result.addProperty("scan_type", "entity_scan");
        result.addProperty("timestamp", System.currentTimeMillis());
        
        // Add world identity
        addWorldIdentity(result);
        
        JsonArray centerPos = new JsonArray();
        centerPos.add(center.x);
        centerPos.add(center.y);
        centerPos.add(center.z);
        result.add("center", centerPos);
        result.addProperty("radius", radius);
        
        JsonArray entities = scanEntities(center, radius);
        result.add("entities", entities);
        result.addProperty("entity_count", entities.size());
        
        sendResponse(data, result);
    }
    
    /**
     * Scan entities within radius - returns raw entity data
     */
    private JsonArray scanEntities(Vec3 center, int radius)
    {
        JsonArray entities = new JsonArray();
        
        for(Entity entity : MC.level.entitiesForRendering())
        {
            if(isWithinRadius(entity.position(), center, radius))
            {
                JsonObject entityData = serializeEntity(entity);
                if(entityData != null)
                {
                    entities.add(entityData);
                }
            }
        }
        
        return entities;
    }
    
    /**
     * Scan blocks within radius - returns raw block data
     */
    private JsonArray scanBlocks(Vec3 center, int radius)
    {
        JsonArray blocks = new JsonArray();
        
        // Scan container blocks
        JsonArray containers = scanContainerBlocks(center, radius);
        for(JsonElement elem : containers)
        {
            blocks.add(elem);
        }
        
        // Scan sign blocks
        JsonArray signs = scanSignBlocks(center, radius);
        for(JsonElement elem : signs)
        {
            blocks.add(elem);
        }
        
        return blocks;
    }
    
    /**
     * Scan for container blocks (chests, barrels, etc.)
     */
    private JsonArray scanContainerBlocks(Vec3 center, int radius)
    {
        JsonArray blocks = new JsonArray();
        Set<BlockPos> scannedPositions = new HashSet<>();
        
        int cx = (int)Math.floor(center.x);
        int cy = (int)Math.floor(center.y);
        int cz = (int)Math.floor(center.z);
        
        // Iterate through cubic volume
        for(int x = cx - radius; x <= cx + radius; x++)
        {
            for(int y = Math.max(MC.level.getMinY(), cy - radius); y <= Math
                .min(MC.level.getMaxY(), cy + radius); y++)
            {
                for(int z = cz - radius; z <= cz + radius; z++)
                {
                    
                    BlockPos pos = new BlockPos(x, y, z);
                    
                    // Skip if already scanned
                    if(scannedPositions.contains(pos))
                    {
                        continue;
                    }
                    scannedPositions.add(pos);
                    
                    // Check if within spherical radius
                    Vec3 blockPos = new Vec3(x + 0.5, y + 0.5, z + 0.5);
                    if(!isWithinRadius(blockPos, center, radius))
                    {
                        continue;
                    }
                    
                    BlockState state = MC.level.getBlockState(pos);
                    Block block = state.getBlock();
                    
                    if(BlockLists.CONTAINER_BLOCKS.contains(block))
                    {
                        blocks.add(serializeBlock(pos, block));
                    }
                }
            }
        }
        
        return blocks;
    }
    
    /**
     * Scan for sign blocks
     */
    private JsonArray scanSignBlocks(Vec3 center, int radius)
    {
        JsonArray blocks = new JsonArray();
        Set<BlockPos> scannedPositions = new HashSet<>();
        
        int cx = (int)Math.floor(center.x);
        int cy = (int)Math.floor(center.y);
        int cz = (int)Math.floor(center.z);
        
        for(int x = cx - radius; x <= cx + radius; x++)
        {
            for(int y = Math.max(MC.level.getMinY(), cy - radius); y <= Math
                .min(MC.level.getMaxY(), cy + radius); y++)
            {
                for(int z = cz - radius; z <= cz + radius; z++)
                {
                    
                    BlockPos pos = new BlockPos(x, y, z);
                    
                    if(scannedPositions.contains(pos))
                    {
                        continue;
                    }
                    scannedPositions.add(pos);
                    
                    Vec3 blockPos = new Vec3(x + 0.5, y + 0.5, z + 0.5);
                    if(!isWithinRadius(blockPos, center, radius))
                    {
                        continue;
                    }
                    
                    BlockState state = MC.level.getBlockState(pos);
                    Block block = state.getBlock();
                    
                    if(BlockLists.SIGN_BLOCKS.contains(block))
                    {
                        blocks.add(serializeSign(pos));
                    }
                }
            }
        }
        
        return blocks;
    }
    
    /**
     * Serialize entity to JSON - raw data, no interpretation
     */
    private JsonObject serializeEntity(Entity entity)
    {
        JsonObject data = new JsonObject();
        
        // Basic entity info
        String entityType =
            BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString();
        data.addProperty("type", entityType);
        data.addProperty("uuid", entity.getUUID().toString());
        
        // Position
        Vec3 pos = entity.position();
        JsonArray posArray = new JsonArray();
        posArray.add(pos.x);
        posArray.add(pos.y);
        posArray.add(pos.z);
        data.add("pos", posArray);
        
        // Type-specific data in "extra" field
        JsonObject extra = new JsonObject();
        
        if(entity instanceof ItemFrame itemFrame)
        {
            extra.addProperty("facing", itemFrame.getDirection().getName());
            extra.addProperty("rotation", itemFrame.getRotation());
            
            ItemStack item = itemFrame.getItem();
            if(!item.isEmpty())
            {
                extra.addProperty("item_id",
                    BuiltInRegistries.ITEM.getKey(item.getItem()).toString());
                extra.addProperty("item_count", item.getCount());
            }
        }
        
        data.add("extra", extra);
        
        return data;
    }
    
    /**
     * Serialize item frame specifically (common operation)
     */
    private JsonObject serializeItemFrame(ItemFrame itemFrame)
    {
        return serializeEntity(itemFrame);
    }
    
    /**
     * Serialize block to JSON - raw data
     */
    private JsonObject serializeBlock(BlockPos pos, Block block)
    {
        JsonObject data = new JsonObject();
        
        String blockType = BuiltInRegistries.BLOCK.getKey(block).toString();
        data.addProperty("type", blockType);
        
        JsonArray posArray = new JsonArray();
        posArray.add(pos.getX());
        posArray.add(pos.getY());
        posArray.add(pos.getZ());
        data.add("pos", posArray);
        
        // Block entity data if applicable
        JsonObject extra = new JsonObject();
        BlockEntity be = MC.level.getBlockEntity(pos);
        if(be != null)
        {
            if(be instanceof ChestBlockEntity chest)
            {
                extra.addProperty("slot_count", chest.getContainerSize());
                // Don't serialize contents here - that's a separate query
            }
        }
        data.add("extra", extra);
        
        return data;
    }
    
    /**
     * Serialize sign with text
     */
    private JsonObject serializeSign(BlockPos pos)
    {
        JsonObject data = new JsonObject();
        
        BlockState state = MC.level.getBlockState(pos);
        Block block = state.getBlock();
        String blockType = BuiltInRegistries.BLOCK.getKey(block).toString();
        data.addProperty("type", blockType);
        
        JsonArray posArray = new JsonArray();
        posArray.add(pos.getX());
        posArray.add(pos.getY());
        posArray.add(pos.getZ());
        data.add("pos", posArray);
        
        // Sign text in extra
        JsonObject extra = new JsonObject();
        BlockEntity be = MC.level.getBlockEntity(pos);
        if(be instanceof SignBlockEntity sign)
        {
            JsonArray lines = new JsonArray();
            for(int i = 0; i < 4; i++)
            {
                lines.add(sign.getFrontText().getMessage(i, false).getString());
            }
            extra.add("lines", lines);
        }
        data.add("extra", extra);
        
        return data;
    }
    
    /**
     * Check if position is within radius of center
     */
    private boolean isWithinRadius(Vec3 pos, Vec3 center, double radius)
    {
        return pos.distanceTo(center) <= radius;
    }
    
    /**
     * Add world identity information to response.
     * Includes server address, dimension, and optionally seed.
     */
    private void addWorldIdentity(JsonObject result)
    {
        // Get dimension
        String dimension = MC.level.dimension().location().toString();
        result.addProperty("dimension", dimension);
        
        // Get server address or world name
        String serverAddress;
        if(MC.isLocalServer())
        {
            // Singleplayer - use world name if available
            if(MC.getSingleplayerServer() != null
                && MC.getSingleplayerServer().getWorldData() != null)
            {
                serverAddress =
                    MC.getSingleplayerServer().getWorldData().getLevelName();
            }else
            {
                serverAddress = "local";
            }
        }else
        {
            // Multiplayer - use server address
            if(MC.getCurrentServer() != null)
            {
                serverAddress = MC.getCurrentServer().ip;
            }else
            {
                serverAddress = "unknown";
            }
        }
        result.addProperty("server", serverAddress);
        
        // Add seed if available (for cache organization like Baritone)
        // Note: Seed may not always be available to client
        long seed = MC.level.getBiomeManager().biomeZoomSeed;
        result.addProperty("seed", seed);
    }
    
    /**
     * Extract radius parameter from request
     */
    private int extractRadius(ServiceMessage data)
    {
        int radius = DEFAULT_RADIUS;
        
        JsonElement paramsEl = data.getParams();
        if(paramsEl != null && paramsEl.isJsonObject())
        {
            JsonObject params = paramsEl.getAsJsonObject();
            if(params.has("radius"))
            {
                radius = params.get("radius").getAsInt();
            }
        }
        
        // Clamp to max radius
        if(radius > MAX_RADIUS)
        {
            LOGGER.warn("Requested radius {} exceeds max {}, clamping",
                radius, MAX_RADIUS);
            radius = MAX_RADIUS;
        }
        
        return radius;
    }
    
    private void sendResponse(ServiceMessage originalData,
        JsonObject responseData)
    {
        String playerName = MC.getUser().getName();
        
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName,
            new ServiceMessage("scan", originalData.getMethod(),
                originalData.getRequestId(), originalData.getCorrelationId(),
                null, responseData, "mqttbot", null)));
    }
    
    private void sendErrorResponse(ServiceMessage originalData, String error)
    {
        JsonObject responseData = new JsonObject();
        responseData.addProperty("error", error);
        sendResponse(originalData, responseData);
    }
}
