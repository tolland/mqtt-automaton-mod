package org.limepepper.mqttbot.mqtt;

public interface MessageHandler {
    boolean canHandle(ServiceMessage msg);
    
    void handle(ServiceMessage msg) throws Exception;
    
}
