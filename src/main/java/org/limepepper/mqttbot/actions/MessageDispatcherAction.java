package org.limepepper.mqttbot.actions;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class MessageDispatcherAction extends Action
    implements MqttMessageListener {
    
    private final List<MessageHandler> handlers;
    
    public MessageDispatcherAction(MessageHandler... handlersList)
    {
        handlers = new ArrayList<>();
        this.handlers.addAll(Arrays.asList(handlersList));
    }
    
    @Override
    public void onMessageArrived(MqttMessageEvent event)
    {
        if(!CORE.isEnabled())
            return;
        MessageData data = event.messageData;
        
        for(MessageHandler handler : getHandlers())
        {
            if(handler.canHandle(data))
            {
                try
                {
                    handler.handle(data);
                }catch(Exception ex)
                {
                    System.out.printf("Failed to handle message %s %s%n", data,
                        ex);
                }
            }
        }
    }
    
    public List<MessageHandler> getHandlers()
    {
        return handlers;
    }
    
    public void addHandler(MessageHandler handler)
    {
        handlers.add(handler);
    }
}
