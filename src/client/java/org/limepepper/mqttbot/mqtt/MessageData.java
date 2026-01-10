package org.limepepper.mqttbot.mqtt;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;

/**
 * Structured MQTT message format for inter-service communication
 */
public class MessageData {
    private static final Gson gson = new Gson();
    
    private String service; // Target service/module (e.g., "baritone",
                            // "inventory", "chat")
    private String method; // Method to call on the service (e.g., "goto",
                           // "mine", "say")
    private String requestId; // Unique request identifier
    private String correlationId; // Correlation ID for request/response
                                  // tracking
    private JsonObject params; // Arbitrary parameters for the method (requests)
    private JsonObject response; // Structured response data (replies)
    private String identity; // Source of the message (e.g., "python_client",
                             // "web_dashboard")
    private String message; // Free text field for debug/informational content
    
    // Default constructor
    public MessageData()
    {}
    
    // Full constructor
    public MessageData(String service, String method, String requestId,
        String correlationId, JsonObject params, JsonObject response,
        String identity, String message)
    {
        this.service = service;
        this.method = method;
        this.requestId = requestId;
        this.correlationId = correlationId;
        this.params = params;
        this.response = response;
        this.identity = identity;
        this.message = message;
    }
    
    // Convenience constructor for requests (no response)
    public MessageData(String service, String method, String requestId,
        String correlationId, JsonObject params, String identity,
        String message)
    {
        this(service, method, requestId, correlationId, params, null, identity,
            message);
    }
    
    /**
     * Parse a JSON string into an MqttMessage object
     *
     * @param jsonString
     *            The JSON string to parse
     * @return MqttMessage object or null if parsing fails
     */
    public static MessageData fromJson(String jsonString)
    {
        try
        {
            return gson.fromJson(jsonString, MessageData.class);
        }catch(JsonSyntaxException e)
        {
            System.err.println(
                "Failed to parse MQTT message JSON: " + e.getMessage());
            System.err.println("Original message: " + jsonString);
            return null;
        }
    }
    
    /**
     * Convert this MqttMessage to JSON string
     *
     * @return JSON string representation
     */
    public String toJson()
    {
        return gson.toJson(this);
    }
    
    /**
     * Check if this message is valid (has required fields)
     *
     * @return true if message has service and method fields
     */
    public boolean isValid()
    {
        return service != null && !service.trim().isEmpty() && method != null
            && !method.trim().isEmpty();
    }
    
    // Getters and setters
    public String getService()
    {
        return service;
    }
    
    public void setService(String service)
    {
        this.service = service;
    }
    
    public String getMethod()
    {
        return method;
    }
    
    public void setMethod(String method)
    {
        this.method = method;
    }
    
    public String getRequestId()
    {
        return requestId;
    }
    
    public void setRequestId(String requestId)
    {
        this.requestId = requestId;
    }
    
    public String getCorrelationId()
    {
        return correlationId;
    }
    
    public void setCorrelationId(String correlationId)
    {
        this.correlationId = correlationId;
    }
    
    public JsonObject getParams()
    {
        return params;
    }
    
    public void setParams(JsonObject params)
    {
        this.params = params;
    }
    
    public JsonObject getResponse()
    {
        return response;
    }
    
    public void setResponse(JsonObject response)
    {
        this.response = response;
    }
    
    public String getIdentity()
    {
        return identity;
    }
    
    public void setIdentity(String identity)
    {
        this.identity = identity;
    }
    
    public String getMessage()
    {
        return message;
    }
    
    public void setMessage(String message)
    {
        this.message = message;
    }
    
    @Override
    public String toString()
    {
        return String.format(
            "MqttMessage{service='%s', method='%s', requestId='%s', correlationId='%s', identity='%s', hasParams=%s, hasResponse=%s, message='%s'}",
            service, method, requestId, correlationId, identity,
            (params != null), (response != null), message);
    }
}
