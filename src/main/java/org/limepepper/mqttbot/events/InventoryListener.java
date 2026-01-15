package org.limepepper.mqttbot.events;

import org.limepepper.mqttbot.event.Event;
import org.limepepper.mqttbot.event.Listener;

import java.util.ArrayList;
import java.util.Map;

public interface InventoryListener extends Listener {
    
    /**
     * Called when any inventory change is detected
     */
    void onInventoryChange(Map<String, Integer> itemCounts, int emptySlots,
        int fullSlots);
    
    /**
     * Called when inventory becomes full (no empty slots)
     */
    void onInventoryFull(Map<String, Integer> itemCounts);
    
    /**
     * Called when a specific item's count changes significantly
     */
    void onItemCountChange(String itemId, int oldCount, int newCount,
        int totalCount);
    
    /**
     * Event fired when any inventory change is detected
     */
    class InventoryChangeEvent extends Event<InventoryListener> {
        private final Map<String, Integer> itemCounts;
        private final int emptySlots;
        private final int fullSlots;
        
        public InventoryChangeEvent(Map<String, Integer> itemCounts,
            int emptySlots, int fullSlots)
        {
            this.itemCounts = itemCounts;
            this.emptySlots = emptySlots;
            this.fullSlots = fullSlots;
        }
        
        @Override
        public void fire(ArrayList<InventoryListener> listeners)
        {
            for(InventoryListener listener : listeners)
            {
                listener.onInventoryChange(itemCounts, emptySlots, fullSlots);
            }
        }
        
        @Override
        public Class<InventoryListener> getListenerType()
        {
            return InventoryListener.class;
        }
    }
    
    /**
     * Event fired when inventory is completely full
     */
    class InventoryFullEvent extends Event<InventoryListener> {
        private final Map<String, Integer> itemCounts;
        
        public InventoryFullEvent(Map<String, Integer> itemCounts)
        {
            this.itemCounts = itemCounts;
        }
        
        @Override
        public void fire(ArrayList<InventoryListener> listeners)
        {
            for(InventoryListener listener : listeners)
            {
                listener.onInventoryFull(itemCounts);
            }
        }
        
        @Override
        public Class<InventoryListener> getListenerType()
        {
            return InventoryListener.class;
        }
    }
    
    /**
     * Event fired when a specific item's count changes
     */
    class ItemCountChangeEvent extends Event<InventoryListener> {
        private final String itemId;
        private final int oldCount;
        private final int newCount;
        private final int totalCount;
        
        public ItemCountChangeEvent(String itemId, int oldCount, int newCount,
            int totalCount)
        {
            this.itemId = itemId;
            this.oldCount = oldCount;
            this.newCount = newCount;
            this.totalCount = totalCount;
        }
        
        @Override
        public void fire(ArrayList<InventoryListener> listeners)
        {
            for(InventoryListener listener : listeners)
            {
                listener.onItemCountChange(itemId, oldCount, newCount,
                    totalCount);
            }
        }
        
        @Override
        public Class<InventoryListener> getListenerType()
        {
            return InventoryListener.class;
        }
    }
}
