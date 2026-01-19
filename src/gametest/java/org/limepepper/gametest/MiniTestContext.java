package org.limepepper.gametest;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import org.limepepper.gametest.facade.TestServerFacade;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.limepepper.gametest.BotTestHelper.*;

/**
 * A mini test context that provides isolated test areas using TestLocation.
 * Each test gets its own area to avoid cross-test contamination.
 */
@SuppressWarnings("UnstableApiUsage")
public class MiniTestContext implements AutoCloseable {
    private static int testIndexCounter = 0;
    
    /**
     * Creates a block dictionary with common block aliases.
     *
     * @return a map with common block aliases (stone, dirt, farmland, etc.)
     */
    public static Map<String, String> createCommonBlockDict()
    {
        Map<String, String> dict = new HashMap<>();
        dict.put("stone", "minecraft:stone");
        dict.put("chest", "minecraft:chest");
        dict.put("smooth", "minecraft:smooth_stone");
        dict.put("dirt", "minecraft:dirt");
        dict.put("farm", "minecraft:farmland");
        dict.put("carrot", "minecraft:carrots[age=7]");
        dict.put("air", "minecraft:air");
        return dict;
    }
    
    private final ClientGameTestContext context;
    private final TestServerFacade server;
    private final MiniTestLocation location;
    private final List<String> placedBlocks = new ArrayList<>();
    private boolean isClosed = false;
    
    /**
     * Creates a new mini test context with an isolated test area.
     * Each context automatically gets a unique test index to ensure isolation.
     *
     * @param context
     *            the client game test context
     * @param server
     *            the server facade (integrated or external)
     */
    public MiniTestContext(ClientGameTestContext context,
        TestServerFacade server)
    {
        this.context = context;
        this.server = server;
        this.location = new MiniTestLocation(testIndexCounter++);
        
        setup();
    }
    
    /**
     * Sets up the test area: teleports player and prepares base environment.
     */
    private void setup()
    {
        String playerName =
            server.getPlayerName() != null ? server.getPlayerName() : "@p";
        
        BotTest.LOGGER.debug("Setting up test area for player: {}", playerName);
        
        // Ensure player is in creative mode (critical for external servers)
        BotTest.LOGGER.debug("Executing: gamemode creative");
        server.executeCommand("gamemode creative");
        context.waitTick();
        
        // Ensure base platform exists
        BotTest.LOGGER.debug("Setting base platform block");
        setBlock(0, -1, 0, "minecraft:smooth_stone");
        context.waitTick();
        
        // Teleport player to test location
        String tpCommand = location.tp(playerName, 0, 0, 0, 0, 0);
        BotTest.LOGGER.debug("Executing teleport: {}", tpCommand);
        server.executeCommand(tpCommand);
        context.waitTick();
        
        String rotateCommand = "rotate " + playerName + " 0 0";
        BotTest.LOGGER.debug("Executing rotate: {}", rotateCommand);
        server.executeCommand(rotateCommand);
        context.waitTick();
        
        // Set game rules for consistent testing
        BotTest.LOGGER.debug("Executing: gamerule randomTickSpeed 0");
        server.executeCommand("gamerule randomTickSpeed 0");
        
        context.waitTick();
        BotTest.LOGGER.debug("Test area setup complete at ({}, {}, {})",
            location.baseX, location.baseY, location.baseZ);
    }
    
    /**
     * Cleans up all blocks placed during the test and resets state.
     */
    @Override
    public void close()
    {
        if(isClosed)
            return;
        
        isClosed = true;
        
        BotTest.LOGGER.debug("Tearing down test area at ({}, {}, {})",
            location.baseX, location.baseY, location.baseZ);
        
        // Remove all placed blocks
        for(String coords : placedBlocks)
        {
            server.executeCommand(
                String.format("setblock %s minecraft:air replace", coords));
        }
        
        // Reset game rules
        BotTest.LOGGER.debug("Resetting game rules");
        server.executeCommand("gamerule randomTickSpeed 3");
        
        // Reset gamemode
        BotTest.LOGGER.debug("Resetting gamemode to creative");
        server.executeCommand("gamemode creative");
        
        // Clear client-side state
        BotTest.LOGGER.debug("Clearing inventory");
        clearInventory(context);
        context.waitTick();
        
        clearChat(context);
        clearToasts(context);
        
        BotTest.LOGGER.debug("Clearing nearby items with: kill @e[type=item]");
        clearNearbyItems(server);
        
        // Give the world a moment to process the cleanup
        context.waitTick();
        BotTest.LOGGER.debug("Teardown complete");
    }
    
    /**
     * Places a block at the given relative coordinates from the test location.
     * The block will be automatically cleaned up during teardown.
     *
     * @param dx
     *            relative X offset
     * @param dy
     *            relative Y offset
     * @param dz
     *            relative Z offset
     * @param blockId
     *            the block ID (e.g., "minecraft:stone")
     */
    public void setBlock(int dx, int dy, int dz, String blockId)
    {
        if(isClosed)
            throw new IllegalStateException("Test context is already closed");
        
        String coords = location.abs(dx, dy, dz);
        server.executeCommand(
            String.format("setblock %s %s replace", coords, blockId));
        placedBlocks.add(coords);
    }
    
    /**
     * Places a block at the given relative coordinates with block state.
     *
     * @param dx
     *            relative X offset
     * @param dy
     *            relative Y offset
     * @param dz
     *            relative Z offset
     * @param blockId
     *            the block ID with optional state (e.g.,
     *            "minecraft:carrots[age=7]")
     */
    public void setBlockWithState(int dx, int dy, int dz, String blockId)
    {
        setBlock(dx, dy, dz, blockId);
    }
    
    /**
     * Places blocks in a layer using a 2D array representation.
     * The array represents a top-down view where rows are Z coordinates and
     * columns are X coordinates. The player is always at the center of the
     * array.
     * <p>
     * Requirements:
     * - All rows and columns must have odd lengths
     * - The center cell (where player is) is usually "player" or null
     * - All blocks are placed relative to the center position
     * <p>
     * Example:
     *
     * <pre>{@code
     * setBlockLayer(-1, MiniTestContext.createCommonBlockDict(),
     *     new String[][]{{"stone", "stone", "stone"},
     *         {"stone", "stone", "stone"}, {"stone", "stone", "stone"},});
     * }</pre>
     *
     * @param y
     *            the Y level (relative to test location)
     * @param blockDict
     *            map of block aliases to block IDs (e.g., "stone" ->
     *            "minecraft:stone")
     * @param layer
     *            2D array where each cell is either null, "player", or a block
     *            alias
     *            from blockDict. Rows represent Z coordinates, columns
     *            represent X
     *            coordinates. Must have odd dimensions with player at center.
     */
    public void setBlockLayer(int y, Map<String, String> blockDict,
        String[][] layer)
    {
        if(isClosed)
            throw new IllegalStateException("Test context is already closed");
        
        if(layer.length == 0)
            throw new IllegalArgumentException("Layer must not be empty");
        
        // Validate all rows have odd length
        for(int z = 0; z < layer.length; z++)
        {
            if(layer[z] == null)
                throw new IllegalArgumentException("Layer rows cannot be null");
            if(layer[z].length % 2 == 0)
                throw new IllegalArgumentException(
                    "All rows must have odd length, but row " + z
                        + " has length " + layer[z].length);
        }
        
        if(layer.length % 2 == 0)
            throw new IllegalArgumentException(
                "Layer must have odd number of rows, but has " + layer.length);
        
        // Calculate center position
        int centerZ = layer.length / 2;
        int centerX = layer[centerZ].length / 2;
        
        // Place blocks relative to center position
        for(int z = 0; z < layer.length; z++)
        {
            if(layer[z].length != layer[centerZ].length)
                throw new IllegalArgumentException(
                    "All rows must have the same length");
            
            for(int x = 0; x < layer[z].length; x++)
            {
                String cell = layer[z][x];
                
                // Skip player marker and null cells
                if(cell == null || "player".equals(cell))
                    continue;
                
                // Look up block in dictionary
                String blockId = blockDict.get(cell);
                if(blockId == null)
                    throw new IllegalArgumentException(
                        "Unknown block alias: " + cell);
                
                // Calculate relative position from center
                int dx = x - centerX;
                int dz = z - centerZ;
                
                setBlock(dx, y, dz, blockId);
            }
        }
    }
    
    /**
     * Gets the test location for this context.
     *
     * @return the TestLocation instance
     */
    public MiniTestLocation getLocation()
    {
        return location;
    }
    
    /**
     * Gets the client game test context.
     *
     * @return the context
     */
    public ClientGameTestContext getContext()
    {
        return context;
    }
    
    /**
     * Gets the server facade.
     *
     * @return the server facade
     */
    public TestServerFacade getServer()
    {
        return server;
    }
    
    /**
     * Teleports the player to a specific position relative to the test
     * location.
     *
     * @param dx
     *            relative X offset
     * @param dy
     *            relative Y offset
     * @param dz
     *            relative Z offset
     * @param yaw
     *            player yaw rotation
     * @param pitch
     *            player pitch rotation
     */
    public void teleportPlayer(float dx, float dy, float dz, float yaw,
        float pitch)
    {
        String playerName =
            server.getPlayerName() != null ? server.getPlayerName() : "@p";
        server.executeCommand(location.tp(playerName, dx, dy, dz, yaw, pitch));
    }
    
}
