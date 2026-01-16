package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;
import com.google.gson.JsonSyntaxException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class BaritoneCollectHandlerDeserializerStringInputTest {
    
    private final Gson gson = new GsonBuilder()
        .registerTypeAdapter(
            BaritoneCollectHandler.BaritoneCollectCommand.class,
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer())
        .create();
    
    @Test
    void validJsonStringParsesToCommand()
    {
        String json = "{\"block\":\"minecraft:stone\",\"range\":10}";
        
        BaritoneCollectHandler.BaritoneCollectCommand cmd = gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class);
        
        assertNotNull(cmd);
        assertEquals("minecraft:stone", cmd.block());
        assertEquals(10, cmd.range());
    }
    
    @Test
    void paramsLiteralNullReturnsNull()
    {
        String json = "null";
        
        BaritoneCollectHandler.BaritoneCollectCommand cmd = gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class);
        
        assertNull(cmd);
    }
    
    @Test
    void emptyStringReturnsNull()
    {
        String json = "";
        
        // Gson returns null for empty input rather than throwing in this
        // environment/configuration; assert null result
        BaritoneCollectHandler.BaritoneCollectCommand cmd = gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class);
        assertNull(cmd);
    }
    
    @Test
    void malformedJsonThrowsJsonSyntaxException()
    {
        String json = "{ invalid json ";
        
        assertThrows(JsonSyntaxException.class, () -> gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class));
    }
    
    @Test
    void missingBlockThrowsJsonParseException()
    {
        String json = "{\"range\":10}";
        
        assertThrows(JsonParseException.class, () -> gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class));
    }
    
    @Test
    void rangeAsStringParsesToInt()
    {
        String json = "{\"block\":\"minecraft:stone\",\"range\":\"15\"}";
        
        BaritoneCollectHandler.BaritoneCollectCommand cmd = gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class);
        
        assertNotNull(cmd);
        assertEquals("minecraft:stone", cmd.block());
        assertEquals(15, cmd.range());
    }
    
    @Test
    void invalidRangeStringThrowsNumberFormatException()
    {
        String json = "{\"block\":\"minecraft:stone\",\"range\":\"invalid\"}";
        
        assertThrows(NumberFormatException.class, () -> gson.fromJson(json,
            BaritoneCollectHandler.BaritoneCollectCommand.class));
    }
}
