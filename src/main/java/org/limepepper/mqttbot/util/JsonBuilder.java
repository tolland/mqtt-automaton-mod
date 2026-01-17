package org.limepepper.mqttbot.util;

import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

public class JsonBuilder {
    public static JsonObject obj(String key, Object value, Object... rest)
    {
        JsonObject obj = new JsonObject();
        obj.add(key, toElement(value));
        
        for(int i = 0; i < rest.length; i += 2)
        {
            obj.add((String)rest[i], toElement(rest[i + 1]));
        }
        return obj;
    }
    
    private static JsonElement toElement(Object value)
    {
        return switch(value)
        {
            case null -> JsonNull.INSTANCE;
            case String s -> new JsonPrimitive(s);
            case Number number -> new JsonPrimitive(number);
            case Boolean b -> new JsonPrimitive(b);
            case JsonElement jsonElement -> jsonElement;
            default -> new JsonPrimitive(value.toString());
        };
    }
}
