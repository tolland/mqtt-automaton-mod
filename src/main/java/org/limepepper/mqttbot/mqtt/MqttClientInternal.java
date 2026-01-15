package org.limepepper.mqttbot.mqtt;

import net.minecraft.client.Minecraft;
import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.config.MqttBotConfig;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttMessageListener;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * backend class for interface with a paho MQTT client.
 * Allows switching connection to a different broker
 */
public class MqttClientInternal extends Action implements MqttReplyListener {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(MqttClientInternal.class);
    private final MqttBotConfig config = MqttBotConfig.getInstance();
    
    public static final MqttClientInternal INSTANCE = new MqttClientInternal();
    
    private MqttClientInternal()
    {
        LOGGER.info("Initializing MqttClientInternal");
        init();
    }
    
    MqttClient sampleClient;
    int qos = 2;
    
    public static final Minecraft MC = Minecraft.getInstance();
    
    void init()
    {
        LOGGER.info("Initializing MQTT client");
        LOGGER.debugMqtt("MqttClientInternal.init() called");
        String broker = config.getMqttBroker();
        qos = config.getMqttQos();
        MemoryPersistence persistence = new MemoryPersistence();
        
        Minecraft mc = Minecraft.getInstance();
        if(mc == null)
        {
            LOGGER.error("Minecraft.getInstance() returned null!");
            return;
        }
        if(mc.getUser() == null)
        {
            LOGGER.error("mc.getUser() returned null!");
            return;
        }
        String clientId = mc.getUser().getName();
        LOGGER.info("MQTT ClientId: {}", clientId);
        
        try
        {
            LOGGER.debugMqtt("Creating MQTT client for user: {}",
                mc.getUser().getName());
            
            sampleClient = new MqttClient(broker, clientId, persistence);
            MqttConnectOptions connOpts = new MqttConnectOptions();
            connOpts.setCleanSession(true);
            
            sampleClient.setCallback(new MqttCallback()
            {
                public void connectionLost(Throwable cause)
                {
                    LOGGER.warn("MQTT connection lost", cause);
                }
                
                public void messageArrived(String topic, MqttMessage message)
                    throws Exception
                {
                    LOGGER.debugMqtt("MQTT message received on topic {}: {}",
                        topic, message.toString());
                    handleMqttMessage(topic, message.toString());
                }
                
                public void deliveryComplete(IMqttDeliveryToken token)
                {
                    LOGGER.debugMqtt("MQTT message delivery complete");
                }
            });
            
            sampleClient.connect(connOpts);
            LOGGER.info("Connected to MQTT broker: {}", broker);
            
            // all command messages
            sampleClient.subscribe("mqttbot/bots/command");
            // commands for this specific bot
            String clientTopic = String.format("mqttbot/%s/command", clientId);
            LOGGER.info("Subscribing to MQTT topics: mqttbot/bots/command, {}",
                clientTopic);
            sampleClient.subscribe(clientTopic);
            
            LOGGER.debugMqtt(
                "Registering MqttClientInternal as MqttReplyListener");
            EventManager.INSTANCE.add(MqttReplyListener.class, this);
            LOGGER.info("MqttClientInternal initialized successfully");
            
        }catch(MqttException e)
        {
            LOGGER.error("Failed to initialize MQTT client", e);
        }
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
        MessageData structuredMessage = MessageData.fromJson(rawMessage);
        
        if(structuredMessage != null && structuredMessage.isValid())
        {
            LOGGER
                .debug("Firing MqttMessageEvent for valid structured message");
            EventManager.fire(new MqttMessageListener.MqttMessageEvent(botId,
                structuredMessage));
        }else
        {
            // Fallback: try to handle as legacy format based on topic
            LOGGER.warn("Received invalid/legacy message format: {}",
                rawMessage);
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
            sampleClient.publish(topic, mqttMessage);
            LOGGER.debugMqtt("Message published successfully to {}", topic);
            
        }catch(MqttException me)
        {
            LOGGER.error(
                "Failed to publish MQTT message to topic {}: {} (reason: {}, cause: {})",
                topic, me.getMessage(), me.getReasonCode(), me.getCause(), me);
        }
    }
    
    @Override
    public void onReplyArrived(MqttReplyEvent mqttReplyEvent)
    {
        LOGGER.debug("Handling MqttReplyEvent for bot: {}",
            mqttReplyEvent.botId);
        LOGGER.debugMqtt("Reply data: {}", mqttReplyEvent.messageData.toJson());
        publish("mqttbot/" + mqttReplyEvent.botId + "/reply",
            mqttReplyEvent.messageData.toJson());
    }
}
