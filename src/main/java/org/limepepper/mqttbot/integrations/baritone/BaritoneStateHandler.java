package org.limepepper.mqttbot.integrations.baritone;

import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * Handler for baritone state queries.
 * Emits separate response objects for each relevant state component.
 */
public final class BaritoneStateHandler extends Action
    implements org.limepepper.mqttbot.mqtt.MessageHandler {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BaritoneStateHandler.class);
    
    private BaritoneStateHandler()
    {
        // Private constructor
    }
    
    public static BaritoneStateHandler create()
    {
        return new BaritoneStateHandler();
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
        
        // Send pathingState response (includes correlation IDs if active)
        sendPathingStateResponse(playerName, requestId, correlationId);
    }
    
    private void sendPathingStateResponse(String playerName, String requestId,
        String correlationId)
    {
        try
        {
            MessageData messageData = new MessageData(Constants.SERVICE_NAME,
                "state", requestId, correlationId, null,
                PathingState.INSTANCE.toJson(), playerName, null);
            
            EventManager.fire(
                new MqttReplyListener.MqttReplyEvent(playerName, messageData));
            
            LOGGER.debug("Sent pathingState response");
        }catch(Exception e)
        {
            LOGGER.error("Error sending pathingState response: {}",
                e.getMessage(), e);
        }
    }
    
}
