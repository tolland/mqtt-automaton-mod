package org.limepepper.mqttbot.mqtt;

public interface MessageHandler {
    boolean canHandle(MessageData msg);
    
    void handle(MessageData msg) throws Exception;
    
}
