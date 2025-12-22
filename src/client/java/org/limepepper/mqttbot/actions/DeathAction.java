package org.limepepper.mqttbot.actions;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DeathListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

public final class DeathAction extends Action implements DeathListener {

    @Override
    public void onEnable() {
        EVENTS.add(DeathListener.class, this);
    }

    @Override
    public void onDisable() {
        EVENTS.remove(DeathListener.class, this);
    }

    @Override
    public void onDeath() {
//        MqttHandler.INSTANCE.publish("baritone/event/bot1", "onDeath");
        EventManager.fire(new MqttReplyListener.MqttReplyEvent("botId todo", new MessageData(
                "player", "onDeath", "123", null, null, null, null)));
    }
}
