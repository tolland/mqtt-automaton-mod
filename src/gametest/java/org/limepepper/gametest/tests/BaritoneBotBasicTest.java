package org.limepepper.gametest.tests;

import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.gametest.v1.TestInput;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import org.limepepper.gametest.BotTest;
import org.limepepper.gametest.MiniTestContext;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

import static org.limepepper.gametest.BotTestHelper.*;

@SuppressWarnings("UnstableApiUsage")
public enum BaritoneBotBasicTest
{
    ;
    
    public static void testBaritoneIsWorking(ClientGameTestContext context,
        TestSingleplayerContext spContext)
    {
        TestInput input = context.getInput();
        TestServerContext server = spContext.getServer();
        
        BotTest.LOGGER.info("Testing Baritone pathing functionality");
        
        // Use MiniTestContext for isolated setup/teardown
        try(MiniTestContext testCtx = new MiniTestContext(context, server))
        {
            // Create block dictionary for easier test definition
            Map<String, String> blocks = new HashMap<>();
            blocks.put("stone", "minecraft:stone");
            
            // Set up a platform at Y=-1 to prevent falling into void
            // Create a 7x5 platform to cover starting position and destination
            // (3 blocks east)
            testCtx.setBlockLayer(-1, blocks, new String[][]{
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=-2
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=-1
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=0
                                                                                 // (center)
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=1
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"} // Z=2
            });
            
            // Set up a platform at Y=0 for the destination
            // Leave center clear for player, but ensure path is clear
            testCtx.setBlockLayer(0, blocks,
                new String[][]{{null, null, null, null, null, null, null}, // Z=-2
                    {null, null, null, null, null, null, null}, // Z=-1
                    {null, null, "player", null, null, null, null}, // Z=0
                                                                    // (center -
                                                                    // player
                                                                    // start)
                    {null, null, null, null, null, null, null}, // Z=1
                    {null, null, null, null, null, null, null} // Z=2
                });
                
            // Teleport to test location
            testCtx.teleportPlayer(0.5F, 0, 0.5f, 0f, 0f);
            
            // Set gamemode to survival for realistic pathing
            runCommand(server, "gamemode survival");
            context.waitTick();
            
            // Capture starting position to calculate target coordinates
            AtomicReference<BlockPos> startPosRef = new AtomicReference<>();
            context.runOnClient(mc -> {
                assert mc.player != null;
                startPosRef.set(mc.player.blockPosition());
            });
            context.waitTick(); // Ensure position is captured
            
            BlockPos startPos = startPosRef.get();
            if(startPos == null)
            {
                throw new RuntimeException(
                    "Failed to capture starting position");
            }
            
            // Calculate target position using relative coordinates (3 blocks
            // east)
            BlockPos targetPos = startPos.offset(3, 0, 0);
            
            // Send baritone command to path to the target location
            String gotoCmd = String.format("#goto %d %d %d", targetPos.getX(),
                targetPos.getY(), targetPos.getZ());
            sendChat(context, gotoCmd);
            
            // Wait for baritone bot to arrive at the target location
            waitForLocation(context, targetPos.getX(), targetPos.getY(),
                targetPos.getZ());
            
            context.waitTick();
            context.takeScreenshot("baritone_test");
            
            BotTest.LOGGER.info("Baritone pathing test completed successfully");
        }
        // MiniTestContext automatically handles cleanup via close()
    }
    
    public static void testBaritoneIsWorking2(ClientGameTestContext context,
        TestSingleplayerContext spContext)
    {
        TestInput input = context.getInput();
        TestServerContext server = spContext.getServer();
        
        BotTest.LOGGER.info("Testing Baritone pathing functionality");
        
        // Use MiniTestContext for isolated setup/teardown
        try(MiniTestContext testCtx = new MiniTestContext(context, server))
        {
            // Create block dictionary for easier test definition
            Map<String, String> blocks = new HashMap<>();
            blocks.put("stone", "minecraft:stone");
            
            // Set up a platform at Y=-1 to prevent falling into void
            // Create a 7x5 platform to cover starting position and destination
            // (3 blocks east)
            testCtx.setBlockLayer(-1, blocks, new String[][]{
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=-2
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=-1
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=0
                                                                                 // (center)
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"}, // Z=1
                {"stone", "stone", "stone", "stone", "stone", "stone", "stone"} // Z=2
            });
            
            // Set up a platform at Y=0 for the destination
            // Leave center clear for player, but ensure path is clear
            testCtx.setBlockLayer(0, blocks,
                new String[][]{{null, null, null, null, null, null, null}, // Z=-2
                    {null, null, null, null, null, null, null}, // Z=-1
                    {null, null, "player", null, null, null, null}, // Z=0
                                                                    // (center -
                                                                    // player
                                                                    // start)
                    {null, null, null, null, null, null, null}, // Z=1
                    {null, null, null, null, null, null, null} // Z=2
                });
                
            // Teleport to test location
            testCtx.teleportPlayer(0.5F, 0, 0.5f, 0f, 0f);
            
            // Set gamemode to survival for realistic pathing
            runCommand(server, "gamemode survival");
            context.waitTick();
            
            // Capture starting position to calculate target coordinates
            AtomicReference<BlockPos> startPosRef = new AtomicReference<>();
            context.runOnClient(mc -> {
                assert mc.player != null;
                startPosRef.set(mc.player.blockPosition());
            });
            context.waitTick(); // Ensure position is captured
            
            BlockPos startPos = startPosRef.get();
            if(startPos == null)
            {
                throw new RuntimeException(
                    "Failed to capture starting position");
            }
            
            // Calculate target position using relative coordinates (3 blocks
            // east)
            BlockPos targetPos = startPos.offset(3, 0, 0);
            
            // Send baritone command to path to the target location
            String gotoCmd = String.format("#goto %d %d %d", targetPos.getX(),
                targetPos.getY(), targetPos.getZ());
            // sendChat(context, gotoCmd);
            String botId = "Wurst-Bot";
            var params = new JsonObject();
            params.addProperty("params", gotoCmd);
            MessageData structuredMessage = new MessageData("baritone", "goto",
                UUID.randomUUID().toString(), UUID.randomUUID().toString(),
                params, "mqttbot", null
            
            );
            EventManager.fire(new MqttMessageListener.MqttMessageEvent(botId,
                structuredMessage));
            
            // Wait for baritone bot to arrive at the target location
            waitForLocation(context, targetPos.getX(), targetPos.getY(),
                targetPos.getZ());
            
            context.waitTick();
            context.takeScreenshot("baritone_test2");
            
            BotTest.LOGGER.info("Baritone pathing test completed successfully");
        }
        // MiniTestContext automatically handles cleanup via close()
    }
}
