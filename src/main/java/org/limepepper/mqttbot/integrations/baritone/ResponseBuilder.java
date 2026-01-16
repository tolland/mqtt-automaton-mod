package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import com.google.gson.JsonObject;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

/**
 * Builds and sends MQTT responses
 */
class ResponseBuilder {
    
    private static final MqttCore mqttCore = MqttCore.INSTANCE;
    
    void sendGotoSuccess(String message, int x, int y, int z)
    {
        JsonObject response = new JsonObject();
        response.addProperty("status", "success");
        response.addProperty("message", message);
        response.addProperty("x", x);
        response.addProperty("y", y);
        response.addProperty("z", z);
        response.addProperty("player", getPlayerName());
        
        sendResponse("goto", response);
    }
    
    void sendGotoFailure(String message, String reason)
    {
        JsonObject response = new JsonObject();
        response.addProperty("status", "failure");
        response.addProperty("message", message);
        response.addProperty("reason", reason);
        response.addProperty("player", getPlayerName());
        
        sendResponse("goto", response);
    }
    
    void sendPathingEvent(String type, String detail)
    {
        JsonObject response = createPathingResponse(type,
            BaritonePathing.pathing.getGoal(), detail);
        sendResponse("pathing", response);
    }
    
    void sendPathingEventWithPayload(String type, JsonObject payload)
    {
        sendResponse(type, payload);
    }
    
    private void sendResponse(String method, JsonObject response)
    {
        try
        {
            String playerName = getPlayerName();
            MessageData messageData =
                new MessageData(BaritonePathing.SERVICE_NAME, method,
                    BaritonePathing.correlationTracker.getRequestId(),
                    BaritonePathing.correlationTracker.getCorrelationId(), null,
                    response, BaritonePathing.correlationTracker.getIdentity(),
                    null);
            
            EventManager.fire(
                new MqttReplyListener.MqttReplyEvent(playerName, messageData));
        }catch(Exception e)
        {
            e.printStackTrace();
        }
    }
    
    private JsonObject createPathingResponse(String type, Goal goal,
        String detail)
    {
        JsonObject response = new JsonObject();
        response.addProperty("type", type);
        response.addProperty("player", getPlayerName());
        
        if(detail != null)
        {
            response.addProperty("detail", detail);
        }
        
        GoalDataExtractor.GoalData goalData = GoalDataExtractor.extract(goal);
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
        
        return response;
    }
    
    private String getPlayerName()
    {
        return mqttCore.getPlayerName();
    }
}
