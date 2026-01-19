package org.limepepper.gametest.facade;

import net.fabricmc.fabric.api.client.gametest.v1.TestInput;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import org.jetbrains.annotations.Nullable;
import org.limepepper.gametest.utils.ExternalServerConnection;
import org.lwjgl.glfw.GLFW;

/**
 * Facade implementation for external servers (PaperMC, Spigot, etc.).
 * Executes commands by sending them via chat as an OP player, since we don't
 * have direct JVM access to the server process.
 */
@SuppressWarnings("UnstableApiUsage")
public class ExternalServerFacade implements TestServerFacade {
    
    private final ClientGameTestContext context;
    private final ExternalServerConnection connection;
    private final String playerName;
    
    /**
     * Creates a facade for an external server connection.
     *
     * @param context
     *            The client game test context
     * @param connection
     *            The external server connection
     * @param playerName
     *            The name of the player/bot on the server
     */
    public ExternalServerFacade(
        ClientGameTestContext context,
        ExternalServerConnection connection,
        String playerName)
    {
        this.context = context;
        this.connection = connection;
        this.playerName = playerName;
    }
    
    @Override
    public void executeCommand(String command)
    {
        // Send command via chat as OP player
        TestInput input = context.getInput();
        input.pressKey(GLFW.GLFW_KEY_T);
        input.typeChars("/" + command);
        input.pressKey(GLFW.GLFW_KEY_ENTER);
        
        // Give server time to process command
        // context.waitTicks(2);
    }
    
    @Override
    public void waitForChunksDownload()
    {
        connection.waitForChunksDownload();
    }
    
    @Override
    public void waitForChunksRender()
    {
        connection.waitForChunksRender();
    }
    
    @Override
    public boolean isIntegratedServer()
    {
        return false;
    }
    
    @Override
    @Nullable
    public String getPlayerName()
    {
        return playerName;
    }
}
