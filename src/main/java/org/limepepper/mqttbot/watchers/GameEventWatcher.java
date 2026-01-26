package org.limepepper.mqttbot.watchers;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientWorldEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientSendMessageEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ChatMessageListener;
import org.limepepper.mqttbot.events.ClientDisconnectListener;
import org.limepepper.mqttbot.events.ClientJoinListener;
import org.limepepper.mqttbot.events.HeartbeatListener;
import org.limepepper.mqttbot.util.MqttBotLogger;

public class GameEventWatcher {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(GameEventWatcher.class);
    
    private static final int CHECK_INTERVAL = 100;
    private static int tickCounter = 0;
    
    public static void init()
    {
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            String playerName = client.getUser().getName();
            String world = client.level != null
                ? client.level.dimension().location().toString() : "unknown";
            EventManager
                .fire(
                    new ClientJoinListener.ClientJoinEvent(playerName, world));
        });
        
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            String playerName = client.getUser().getName();
            EventManager
                .fire(new ClientDisconnectListener.ClientDisconnectEvent(
                    playerName));
        });
        
        ClientSendMessageEvents.CHAT.register((message -> EventManager
            .fire(new ChatMessageListener.ChatMessageEvent(message))));
        
        ClientReceiveMessageEvents.CHAT.register((message, signedMessage,
            sender, params, receptionTimestamp) -> LOGGER.info(
                "Received chat message sent by {} at time {}: {}",
                sender == null ? "null" : sender.getName(),
                receptionTimestamp.toEpochMilli(), message.getString()));
        
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            
            if(client.level == null)
                return;
            
            if(++tickCounter < CHECK_INTERVAL)
            {
                return;
            }
            tickCounter = 0;
            
            EventManager.fire(HeartbeatListener.HeaertbeatEvent.INSTANCE);
        });
        
        ClientWorldEvents.AFTER_CLIENT_WORLD_CHANGE
            .register((client, world) -> {
                LOGGER.info("World loaded: {}", world.dimension().location());
            });
    }
}
