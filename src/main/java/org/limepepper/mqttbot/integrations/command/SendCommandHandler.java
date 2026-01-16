package org.limepepper.mqttbot.integrations.command;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
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
            {
                JsonElement paramsEl = data.getParams();
                String cmd = null;
                if(paramsEl != null && paramsEl.isJsonObject())
                {
                    JsonObject params = paramsEl.getAsJsonObject();
                    if(params.has("message"))
                        cmd = params.get("message").getAsString();
                }
                System.out.println("cmd is " + cmd);
                if(cmd != null && MC.player != null)
                {
                    MC.getConnection().sendChat(cmd);
                }
            }
            break;
            case "chatCommand":
            {
                JsonElement paramsEl = data.getParams();
                String chatCommand = null;
                if(paramsEl != null && paramsEl.isJsonObject())
                {
                    JsonObject params = paramsEl.getAsJsonObject();
                    if(params.has("message"))
                        chatCommand = params.get("message").getAsString();
                }
                System.out.println("cmd is " + chatCommand);
                if(chatCommand != null && MC.player != null)
                {
                    MC.getConnection().sendCommand(chatCommand);
                }
            }
            break;
            case "sendCommand":
            {
                JsonElement paramsEl = data.getParams();
                String sendCommand = null;
                if(paramsEl != null && paramsEl.isJsonObject())
                {
                    JsonObject params = paramsEl.getAsJsonObject();
                    if(params.has("message"))
                        sendCommand = params.get("message").getAsString();
                }
                System.out.println("cmd is " + sendCommand);
                if(sendCommand != null && MC.player != null)
                {
                    MC.getConnection().sendCommand(sendCommand);
                    
                    String botId = MC.getUser().getName();
                    
                    JsonObject successParams = new JsonObject();
                    successParams.addProperty("status", "success");
                    successParams.addProperty("message", "message sent");
                    
                    MessageData replyData = new MessageData("wurst",
                        mqttMessageEvent.messageData.getMethod(),
                        mqttMessageEvent.messageData.getRequestId(),
                        mqttMessageEvent.messageData.getCorrelationId(), null,
                        successParams, "minecraft_client",
                        "mqttbot_client_" + botId);
                    EventManager.fire(
                        new MqttReplyListener.MqttReplyEvent(botId, replyData));
                }
            }
            break;
            default:
            System.out.println("unknownn method in commands handler");
        }
    }
    
}
