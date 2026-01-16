package org.limepepper.gametest.utils;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.impl.client.gametest.threading.ThreadingImpl;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;

/**
 * Context for connecting to an external server (e.g., PaperMC in Docker).
 * Use this in try-with-resources to automatically disconnect when done.
 */
@SuppressWarnings("UnstableApiUsage")
public class ExternalServerContext implements AutoCloseable {
    private final ClientGameTestContext context;
    private final String host;
    private final int port;
    private ExternalServerConnection activeConnection;
    
    public ExternalServerContext(ClientGameTestContext context, String host,
        int port)
    {
        this.context = context;
        this.host = host;
        this.port = port;
    }
    
    /**
     * Connects the client to the external server.
     *
     * @return The connection handle
     */
    public ExternalServerConnection connect()
    {
        ThreadingImpl.checkOnGametestThread("connect");
        
        if(activeConnection != null)
        {
            throw new IllegalStateException("Already connected to server");
        }
        
        context.runOnClient(client -> {
            String address = host + ":" + port;
            ServerData serverInfo =
                new ServerData("Test Server", address, ServerData.Type.OTHER);
            
            ConnectScreen.startConnecting(client.screen, client,
                ServerAddress.parseString(address), serverInfo, false, null);
        });
        
        // Wait for world to load
        context.waitFor(client -> client.level != null, 200); // 10 second
                                                              // timeout
        context.waitTicks(10); // Give it a bit more time to stabilize
        
        activeConnection = new ExternalServerConnection(context);
        
        return activeConnection;
    }
    
    /**
     * Disconnects from the server if connected.
     */
    @Override
    public void close()
    {
        ThreadingImpl.checkOnGametestThread("close");
        
        if(activeConnection != null)
        {
            activeConnection.close();
            activeConnection = null;
        }
    }
    
    /**
     * Builder for creating external server connections with various options.
     */
    public static class Builder {
        private final ClientGameTestContext context;
        private String host = "localhost";
        private int port = 25565;
        private Integer simulatedLatencyMs;
        
        public Builder(ClientGameTestContext context)
        {
            this.context = context;
        }
        
        public Builder host(String host)
        {
            this.host = host;
            return this;
        }
        
        public Builder port(int port)
        {
            this.port = port;
            return this;
        }
        
        /**
         * Simulate network latency (requires a mod like Lag Goggles or custom
         * implementation).
         */
        public Builder withSimulatedLatency(int latencyMs)
        {
            this.simulatedLatencyMs = latencyMs;
            return this;
        }
        
        public ExternalServerContext build()
        {
            ExternalServerContext serverContext =
                new ExternalServerContext(context, host, port);
            
            if(simulatedLatencyMs != null)
            {
                // You would implement latency simulation here
                // This could involve injecting into the network pipeline
                setupLatencySimulation(serverContext, simulatedLatencyMs);
            }
            
            return serverContext;
        }
        
        private void setupLatencySimulation(ExternalServerContext serverContext,
            int latencyMs)
        {
            // TODO: Implement latency simulation
            // This would require access to the Connection object and adding a
            // delay handler
            // You might use a mixin or accessor to inject into the netty
            // pipeline
        }
    }
}
