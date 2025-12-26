package org.limepepper.mqttbot.integrations.baritone;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import net.minecraft.client.Minecraft;

/**
 * The purpose of this enum class is to control baritone by
 * issuing pathing commands, and other ancillary commands.
 *
 * @TODO ideally we would migrate to calling baritone API
 * directly, i.e. not via chat, in order to have
 * some more visibility into errors and edge cases.
 */
public final class BaritoneCmds extends Action implements MqttMessageListener {
    public static final BaritoneCmds INSTANCE = new BaritoneCmds();

    public static final Minecraft MC = Minecraft.getInstance();

    private BaritoneCmds() {
    }

    /**
     *
     *
     */
    public static void init() {
        EventManager.INSTANCE.add(MqttMessageListener.class, BaritoneCmds.INSTANCE);

    }

    @Override
    public void onMessageArrived(MqttMessageEvent mqttMessageEvent) {
        if (MC.player == null) return;
        MessageData data = mqttMessageEvent.messageData;
        System.out.println("recieved message in baritone pathing");
        if (!mqttMessageEvent.messageData.getService().equals("baritone")) return;
        System.out.println("message for baritone");
        switch (mqttMessageEvent.messageData.getMethod()) {
            case "goto":
                handleGotoCommand(data);
                break;
            case "pause":
                MC.getConnection().sendChatMessage("#pause");
                break;
            case "resume":
                MC.getConnection().sendChatMessage("#resume");
                break;
            case "cancel":
                MC.getConnection().sendChatMessage("#cancel");
                break;
            case "chat":
                // Legacy support - will be removed soon
                String cmd = data.getParams().get("message").getAsString();
                System.out.println("Legacy chat cmd: " + cmd);
                if (MC.player != null) {
                    MC.getConnection().sendChatMessage(cmd);
                }
                break;
            default:
                System.out.println("Unknown method in baritone: " + mqttMessageEvent.messageData.getMethod());
        }

    }

    /**
     * Handle structured goto commands with x, y, z parameters
     * This is a temporary shim - will be replaced with direct Baritone API calls
     */
    private void handleGotoCommand(MessageData data) {
        try {
            if (data.getParams() == null) {
                System.out.println("Error: goto command missing params");
                return;
            }
            
            // Extract coordinates from params
            int x = data.getParams().get("x").getAsInt();
            int y = data.getParams().get("y").getAsInt(); 
            int z = data.getParams().get("z").getAsInt();
            
            // Build the goto command string (temporary shim)
            String gotoCmd = String.format("#goto %d %d %d", x, y, z);
            System.out.println("Executing goto command: " + gotoCmd);

            if (MC.player != null) {
                MC.getConnection().sendChatMessage(gotoCmd);
            } else {
                System.out.println("Error: Player is null, cannot execute goto command");
            }
            
        } catch (Exception e) {
            System.out.println("Error handling goto command: " + e.getMessage());
            e.printStackTrace();
        }
    }

}
