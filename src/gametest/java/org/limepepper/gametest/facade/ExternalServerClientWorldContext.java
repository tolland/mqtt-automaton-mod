package org.limepepper.gametest.facade;

import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.minecraft.SharedConstants;
import org.limepepper.gametest.utils.ExternalServerConnection;

/**
 * Adapter that wraps ExternalServerConnection to provide TestClientWorldContext
 * interface. This allows external server connections to be used wherever
 * TestClientWorldContext is expected.
 */
@SuppressWarnings("UnstableApiUsage")
public class ExternalServerClientWorldContext implements TestClientWorldContext {

    private final ExternalServerConnection connection;

    public ExternalServerClientWorldContext(ExternalServerConnection connection)
    {
        this.connection = connection;
    }

    @Override
    public int waitForChunksDownload(int timeout)
    {
        // Use the external server connection's implementation
        connection.waitForChunksDownload();
        // Return approximate ticks waited (not precise, but reasonable estimate)
        return 20; // roughly 1 second
    }

    /**
     * Waits for chunks to be rendered.
     * Note: timeout parameter is ignored as ExternalServerConnection
     * uses its own timeout logic.
     *
     * @param timeout The number of ticks before timing out (currently ignored)
     * @return The approximate number of ticks waited
     */
    public int waitForChunksRender(int timeout)
    {
        connection.waitForChunksRender();
        // Return approximate ticks waited
        return 40; // roughly 2 seconds
    }

    /**
     * Default implementation delegating to timeout version.
     */
    public int waitForChunksRender()
    {
        return waitForChunksRender(SharedConstants.TICKS_PER_MINUTE);
    }
}
