package org.limepepper.mqttbot.action;

import java.util.*;

public final class FeatureRegistry {
    
    private final Map<Class<? extends Feature>, Feature> features =
        new HashMap<>();
    private final Set<Class<? extends Feature>> enabled = new HashSet<>();
    
    public <T extends Feature> void register(T feature)
    {
        features.put(feature.getClass(), feature);
    }
    
    public void enable(Class<? extends Feature> cls)
    {
        Feature f = features.get(cls);
        if(f != null && enabled.add(cls))
        {
            f.onEnable();
        }
    }
    
    public void disable(Class<? extends Feature> cls)
    {
        Feature f = features.get(cls);
        if(f != null && enabled.remove(cls))
        {
            f.onDisable();
        }
    }
    
    public boolean isEnabled(Class<? extends Feature> cls)
    {
        return enabled.contains(cls);
    }
    
    public Collection<Feature> all()
    {
        return features.values();
    }
}
