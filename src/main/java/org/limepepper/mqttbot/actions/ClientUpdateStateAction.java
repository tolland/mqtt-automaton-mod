package org.limepepper.mqttbot.actions;

import baritone.api.utils.BetterBlockPos;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.events.ClientListener;
import org.limepepper.mqttbot.events.DeathListener;
import org.limepepper.mqttbot.presence.DevicePresence;
import org.limepepper.mqttbot.presence.ReadinessState;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * Game, Player and mc client related event actions.
 */
public class ClientUpdateStateAction extends Action
    implements ClientListener, DeathListener {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(ClientUpdateStateAction.class);
    private final DevicePresence presence =
        DevicePresence.getInstance(CORE.getPlayerName());
    
    @Override
    public void onClientJoin(ClientJoinEvent event)
    {
        try
        {
            // Player joined world - now ready
            JsonObject additionalData = new JsonObject();
            additionalData.addProperty("world", event.getWorld());
            additionalData.addProperty("player", event.getPlayerName());
            
            BetterBlockPos pos =
                MqttCore.baritone.getPlayerContext().playerFeet();
            JsonObject position = new JsonObject();
            position.addProperty("x", pos.x);
            position.addProperty("y", pos.y);
            position.addProperty("z", pos.z);
            additionalData.add("position", position);
            
            additionalData.addProperty("health",
                Minecraft.getInstance().player.getHealth());
            
            ReadinessState state = ReadinessState.ready(
                "IN_WORLD_READY",
                "player_joined_world",
                additionalData);
            
            presence.publishReadiness(state);
            
        }catch(MqttException e)
        {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }
    
    @Override
    public void onClientDisconnect(ClientDisconnectEvent event)
    {
        try
        {
            // Player disconnected - not ready
            ReadinessState state = ReadinessState.notReady(
                "DISCONNECTED",
                "player_left_world",
                null);
            
            presence.publishReadiness(state);
            
        }catch(MqttException e)
        {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }
    
    @Override
    public void onDeath()
    {
        try
        {
            ReadinessState state = ReadinessState.notReady(
                "IN_WORLD_DEAD",
                "player_died",
                null);
            
            presence.publishReadiness(state);
            
        }catch(MqttException e)
        {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }
    
    // New method for respawn
    public void onPlayerRespawn()
    {
        try
        {
            JsonObject additionalData = new JsonObject();
            BetterBlockPos pos =
                MqttCore.baritone.getPlayerContext().playerFeet();
            JsonObject position = new JsonObject();
            position.addProperty("x", pos.x);
            position.addProperty("y", pos.y);
            position.addProperty("z", pos.z);
            additionalData.add("position", position);
            
            ReadinessState state = ReadinessState.ready(
                "IN_WORLD_READY",
                "player_respawned",
                additionalData);
            
            presence.publishReadiness(state);
            
        }catch(MqttException e)
        {
            LOGGER.error("Failed to publish readiness: {}", e.getMessage());
        }
    }
}
