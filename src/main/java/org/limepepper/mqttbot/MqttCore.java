package org.limepepper.mqttbot;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import org.limepepper.mqttbot.actions.*;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.*;
import org.limepepper.mqttbot.mqtt.MqttClientInternal;

public enum MqttCore
{
    INSTANCE;
    
    public static final Minecraft MC = Minecraft.getInstance();
    private BotState botState = BotState.IDLE;
    
    public void initialize()
    {
        System.out.println("Starting MqttBot Client...");
        
        // ensure initialized first
        EventManager eventManager = EventManager.INSTANCE;
        
        eventManager.add(ClientListener.class, new ClientAction());
        eventManager.add(DeathListener.class, new DeathAction());
        eventManager.add(DamageListener.class, new DamageAction());
        eventManager.add(DayNightListener.class, new DayNightAction());
        eventManager.add(InventoryListener.class, new InventoryAction());
        eventManager.add(ChatMessageListener.class, new ChatMessageAction());
        
        // PlayerJoinCallback.EVENT.register(new PlayerJoinHandler());
        
        MqttClientInternal handler = MqttClientInternal.INSTANCE;
    }
    
    public EventManager getEventManager()
    {
        return EventManager.INSTANCE;
    }
    
    public boolean isEnabled()
    {
        return true;
    }
    
    /**
     * Sends a chat message to the server.
     * This method can be mocked for testing.
     */
    public void sendChat(String message)
    {
        if(MC.getConnection() != null)
        {
            MC.getConnection().sendChat(message);
        }
    }
    
    /**
     * Gets the local player instance.
     * Returns null if not connected or player not available.
     * This method can be mocked for testing.
     */
    public LocalPlayer getPlayer()
    {
        return MC.player;
    }
    
    /**
     * Gets the player's name.
     * Returns "unknown" if player is not available.
     * This method can be mocked for testing.
     */
    public String getPlayerName()
    {
        if(MC.player != null)
        {
            return MC.getUser().getName();
        }
        return "unknown";
    }
    
    public BotState getBotState()
    {
        return botState;
    }
    
    public void setBotState(BotState botState)
    {
        this.botState = botState;
    }
    
    /**
     * Check what state the bot is in.
     */
    public enum BotState
    {
        IDLE,
        BUSY,
        ERROR
    }
}
