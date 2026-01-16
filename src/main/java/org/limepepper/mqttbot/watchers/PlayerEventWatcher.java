package org.limepepper.mqttbot.watchers;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.util.MqttBotLogger;

public class PlayerEventWatcher {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(PlayerEventWatcher.class);
    
    public static void init()
    {
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            EventManager.fire(ClientListener.ClientJoinEvent.INSTANCE);
        });
        
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            EventManager.fire(ClientListener.ClientDisconnectEvent.INSTANCE);
        });
        
        // ClientSendMessageEvents.CHAT.register(
        // (message -> LOGGER.info("Sent chat message: " + message)));
        //
        // ClientReceiveMessageEvents.CHAT.register(
        // (message,
        // signedMessage,
        // sender,
        // params,
        // receptionTimestamp) -> LOGGER.info(
        // "Received chat message sent by {} at time {}: {}",
        // sender == null ? "null" : sender.getName(),
        // receptionTimestamp.toEpochMilli(), message.getString()));
    }
}
