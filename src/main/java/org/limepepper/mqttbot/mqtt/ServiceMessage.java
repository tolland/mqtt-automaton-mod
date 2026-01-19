package org.limepepper.mqttbot.mqtt;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;
import java.time.Instant;

/**
 * Structured MQTT message format for inter-service communication
 */
public class ServiceMessage {
    private static final Gson gson = new Gson();
    
    /**
     * Target service/module (e.g., "baritone", "inventory", "chat")
     */
    private String service;
    
    /**
     * Method to call on the service (e.g., "goto", "mine", "say")
     */
    private String method;
    
    /**
     * Unique request identifier
     */
    private String requestId;
    
    /**
     * Correlation ID for request/response tracking
     */
    private String correlationId;
    
    /**
     * Arbitrary parameters for the method (requests)
     */
    private JsonElement params;
    
    /**
     * Structured response data (replies)
     */
    private JsonElement response;
    
    /**
     * Source of the message (e.g., "python_client", "web_dashboard")
     */
    private String identity;
    
    /**
     * Free text field for debug/informational content
     */
    private String message;
    
    /**
     * ISO-8601 timestamp for when this message was created (UTC)
     */
    private String timestamp;
    
    // Default constructor
    public ServiceMessage()
    {
        // Populate timestamp centrally so all messages created in code have it
        this.timestamp = Instant.now().toString();
    }
    
    /**
     * ServiceMessage is JsonObject representing an MQTT-bot mqtt message
     *
     * @param service
     *            A string identifying the target service
     * @param method
     *            A string identifying the method to call
     * @param requestId
     *            A uuid string identifying this request
     * @param correlationId
     *            A uuid identifier conserved over groups of requests
     * @param params
     *            A JsonObject containing method parameters outgoing
     * @param identity
     *            A string identifying the source of the message
     * @param message
     *            A human readable message for logging/debugging
     */
    public ServiceMessage(String service, String method, String requestId,
        String correlationId, JsonElement params, JsonElement response,
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
        this.timestamp = Instant.now().toString();
    }
    
    /**
     * Convenience constructor for requests (no response)
     *
     * @param service
     *            A string identifying the target service
     * @param method
     *            A string identifying the method to call
     * @param requestId
     *            A uuid string identifying this request
     * @param correlationId
     *            A uuid identifier conserved over groups of requests
     * @param params
     *            A JsonObject containing method parameters outgoing
     * @param identity
     *            A string identifying the source of the message
     * @param message
     *            A human readable message for logging/debugging
     */
    public ServiceMessage(String service, String method, String requestId,
        String correlationId, JsonElement params, String identity,
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
    public static ServiceMessage fromJson(String jsonString)
    {
        try
        {
            ServiceMessage md = gson.fromJson(jsonString, ServiceMessage.class);
            if(md != null && (md.timestamp == null || md.timestamp.isEmpty()))
            {
                md.timestamp = Instant.now().toString();
            }
            return md;
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
     * Check if this message is valid (has required fields). This is a basic
     * validation that only checks service and method. For stricter validation
     * including correlation IDs, use isValidRequest() or isValidResponse().
     *
     * @return true if message has service and method fields
     */
    public boolean isValid()
    {
        return service != null && !service.trim().isEmpty() && method != null
            && !method.trim().isEmpty();
    }
    
    /**
     * Validates that this message is a valid request with all required fields
     * including correlation IDs.
     *
     * @return true if this is a valid request (has service, method, requestId,
     *         and correlationId)
     */
    public boolean isValidRequest()
    {
        return isValid() && requestId != null && !requestId.trim().isEmpty()
            && correlationId != null && !correlationId.trim().isEmpty();
    }
    
    /**
     * Validates that this message is a valid response with all required fields
     * including correlation IDs.
     *
     * @return true if this is a valid response (has service, method, requestId,
     *         correlationId, and response data)
     */
    public boolean isValidResponse()
    {
        return isValidRequest() && response != null;
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
    
    public JsonElement getParams()
    {
        return params;
    }
    
    public void setParams(JsonElement params)
    {
        this.params = params;
    }
    
    // Backwards-compatible overload for callers that pass JsonObject
    public void setParams(JsonObject params)
    {
        this.params = params;
    }
    
    public JsonElement getResponse()
    {
        return response;
    }
    
    public void setResponse(JsonElement response)
    {
        this.response = response;
    }
    
    // Backwards-compatible overload for callers that expect JsonObject
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
    
    public String getTimestamp()
    {
        return timestamp;
    }
    
    public void setTimestamp(String timestamp)
    {
        this.timestamp = timestamp;
    }
    
    @Override
    public String toString()
    {
        return String.format(
            "MqttMessage{service='%s', method='%s', requestId='%s', correlationId='%s', identity='%s', hasParams=%s, hasResponse=%s, timestamp='%s', message='%s'}",
            service, method, requestId, correlationId, identity,
            (params != null), (response != null), timestamp, message);
    }
}
