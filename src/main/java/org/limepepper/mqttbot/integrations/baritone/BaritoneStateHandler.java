package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.JsonObject;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * Handler for baritone state queries. Returns comprehensive state information
 * including current request, phase, and request history for debugging.
 *
 * <p>
 * Response includes:
 * <ul>
 * <li>Current request details (if any)</li>
 * <li>Current phase</li>
 * <li>Request history statistics</li>
 * <li>Full event timeline for current request</li>
 * <li>Recent completed requests with their timelines</li>
 * </ul>
 * </p>
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
        
        // Build comprehensive state response
        JsonObject response = new JsonObject();
        response.addProperty("stateType", "baritoneState");
        
        // Include current pathing state
        response.add("currentState", PathingState.INSTANCE.toJson());
        
        // Include request history (last 10 requests)
        response.add("requestHistory", RequestHistory.INSTANCE.toJson());
        
        // Include history statistics
        response.add("historyStats", RequestHistory.INSTANCE.getStatistics());
        
        // Include event timeline for current request if active
        PathingRequest currentRequest =
            PathingState.INSTANCE.getCurrentRequest();
        if(currentRequest != null)
        {
            com.google.gson.JsonArray timeline =
                new com.google.gson.JsonArray();
            for(String event : currentRequest.getEventTimeline())
            {
                timeline.add(event);
            }
            response.add("currentRequestTimeline", timeline);
        }
        
        // Send response
        MessageData messageData = new MessageData(Constants.SERVICE_NAME,
            "state", requestId, correlationId, null, response, playerName,
            null);
        
        EventManager
            .fire(
                new MqttReplyListener.MqttReplyEvent(playerName, messageData));
        
        LOGGER.debug("Sent comprehensive state response with history");
    }
    
}
