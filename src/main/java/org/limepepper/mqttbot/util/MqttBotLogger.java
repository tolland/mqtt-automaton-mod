package org.limepepper.mqttbot.util;

import org.limepepper.mqttbot.config.MqttBotConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MqttBotLogger {
    private final Logger logger;
    private final MqttBotConfig config;
    
    public MqttBotLogger(String name)
    {
        this.logger = LoggerFactory.getLogger(name);
        this.config = MqttBotConfig.getInstance();
    }
    
    public MqttBotLogger(Class<?> clazz)
    {
        this(clazz.getName());
    }
    
    public void trace(String message, Object... args)
    {
        if(config.isLogLevelEnabled("TRACE"))
        {
            logger.trace(message, args);
        }
    }
    
    public void debug(String message, Object... args)
    {
        if(config.isLogLevelEnabled("DEBUG"))
        {
            logger.debug(message, args);
        }
    }
    
    public void info(String message, Object... args)
    {
        if(config.isLogLevelEnabled("INFO"))
        {
            logger.info(message, args);
        }
    }
    
    public void warn(String message, Object... args)
    {
        if(config.isLogLevelEnabled("WARN"))
        {
            logger.warn(message, args);
        }
    }
    
    public void error(String message, Object... args)
    {
        if(config.isLogLevelEnabled("ERROR"))
        {
            logger.error(message, args);
        }
    }
    
    public void error(String message, Throwable throwable)
    {
        if(config.isLogLevelEnabled("ERROR"))
        {
            logger.error(message, throwable);
        }
    }
    
    // Convenience methods for specific debug categories
    public void debugEvents(String message, Object... args)
    {
        if(config.isDebugEvents() && config.isLogLevelEnabled("DEBUG"))
        {
            logger.debug("[EVENTS] {} '{}'", message, args);
        }
    }
    
    public void debugMqtt(String message, Object... args)
    {
        // if(config.isDebugMqtt() && config.isLogLevelEnabled("DEBUG"))
        // {
        logger.debug("[MQTT] " + message, args);
        // }
    }
}
