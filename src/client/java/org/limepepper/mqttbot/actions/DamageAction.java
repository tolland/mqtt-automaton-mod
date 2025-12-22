package org.limepepper.mqttbot.actions;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DamageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

public class DamageAction extends Action implements DamageListener {

    @Override
    public void onDamage() {
        EventManager.fire(new MqttReplyListener.MqttReplyEvent("botId todo", new MessageData(
                "player", "onDamage", "123", null, null, null, null)));
    }


}
