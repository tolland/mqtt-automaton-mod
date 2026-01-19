package org.limepepper.mqttbot.mqtt;

import net.minecraft.client.Minecraft;
import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.config.MqttBotConfig;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.presence.DeviceConfig;
import org.limepepper.mqttbot.presence.DevicePresence;
import org.limepepper.mqttbot.util.MqttBotLogger;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * backend class for interface with a paho MQTT client.
 * Allows switching connection to a different broker
 */
public class MqttClientInternal extends Action
    implements MqttReplyListener {
    
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(MqttClientInternal.class);
    
    private MqttClient mqttClient;
    int qos = 2;
    private DevicePresence presence;
    
    private final MqttBotConfig config = MqttBotConfig.getInstance();
    
    public static final MqttClientInternal INSTANCE = new MqttClientInternal();
    
    private MqttClientInternal()
    {
        LOGGER.info("Initializing MqttClientInternal");
        try
        {
            init();
        }catch(MqttException e)
        {
            LOGGER.error("Failed to initialize MQTT client: {}", e.getMessage(),
                e);
        }
    }
    
    public static final Minecraft MC = Minecraft.getInstance();
    
    void init() throws MqttException
    {
        LOGGER.info("Initializing MQTT client");
        LOGGER.debugMqtt("MqttClientInternal.init() called");
        String broker = config.getMqttBroker();
        qos = config.getMqttQos();
        MemoryPersistence persistence = new MemoryPersistence();
        
        LOGGER.debugMqtt("Creating MQTT client for user: {}",
            CORE.getPlayerName());
        
        mqttClient = new MqttClient(broker, CORE.getPlayerName(), persistence);
        
        LOGGER.info("MQTT ClientId: {}", CORE.getPlayerName());
        
        presence =
            DevicePresence.createInstance(CORE.getPlayerName(), mqttClient);
        MqttConnectOptions connOpts = presence.createConnectionOptions();
        
        mqttClient.setCallback(new MqttCallback()
        {
            public void connectionLost(Throwable cause)
            {
                LOGGER.warn("MQTT connection lost", cause);
            }
            
            public void messageArrived(String topic, MqttMessage message)
            {
                if(message.toString() == null
                    || message.toString().isEmpty())
                {
                    LOGGER.debugMqtt(
                        "Ignoring empty MQTT message on topic {}",
                        topic);
                    return;
                }
                LOGGER.debugMqtt(
                    "MQTT message received on topic {}: {} - isRetained: {}",
                    topic, message.toString(), message.isRetained());
                handleMqttMessage(topic, message.toString());
            }
            
            public void deliveryComplete(IMqttDeliveryToken token)
            {
                LOGGER.debugMqtt("MQTT message delivery complete");
            }
        });
        
        mqttClient.connect(connOpts);
        LOGGER.info("Connected to MQTT broker: {}", broker);
        
        // all command messages
        mqttClient.subscribe("mqttbot/*/command");
        // commands for this specific bot
        String clientTopic =
            String.format("mqttbot/%s/command", CORE.getPlayerName());
        LOGGER.info("Subscribing to MQTT topics: mqttbot/bots/command, {}",
            clientTopic);
        mqttClient.subscribe(clientTopic);
        
        LOGGER.debugMqtt(
            "Registering MqttClientInternal as MqttReplyListener");
        EventManager.INSTANCE.add(MqttReplyListener.class, this);
        
        // Immediately announce we're online
        String connectionId = UUID.randomUUID().toString();
        presence.announceOnline(connectionId);
        
        // Publish device configuration
        publishDeviceConfig();
        
        LOGGER.info("MqttClientInternal initialized successfully");
    }
    
    private void publishDeviceConfig() throws MqttException
    {
        DeviceConfig config = new DeviceConfig(
            CORE.getPlayerName(),
            CORE.getPlayerName(), // name
            "MinecraftClient", // model
            "mqttbot-mod", // manufacturer
            "1.0.0", // sw_version
            List.of(
                "baritone.goto",
                "baritone.cancel",
                "inventory.query",
                "inventory.drop"),
            Map.of(
                "max_concurrent_tasks", 1,
                "supports_correlation_ids", true,
                "baritone_version", "1.21.8"),
            Map.of(
                "command", "mqttbot/" + CORE.getPlayerName() + "/command",
                "events", "mqttbot/" + CORE.getPlayerName() + "/events",
                "availability", presence.getAvailabilityTopic(),
                "readiness", presence.getReadinessTopic()));
        
        presence.publishConfig(config);
    }
    
    public void shutdown() throws MqttException
    {
        // Gracefully announce offline before disconnecting
        presence.announceOffline();
        mqttClient.disconnect();
    }
    
    /**
     * Messages from mod services router back here to be published to MQTT
     * broker
     *
     * @param event
     *            event containing reply data in {@link ServiceMessage} format
     */
    @Override
    public void onReplyArrived(MqttReplyEvent event)
    {
        LOGGER.debug("Handling MqttReplyEvent for bot: {}",
            event.botId);
        LOGGER.debugMqtt("Reply data: {}", event.serviceMessage.toJson());
        var msg = event.serviceMessage;
        var botId = event.botId;
        var topic = String.format("mqttbot/%s/%s", botId, event.topic);
        publish(topic, msg.toJson());
    }
    
    /**
     * Handle incoming MQTT messages and route them to appropriate services
     *
     * @param topic
     *            The MQTT topic the message was received on
     * @param rawMessage
     *            The raw message content (expected to be JSON)
     */
    public void handleMqttMessage(String topic, String rawMessage)
    {
        LOGGER.debugMqtt("Handling MQTT message on topic: {}", topic);
        if(!topic.startsWith("mqttbot"))
            return;
        if(!topic.endsWith("command"))
            return;
        String botId = topic.split("/")[1]; // Extracts 'Player123' from
        // 'mqttbot/Player123/command'
        LOGGER.debugMqtt("Raw message for bot {}: {}", botId, rawMessage);
        
        // Try to parse as structured JSON message first
        ServiceMessage structuredMessage = ServiceMessage.fromJson(rawMessage);
        
        if(structuredMessage != null && structuredMessage.isValid())
        {
            LOGGER
                .debug("Firing MqttMessageEvent for valid structured message");
            EventManager.fire(new MqttMessageListener.MqttMessageEvent(botId,
                structuredMessage));
        }else
        {
            // Fallback: try to handle as legacy format based on topic
            LOGGER.warn(
                "Received invalid/legacy message format: '{}' on topic: {}",
                rawMessage, topic);
            throw new IllegalArgumentException(
                "Invalid or unsupported MQTT message format");
        }
    }
    
    public void publish(String topic, String message)
    {
        LOGGER.debugMqtt("Publishing MQTT message to topic: {}", topic);
        
        try
        {
            LOGGER.debugMqtt("Message content: {}", message);
            MqttMessage mqttMessage = new MqttMessage(message.getBytes());
            mqttMessage.setQos(qos);
            mqttClient.publish(topic, mqttMessage);
            LOGGER.debugMqtt("Message published successfully to {}", topic);
            
        }catch(MqttException me)
        {
            LOGGER.error(
                "Failed to publish MQTT message to topic {}: {} (reason: {}, cause: {})",
                topic, me.getMessage(), me.getReasonCode(), me.getCause(), me);
        }
    }
    
}
