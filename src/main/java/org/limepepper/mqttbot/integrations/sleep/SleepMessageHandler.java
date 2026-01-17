package org.limepepper.mqttbot.integrations.sleep;

import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.util.MqttBotLogger;

public final class SleepMessageHandler extends Action
    implements MqttMessageListener {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(SleepMessageHandler.class);
    
    public static final SleepMessageHandler INSTANCE =
        new SleepMessageHandler();
    public static final Minecraft MC = Minecraft.getInstance();
    
    private SleepMessageHandler()
    {}
    
    /**
     * Initialize the sleep message handler
     */
    public static void init()
    {
        EventManager.INSTANCE.add(MqttMessageListener.class,
            SleepMessageHandler.INSTANCE);
        LOGGER.debug("SleepMessageHandler initialized");
    }
    
    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent)
    {
        MessageData data = mqttMessageEvent.messageData;
        // LOGGER.debug("recieved message in sleep handler");
        if(!mqttMessageEvent.messageData.getService().equals("sleep"))
            return;
        LOGGER.debug("message for sleep service");
        if(mqttMessageEvent.messageData.getMethod().equals("start"))
        {
            if(MC.player != null)
            {
                // Pass the full correlation information from the incoming
                // message
                String requestId = data.getRequestId();
                String correlationId = data.getCorrelationId();
                String identity = data.getIdentity();
                SleepUtil.start(requestId, correlationId, identity, 3);
            }
        }else
        {
            LOGGER.debug("unknown method in sleep handler");
        }
    }
    
}
