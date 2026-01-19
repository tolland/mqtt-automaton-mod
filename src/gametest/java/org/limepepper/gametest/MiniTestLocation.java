
package org.limepepper.gametest;

/**
 * The purpose of this class is to provide isolated test locations
 * for game tests, so that each test can run in its own area without
 * interfering with other tests.
 */
public class MiniTestLocation {
    public final int baseX;
    public final int baseY;
    public final int baseZ;
    
    public MiniTestLocation(int index)
    {
        // locate in middle of chunk
        this.baseX = 8 + (index * 16);
        // avoid any generated stuff
        this.baseY = 74;
        this.baseZ = 8;
    }
    
    public String abs(int dx, int dy, int dz)
    {
        return String.format("%d %d %d", baseX + dx, baseY + dy, baseZ + dz);
    }
    
    public String relCmd(int dx, int dy, int dz)
    {
        return String.format("~%s ~%s ~%s", fmt(dx), fmt(dy), fmt(dz));
    }
    
    /**
     * Generates a teleport command with explicit player name.
     *
     * @param playerName
     *            The player name to teleport
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
     * @return The teleport command
     */
    public String tp(String playerName, float dx, float dy, float dz, float yaw,
        float pitch)
    {
        return String.format("minecraft:tp %s %.2f %.2f %.2f %.1f %.1f",
            playerName,
            baseX + dx, baseY + dy, baseZ + dz, yaw, pitch);
    }
    
    /**
     * Generates a teleport command using @p selector (for integrated servers).
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
     * @return The teleport command
     */
    public String tp(float dx, float dy, float dz, float yaw, float pitch)
    {
        return tp("@p", dx, dy, dz, yaw, pitch);
    }
    
    private static String fmt(int offset)
    {
        return offset == 0 ? "~" : "~" + offset;
    }
}
