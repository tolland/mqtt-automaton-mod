package org.limepepper.gametest.facade;

import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import org.jetbrains.annotations.Nullable;

/**
 * Facade interface that abstracts server operations for testing.
 * Allows tests to work with both integrated servers (singleplayer) and
 * external servers (PaperMC/Spigot) using the same API.
 * <p>
 * This facade translates high-level test operations into either:
 * - Direct server-side execution (for integrated servers with JVM access)
 * - Client-side command execution (for external servers via OP player)
 */
@SuppressWarnings("UnstableApiUsage")
public interface TestServerFacade {

    /**
     * Executes a command on the server.
     * For integrated servers, this runs directly on the server thread.
     * For external servers, this sends the command via chat as an OP player.
     *
     * @param command The command to execute (without leading slash)
     */
    void executeCommand(String command);

    /**
     * Gets the client world context for chunk waiting and world access.
     *
     * @return The client world context
     */
    TestClientWorldContext getClientWorld();

    /**
     * Checks if this facade is backed by an integrated server.
     * Useful for tests that need different behavior between integrated and external.
     *
     * @return true if using integrated server, false for external server
     */
    boolean isIntegratedServer();

    /**
     * Gets the player name that commands will execute as.
     * For integrated servers, this is typically resolved via @p.
     * For external servers, this is the actual bot username.
     *
     * @return The player name, or null if using @p selector
     */
    @Nullable
    String getPlayerName();
}
