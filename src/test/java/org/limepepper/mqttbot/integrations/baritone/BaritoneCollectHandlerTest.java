package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.JsonParseException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import com.google.gson.JsonObject;

import static org.junit.jupiter.api.Assertions.*;

class BaritoneCollectHandlerTest {
    
    @BeforeEach
    void setUp()
    {}
    
    @AfterEach
    void tearDown()
    {}
    
    @Test
    void create()
    {}
    
    @Test
    void canHandle()
    {}
    
    @Test
    void handle()
    {}
    
    @Test
    void deserializeValidJsonObject()
    {
        JsonObject json = new JsonObject();
        json.addProperty("block", "minecraft:stone");
        json.addProperty("range", 10);
        
        BaritoneCollectHandler.BaritoneCollectCommandDeserializer deserializer =
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer();
        
        BaritoneCollectHandler.BaritoneCollectCommand command =
            deserializer.deserialize(json, null, null);
        
        assertEquals("minecraft:stone", command.block());
        assertEquals(10, command.range());
    }
    
    @Test
    void deserializeJsonWithStringRange()
    {
        JsonObject json = new JsonObject();
        json.addProperty("block", "minecraft:stone");
        json.addProperty("range", "15");
        
        BaritoneCollectHandler.BaritoneCollectCommandDeserializer deserializer =
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer();
        
        BaritoneCollectHandler.BaritoneCollectCommand command =
            deserializer.deserialize(json, null, null);
        
        assertEquals("minecraft:stone", command.block());
        assertEquals(15, command.range());
    }
    
    @Test
    void deserializeJsonWithInvalidRangeThrowsException()
    {
        JsonObject json = new JsonObject();
        json.addProperty("block", "minecraft:stone");
        json.addProperty("range", "invalid");
        
        BaritoneCollectHandler.BaritoneCollectCommandDeserializer deserializer =
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer();
        
        assertThrows(NumberFormatException.class,
            () -> deserializer.deserialize(json, null, null));
    }
    
    @Test
    void deserializeJsonWithoutBlockThrowsException()
    {
        JsonObject json = new JsonObject();
        json.addProperty("range", 10);
        
        BaritoneCollectHandler.BaritoneCollectCommandDeserializer deserializer =
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer();
        
        assertThrows(JsonParseException.class,
            () -> deserializer.deserialize(json, null, null));
    }
    
    @Test
    void deserializeJsonWithNonPrimitiveRangeThrowsException()
    {
        JsonObject json = new JsonObject();
        json.addProperty("block", "minecraft:stone");
        json.add("range", new JsonObject());
        
        BaritoneCollectHandler.BaritoneCollectCommandDeserializer deserializer =
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer();
        
        assertThrows(JsonParseException.class,
            () -> deserializer.deserialize(json, null, null));
    }
}
