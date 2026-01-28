package org.limepepper.mqttbot.util;

import com.google.common.collect.ImmutableSet;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

public enum BlockLists
{
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
    
    public static final ImmutableSet<Block> CONTAINER_BLOCKS = ImmutableSet.of(
        Blocks.CHEST,
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
        Blocks.BARREL
    
    );
    
}
