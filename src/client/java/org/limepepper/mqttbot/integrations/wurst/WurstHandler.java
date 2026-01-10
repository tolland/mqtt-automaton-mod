package org.limepepper.mqttbot.integrations.wurst;

import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import net.minecraft.client.Minecraft;
import net.wurstclient.WurstClient;
import net.wurstclient.command.CmdException;
import net.wurstclient.command.CmdList;
import net.wurstclient.command.Command;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

public class WurstHandler extends Action implements MqttMessageListener {
    public static final Minecraft MC = Minecraft.getInstance();
    
    // Queue to hold commands that need to be executed on the main thread
    private static final ConcurrentLinkedQueue<CommandTask> commandQueue =
        new ConcurrentLinkedQueue<>();
    
    // Data class to hold command execution tasks
    private static class CommandTask {
        final MessageData originalData;
        final String commandName;
        final List<String> args;
        
        CommandTask(MessageData originalData, String commandName,
            List<String> args)
        {
            this.originalData = originalData;
            this.commandName = commandName;
            this.args = args;
        }
    }
    
    public static void init()
    {
        EventManager.INSTANCE.add(MqttMessageListener.class,
            new WurstHandler());
        
        // Register client tick event to process queued commands on main thread
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            CommandTask task;
            while((task = commandQueue.poll()) != null)
            {
                executeWurstCommandOnMainThread(task);
            }
        });
    }
    
    @Override
    public void onMessageArrived(
        MqttMessageListener.MqttMessageEvent mqttMessageEvent)
    {
        MessageData data = mqttMessageEvent.messageData;
        System.out.println("received message in wurst handler");
        
        if(!data.getService().equals("wurst"))
        {
            return;
        }
        
        System.out.println("message for wurst service");
        
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
    private void handleArbitraryCommand(MessageData data)
    {
        try
        {
            JsonObject params = data.getParams();
            if(params == null)
            {
                sendErrorReply(data, "No parameters provided for command",
                    "MISSING_PARAMETERS");
                return;
            }
            
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
                if(params.get("args").isJsonArray())
                {
                    // Handle array of arguments
                    params.get("args").getAsJsonArray()
                        .forEach(element -> args.add(element.getAsString()));
                }else
                {
                    // Handle single string argument (split by spaces)
                    String argsString = params.get("args").getAsString();
                    if(!argsString.trim().isEmpty())
                    {
                        args.addAll(Arrays.asList(argsString.split("\\s+")));
                    }
                }
            }
            
            // Queue the command for execution on the main thread
            commandQueue.offer(new CommandTask(data, commandName, args));
            
        }catch(Exception e)
        {
            sendErrorReply(data,
                "Error parsing command parameters: " + e.getMessage(),
                "PARSE_ERROR");
        }
    }
    
    /**
     * Execute a Wurst command on the main client thread (called from tick
     * event)
     */
    private static void executeWurstCommandOnMainThread(CommandTask task)
    {
        try
        {
            CmdList cmds = WurstClient.INSTANCE.getCmds();
            Command cmd = cmds.getCmdByName(task.commandName);
            
            if(cmd == null)
            {
                sendErrorReplyStatic(task.originalData,
                    "Command not found: " + task.commandName,
                    "COMMAND_NOT_FOUND");
                return;
            }
            
            System.out.println("Executing Wurst command: " + task.commandName
                + " with args: " + task.args);
            cmd.call(task.args.toArray(new String[0]));
            
            // Send success reply
            sendSuccessReplyStatic(task.originalData,
                "Command executed successfully: " + task.commandName + " "
                    + String.join(" ", task.args));
            
        }catch(CmdException e)
        {
            String errorMsg = "Wurst command failed: " + e.getMessage();
            System.err.println(errorMsg);
            sendErrorReplyStatic(task.originalData, errorMsg,
                "COMMAND_EXECUTION_ERROR");
        }catch(Exception e)
        {
            String errorMsg =
                "Unexpected error executing Wurst command: " + e.getMessage();
            System.err.println(errorMsg);
            sendErrorReplyStatic(task.originalData, errorMsg,
                "UNEXPECTED_ERROR");
        }
    }
    
    /**
     * Send an error reply message to the client (instance method)
     */
    private void sendErrorReply(MessageData originalData, String errorMessage,
        String errorCode)
    {
        sendErrorReplyStatic(originalData, errorMessage, errorCode);
    }
    
    /**
     * Send an error reply message to the client (static method)
     */
    private static void sendErrorReplyStatic(MessageData originalData,
        String errorMessage, String errorCode)
    {
        try
        {
            String botId = MC.getUser().getName();
            
            JsonObject errorParams = new JsonObject();
            errorParams.addProperty("success", false);
            errorParams.addProperty("error", errorMessage);
            errorParams.addProperty("errorCode", errorCode);
            if(originalData.getMethod() != null)
            {
                errorParams.addProperty("originalMethod",
                    originalData.getMethod());
            }
            
            MessageData replyData = new MessageData("wurst", "response",
                originalData.getRequestId(), originalData.getCorrelationId(),
                errorParams, "minecraft_client", errorMessage);
            
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
    private static void sendSuccessReplyStatic(MessageData originalData,
        String successMessage)
    {
        try
        {
            String botId = MC.getUser().getName();
            
            JsonObject successParams = new JsonObject();
            successParams.addProperty("success", true);
            successParams.addProperty("message", successMessage);
            if(originalData.getMethod() != null)
            {
                successParams.addProperty("originalMethod",
                    originalData.getMethod());
            }
            
            MessageData replyData = new MessageData("wurst", "response",
                originalData.getRequestId(), originalData.getCorrelationId(),
                successParams, "minecraft_client", successMessage);
            
            EventManager
                .fire(new MqttReplyListener.MqttReplyEvent(botId, replyData));
            
        }catch(Exception e)
        {
            System.err
                .println("Failed to send success reply: " + e.getMessage());
        }
    }
}
