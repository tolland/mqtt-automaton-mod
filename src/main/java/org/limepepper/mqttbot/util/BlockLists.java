package org.limepepper.mqttbot.util;

import com.google.common.collect.ImmutableSet;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

import java.util.Set;

/**
 * Predefined lists of blocks for various purposes.
 * Used for efficient filtering during world scans and interactions.
 */
public enum BlockLists {
    ;

    public static String[] getInteractiveBlocks()
    {
        return new String[]{"minecraft:white_bed",

        };
    }

    public static String[] getAllInteractiveBlocks()
    {
        return new String[]{"minecraft:lectern",
            // "minecraft:smooth_stone",
            "minecraft:carved_pumpkin", "minecraft:white_bed",
            "minecraft:shulker_box",
            // "minecraft:chest",
            // "minecraft:crafting_table",
            // "minecraft:beacon",
            // "minecraft:ender_chest",
            // "minecraft:loom",
            "minecraft:stone_button[face=floor]",

            // Sound/interaction blocks
            "minecraft:note_block", "minecraft:bell", "minecraft:jukebox",

            // Redstone/display blocks
            "minecraft:comparator", "minecraft:repeater",
            "minecraft:tripwire_hook", "minecraft:observer",

            // Amethyst & crystal variants
            // these appear to be farmable
            // "minecraft:amethyst_cluster",
            // "minecraft:large_amethyst_bud",

            // Sculk variants
            "minecraft:sculk_sensor", "minecraft:calibrated_sculk_sensor",
            "minecraft:sculk_shrieker",

            // Cauldron (can be filled/emptied)
            "minecraft:cauldron",

            // Cartography table, smithing table (like lectern)
            "minecraft:cartography_table", "minecraft:smithing_table",

            // Barrel (interactive storage)
            "minecraft:barrel",

            // Decorated pot (can interact)
            "minecraft:decorated_pot",

            // Campfire (can cook, add logs)
            "minecraft:campfire",

            // Grindstone (interactive)
            "minecraft:grindstone",

            // Composters (can add items)
            "minecraft:composter"};
    }

    /**
     * All container blocks that can store items.
     * Used for chest sorting and inventory management.
     */
    public static final Set<Block> CONTAINER_BLOCKS = Set.of(
        Blocks.CHEST,
        Blocks.TRAPPED_CHEST,
        Blocks.ENDER_CHEST,
        Blocks.BARREL,
        Blocks.SHULKER_BOX,
        Blocks.WHITE_SHULKER_BOX,
        Blocks.ORANGE_SHULKER_BOX,
        Blocks.MAGENTA_SHULKER_BOX,
        Blocks.LIGHT_BLUE_SHULKER_BOX,
        Blocks.YELLOW_SHULKER_BOX,
        Blocks.LIME_SHULKER_BOX,
        Blocks.PINK_SHULKER_BOX,
        Blocks.GRAY_SHULKER_BOX,
        Blocks.LIGHT_GRAY_SHULKER_BOX,
        Blocks.CYAN_SHULKER_BOX,
        Blocks.PURPLE_SHULKER_BOX,
        Blocks.BLUE_SHULKER_BOX,
        Blocks.BROWN_SHULKER_BOX,
        Blocks.GREEN_SHULKER_BOX,
        Blocks.RED_SHULKER_BOX,
        Blocks.BLACK_SHULKER_BOX,
        Blocks.HOPPER,
        Blocks.DISPENSER,
        Blocks.DROPPER,
        Blocks.FURNACE,
        Blocks.BLAST_FURNACE,
        Blocks.SMOKER,
        Blocks.BREWING_STAND,
        Blocks.CRAFTING_TABLE,  // Has no inventory but worth tracking
        Blocks.CRAFTER  // 1.21+ block
    );

    /**
     * Sign blocks for reading labels.
     */
    public static final Set<Block> SIGN_BLOCKS = Set.of(
        Blocks.OAK_SIGN,
        Blocks.SPRUCE_SIGN,
        Blocks.BIRCH_SIGN,
        Blocks.JUNGLE_SIGN,
        Blocks.ACACIA_SIGN,
        Blocks.DARK_OAK_SIGN,
        Blocks.MANGROVE_SIGN,
        Blocks.CHERRY_SIGN,
        Blocks.BAMBOO_SIGN,
        Blocks.CRIMSON_SIGN,
        Blocks.WARPED_SIGN,
        Blocks.OAK_WALL_SIGN,
        Blocks.SPRUCE_WALL_SIGN,
        Blocks.BIRCH_WALL_SIGN,
        Blocks.JUNGLE_WALL_SIGN,
        Blocks.ACACIA_WALL_SIGN,
        Blocks.DARK_OAK_WALL_SIGN,
        Blocks.MANGROVE_WALL_SIGN,
        Blocks.CHERRY_WALL_SIGN,
        Blocks.BAMBOO_WALL_SIGN,
        Blocks.CRIMSON_WALL_SIGN,
        Blocks.WARPED_WALL_SIGN
    );

    /**
     * Crop blocks for farming automation.
     */
    public static final Set<Block> CROP_BLOCKS = Set.of(
        Blocks.WHEAT,
        Blocks.CARROTS,
        Blocks.POTATOES,
        Blocks.BEETROOTS,
        Blocks.NETHER_WART,
        Blocks.SUGAR_CANE,
        Blocks.BAMBOO,
        Blocks.CACTUS,
        Blocks.SWEET_BERRY_BUSH,
        Blocks.COCOA
    );
}
