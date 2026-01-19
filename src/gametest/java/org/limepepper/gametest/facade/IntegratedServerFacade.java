package org.limepepper.gametest.facade;

import com.mojang.brigadier.ParseResults;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.commands.CommandSourceStack;
import org.jetbrains.annotations.Nullable;

/**
 * Facade implementation for integrated (singleplayer) servers.
 * Provides direct JVM access to the server for synchronous command execution.
 */
@SuppressWarnings("UnstableApiUsage")
public class IntegratedServerFacade implements TestServerFacade {

    private final TestSingleplayerContext singleplayerContext;

    public IntegratedServerFacade(TestSingleplayerContext singleplayerContext)
    {
        this.singleplayerContext = singleplayerContext;
    }

    @Override
    public void executeCommand(String command)
    {
        String commandWithPlayer = "execute as @p at @s run " + command;
        singleplayerContext.getServer().runOnServer(mc -> {
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

    @Override
    public TestClientWorldContext getClientWorld()
    {
        return singleplayerContext.getClientWorld();
    }

    @Override
    public boolean isIntegratedServer()
    {
        return true;
    }

    @Override
    @Nullable
    public String getPlayerName()
    {
        // Integrated server uses @p selector, no fixed name needed
        return null;
    }
}
