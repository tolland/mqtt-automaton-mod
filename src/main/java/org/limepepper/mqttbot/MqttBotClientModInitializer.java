package org.limepepper.mqttbot;

import net.fabricmc.api.ClientModInitializer;
import org.limepepper.mqttbot.integrations.baritone.BaritonePathing;
import org.limepepper.mqttbot.integrations.command.SendCommandHandler;
import org.limepepper.mqttbot.integrations.inventory.InventoryQueryHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepMessageHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepUtil;
import org.limepepper.mqttbot.integrations.warp.WarpMessageHandler;
import org.limepepper.mqttbot.integrations.wurst.WurstHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.limepepper.mqttbot.watchers.ClientNightWatcher;
import org.limepepper.mqttbot.watchers.InventoryWatcher;
import org.limepepper.mqttbot.watchers.PlayerEventWatcher;

public class MqttBotClientModInitializer implements ClientModInitializer {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(MqttBotClientModInitializer.class);
    
    @Override
    public void onInitializeClient()
    {
        
        MqttCore.INSTANCE.initialize();
        
        ClientNightWatcher.init();
        InventoryWatcher.init();
        PlayerEventWatcher.init();
        
        SleepUtil.init();
        SleepMessageHandler.init();
        
        WarpMessageHandler.init();
        SendCommandHandler.init();
        InventoryQueryHandler.init();
        
        if(net.fabricmc.loader.api.FabricLoader.getInstance()
            .isModLoaded("baritone"))
        {
            try
            {
                Class<?> baritoneApi = Class.forName("baritone.api.IBaritone");
                try
                {
                    baritoneApi.getMethod("getCollectProcess");
                    LOGGER.info(
                        "Baritone mod detected and compatible API present, initializing Baritone integration");
                    BaritonePathing.init();
                }catch(NoSuchMethodException nsme)
                {
                    LOGGER.info(
                        "Baritone mod detected but required method getCollectProcess() not found; skipping Baritone integration");
                }
            }catch(ClassNotFoundException cnfe)
            {
                LOGGER.info(
                    "Baritone mod loaded but API classes not found; skipping Baritone integration");
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
