package org.limepepper.mqttbot.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.yaml.snakeyaml.Yaml;

import java.io.FileInputStream;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;

public class MqttBotConfig {
    private static final Logger LOGGER =
        LoggerFactory.getLogger("mqttbot-config");
    private static MqttBotConfig instance;
    
    private String logLevel = "INFO";
    private String mqttBroker = "tcp://mosquitto.lan:1883";
    private int mqttQos = 2;
    private boolean debugEvents = false;
    private boolean debugMqtt = true;
    
    private MqttBotConfig()
    {
        loadConfig();
    }
    
    public static MqttBotConfig getInstance()
    {
        if(instance == null)
        {
            instance = new MqttBotConfig();
        }
        return instance;
    }
    
    private void loadConfig()
    {
        try
        {
            Path configPath = Paths.get("config.yml");
            
            if(!Files.exists(configPath))
            {
                LOGGER.info("Config file not found at {}, using defaults",
                    configPath.toAbsolutePath());
                return;
            }
            
            Yaml yaml = new Yaml();
            try(InputStream inputStream =
                new FileInputStream(configPath.toFile()))
            {
                Map<String, Object> data = yaml.load(inputStream);
                
                if(data != null)
                {
                    // Load log level
                    if(data.containsKey("log_level"))
                    {
                        logLevel = (String)data.get("log_level");
                        LOGGER.info("Loaded log level: {}", logLevel);
                    }
                    
                    // Load MQTT config
                    @SuppressWarnings("unchecked")
                    Map<String, Object> mqttConfig =
                        (Map<String, Object>)data.get("mqtt");
                    if(mqttConfig != null)
                    {
                        if(mqttConfig.containsKey("broker"))
                        {
                            mqttBroker = (String)mqttConfig.get("broker");
                        }
                        if(mqttConfig.containsKey("qos"))
                        {
                            mqttQos = (Integer)mqttConfig.get("qos");
                        }
                    }
                    
                    // Load bot config
                    @SuppressWarnings("unchecked")
                    Map<String, Object> botConfig =
                        (Map<String, Object>)data.get("bot");
                    if(botConfig != null)
                    {
                        if(botConfig.containsKey("debug_events"))
                        {
                            debugEvents =
                                (Boolean)botConfig.get("debug_events");
                        }
                        if(botConfig.containsKey("debug_mqtt"))
                        {
                            debugMqtt = (Boolean)botConfig.get("debug_mqtt");
                        }
                    }
                }
                
                LOGGER.info("Configuration loaded successfully");
            }
        }catch(Exception e)
        {
            LOGGER.error("Failed to load config file, using defaults", e);
        }
    }
    
    public String getLogLevel()
    {
        return logLevel;
    }
    
    public String getMqttBroker()
    {
        return mqttBroker;
    }
    
    public int getMqttQos()
    {
        return mqttQos;
    }
    
    public boolean isDebugEvents()
    {
        return debugEvents;
    }
    
    public boolean isDebugMqtt()
    {
        return debugMqtt;
    }
    
    public boolean isLogLevelEnabled(String level)
    {
        return getLogLevelValue(level) >= getLogLevelValue(logLevel);
    }
    
    private int getLogLevelValue(String level)
    {
        return switch(level.toUpperCase())
        {
            case "TRACE" -> 0;
            case "DEBUG" -> 1;
            case "INFO" -> 2;
            case "WARN" -> 3;
            case "ERROR" -> 4;
            default -> 2; // Default to INFO
        };
    }
}
