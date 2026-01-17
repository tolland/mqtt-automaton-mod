package org.limepepper.mqttbot.integrations.command;

import org.limepepper.mqttbot.util.MqttBotLogger;

import static org.junit.jupiter.api.Assertions.*;

class SendCommandHandlerTest {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(SendCommandHandlerTest.class);
    
    @org.junit.jupiter.api.BeforeEach
    void setUp()
    {}
    
    @org.junit.jupiter.api.AfterEach
    void tearDown()
    {}
    
    @org.junit.jupiter.api.Test
    void onMessageArrived()
    {
        // dummy test
        LOGGER.debug("onMessageArrived");
    }
}
