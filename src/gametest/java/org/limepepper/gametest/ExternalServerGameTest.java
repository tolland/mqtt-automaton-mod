package org.limepepper.gametest;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import org.limepepper.gametest.facade.TestServerFacade;
import org.limepepper.gametest.tests.AutoFarmTest;
import org.limepepper.gametest.tests.BaritoneBotBasicTest;
import org.limepepper.gametest.utils.ExternalServerConnection;
import org.limepepper.gametest.utils.ExternalServerContext;
import org.limepepper.gametest.utils.ExternalServerTestHelper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import static org.limepepper.gametest.BlockLists.getInteractiveBlocks;
import static org.limepepper.gametest.BotTestHelper.runWurstCommand;

@SuppressWarnings("UnstableApiUsage")
public class ExternalServerGameTest implements FabricClientGameTest {
    private static final Logger LOGGER =
        LoggerFactory.getLogger("external-server-test");
    private static final Minecraft MC = Minecraft.getInstance();
    
    @Override
    public void runTest(ClientGameTestContext context)
    {
        // Wait for your Docker PaperMC server to be ready
        LOGGER.info("Waiting for external PaperMC server.. .");
        
        if(!ExternalServerTestHelper.waitForServerReady("docker.lan", 25565,
            30))
        {
            throw new AssertionError("PaperMC server did not start in time");
        }
        
        // Connect to the external server
        try(ExternalServerContext serverContext =
            new ExternalServerContext.Builder(context).host("docker.lan")
                .port(25565)
                // . withSimulatedLatency(100) // Optional: simulate 100ms
                // latency
                .build())
        {
            
            try(ExternalServerConnection connection = serverContext.connect())
            {
                LOGGER.info("Connected to external PaperMC server!");
                
                // Wait for chunks to load
                connection.waitForChunksDownload();
                context.waitTicks(5);
                
                // Get the client world
                ClientLevel clientLevel = connection.getClientLevel();
                if(clientLevel == null)
                {
                    throw new AssertionError(
                        "Client level is null after connection");
                }
                
                assert MC.level != null;
                LOGGER.info("Client level loaded: {}",
                    String.valueOf(MC.level.dimension()));
                
                // Take a screenshot
                context.takeScreenshot("external_server_spawn");
                
                // Test with the client world
                connection.withClientLevel(level -> {
                    LOGGER.info("Player position: {}",
                        level.players().getFirst().position());
                    
                    // Test blocks around player
                    BlockPos playerPos =
                        level.players().getFirst().blockPosition();
                    LOGGER.info("Block at player feet: {}",
                        level.getBlockState(playerPos).getBlock().getName()
                            .getString());
                });
                
                // Compute something from the world
                int loadedChunks = connection.computeWithClientLevel(
                    level -> level.getChunkSource().getLoadedChunksCount());
                LOGGER.info("Loaded chunks: {}", loadedChunks);
                
                // Create facade (automatically gets player name)
                TestServerFacade server = connection.createFacade();
                LOGGER.info("Created facade for player: {}",
                    server.getPlayerName());
                
                // Test your mod's functionality
                testModFeature(context, server);
                
                LOGGER.info("All external server tests passed!");
            }
        }
    }
    
    private void testModFeature(ClientGameTestContext context,
        TestServerFacade server)
    {
        LOGGER.info("Testing mod feature...");
        
        // Example: Using facade with MiniTestContext for isolated testing
        try(MiniTestContext testCtx = new MiniTestContext(context, server))
        {
            LOGGER.info("Setting up test area at test location");
            
            // Set some blocks
            testCtx.setBlock(0, 0, 1, "minecraft:stone");
            testCtx.setBlock(1, 0, 1, "minecraft:dirt");
            
            // Execute server commands
            server.executeCommand("time set noon");
            server.executeCommand("weather clear");
            
            context.waitTicks(5);
            // Test automatically cleans up blocks on close
        }
        
        runWurstCommand(context,
            "setmode WurstLogo visibility only_when_outdated");
        runWurstCommand(context, "setcheckbox HackList animations off");
        
        context.waitTicks(20); // Wait 1 second
        context.takeScreenshot("mod_feature_test");
        
        for(String block : getInteractiveBlocks())
        {
            
            AutoFarmTest.testAutoFarmPlaceAtFootLevel(context, server, block);
            
        }
        BaritoneBotBasicTest.testBaritoneIsWorking(context, server);
        BaritoneBotBasicTest.testBaritoneIsWorking2(context, server);
    }
    
}
