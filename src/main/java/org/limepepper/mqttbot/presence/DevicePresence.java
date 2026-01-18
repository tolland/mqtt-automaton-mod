package org.limepepper.mqttbot.presence;

import com.google.gson.JsonObject;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.nio.charset.StandardCharsets;
import java.time.Instant;

/**
 * Generic MQTT device presence/liveness manager following Home Assistant
 * discovery pattern.
 *
 * <p>
 * Manages:
 * <ul>
 * <li>Availability (online/offline) with LWT</li>
 * <li>Device configuration (capabilities)</li>
 * <li>Readiness state (can accept tasks)</li>
 * <li>Optional heartbeat for fast detection</li>
 * </ul>
 * </p>
 */
public class DevicePresence
{
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(DevicePresence.class);

    private final String deviceId;
    private final String baseTopic;
    private final MqttClient mqttClient;

    private String availabilityTopic;
    private String configTopic;
    private String readinessTopic;
    private String stateTopic;
    private String heartbeatTopic;

    /**
     * Create device presence manager
     *
     * @param deviceId
     *            Unique device identifier (e.g., player name)
     * @param mqttClient
     *            Connected MQTT client
     */
    public DevicePresence(String deviceId, MqttClient mqttClient)
    {
        this.deviceId = deviceId;
        this.baseTopic = "mqttbot/" + deviceId;
        this.mqttClient = mqttClient;

        this.availabilityTopic = baseTopic + "/availability";
        this.configTopic = baseTopic + "/config";
        this.readinessTopic = baseTopic + "/readiness";
        this.stateTopic = baseTopic + "/state";
        this.heartbeatTopic = baseTopic + "/heartbeat";
    }

    /**
     * Setup MQTT connection with LWT (Last Will and Testament)
     *
     * @return MqttConnectOptions configured with LWT
     */
    public MqttConnectOptions createConnectionOptions()
    {
        MqttConnectOptions options = new MqttConnectOptions();
        options.setCleanSession(false); // Persistent session
        options.setAutomaticReconnect(true);
        options.setKeepAliveInterval(20); // 20 second keepalive
        options.setConnectionTimeout(10);

        // Set Last Will and Testament - published when connection drops
        JsonObject lwt = new JsonObject();
        lwt.addProperty("state", "offline");
        lwt.addProperty("timestamp", Instant.now().toString());

        options.setWill(availabilityTopic,
            lwt.toString().getBytes(StandardCharsets.UTF_8), 1, // QoS 1
            true // Retained
        );

        LOGGER.info("Created MQTT connection options with LWT on topic: {}",
            availabilityTopic);

        return options;
    }

    /**
     * Announce device is online (call immediately after connecting)
     *
     * @param connectionId
     *            Unique connection identifier
     * @throws MqttException
     *             if publish fails
     */
    public void announceOnline(String connectionId) throws MqttException
    {
        JsonObject availability = new JsonObject();
        availability.addProperty("state", "online");
        availability.addProperty("timestamp", Instant.now().toString());
        availability.addProperty("connection_id", connectionId);

        publish(availabilityTopic, availability, 1, true);
        LOGGER.info("Announced device online: {}", deviceId);
    }

    /**
     * Announce device is offline (call before disconnecting)
     *
     * @throws MqttException
     *             if publish fails
     */
    public void announceOffline() throws MqttException
    {
        JsonObject availability = new JsonObject();
        availability.addProperty("state", "offline");
        availability.addProperty("timestamp", Instant.now().toString());

        publish(availabilityTopic, availability, 1, true);
        LOGGER.info("Announced device offline: {}", deviceId);
    }

    /**
     * Publish device configuration (capabilities, services, etc)
     *
     * @param config
     *            Device configuration object
     * @throws MqttException
     *             if publish fails
     */
    public void publishConfig(DeviceConfig config) throws MqttException
    {
        publish(configTopic, config.toJson(), 1, true);
        LOGGER.debug("Published device config for: {}", deviceId);
    }

    /**
     * Publish readiness state
     *
     * @param state
     *            Current readiness state
     * @throws MqttException
     *             if publish fails
     */
    public void publishReadiness(ReadinessState state) throws MqttException
    {
        publish(readinessTopic, state.toJson(), 1, false);
        LOGGER.debug("Published readiness: {} (can_accept_tasks={})", state,
            state.canAcceptTasks());
    }

    /**
     * Publish detailed state (for monitoring/debugging)
     *
     * @param state
     *            Full device state
     * @throws MqttException
     *             if publish fails
     */
    public void publishState(JsonObject state) throws MqttException
    {
        state.addProperty("timestamp", Instant.now().toString());
        publish(stateTopic, state, 0, false); // QoS 0 for frequent updates
    }

    /**
     * Publish heartbeat (for fast liveness detection)
     *
     * @param sequence
     *            Sequence number
     * @throws MqttException
     *             if publish fails
     */
    public void publishHeartbeat(long sequence) throws MqttException
    {
        JsonObject heartbeat = new JsonObject();
        heartbeat.addProperty("timestamp", Instant.now().toString());
        heartbeat.addProperty("sequence", sequence);

        publish(heartbeatTopic, heartbeat, 0, false);
    }

    /**
     * Helper to publish JSON object
     */
    private void publish(String topic, JsonObject payload, int qos,
        boolean retained) throws MqttException
    {
        MqttMessage message = new MqttMessage(
            payload.toString().getBytes(StandardCharsets.UTF_8));
        message.setQos(qos);
        message.setRetained(retained);

        mqttClient.publish(topic, message);
    }

    // Getters

    public String getDeviceId()
    {
        return deviceId;
    }

    public String getAvailabilityTopic()
    {
        return availabilityTopic;
    }

    public String getConfigTopic()
    {
        return configTopic;
    }

    public String getReadinessTopic()
    {
        return readinessTopic;
    }

    public String getStateTopic()
    {
        return stateTopic;
    }

    public String getHeartbeatTopic()
    {
        return heartbeatTopic;
    }
}
