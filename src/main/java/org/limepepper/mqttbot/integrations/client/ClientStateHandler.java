package org.limepepper.mqttbot.integrations.client;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.integrations.baritone.*;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * Handler for baritone state queries.
 * Emits separate response objects for each relevant state component.
 */
public final class ClientStateHandler extends Action
    implements org.limepepper.mqttbot.mqtt.MessageHandler {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(ClientStateHandler.class);
    
    private ClientStateHandler()
    {
        // Private constructor
    }
    
    public static ClientStateHandler create()
    {
        return new ClientStateHandler();
    }
    
    @Override
    public boolean canHandle(MessageData msg)
    {
        return "baritone".equals(msg.getService())
            && "state".equals(msg.getMethod());
    }
    
    @Override
    public void handle(MessageData msg) throws Exception
    {
        String playerName = CORE.getPlayerName();
        String requestId = msg.getRequestId();
        String correlationId = msg.getCorrelationId();
        
    }
    
}
