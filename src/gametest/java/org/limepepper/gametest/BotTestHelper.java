package org.limepepper.gametest;

import com.mojang.brigadier.ParseResults;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.fabricmc.fabric.api.client.gametest.v1.TestInput;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.commands.CommandSourceStack;
import org.lwjgl.glfw.GLFW;

@SuppressWarnings("UnstableApiUsage")
public enum BotTestHelper
{
    ;
    
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
}
