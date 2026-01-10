package org.limepepper.mqttbot;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientSendMessageEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.integrations.baritone.BaritoneCmds;
import org.limepepper.mqttbot.integrations.baritone.BaritonePathing;
import org.limepepper.mqttbot.integrations.command.SendCommandHandler;
import org.limepepper.mqttbot.integrations.inventory.InventoryQueryHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepMessageHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepUtil;
import org.limepepper.mqttbot.integrations.warp.WarpMessageHandler;
import org.limepepper.mqttbot.integrations.wurst.WurstHandler;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.limepepper.mqttbot.watchers.ClientNightWatcher;
import org.limepepper.mqttbot.watchers.InventoryWatcher;

public class MqttBotClientModInitializer implements ClientModInitializer {
    private static final MqttBotLogger LOGGER = new MqttBotLogger(MqttBotClientModInitializer.class);
    private static boolean initialized;

    @Override
    public void onInitializeClient() {

        if (initialized)
            throw new RuntimeException(
                    "MqttBotInitializer.onInitialize() ran twice!");

        MqttCore.INSTANCE.initialize();

        ClientNightWatcher.init();
        InventoryWatcher.init();

        ClientPlayConnectionEvents.JOIN.register((
                handler,
                sender,
                client) -> {
            EventManager.fire(ClientListener.ClientJoinEvent.INSTANCE);
        });

        SleepUtil.init();
        SleepMessageHandler.init();

        WarpMessageHandler.init();
        SendCommandHandler.init();
        InventoryQueryHandler.init();
        initialized = true;

        if (net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("baritone")) {
            LOGGER.info("Baritone mod detected, initializing Baritone integration");
            BaritonePathing.init();
            BaritoneCmds.init();
        } else {
            LOGGER.info("Baritone mod not loaded, skipping Baritone integration");
        }

        if (net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("wurst")) {
            LOGGER.info("Wurst mod detected, initializing Wurst integration");
            WurstHandler.init();
        } else {
            LOGGER.info("Wurst mod not loaded, skipping Wurst integration");
        }

        ClientSendMessageEvents.CHAT.register((message -> LOGGER.info("Sent chat message: " + message)));

        ClientReceiveMessageEvents.CHAT.register((
                message,
                signedMessage,
                sender,
                params,
                receptionTimestamp
        ) -> LOGGER.info("Received chat message sent by {} at time {}: {}", sender == null ? "null" : sender.getName(), receptionTimestamp.toEpochMilli(), message.getString()));


        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            dispatcher.register(Commands.literal("test_command").executes(context -> {
                context.getSource().sendSuccess(() -> Component.literal("Called /test_command."), false);
                return 1;
            }));
            dispatcher.register(Commands.literal("test_reply").executes(context -> {
                LOGGER.debug("test_reply command executed");
                LOGGER.debug("Firing MqttReplyEvent for testing");
                EventManager.fire(new MqttReplyListener.MqttReplyEvent("botId", new MessageData(
                                "baritone",
                                "pathing",
                                "123",
                                null,
                                null,
                                null,
                                "Test reply from /test_reply")
                        )
                );
                LOGGER.debug("MqttReplyEvent fired successfully");
                return 1;
            }));
            dispatcher.register(Commands.literal("test_sleep").executes(context -> {
                LOGGER.debug("test_sleep command executed");
                SleepUtil.start("bot id", 3);
                LOGGER.debug("Sleep utility started");
                return 1;
            }));
        });

    }
}
