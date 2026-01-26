package org.limepepper.mqttbot.integrations.wurst;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.wurstclient.WurstClient;
import net.wurstclient.command.CmdException;
import net.wurstclient.command.CmdList;
import net.wurstclient.command.Command;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

public class WurstService {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(WurstService.class);
    public static final WurstService INSTANCE = new WurstService();
    
    private final ConcurrentLinkedQueue<CommandTask> commandQueue =
        new ConcurrentLinkedQueue<>();
    
    private record CommandTask(String commandName, List<String> args)
    {}
    
    private WurstService()
    {
        // Register client tick event to process queued commands on main thread
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            CommandTask task;
            while((task = commandQueue.poll()) != null)
            {
                executeWurstCommandOnMainThread(task);
            }
        });
    }
    
    public void executeCommand(String commandName, List<String> args)
    {
        commandQueue.offer(new CommandTask(commandName, args));
    }
    
    private void executeWurstCommandOnMainThread(CommandTask task)
    {
        try
        {
            CmdList cmds = WurstClient.INSTANCE.getCmds();
            Command cmd = cmds.getCmdByName(task.commandName);
            
            if(cmd == null)
            {
                LOGGER.error("Command not found: " + task.commandName);
                return;
            }
            
            LOGGER.debug("Executing Wurst command: " + task.commandName
                + " with args: " + task.args);
            cmd.call(task.args.toArray(new String[0]));
            
        }catch(CmdException e)
        {
            LOGGER.error("Wurst command failed: " + e.getMessage());
        }catch(Exception e)
        {
            LOGGER.error(
                "Unexpected error executing Wurst command: " + e.getMessage());
        }
    }
}
