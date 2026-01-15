package org.limepepper.mqttbot;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientSendMessageEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientListener;
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

public class MqttBotClientModInitializer implements ClientModInitializer {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(MqttBotClientModInitializer.class);
    private static boolean initialized;
    
    @Override
    public void onInitializeClient()
    {
        
        MqttCore.INSTANCE.initialize();
        
        ClientNightWatcher.init();
        InventoryWatcher.init();
        
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            EventManager.fire(ClientListener.ClientJoinEvent.INSTANCE);
        });
        
        SleepUtil.init();
        SleepMessageHandler.init();
        
        WarpMessageHandler.init();
        SendCommandHandler.init();
        InventoryQueryHandler.init();
        initialized = true;
        
        if(net.fabricmc.loader.api.FabricLoader.getInstance()
            .isModLoaded("baritone"))
        {
            LOGGER.info(
                "Baritone mod detected, initializing Baritone integration");
            BaritonePathing.init();
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
        
        ClientSendMessageEvents.CHAT.register(
            (message -> LOGGER.info("Sent chat message: " + message)));
        
        ClientReceiveMessageEvents.CHAT.register((message, signedMessage,
            sender, params, receptionTimestamp) -> LOGGER.info(
                "Received chat message sent by {} at time {}: {}",
                sender == null ? "null" : sender.getName(),
                receptionTimestamp.toEpochMilli(), message.getString()));
        
    }
}
