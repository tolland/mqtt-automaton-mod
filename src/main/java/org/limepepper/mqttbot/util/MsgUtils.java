package org.limepepper.mqttbot.util;

import com.google.gson.JsonObject;
import org.limepepper.mqttbot.integrations.baritone.CorrelationIds;
import org.limepepper.mqttbot.mqtt.ServiceMessage;

public enum MsgUtils
{
    INSTANCE;
    
    public static String formatMessage(String botId, String method,
        String params)
    {
        return String.format(
            "{\"botId\": \"%s\", \"method\": \"%s\", \"params\": \"%s\"}",
            botId, method, params);
    }
    
    public static ServiceMessage msgData(String service, String method,
        String requestId,
        String correlationId,
        JsonObject params)
    {
        ServiceMessage msgData = new ServiceMessage();
        msgData.setRequestId(requestId);
        msgData.setCorrelationId(correlationId);
        msgData.setService(service);
        msgData.setMethod(method);
        msgData.setParams(params);
        return msgData;
    }
    
    /**
     * Strip Minecraft color codes from a message
     * Color codes are in the format §x where x is a character
     */
    public static String stripColorCodes(String message)
    {
        if(message == null)
            return "";
        return message.replaceAll("§[0-9a-fk-or]", "");
    }
    
    /**
     * Creates a success ServiceMessage with correlation IDs
     *
     * @param ids
     *            The correlation IDs from the original request
     * @param service
     *            The service name
     * @param method
     *            The method name
     * @param event_type
     *            The event type/status
     * @param message
     *            The message content
     * @return ServiceMessage ready to send
     */
    public static ServiceMessage ctSuccess(CorrelationIds ids, String service,
        String method, String event_type, String message)
    {
        java.util.Objects.requireNonNull(ids,
            "CorrelationIds cannot be null when creating success response");
        JsonObject resp = new JsonObject();
        resp.addProperty("status", event_type);
        resp.addProperty("message", message);
        return new ServiceMessage(service, method, ids.requestId(),
            ids.correlationId(), null, resp, "mqttbot", message);
        
    }
    
}
