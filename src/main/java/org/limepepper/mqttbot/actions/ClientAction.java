package org.limepepper.mqttbot.actions;

import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.UUID;

public class ClientAction extends Action implements ClientListener {
    @Override
    public void onClientJoin()
    {
        // MqttHandler.INSTANCE.publish("baritone/event/bot1", "client join");
        var mc = Minecraft.getInstance();
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(
            CORE.getPlayerName(), new MessageData("player", "join",
                UUID.randomUUID().toString(), null, null, null, null)));
        
    }
    
    @Override
    public void onClientDisconnect()
    {
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(
            CORE.getPlayerName(), new MessageData("player", "disconnect",
                UUID.randomUUID().toString(), null, null, null, null)));
        
    }
}
