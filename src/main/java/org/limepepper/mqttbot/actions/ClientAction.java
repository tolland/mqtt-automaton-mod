package org.limepepper.mqttbot.actions;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientDisconnectListener;
import org.limepepper.mqttbot.events.ClientJoinListener;
import org.limepepper.mqttbot.events.ClientWorldChangeListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;

import java.util.UUID;

/**
 * Game, Player and mc client related event actions.
 */
public class ClientAction extends Action
    implements ClientJoinListener, ClientDisconnectListener,
    ClientWorldChangeListener {
    @Override
    public void onClientJoin(ClientJoinEvent event)
    {
        // MqttHandler.INSTANCE.publish("baritone/event/bot1", "client join");
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(
            event.getPlayerName(),
            new ServiceMessage("events",
                "player_join",
                UUID.randomUUID().toString(),
                null,
                null,
                null,
                event.getPlayerName(),
                "player joined " + event.getWorld()),
            "events"));
        
    }
    
    @Override
    public void onClientDisconnect(ClientDisconnectEvent event)
    {
        EventManager
            .fire(new MqttReplyListener.MqttReplyEvent(event.getPlayerName(),
                new ServiceMessage("events", "player_disconnect",
                    UUID.randomUUID().toString(), null, null, null,
                    event.getPlayerName(), "player disconnected"),
                "events"));
    }
    
    @Override
    public void onClientWorldChange(ClientWorldChangeEvent event)
    {
        
    }
}
