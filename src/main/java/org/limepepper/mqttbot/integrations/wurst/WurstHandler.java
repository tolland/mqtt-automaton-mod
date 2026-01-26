package org.limepepper.mqttbot.integrations.wurst;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class WurstHandler extends Action implements MqttMessageListener {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(WurstHandler.class);
    public static final Minecraft MC = Minecraft.getInstance();
    
    public static void init()
    {
        EventManager.INSTANCE.add(MqttMessageListener.class,
            new WurstHandler());
    }
    
    @Override
    public void onMessageArrived(
        MqttMessageListener.MqttMessageEvent mqttMessageEvent)
    {
        ServiceMessage data = mqttMessageEvent.serviceMessage;
        LOGGER.debug("received message in wurst handler");
        
        if(!data.getService().equals("wurst"))
        {
            return;
        }
        
        LOGGER.debug("message for wurst service");
        
        // Check if player is online
        if(MC.player == null)
        {
            sendErrorReply(data, "Player is not online", "PLAYER_OFFLINE");
            return;
        }
        
        switch(data.getMethod())
        {
            case "command":
            handleArbitraryCommand(data);
            break;
            default:
            sendErrorReply(data, "Unknown method: " + data.getMethod(),
                "UNKNOWN_METHOD");
        }
    }
    
    /**
     * Handle arbitrary Wurst commands with flexible parameter parsing
     */
    private void handleArbitraryCommand(ServiceMessage data)
    {
        try
        {
            JsonElement paramsEl = data.getParams();
            if(paramsEl == null || paramsEl.isJsonNull()
                || !paramsEl.isJsonObject())
            {
                sendErrorReply(data, "No parameters provided for command",
                    "MISSING_PARAMETERS");
                return;
            }
            JsonObject params = paramsEl.getAsJsonObject();
            
            // Get the command name
            String commandName = null;
            if(params.has("command"))
            {
                commandName = params.get("command").getAsString();
            }else
            {
                sendErrorReply(data, "No 'command' parameter specified",
                    "MISSING_COMMAND");
                return;
            }
            
            // Get command arguments
            List<String> args = new ArrayList<>();
            if(params.has("args"))
            {
                JsonElement argsEl = params.get("args");
                if(argsEl.isJsonArray())
                {
                    // Handle array of arguments
                    JsonArray arr = argsEl.getAsJsonArray();
                    arr.forEach(element -> args.add(element.getAsString()));
                }else
                {
                    // Handle single string argument (split by spaces)
                    String argsString = argsEl.getAsString();
                    if(!argsString.trim().isEmpty())
                    {
                        args.addAll(Arrays.asList(argsString.split("\\s+")));
                    }
                }
            }
            
            WurstService.INSTANCE.executeCommand(commandName, args);
            
            // Send success reply
            sendSuccessReplyStatic(data,
                "Command queued successfully: " + commandName + " "
                    + String.join(" ", args));
            
        }catch(Exception e)
        {
            sendErrorReply(data,
                "Error parsing command parameters: " + e.getMessage(),
                "PARSE_ERROR");
        }
    }
    
    /**
     * Send an error reply message to the client (instance method)
     */
    private void sendErrorReply(ServiceMessage originalData,
        String errorMessage,
        String errorCode)
    {
        sendErrorReplyStatic(originalData, errorMessage, errorCode);
    }
    
    /**
     * Send an error reply message to the client (static method)
     */
    private static void sendErrorReplyStatic(ServiceMessage originalData,
        String errorMessage, String errorCode)
    {
        try
        {
            String botId = MC.getUser().getName();
            
            JsonObject errorParams = new JsonObject();
            errorParams.addProperty("status", "failed");
            errorParams.addProperty("error", errorMessage);
            errorParams.addProperty("errorCode", errorCode);
            if(originalData.getMethod() != null)
            {
                errorParams.addProperty("originalMethod",
                    originalData.getMethod());
            }
            
            ServiceMessage replyData = new ServiceMessage("wurst",
                originalData.getMethod(), originalData.getRequestId(),
                originalData.getCorrelationId(), null, errorParams,
                "minecraft_client", errorMessage);
            
            EventManager
                .fire(new MqttReplyListener.MqttReplyEvent(botId, replyData));
            
        }catch(Exception e)
        {
            System.err.println("Failed to send error reply: " + e.getMessage());
        }
    }
    
    /**
     * Send a success reply message to the client (static method)
     */
    private static void sendSuccessReplyStatic(ServiceMessage originalData,
        String successMessage)
    {
        try
        {
            String botId = MC.getUser().getName();
            
            JsonObject successParams = new JsonObject();
            successParams.addProperty("status", "success");
            successParams.addProperty("message", successMessage);
            if(originalData.getMethod() != null)
            {
                successParams.addProperty("originalMethod",
                    originalData.getMethod());
            }
            
            ServiceMessage replyData = new ServiceMessage("wurst",
                originalData.getMethod(), originalData.getRequestId(),
                originalData.getCorrelationId(), null, successParams,
                "minecraft_client", successMessage);
            
            EventManager
                .fire(new MqttReplyListener.MqttReplyEvent(botId, replyData));
            
        }catch(Exception e)
        {
            System.err
                .println("Failed to send success reply: " + e.getMessage());
        }
    }
}
