package org.limepepper.mqttbot.integrations.baritone;

import baritone.api.pathing.goals.Goal;
import com.google.gson.JsonObject;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;

/**
 * Builds and sends MQTT responses for Baritone-related actions.
 */
class ResponseBuilder {
    
    private static final MqttCore mqttCore = MqttCore.INSTANCE;
    
    static void sendGotoSuccess(String message, int x, int y, int z)
    {
        JsonObject response = new JsonObject();
        response.addProperty("status", "success");
        response.addProperty("message", message);
        response.addProperty("x", x);
        response.addProperty("y", y);
        response.addProperty("z", z);
        response.addProperty("player", mqttCore.getPlayerName());
        
        ResponseBuilder.sendResponse("goto", response);
    }
    
    static void sendGotoFailure(String message, String reason)
    {
        JsonObject response = new JsonObject();
        response.addProperty("status", "failure");
        response.addProperty("message", message);
        response.addProperty("reason", reason);
        response.addProperty("player", mqttCore.getPlayerName());
        
        sendResponse("goto", response);
    }
    
    static void sendPathingEvent(String type, String detail)
    {
        JsonObject response =
            createPathingResponse(type, MqttCore.pathing.getGoal(), detail);
        sendResponse("pathing", response);
    }
    
    static void sendPathingEventWithPayload(String type, JsonObject payload)
    {
        sendResponse(type, payload);
    }
    
    private static void sendResponse(String method, JsonObject response)
    {
        try
        {
            String playerName = mqttCore.getPlayerName();
            MessageData messageData = new MessageData(Constants.SERVICE_NAME,
                method, CorrelationTracker.INSTANCE.getRequestId(),
                CorrelationTracker.INSTANCE.getCorrelationId(), null, response,
                mqttCore.getPlayerName(), null);
            
            EventManager.fire(
                new MqttReplyListener.MqttReplyEvent(playerName, messageData));
        }catch(Exception e)
        {
            e.printStackTrace();
        }
    }
    
    private static JsonObject createPathingResponse(String type, Goal goal,
        String detail)
    {
        JsonObject response = new JsonObject();
        response.addProperty("type", type);
        response.addProperty("player", mqttCore.getPlayerName());
        
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
