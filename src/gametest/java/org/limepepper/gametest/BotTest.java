package org.limepepper.gametest;

import io.moquette.broker.Server;
import io.moquette.broker.config.MemoryConfig;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.TestInput;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.gametest.v1.world.TestWorldBuilder;
import net.minecraft.SharedConstants;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.FlatLevelSource;
import net.minecraft.world.level.levelgen.flat.FlatLayerInfo;
import net.minecraft.world.level.levelgen.flat.FlatLevelGeneratorSettings;
import org.limepepper.gametest.facade.IntegratedServerFacade;
import org.limepepper.gametest.facade.TestServerFacade;
import org.limepepper.gametest.tests.AutoFarmTest;
import org.limepepper.gametest.tests.BaritoneBotBasicTest;
import org.lwjgl.glfw.GLFW;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.List;
import java.util.Properties;

import static org.limepepper.gametest.BotTestHelper.*;

@SuppressWarnings("UnstableApiUsage")
public class BotTest implements FabricClientGameTest {
    
    public static final Logger LOGGER = LoggerFactory.getLogger("Mqtt Test");
    
    @Override
    public void runTest(ClientGameTestContext context)
    {
        
        Properties props = new Properties();
        props.put("port", "18883");
        props.put("host", "127.0.0.1");
        
        io.moquette.broker.Server broker = new Server();
        try
        {
            broker.startServer(new MemoryConfig(props));
            
            LOGGER.info("Started MQTT broker for testing");
            
            launchGameTestServer(context);
            
        }catch(IOException e)
        {
            throw new RuntimeException(e);
        }finally
        {
            broker.stopServer();
            LOGGER.info("Stopped MQTT broker after testing");
        }
        
        LOGGER.info("Test complete");
    }
    
    private void launchGameTestServer(ClientGameTestContext context)
    {
        LOGGER.info("Starting Wurst Client GameTest");
        hideSplashTexts(context);
        waitForTitleScreenFade(context);
        
        LOGGER.info("Creating test world");
        TestWorldBuilder worldBuilder = context.worldBuilder();
        worldBuilder.adjustSettings(creator -> {
            String mcVersion = SharedConstants.getCurrentVersion().name();
            creator.setName("E2E Test " + mcVersion);
            creator.setGameMode(WorldCreationUiState.SelectedGameMode.CREATIVE);
            creator.getGameRules().getRule(GameRules.RULE_SENDCOMMANDFEEDBACK)
                .set(false, null);
            applyFlatPresetWithSmoothStone(creator);
        });
        
        try(TestSingleplayerContext spContext = worldBuilder.create())
        {
            TestClientWorldContext world = spContext.getClientWorld();
            TestServerFacade server = new IntegratedServerFacade(spContext);
            testInWorld(context, server);
            LOGGER.info("Exiting test world");
        }
    }
    
    private void testInWorld(ClientGameTestContext context,
        TestServerFacade server)
    {
        TestInput input = context.getInput();
        
        runWurstCommand(context,
            "setmode WurstLogo visibility only_when_outdated");
        runWurstCommand(context, "setcheckbox HackList animations off");
        
        runCommand(server, "time set noon");
        runCommand(server, "tp 0 -60 0");
        // runCommand(server, "fill ~ ~-3 ~ ~ ~-1 ~ smooth_stone");
        // runCommand(server, "fill ~-12 ~-3 ~10 ~12 ~9 ~10 smooth_stone");
        
        LOGGER.info("Loading chunks");
        context.waitTicks(2);
        // world.waitForChunksRender();
        
        input.pressKey(GLFW.GLFW_KEY_F3);
        input.pressKey(GLFW.GLFW_KEY_F5);
        
        context.waitTicks(10);
        
        for(String block : List.of("minecraft:comparator"))
        {
            
            AutoFarmTest.testAutoFarmPlaceAtFootLevel(context, server, block);
            
        }
        BaritoneBotBasicTest.testBaritoneIsWorking(context, server);
        BaritoneBotBasicTest.testBaritoneIsWorking2(context, server);
    }
    
    private void applyFlatPresetWithSmoothStone(WorldCreationUiState creator)
    {
        FlatLevelGeneratorSettings config = ((FlatLevelSource)creator
            .getSettings().selectedDimensions().overworld()).settings();
        
        List<FlatLayerInfo> layers =
            List.of(new FlatLayerInfo(1, Blocks.BEDROCK),
                new FlatLayerInfo(2, Blocks.DIRT),
                new FlatLayerInfo(1, Blocks.SMOOTH_STONE));
        
        creator.updateDimensions(
            (drm, dorHolder) -> dorHolder.replaceOverworldGenerator(drm,
                new FlatLevelSource(config.withBiomeAndLayers(layers,
                    config.structureOverrides(), config.getBiome()))));
    }
}
