package org.limepepper.mqttbot;

import net.fabricmc.api.ClientModInitializer;
import org.limepepper.mqttbot.integrations.command.SendCommandHandler;
import org.limepepper.mqttbot.integrations.inventory.InventoryQueryHandler;
import org.limepepper.mqttbot.integrations.scan.ScanHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepMessageHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepUtil;
import org.limepepper.mqttbot.integrations.warp.WarpMessageHandler;
import org.limepepper.mqttbot.integrations.wurst.WurstHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.limepepper.mqttbot.watchers.ClientNightWatcher;
import org.limepepper.mqttbot.watchers.InventoryWatcher;
import org.limepepper.mqttbot.watchers.GameEventWatcher;

public class MqttBotClientModInitializer implements ClientModInitializer {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(MqttBotClientModInitializer.class);
    
    @Override
    public void onInitializeClient()
    {
        
        MqttCore.INSTANCE.initialize();
        
        ClientNightWatcher.init();
        InventoryWatcher.init();
        GameEventWatcher.init();
        
        SleepUtil.init();
        SleepMessageHandler.init();
        
        WarpMessageHandler.init();
        SendCommandHandler.init();
        InventoryQueryHandler.init();
        ScanHandler.init();
        
        if(net.fabricmc.loader.api.FabricLoader.getInstance()
            .isModLoaded("baritone"))
        {
            try
            {
                Class<?> baritoneApi = Class.forName("baritone.api.IBaritone");
                baritoneApi.getMethod("getCollectProcess");
                
            }catch(Throwable t)
            {
                LOGGER.info("Failed to initialize Baritone integration: "
                    + t.getMessage());
            }
        }else
        {
            LOGGER
                .info("Baritone mod not loaded, skipping Baritone integration");
        }
        
        if(net.fabricmc.loader.api.FabricLoader.getInstance()
            .isModLoaded("wurst"))
        {
            LOGGER.info("Wurst mod detected, initializing Wurst integration");
            WurstHandler.init();
        }else
        {
            LOGGER.info("Wurst mod not loaded, skipping Wurst integration");
        }
        
    }
}
