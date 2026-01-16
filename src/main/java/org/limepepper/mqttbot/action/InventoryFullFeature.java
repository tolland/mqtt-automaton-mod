package org.limepepper.mqttbot.action;

import org.limepepper.mqttbot.watchers.InventoryWatcher;

public final class InventoryFullFeature extends Feature {
    
    @Override
    protected void onEnable()
    {
        InventoryWatcher.enable();
    }
    
    @Override
    protected void onDisable()
    {
        InventoryWatcher.disable();
    }
}
