package org.limepepper.mqttbot.watchers;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.entity.player.PlayerInventory;
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
            if (client.currentScreen instanceof HandledScreen) {
                return;
            }

            // Need a valid player
            if (client.player == null || client.world == null) {
                return;
            }

            checkInventoryChanges(client);
        });
    }

    private static void checkInventoryChanges(MinecraftClient client) {
        PlayerInventory inventory = client.player.getInventory();

        // Build current inventory snapshot
        Map<String, Integer> currentItemCounts = new HashMap<>();
        int emptySlots = 0;
        int fullSlots = 0;

        // Check main inventory (0-35) and hotbar (already included in main)
        // PlayerInventory.main contains all 36 slots (0-8 hotbar, 9-35 main inventory)
        for (int i = 0; i < inventory.main.size(); i++) {
            ItemStack stack = inventory.main.get(i);

            if (stack.isEmpty()) {
                emptySlots++;
            } else {
                fullSlots++;
                String itemId = Registries.ITEM.getId(stack.getItem()).toString();
                currentItemCounts.merge(itemId, stack.getCount(), Integer::sum);
            }
        }

        boolean isNowFull = (emptySlots == 0);

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

        // Check if inventory became full
        if (isNowFull && !wasPreviouslyFull) {
            System.out.println("[InventoryWatcher] Inventory is now full!");
            EventManager.fire(new InventoryListener.InventoryFullEvent(
                new HashMap<>(currentItemCounts)
            ));
        }

        // Update previous state
        previousItemCounts = currentItemCounts;
        wasPreviouslyFull = isNowFull;
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
