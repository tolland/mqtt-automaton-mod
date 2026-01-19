package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import org.limepepper.mqttbot.mqtt.ServiceMessage;
import org.mockito.Mockito;

import static org.junit.jupiter.api.Assertions.*;

class BaritoneCollectHandlerParamsFlowTest {
    
    private final Gson gson = new GsonBuilder()
        .registerTypeAdapter(
            BaritoneCollectHandler.BaritoneCollectCommand.class,
            new BaritoneCollectHandler.BaritoneCollectCommandDeserializer())
        .create();
    
    @Test
    void validJsonParamsParsesToCommand()
    {
        ServiceMessage msg = Mockito.mock(ServiceMessage.class);
        JsonObject obj = new JsonObject();
        obj.addProperty("block", "minecraft:stone");
        obj.addProperty("range", 10);
        Mockito.when(msg.getParams()).thenReturn(obj);
        
        BaritoneCollectHandler.BaritoneCollectCommand cmd =
            gson.fromJson(msg.getParams(),
                BaritoneCollectHandler.BaritoneCollectCommand.class);
        
        assertNotNull(cmd);
        assertEquals("minecraft:stone", cmd.block());
        assertEquals(10, cmd.range());
    }
    
    @Test
    void emptyParamsThrowsJsonParseException()
    {
        // ServiceMessage.getParams() has type JsonElement, so return an empty
        // object
        // to simulate params being present but empty.
        ServiceMessage msg = Mockito.mock(ServiceMessage.class);
        JsonObject empty = new JsonObject();
        Mockito.when(msg.getParams()).thenReturn(empty);
        
        assertThrows(JsonParseException.class,
            () -> gson.fromJson(msg.getParams(),
                BaritoneCollectHandler.BaritoneCollectCommand.class));
    }
    
    @Test
    void nullParamsReturnsNull()
    {
        ServiceMessage msg = Mockito.mock(ServiceMessage.class);
        Mockito.when(msg.getParams()).thenReturn(null);
        
        // Gson.fromJson with a null JsonElement returns null (no exception)
        BaritoneCollectHandler.BaritoneCollectCommand cmd =
            gson.fromJson(msg.getParams(),
                BaritoneCollectHandler.BaritoneCollectCommand.class);
        
        assertNull(cmd);
    }
    
    @Test
    void missingBlockThrowsJsonParseException()
    {
        ServiceMessage msg = Mockito.mock(ServiceMessage.class);
        JsonObject obj = new JsonObject();
        obj.addProperty("range", 10);
        Mockito.when(msg.getParams()).thenReturn(obj);
        
        assertThrows(JsonParseException.class,
            () -> gson.fromJson(msg.getParams(),
                BaritoneCollectHandler.BaritoneCollectCommand.class));
    }
    
    @Test
    void rangeAsStringParsesToInt()
    {
        ServiceMessage msg = Mockito.mock(ServiceMessage.class);
        JsonObject obj = new JsonObject();
        obj.addProperty("block", "minecraft:stone");
        obj.addProperty("range", "15");
        Mockito.when(msg.getParams()).thenReturn(obj);
        
        BaritoneCollectHandler.BaritoneCollectCommand cmd =
            gson.fromJson(msg.getParams(),
                BaritoneCollectHandler.BaritoneCollectCommand.class);
        
        assertNotNull(cmd);
        assertEquals("minecraft:stone", cmd.block());
        assertEquals(15, cmd.range());
    }
    
    @Test
    void invalidRangeStringThrowsNumberFormatException()
    {
        ServiceMessage msg = Mockito.mock(ServiceMessage.class);
        JsonObject obj = new JsonObject();
        obj.addProperty("block", "minecraft:stone");
        obj.addProperty("range", "invalid");
        Mockito.when(msg.getParams()).thenReturn(obj);
        
        assertThrows(NumberFormatException.class,
            () -> gson.fromJson(msg.getParams(),
                BaritoneCollectHandler.BaritoneCollectCommand.class));
    }
}
