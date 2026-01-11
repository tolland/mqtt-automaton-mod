package org.limepepper.mqttbot.integrations.command;

import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;

/**
 * handlers a request over mqtt for the client to send a command to the server
 * e.g. "/help"
 */
public final class SendCommandHandler extends Action
    implements MqttMessageListener {
    
    public static final Minecraft MC = Minecraft.getInstance();
    
    public static void init()
    {
        EventManager.INSTANCE.add(MqttMessageListener.class,
            new SendCommandHandler());
    }
    
    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent)
    {
        MessageData data = mqttMessageEvent.messageData;
        System.out.println("received message in commands handler");
        if(!mqttMessageEvent.messageData.getService().equals("commands"))
            return;
        System.out.println("message for commands service");
        switch(mqttMessageEvent.messageData.getMethod())
        {
            case "chatMessage":
            String cmd = data.getParams().get("message").getAsString();
            System.out.println("cmd is " + cmd);
            if(MC.player != null)
            {
                
                MC.getConnection().sendChat(cmd);
            }
            
            break;
            case "chatCommand":
            String chatCommand = data.getParams().get("message").getAsString();
            System.out.println("cmd is " + chatCommand);
            if(MC.player != null)
            {
                
                MC.getConnection().sendCommand(chatCommand);
            }
            
            break;
            case "sendCommand":
            String sendCommand = data.getParams().get("message").getAsString();
            System.out.println("cmd is " + sendCommand);
            if(MC.player != null)
            {
                
                MC.getConnection().sendCommand(sendCommand);
            }
            
            break;
            default:
            System.out.println("unknownn method in commands handler");
        }
    }
    
}
