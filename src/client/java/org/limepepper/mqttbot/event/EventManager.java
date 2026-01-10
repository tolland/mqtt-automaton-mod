package org.limepepper.mqttbot.event;

import org.limepepper.mqttbot.util.MqttBotLogger;
import net.minecraft.ReportedException;
import net.minecraft.CrashReport;
import net.minecraft.CrashReportCategory;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Objects;

public final class EventManager {
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(EventManager.class);
    public static EventManager INSTANCE = new EventManager();
    
    private final HashMap<Class<? extends Listener>, ArrayList<? extends Listener>> listenerMap =
        new HashMap<>();
    
    private EventManager()
    {
        
    }
    
    public static <L extends Listener, E extends Event<L>> void fire(E event)
    {
        INSTANCE.fireImpl(event);
    }
    
    private <L extends Listener, E extends Event<L>> void fireImpl(E event)
    {
        
        try
        {
            Class<L> type = event.getListenerType();
            @SuppressWarnings("unchecked")
            ArrayList<L> listeners = (ArrayList<L>)listenerMap.get(type);
            
            LOGGER.debugEvents("EventManager.fireImpl - Event type: {}",
                type.getName());
            LOGGER.debugEvents("Listeners found: {}",
                (listeners != null ? listeners.size() : "null"));
            if(listeners != null)
            {
                for(int i = 0; i < listeners.size(); i++)
                {
                    L listener = listeners.get(i);
                    if(listener != null)
                    {
                        LOGGER.debugEvents("Listener {}: {}", i,
                            listener.getClass().getName());
                    }else
                    {
                        LOGGER.debugEvents("Listener {}: NULL", i);
                    }
                }
            }
            
            if(listeners == null || listeners.isEmpty())
                return;
                
            // Creating a copy of the list to avoid concurrent modification
            // issues.
            ArrayList<L> listeners2 = new ArrayList<>(listeners);
            
            // remove() sets an element to null before removing it. When one
            // thread calls remove() while another calls fire(), it is possible
            // for this list to contain null elements, which need to be filtered
            // out.
            int nullCount = 0;
            for(L listener : listeners2)
            {
                if(listener == null)
                    nullCount++;
            }
            if(nullCount > 0)
            {
                LOGGER.warn("Found {} null listeners, filtering them out",
                    nullCount);
            }
            
            listeners2.removeIf(Objects::isNull);
            
            LOGGER.debugEvents("After filtering nulls, listeners count: {}",
                listeners2.size());
            if(!listeners2.isEmpty())
            {
                LOGGER.debugEvents("About to fire event to {} listeners",
                    listeners2.size());
                event.fire(listeners2);
                LOGGER.debugEvents("Event fired successfully");
            }else
            {
                LOGGER.debugEvents(
                    "No valid listeners remaining after null filtering!");
            }
            
        }catch(Throwable e)
        {
            LOGGER.error("Error firing MqttBot event: {}",
                event.getClass().getName(), e);
            
            String message = "Firing MqttBot event";
            CrashReport report = CrashReport.forThrowable(e, message);
            
            CrashReportCategory section = report.addCategory("Affected event");
            section.setDetail("Event class", () -> event.getClass().getName());
            
            throw new ReportedException(report);
        }
    }
    
    public <L extends Listener> void add(Class<L> type, L listener)
    {
        try
        {
            @SuppressWarnings("unchecked")
            ArrayList<L> listeners = (ArrayList<L>)listenerMap.get(type);
            
            if(listeners == null)
            {
                listeners = new ArrayList<>(Arrays.asList(listener));
                listenerMap.put(type, listeners);
                return;
            }
            
            listeners.add(listener);
            
        }catch(Throwable e)
        {
            LOGGER.error("Error adding event listener: {} -> {}",
                type.getName(), listener.getClass().getName(), e);
            
            String message = "Adding MqttBot event listener";
            CrashReport report = CrashReport.forThrowable(e, message);
            
            CrashReportCategory section =
                report.addCategory("Affected listener");
            section.setDetail("Listener type", type::getName);
            section.setDetail("Listener class",
                () -> listener.getClass().getName());
            
            throw new ReportedException(report);
        }
    }
    
    public <L extends Listener> void remove(Class<L> type, L listener)
    {
        try
        {
            @SuppressWarnings("unchecked")
            ArrayList<L> listeners = (ArrayList<L>)listenerMap.get(type);
            
            if(listeners != null)
                listeners.remove(listener);
            
        }catch(Throwable e)
        {
            LOGGER.error("Error removing event listener: {} -> {}",
                type.getName(), listener.getClass().getName(), e);
            
            String message = "Removing MqttBot event listener";
            CrashReport report = CrashReport.forThrowable(e, message);
            
            CrashReportCategory section =
                report.addCategory("Affected listener");
            section.setDetail("Listener type", type::getName);
            section.setDetail("Listener class",
                () -> listener.getClass().getName());
            
            throw new ReportedException(report);
        }
    }
    
}
