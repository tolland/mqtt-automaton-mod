package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Maintains a circular buffer of completed pathing requests for debugging and
 * analysis. When Baritone gets stuck or fails, this history helps diagnose
 * patterns and issues.
 */
public enum RequestHistory
{
    INSTANCE;
    
    private final Deque<PathingRequest> history = new ArrayDeque<>();
    private int maxHistorySize = 20; // Default, configurable
    
    /**
     * Records a completed request to history
     *
     * @param request
     *            The completed PathingRequest
     */
    public synchronized void recordRequest(PathingRequest request)
    {
        if(request == null)
        {
            return;
        }
        
        // Only record if request reached a terminal state
        if(!request.getPhase().isTerminal())
        {
            return;
        }
        
        history.addFirst(request);
        
        // Trim to max size
        while(history.size() > maxHistorySize)
        {
            history.removeLast();
        }
    }
    
    /**
     * Get the most recent N requests
     *
     * @param count
     *            Number of requests to retrieve
     * @return List of requests, most recent first
     */
    public synchronized List<PathingRequest> getRecent(int count)
    {
        return history.stream().limit(count).collect(Collectors.toList());
    }
    
    /**
     * Get all requests in history
     *
     * @return List of all requests, most recent first
     */
    public synchronized List<PathingRequest> getAll()
    {
        return List.copyOf(history);
    }
    
    /**
     * Clear all history
     */
    public synchronized void clear()
    {
        history.clear();
    }
    
    /**
     * Set maximum history size
     *
     * @param size
     *            Maximum number of requests to keep
     */
    public void setMaxHistorySize(int size)
    {
        this.maxHistorySize = Math.max(1, size);
    }
    
    /**
     * Dump history as formatted string for logging
     *
     * @return Multi-line string with request history
     */
    public synchronized String dumpHistory()
    {
        if(history.isEmpty())
        {
            return "No request history available";
        }
        
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("=== Recent Pathing Requests (%d) ===\n",
            history.size()));
        
        int i = 1;
        for(PathingRequest req : history)
        {
            sb.append(String.format("\n#%d: %s\n", i++, req.toString()));
            sb.append(String.format("  Target: %s\n", req.getTargetPos()));
            sb.append(
                String.format("  Phase: %s\n", req.getPhase()));
            sb.append(String.format("  Duration: %.1f seconds\n",
                req.getElapsedTime().toMillis() / 1000.0));
            
            if(req.getFailureReason() != null)
            {
                sb.append(
                    String.format("  Failure: %s\n", req.getFailureReason()));
            }
            
            // Include event timeline
            List<String> events = req.getEventTimeline();
            if(!events.isEmpty())
            {
                sb.append("  Timeline:\n");
                for(String event : events)
                {
                    sb.append("    ").append(event).append("\n");
                }
            }
        }
        
        return sb.toString();
    }
    
    /**
     * Dump history as JSON for MQTT transmission
     *
     * @return JsonArray of request objects
     */
    public synchronized JsonArray toJson()
    {
        JsonArray array = new JsonArray();
        for(PathingRequest req : history)
        {
            JsonObject json = req.toJson();
            
            // Add event timeline
            JsonArray events = new JsonArray();
            for(String event : req.getEventTimeline())
            {
                events.add(event);
            }
            json.add("timeline", events);
            
            array.add(json);
        }
        return array;
    }
    
    /**
     * Get statistics about recent requests
     *
     * @return JsonObject with stats
     */
    public synchronized JsonObject getStatistics()
    {
        JsonObject stats = new JsonObject();
        stats.addProperty("totalRequests", history.size());
        
        long successful =
            history.stream()
                .filter(r -> r.getPhase() == PathingPhase.GOAL_REACHED)
                .count();
        long failed =
            history.stream().filter(r -> r.getPhase() == PathingPhase.FAILED)
                .count();
        long stuck =
            history.stream().filter(r -> r.getPhase() == PathingPhase.STUCK)
                .count();
        long cancelled =
            history.stream().filter(r -> r.getPhase() == PathingPhase.CANCELLED)
                .count();
        
        stats.addProperty("successful", successful);
        stats.addProperty("failed", failed);
        stats.addProperty("stuck", stuck);
        stats.addProperty("cancelled", cancelled);
        
        if(!history.isEmpty())
        {
            double avgDuration = history.stream()
                .mapToLong(r -> r.getElapsedTime().getSeconds()).average()
                .orElse(0.0);
            stats.addProperty("avgDurationSeconds", avgDuration);
        }
        
        return stats;
    }
}
