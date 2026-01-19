package org.limepepper.gametest.tests;

import net.fabricmc.fabric.api.client.gametest.v1.TestInput;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import org.limepepper.gametest.MiniTestContext;
import org.limepepper.gametest.BotTest;
import org.limepepper.gametest.facade.TestServerFacade;

import java.util.HashMap;
import java.util.Map;

import static org.limepepper.gametest.BotTestHelper.*;

@SuppressWarnings("UnstableApiUsage")
public enum AutoFarmTest
{
    ;
    
    public static void testAutoFarmPlaceAtFootLevel(
        ClientGameTestContext context, TestServerFacade server,
        String interactBlock)
    {
        TestInput input = context.getInput();
        
        BotTest.LOGGER.info("Testing AutoFarm place at foot level with {}",
            interactBlock);
        
        // Use MiniTestContext for isolated setup/teardown
        try(MiniTestContext testCtx = new MiniTestContext(context, server))
        {
            // Create block dictionary for easier test definition
            Map<String, String> blocks = new HashMap<>();
            blocks.put("stone", "minecraft:stone");
            blocks.put("farm", "minecraft:farmland");
            blocks.put("carrot", "minecraft:carrots[age=7]");
            blocks.put("interact", interactBlock);
            
            // Set up layer at Y=-1 (ground level)
            // 5x3 array: center (2,1) is farmland (under player)
            // Original: Z=-2 (stone), Z=-1 (farmland), Z=0 (farmland)
            testCtx.setBlockLayer(-1, blocks,
                new String[][]{{null, "stone", null}, // Z=-2: stone under
                                                      // interactable
                    {null, "farm", null}, // Z=-1: farmland in front
                    {null, "stone", null}, // Z=0: farmland under player
                                           // (center)
                    {null, null, null}, // Z=1: empty
                    {null, null, null} // Z=2: empty
                });
            
            // Set up layer at Y=0 (player level)
            // 5x3 array: center (2,1) is player position
            // Original: Z=-2 (interactable), Z=-1 (carrot), Z=0 (player)
            testCtx.setBlockLayer(0, blocks,
                new String[][]{{null, "interact", null}, // Z=-2: interactable
                                                         // block
                    {null, "carrot", null}, // Z=-1: crop
                    {null, "player", null}, // Z=0: player position (center)
                    {null, null, null}, // Z=1: empty
                    {null, null, null} // Z=2: empty
                });
            
            // Teleport to test location with specific rotation
            testCtx.teleportPlayer(0.3F, 0, 0.4f, -175.8f, 33.5f);
            
            // In case the farmed block doesn't go into inventory
            runWurstCommand(context, "give carrot");
            
            runCommand(server, "gamemode survival");
            waitForCropAge(context, 0, 0, -1, 7);
            
            runWurstCommand(context, "t AutoFarm on");
            context.waitTick();
            waitForCropAge(context, 0, 0, -1, 0);
            debugBlock(0, 0, -1);
            context.waitTick();
            context.takeScreenshot("farm_test5");
            runWurstCommand(context, "t AutoFarm off");
        }
        // MiniTestContext automatically handles cleanup via close()
    }
}
