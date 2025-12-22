package org.limepepper.mqttbot.actions;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

public class ClientAction extends Action implements ClientListener {
    @Override
    public void onClientJoin() {
//        MqttHandler.INSTANCE.publish("baritone/event/bot1", "client join");

        EventManager.fire(new MqttReplyListener.MqttReplyEvent("botId todo", new MessageData(
                "player", "client join", "123", null, null, null, null)));

    }
}
