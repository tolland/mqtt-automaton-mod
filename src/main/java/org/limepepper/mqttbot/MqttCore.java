package org.limepepper.mqttbot;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import baritone.api.behavior.IPathingBehavior;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import org.limepepper.mqttbot.action.BaritonePathingFeature;
import org.limepepper.mqttbot.action.FeatureRegistry;
import org.limepepper.mqttbot.action.InventoryFullFeature;
import org.limepepper.mqttbot.actions.*;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.*;
import org.limepepper.mqttbot.integrations.baritone.BaritoneCollectHandler;
import org.limepepper.mqttbot.integrations.baritone.BaritoneGotoHandler;
import org.limepepper.mqttbot.integrations.baritone.BaritoneStateHandler;
import org.limepepper.mqttbot.integrations.client.BotStateHandler;
import org.limepepper.mqttbot.mqtt.MqttClientInternal;
import org.limepepper.mqttbot.util.MqttBotLogger;

public enum MqttCore
{
    INSTANCE;
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(MqttCore.class);
    
    public static final Minecraft MC = Minecraft.getInstance();
    // Baritone API references
    public static IBaritone baritone =
        BaritoneAPI.getProvider().getPrimaryBaritone();
    public static final IPathingBehavior pathing =
        baritone.getPathingBehavior();
    private BotState botState = BotState.IDLE;
    
    public void initialize()
    {
        LOGGER.debug("Starting MqttBot Client...");
        
        EventManager eventManager = EventManager.INSTANCE;
        
        eventManager.add(ClientListener.class, new ClientAction());
        eventManager.add(DeathListener.class, new DeathAction());
        // @TODO this is not working since 1.20.x changes. need to fix
        eventManager.add(DamageListener.class, new DamageAction());
        eventManager.add(DayNightListener.class, new DayNightAction());
        eventManager.add(InventoryListener.class, new InventoryAction());
        eventManager.add(ChatMessageListener.class, new ChatMessageAction());
        eventManager.add(MqttMessageListener.class,
            // MessageDispatcher is a sub-router to redirect to specific service
            new MessageDispatcherAction(
                // each of these is a command type from the client
                BaritoneGotoHandler.create(), BaritoneCollectHandler.create(),
                BaritoneStateHandler.create(), BotStateHandler.create()));
        
        // PlayerJoinCallback.EVENT.register(new PlayerJoinHandler());
        
        // This sources events into the EventManager from Mqtt
        MqttClientInternal handler = MqttClientInternal.INSTANCE;
        
        // Things that can be toggled
        features().register(new InventoryFullFeature());
        features().register(new BaritonePathingFeature());
        
    }
    
    private final FeatureRegistry featureRegistry = new FeatureRegistry();
    
    public FeatureRegistry features()
    {
        return featureRegistry;
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
