package org.limepepper.mqttbot.integrations.sleep;


import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import net.minecraft.client.MinecraftClient;

public final class SleepMessageHandler extends Action implements MqttMessageListener {

    public static final SleepMessageHandler INSTANCE = new SleepMessageHandler();
    public static final MinecraftClient MC = MinecraftClient.getInstance();

    private SleepMessageHandler() {
    }

    /**
     * Initialize the sleep message handler
     */
    public static void init() {
        EventManager.INSTANCE.add(MqttMessageListener.class, SleepMessageHandler.INSTANCE);
        System.out.println("SleepMessageHandler initialized");
    }


    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent) {
        MessageData data = mqttMessageEvent.messageData;
        System.out.println("recieved message in sleep handler");
        if (!mqttMessageEvent.messageData.getService().equals("sleep")) return;
        System.out.println("message for sleep service");
        switch (mqttMessageEvent.messageData.getMethod()) {
            case "start":
                if (MC.player != null) {
                    // Pass the request ID from the incoming message
                    String requestId = data.getRequestId();
                    SleepUtil.start(requestId, 3);
                }
                break;
            default:
                System.out.println("unknownn method in baritone");
        }
    }

}
