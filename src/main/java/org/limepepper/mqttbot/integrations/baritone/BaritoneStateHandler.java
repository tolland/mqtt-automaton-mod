package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import com.google.gson.JsonObject;
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
        
        // Send pathingState response
        sendPathingStateResponse(playerName, requestId, correlationId);
        
        // Send correlationTracker response
        sendCorrelationTrackerResponse(playerName, requestId, correlationId);
    }
    
    private void sendPathingStateResponse(String playerName, String requestId,
        String correlationId)
    {
        try
        {
            PathingState pathingState = BaritonePathing.getPathingState();
            JsonObject response = new JsonObject();
            response.addProperty("stateType", "pathingState");
            response.addProperty("pathActive", pathingState.isPathActive());
            response.addProperty("announced", pathingState.isAnnounced());
            
            // Add goal information if available
            Goal currentGoal = pathingState.getCurrentGoal();
            if(currentGoal != null)
            {
                GoalDataExtractor.GoalData goalData =
                    GoalDataExtractor.extract(currentGoal);
                if(goalData != null)
                {
                    if(goalData.x() != null)
                        response.addProperty("goalX", goalData.x());
                    if(goalData.y() != null)
                        response.addProperty("goalY", goalData.y());
                    if(goalData.z() != null)
                        response.addProperty("goalZ", goalData.z());
                    response.addProperty("goalType", goalData.kind());
                }
            }else
            {
                response.addProperty("goalType", (String)null);
            }
            
            response.addProperty("player", playerName);
            
            MessageData messageData =
                new MessageData(Constants.SERVICE_NAME, "state", requestId,
                    correlationId, null, response, playerName, null);
            
            EventManager.fire(
                new MqttReplyListener.MqttReplyEvent(playerName, messageData));
            
            LOGGER.debug("Sent pathingState response");
        }catch(Exception e)
        {
            LOGGER.error("Error sending pathingState response: {}",
                e.getMessage(), e);
        }
    }
    
    private void sendCorrelationTrackerResponse(String playerName,
        String requestId, String correlationId)
    {
        try
        {
            CorrelationTracker correlationTracker =
                BaritonePathing.correlationTracker;
            JsonObject response = new JsonObject();
            response.addProperty("stateType", "correlationTracker");
            response.addProperty("requestId",
                correlationTracker.getRequestId());
            response.addProperty("correlationId",
                correlationTracker.getCorrelationId());
            response.addProperty("player", playerName);
            
            MessageData messageData =
                new MessageData(Constants.SERVICE_NAME, "state", requestId,
                    correlationId, null, response, playerName, null);
            
            EventManager.fire(
                new MqttReplyListener.MqttReplyEvent(playerName, messageData));
            
            LOGGER.debug("Sent correlationTracker response");
        }catch(Exception e)
        {
            LOGGER.error("Error sending correlationTracker response: {}",
                e.getMessage(), e);
        }
    }
}
