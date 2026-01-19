package org.limepepper.mqttbot.actions;

import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.HeartbeatListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;

import java.util.UUID;

/**
 * Game, Player and mc client related event actions.
 */
public class HeartbeatAction extends Action implements HeartbeatListener {
    @Override
    public void onHeartbeat()
    {
        var mc = Minecraft.getInstance();
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(
            CORE.getPlayerName(),
            new ServiceMessage("events",
                "heartbeat",
                UUID.randomUUID().toString(),
                null,
                null,
                null,
                null),
            "events"));
        
    }
}
