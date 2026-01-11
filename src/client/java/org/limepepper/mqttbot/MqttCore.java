package org.limepepper.mqttbot;

import net.minecraft.client.Minecraft;
import org.limepepper.mqttbot.actions.*;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.*;
import org.limepepper.mqttbot.mqtt.MqttClientInternal;

public enum MqttCore
{
    INSTANCE;
    
    public static final Minecraft MC = Minecraft.getInstance();
    
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
}
