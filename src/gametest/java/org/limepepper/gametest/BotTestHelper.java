package org.limepepper.gametest;

import com.mojang.brigadier.ParseResults;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.fabricmc.fabric.api.client.gametest.v1.TestInput;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.CropBlock;
import net.wurstclient.WurstClient;
import org.limepepper.gametest.facade.TestServerFacade;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.lwjgl.glfw.GLFW;

@SuppressWarnings("UnstableApiUsage")
public enum BotTestHelper
{
    ;
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BotTestHelper.class);
    
    /**
     * Executes a command using the facade (works with both integrated and
     * external servers).
     *
     * @param server The server facade
     * @param command The command to execute (without leading slash)
     */
    public static void runCommand(TestServerFacade server, String command)
    {
        server.executeCommand(command);
    }

    /**
     * Executes a command on an integrated server (legacy method).
     * Prefer using the TestServerFacade version for new code.
     *
     * @param server The server context
     * @param command The command to execute (without leading slash)
     */
    public static void runCommand(TestServerContext server, String command)
    {
        String commandWithPlayer = "execute as @p at @s run " + command;
        server.runOnServer(mc -> {
            ParseResults<CommandSourceStack> results =
                mc.getCommands().getDispatcher().parse(commandWithPlayer,
                    mc.createCommandSourceStack());

            if(!results.getExceptions().isEmpty())
            {
                StringBuilder errors =
                    new StringBuilder("Invalid command: /" + commandWithPlayer);
                for(CommandSyntaxException e : results.getExceptions().values())
                    errors.append("\n").append(e.getMessage());

                throw new RuntimeException(errors.toString());
            }

            mc.getCommands().performCommand(results, commandWithPlayer);
        });
    }
    
    public static void waitForTitleScreenFade(ClientGameTestContext context)
    {
        context.waitFor(mc -> {
            if(!(mc.screen instanceof TitleScreen titleScreen))
                return false;
            
            return !titleScreen.fading;
        });
    }
    
    /**
     * Clears nearby items using the facade.
     *
     * @param server The server facade
     */
    public static void clearNearbyItems(TestServerFacade server)
    {
        runCommand(server, "kill @e[type=item]");
    }

    /**
     * Clears nearby items (legacy method for TestServerContext).
     *
     * @param server The server context
     */
    public static void clearNearbyItems(TestServerContext server)
    {
        runCommand(server, "kill @e[type=item]");
    }
    
    public static void clearParticles(ClientGameTestContext context)
    {
        context.runOnClient(mc -> mc.particleEngine.clearParticles());
    }
    
    public static void clearToasts(ClientGameTestContext context)
    {
        context.runOnClient(mc -> mc.getToastManager().clear());
    }
    
    public static void hideSplashTexts(ClientGameTestContext context)
    {
        context.runOnClient(mc -> {
            mc.options.hideSplashTexts().set(true);
        });
    }
    
    public static void clearInventory(ClientGameTestContext context)
    {
        TestInput input = context.getInput();
        input.pressKey(GLFW.GLFW_KEY_T);
        input.typeChars("/clear");
        input.pressKey(GLFW.GLFW_KEY_ENTER);
    }
    
    public static void clearChat(ClientGameTestContext context)
    {
        context.runOnClient(mc -> mc.gui.getChat().clearMessages(true));
    }
    
    public static void debugBlock(int relX, int relY, int relZ)
    {
        final Minecraft MC = WurstClient.MC;
        assert MC.player != null;
        var pos = MC.player.blockPosition().offset(relX, relY, relZ);
        assert MC.level != null;
        var state = MC.level.getBlockState(pos);
        
        StringBuilder sb = new StringBuilder();
        sb.append("Block @ ").append(pos).append("\n");
        sb.append("Block: ").append(state.getBlock()).append("\n");
        sb.append("BlockState: ").append(state).append("\n");
        sb.append("Properties:\n");
        
        for(var entry : state.getValues().entrySet())
        {
            sb.append("  ").append(entry.getKey().getName()).append(" = ")
                .append(entry.getValue()).append("\n");
        }
        
        LOGGER.debug(sb.toString());
    }
    
    public static void runWurstCommand(ClientGameTestContext context,
        String command)
    {
        TestInput input = context.getInput();
        input.pressKey(GLFW.GLFW_KEY_T);
        input.typeChars("." + command);
        input.pressKey(GLFW.GLFW_KEY_ENTER);
    }
    
    /**
     * Sends a chat message (e.g., for baritone commands).
     *
     * @param context
     *            the test context
     * @param message
     *            the chat message to send
     */
    public static void sendChat(ClientGameTestContext context, String message)
    {
        TestInput input = context.getInput();
        input.pressKey(GLFW.GLFW_KEY_T);
        input.typeChars(message);
        input.pressKey(GLFW.GLFW_KEY_ENTER);
    }
    
    /**
     * Waits for the player to arrive at a location.
     *
     * @param context
     *            the test context
     * @param absX
     *            player x coordinate
     * @param absY
     *            player y coordinate
     * @param absZ
     *            player z coordinate
     */
    public static void waitForLocation(ClientGameTestContext context, int absX,
        int absY, int absZ)
    {
        
        BlockPos targetPos = new BlockPos(absX, absY, absZ);
        
        context.waitFor(mc -> {
            assert mc.player != null;
            // Check if player is at the target block position
            return mc.player.blockPosition().equals(targetPos);
        });
    }
    
    /**
     * Waits for a crop at the given relative position to reach the given age.
     *
     * @param context
     *            the test context
     * @param relX
     *            relative X position from player
     * @param relY
     *            relative Y position from player
     * @param relZ
     *            relative Z position from player
     * @param age
     *            the expected age of the crop
     */
    public static void waitForCropAge(ClientGameTestContext context, int relX,
        int relY, int relZ, int age)
    {
        context.waitFor(mc -> {
            assert mc.player != null;
            assert mc.level != null;
            var state = mc.level.getBlockState(
                mc.player.blockPosition().offset(relX, relY, relZ));
            return (state.getBlock() instanceof CropBlock)
                && (((net.minecraft.world.level.block.CropBlock)state
                    .getBlock()).getAge(state) == age);
        });
    }
    
    public static void assertOneItemInSlot(ClientGameTestContext context,
        int slot, Item item)
    {
        ItemStack stack = context
            .computeOnClient(mc -> mc.player.getInventory().getItem(slot));
        if(!stack.is(item) || stack.getCount() != 1)
            throw new RuntimeException(
                "Expected 1 " + item.getName().getString() + " at slot " + slot
                    + ", found " + stack.getCount() + " "
                    + stack.getItem().getName().getString() + " instead");
    }
    
    /**
     * Waits for exactly one item of the specified type to appear in the given
     * inventory slot.
     * This method combines waiting and checking in a single client thread
     * deferral to avoid
     * double-deferring issues.
     *
     * @param context
     *            the test context
     * @param slot
     *            the inventory slot to check
     * @param item
     *            the expected item type
     */
    public static void waitForOneItemInSlot(ClientGameTestContext context,
        int slot, Item item)
    {
        context.waitFor(mc -> {
            assert mc.player != null;
            ItemStack stack = mc.player.getInventory().getItem(slot);
            return stack.is(item) && stack.getCount() >= 1;
        });
    }
}
