package org.limepepper.gametest.utils;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.impl.client.gametest.threading.ThreadingImpl;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.network.chat.Component;
import org.jetbrains.annotations.Nullable;
import org.limepepper.gametest.facade.ExternalServerFacade;
import org.limepepper.gametest.facade.TestServerFacade;

/**
 * Connection handle for an external server.
 */
@SuppressWarnings("UnstableApiUsage")
public class ExternalServerConnection implements AutoCloseable {
    private final ClientGameTestContext context;
    private boolean closed = false;
    
    ExternalServerConnection(ClientGameTestContext context)
    {
        this.context = context;
    }
    
    /**
     * Gets the client level (world).
     *
     * @return The client level, or null if not connected
     */
    @Nullable
    public ClientLevel getClientLevel()
    {
        return context.computeOnClient(client -> client.level);
    }

    /**
     * Gets the name of the connected player.
     *
     * @return The player name, or null if not connected
     */
    @Nullable
    public String getPlayerName()
    {
        return context.computeOnClient(client -> {
            if(client.player == null)
                return null;
            return client.player.getName().getString();
        });
    }

    /**
     * Creates a TestServerFacade for this connection.
     * This facade can be used with MiniTestContext and other test utilities.
     *
     * @return A facade wrapping this external server connection
     * @throws IllegalStateException if player is not connected
     */
    public TestServerFacade createFacade()
    {
        String playerName = getPlayerName();
        if(playerName == null)
        {
            throw new IllegalStateException(
                "Cannot create facade: player not connected");
        }
        return new ExternalServerFacade(context, this, playerName);
    }
    
    /**
     * Waits for chunks to be downloaded and rendered.
     */
    public void waitForChunksDownload()
    {
        // Wait for chunks to start loading
        context.waitFor(client -> {
            if(client.level == null)
                return false;
            // Check if we have at least some chunks loaded around spawn
            return client.level.getChunkSource().getLoadedChunksCount() > 0;
        }, 400); // 20 second timeout
        
        // Give renderer time to catch up
        context.waitTicks(20);
    }
    
    /**
     * Waits for chunks to be rendered.
     */
    public void waitForChunksRender()
    {
        waitForChunksDownload();
        
        // Wait for chunk rendering to settle
        context.waitFor(client -> {
            if(client.level == null)
                return false;
            // Additional check that chunks are actually rendered
            return client.levelRenderer.hasRenderedAllSections();
        }, 400);
    }
    
    /**
     * Runs an action with the client level.
     *
     * @param action
     *            The action to run
     */
    public void withClientLevel(java.util.function.Consumer<ClientLevel> action)
    {
        context.runOnClient(client -> {
            if(client.level != null)
            {
                action.accept(client.level);
            }
        });
    }
    
    /**
     * Computes a value from the client level.
     *
     * @param function
     *            The function to compute
     * @return The computed value
     */
    public <T> T computeWithClientLevel(
        java.util.function.Function<ClientLevel, T> function)
    {
        return context.computeOnClient(client -> {
            if(client.level != null)
            {
                return function.apply(client.level);
            }
            return null;
        });
    }
    
    @Override
    public void close()
    {
        if(closed)
            return;
        
        ThreadingImpl.checkOnGametestThread("close");
        
        context.runOnClient(client -> {
            if(client.level == null)
            {
                return; // Already disconnected
            }
            
            client.level.disconnect(Component.literal("Test completed"));
            // client.clearClientLevel();
        });
        
        context.waitFor(client -> client.level == null, 100);
        context.setScreen(TitleScreen::new);
        closed = true;
    }
    
    public boolean isClosed()
    {
        return closed;
    }
}
