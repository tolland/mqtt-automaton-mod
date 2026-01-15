package org.limepepper.mqttbot.actions;

import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DamageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.UUID;

public class DamageAction extends Action implements DamageListener {
    
    @Override
    public void onDamage()
    {
        var mc = Minecraft.getInstance();
        String playerName =
            (mc.player != null) ? mc.getUser().getName() : "unknown";
        EventManager.fire(new MqttReplyListener.MqttReplyEvent(playerName,
            new MessageData("player", "onDamage", UUID.randomUUID().toString(),
                null, null, null, null)));
    }
}
