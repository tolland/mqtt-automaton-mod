package org.limepepper.mqttbot.watchers;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.InventoryListener;

import java.util.HashMap;
import java.util.Map;

/**
 * Monitors player inventory for changes and fires events
 * Uses tick-based polling to detect inventory changes
 */
public final class InventoryWatcher {

    private static Map<String, Integer> previousItemCounts = new HashMap<>();
    private static boolean wasPreviouslyFull = false;
    private static boolean wasPreviouslyFullForPrimary = false;
    private static String previousPrimaryItem = null;
    private static int tickCounter = 0;
    private static final int CHECK_INTERVAL = 10; // Check every 10 ticks (0.5 seconds)

    public static void init() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            // Only check every N ticks to reduce overhead
            if (++tickCounter < CHECK_INTERVAL) {
                return;
            }
            tickCounter = 0;

            // Don't monitor when container/inventory screens are open to avoid conflicts
            if (client.currentScreen instanceof AbstractContainerScreen) {
                return;
            }

            // Need a valid player
            if (client.player == null || client.world == null) {
                return;
            }

            checkInventoryChanges(client);
        });
    }

    private static void checkInventoryChanges(Minecraft client) {
        Inventory inventory = client.player.getInventory();

        // Build current inventory snapshot
        Map<String, Integer> currentItemCounts = new HashMap<>();
        Map<String, Integer> maxStackableSpace = new HashMap<>(); // Tracks how much more of each item can fit
        int emptySlots = 0;
        int fullSlots = 0;

        // Check main inventory (0-35) and hotbar (already included in main)
        // Inventory.main contains all 36 slots (0-8 hotbar, 9-35 main inventory)
        for (int i = 0; i < inventory.getMainStacks().size(); i++) {
            ItemStack stack = inventory.getMainStacks().get(i);

            if (stack.isEmpty()) {
                emptySlots++;
            } else {
                fullSlots++;
                String itemId = Registries.ITEM.getId(stack.getItem()).toString();
                currentItemCounts.merge(itemId, stack.getCount(), Integer::sum);

                // Track stackable space: how much more of this item can fit in this slot
                int maxStackSize = stack.getMaxCount();
                int currentSize = stack.getCount();
                int spaceRemaining = maxStackSize - currentSize;
                maxStackableSpace.merge(itemId, spaceRemaining, Integer::sum);
            }
        }

        boolean isNowFull = (emptySlots == 0);

        // Determine the "primary item" (the one you have the most of)
        String primaryItem = null;
        int maxCount = 0;
        for (Map.Entry<String, Integer> entry : currentItemCounts.entrySet()) {
            if (entry.getValue() > maxCount) {
                maxCount = entry.getValue();
                primaryItem = entry.getKey();
            }
        }

        // Check if inventory is "full for primary item" (can't pick up more of it)
        boolean canPickupPrimaryItem = false;
        if (primaryItem != null) {
            // Can pick up if: (1) have empty slots OR (2) have non-full stacks of this item
            int spaceForPrimary = maxStackableSpace.getOrDefault(primaryItem, 0);
            canPickupPrimaryItem = (emptySlots > 0 || spaceForPrimary > 0);
        }

        boolean isFullForPrimaryItem = (primaryItem != null && !canPickupPrimaryItem);

        // Detect changes by comparing with previous state
        boolean hasChanges = false;

        // Check if item counts changed
        if (!currentItemCounts.equals(previousItemCounts)) {
            hasChanges = true;

            // Fire general inventory change event
            EventManager.fire(new InventoryListener.InventoryChangeEvent(
                new HashMap<>(currentItemCounts),
                emptySlots,
                fullSlots
            ));

            // Fire specific item count change events
            fireItemCountChangeEvents(previousItemCounts, currentItemCounts);
        }

        // Check if inventory became full (no empty slots)
        if (isNowFull && !wasPreviouslyFull) {
            System.out.println("[InventoryWatcher] Inventory is now full (no empty slots)!");
            EventManager.fire(new InventoryListener.InventoryFullEvent(
                new HashMap<>(currentItemCounts)
            ));
        }

        // Check if inventory became "full for primary item" (can't pick up more of it)
        if (isFullForPrimaryItem && !wasPreviouslyFullForPrimary) {
            System.out.println("[InventoryWatcher] Inventory is full for primary item: " + primaryItem
                + " (count: " + currentItemCounts.get(primaryItem) + ")");
            EventManager.fire(new InventoryListener.InventoryFullEvent(
                new HashMap<>(currentItemCounts)
            ));
        }

        // Update previous state
        previousItemCounts = currentItemCounts;
        wasPreviouslyFull = isNowFull;
        wasPreviouslyFullForPrimary = isFullForPrimaryItem;
        previousPrimaryItem = primaryItem;
    }

    /**
     * Fire events for each item that had a count change
     */
    private static void fireItemCountChangeEvents(
            Map<String, Integer> previous,
            Map<String, Integer> current) {

        // Check all items in current inventory
        for (Map.Entry<String, Integer> entry : current.entrySet()) {
            String itemId = entry.getKey();
            int newCount = entry.getValue();
            int oldCount = previous.getOrDefault(itemId, 0);

            if (newCount != oldCount) {
                EventManager.fire(new InventoryListener.ItemCountChangeEvent(
                    itemId,
                    oldCount,
                    newCount,
                    newCount
                ));
            }
        }

        // Check items that were removed completely
        for (Map.Entry<String, Integer> entry : previous.entrySet()) {
            String itemId = entry.getKey();
            if (!current.containsKey(itemId)) {
                int oldCount = entry.getValue();
                EventManager.fire(new InventoryListener.ItemCountChangeEvent(
                    itemId,
                    oldCount,
                    0,
                    0
                ));
            }
        }
    }

    /**
     * Get current inventory item counts (for external queries)
     */
    public static Map<String, Integer> getCurrentItemCounts() {
        return new HashMap<>(previousItemCounts);
    }

    /**
     * Check if inventory is currently full
     */
    public static boolean isInventoryFull() {
        return wasPreviouslyFull;
    }

    private InventoryWatcher() {}
}
