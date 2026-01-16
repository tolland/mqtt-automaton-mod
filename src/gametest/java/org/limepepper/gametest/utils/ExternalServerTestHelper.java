package org.limepepper.gametest.utils;

/**
 * Helper utilities for testing against external servers.
 */
public class ExternalServerTestHelper {
    
    /**
     * Wait for the external server to be ready before connecting.
     *
     * @param host
     *            Server host
     * @param port
     *            Server port
     * @param timeoutSeconds
     *            Maximum time to wait
     * @return true if server is ready, false if timeout
     */
    public static boolean waitForServerReady(String host, int port,
        int timeoutSeconds)
    {
        long startTime = System.currentTimeMillis();
        long timeoutMs = timeoutSeconds * 1000L;
        
        while(System.currentTimeMillis() - startTime < timeoutMs)
        {
            if(isServerReachable(host, port))
            {
                return true;
            }
            
            try
            {
                Thread.sleep(1000);
            }catch(InterruptedException e)
            {
                Thread.currentThread().interrupt();
                return false;
            }
        }
        
        return false;
    }
    
    private static boolean isServerReachable(String host, int port)
    {
        try(java.net.Socket socket = new java.net.Socket())
        {
            socket.connect(new java.net.InetSocketAddress(host, port), 1000);
            return true;
        }catch(Exception e)
        {
            return false;
        }
    }
    
    /**
     * Execute a command via RCON (requires RCON to be enabled on the server).
     */
    public static void executeRconCommand(String host, int rconPort,
        String password, String command)
    {
        // Implement RCON client here
        // You can use a library like rkon-core or implement your own
    }
}
