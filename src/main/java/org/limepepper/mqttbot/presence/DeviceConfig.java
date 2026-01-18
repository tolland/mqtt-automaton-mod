package org.limepepper.mqttbot.presence;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import java.util.List;
import java.util.Map;

/**
 * Device configuration (capabilities, services, metadata) following Home
 * Assistant discovery pattern.
 */
public class DeviceConfig
{
    private final String deviceId;
    private final String name;
    private final String model;
    private final String manufacturer;
    private final String swVersion;
    private final List<String> services;
    private final Map<String, Object> capabilities;
    private final Map<String, String> topics;

    public DeviceConfig(String deviceId, String name, String model,
        String manufacturer, String swVersion, List<String> services,
        Map<String, Object> capabilities, Map<String, String> topics)
    {
        this.deviceId = deviceId;
        this.name = name;
        this.model = model;
        this.manufacturer = manufacturer;
        this.swVersion = swVersion;
        this.services = services;
        this.capabilities = capabilities;
        this.topics = topics;
    }

    /**
     * Convert to JSON for MQTT publication
     */
    public JsonObject toJson()
    {
        JsonObject json = new JsonObject();

        // Device metadata
        JsonObject device = new JsonObject();
        JsonArray identifiers = new JsonArray();
        identifiers.add(deviceId);
        device.add("identifiers", identifiers);
        device.addProperty("name", name);
        device.addProperty("model", model);
        device.addProperty("manufacturer", manufacturer);
        device.addProperty("sw_version", swVersion);
        json.add("device", device);

        // Services
        JsonArray servicesArray = new JsonArray();
        services.forEach(servicesArray::add);
        json.add("services", servicesArray);

        // Capabilities
        JsonObject caps = new JsonObject();
        capabilities.forEach((key, value) -> {
            if(value instanceof String)
            {
                caps.addProperty(key, (String)value);
            }else if(value instanceof Number)
            {
                caps.addProperty(key, (Number)value);
            }else if(value instanceof Boolean)
            {
                caps.addProperty(key, (Boolean)value);
            }
        });
        json.add("capabilities", caps);

        // Topics
        JsonObject topicsObj = new JsonObject();
        topics.forEach(topicsObj::addProperty);
        json.add("topics", topicsObj);

        return json;
    }

    // Getters

    public String getDeviceId()
    {
        return deviceId;
    }

    public String getName()
    {
        return name;
    }

    public List<String> getServices()
    {
        return services;
    }
}
