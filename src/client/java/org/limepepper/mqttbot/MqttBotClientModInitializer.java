package org.limepepper.mqttbot;

import org.limepepper.mqttbot.util.MqttBotLogger;
import org.limepepper.mqttbot.integrations.command.SendCommandHandler;
import org.limepepper.mqttbot.integrations.sleep.SleepUtil;
import org.limepepper.mqttbot.integrations.sleep.SleepMessageHandler;
import org.limepepper.mqttbot.integrations.warp.WarpMessageHandler;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.integrations.baritone.BaritoneCmds;
import org.limepepper.mqttbot.integrations.baritone.BaritonePathing;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import org.limepepper.mqttbot.integrations.wurst.WurstHandler;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.watchers.ClientNightWatcher;
import net.minecraft.server.command.CommandManager;
import net.minecraft.text.Text;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;

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
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            EventManager.fire(ClientListener.ClientJoinEvent.INSTANCE);
        });
        SleepUtil.init();
        SleepMessageHandler.init();
        WarpMessageHandler.init();
        SendCommandHandler.init();
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

        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            dispatcher.register(CommandManager.literal("test_command").executes(context -> {
                context.getSource().sendFeedback(() -> Text.literal("Called /test_command."), false);
                return 1;
            }));
            dispatcher.register(CommandManager.literal("test_reply").executes(context -> {
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
            dispatcher.register(CommandManager.literal("test_sleep").executes(context -> {
                LOGGER.debug("test_sleep command executed");
                SleepUtil.start("bot id", 3);
                LOGGER.debug("Sleep utility started");
                return 1;
            }));
        });

    }
}
