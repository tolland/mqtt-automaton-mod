package org.limepepper.mqttbot;


import org.limepepper.mqttbot.actions.*;
import org.limepepper.mqttbot.actions.ClientAction;
import org.limepepper.mqttbot.actions.DamageAction;
import org.limepepper.mqttbot.actions.DayNightAction;
import org.limepepper.mqttbot.actions.DeathAction;
import org.limepepper.mqttbot.actions.InventoryAction;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.*;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.events.DamageListener;
import org.limepepper.mqttbot.events.DayNightListener;
import org.limepepper.mqttbot.events.DeathListener;
import org.limepepper.mqttbot.events.InventoryListener;
import org.limepepper.mqttbot.mqtt.MqttClientInternal;
import net.minecraft.client.Minecraft;

public enum MqttCore {
    INSTANCE;

    public static final Minecraft MC = Minecraft.getInstance();

    public void initialize() {
        System.out.println("Starting MqttBot Client...");

        // ensure initialized first
        EventManager eventManager = EventManager.INSTANCE;

        eventManager.add(ClientListener.class, new ClientAction());
        eventManager.add(DeathListener.class, new DeathAction());
        eventManager.add(DamageListener.class, new DamageAction());
        eventManager.add(DayNightListener.class, new DayNightAction());
        eventManager.add(InventoryListener.class, new InventoryAction());

        //PlayerJoinCallback.EVENT.register(new PlayerJoinHandler());

        MqttClientInternal handler = MqttClientInternal.INSTANCE;
    }


    public EventManager getEventManager() {
        return EventManager.INSTANCE;
    }

    public boolean isEnabled() {
        return true;
    }
}
