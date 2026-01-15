package org.limepepper.mqttbot.util;

import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

public class JsonBuilder {
    public static JsonObject obj(String key, Object value, Object... rest) {
        JsonObject obj = new JsonObject();
        obj.add(key, toElement(value));

        for (int i = 0; i < rest.length; i += 2) {
            obj.add((String) rest[i], toElement(rest[i + 1]));
        }
        return obj;
    }

    private static JsonElement toElement(Object value) {
        if (value == null) return JsonNull.INSTANCE;
        if (value instanceof String) return new JsonPrimitive((String) value);
        if (value instanceof Number) return new JsonPrimitive((Number) value);
        if (value instanceof Boolean) return new JsonPrimitive((Boolean) value);
        if (value instanceof JsonElement) return (JsonElement) value;
        return new JsonPrimitive(value.toString());
    }
}
