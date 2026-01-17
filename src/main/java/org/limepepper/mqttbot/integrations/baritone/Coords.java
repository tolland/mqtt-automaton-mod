package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import org.jetbrains.annotations.NotNull;

public record Coords(float poxX, float poxY, float poxZ)
{
    
    private static final Gson gson = new Gson();
    
    @Override
    public @NotNull String toString()
    {
        return String.format("Coords{x=%.2f, y=%.2f, z=%.2f}", poxX, poxY,
            poxZ);
    }
    
    public JsonElement toJson()
    {
        return gson.toJsonTree(this);
    }
}
