package org.limepepper.mqttbot.integrations.baritone;

import com.google.gson.JsonObject;
import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.action.Action;
import org.limepepper.mqttbot.action.BaritonePathingFeature;
import org.limepepper.mqttbot.action.InventoryFullFeature;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.MqttReplyListener;
import org.limepepper.mqttbot.mqtt.MessageData;
import org.limepepper.mqttbot.mqtt.MessageHandler;
import org.limepepper.mqttbot.util.MqttBotLogger;

/**
 * Handler for Baritone cancel commands. Cancels any active pathing or collect
 * process.
 *
 * <p>
 * This is critical for request preemption - when the Python client needs to
 * interrupt the current operation (e.g., inventory full event during farming),
 * it sends a cancel command first.
 * </p>
 */
public final class BaritoneCancel extends Action implements MessageHandler
{
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(BaritoneCancel.class);

    private BaritoneCancel()
    {
        // Private constructor
    }

    public static BaritoneCancel create()
    {
        return new BaritoneCancel();
    }

    @Override
    public boolean canHandle(MessageData msg)
    {
        return "baritone".equals(msg.getService())
            && "cancel".equals(msg.getMethod());
    }

    @Override
    public void handle(MessageData msg) throws Exception
    {
        LOGGER.info("Received cancel request");

        // Get correlation IDs from request
        String requestId = msg.getRequestId();
        String correlationId = msg.getCorrelationId();
        String playerName = CORE.getPlayerName();

        // Check if there's an active pathing request
        PathingRequest activeRequest = PathingState.INSTANCE.getCurrentRequest();
        boolean hadActiveRequest = PathingState.INSTANCE.hasActiveRequest();

        if(hadActiveRequest)
        {
            LOGGER.info("Cancelling active request: {}", activeRequest);
            activeRequest.logEvent("CANCEL_REQUESTED", "Cancel command received");
            PathingState.INSTANCE.transitionTo(PathingPhase.CANCELLED);
        }

        // Cancel Baritone processes (idempotent - safe to call even if nothing
        // active)
        try
        {
            MqttCore.baritone.getPathingBehavior().cancelEverything();
            LOGGER.debug("Called Baritone cancelEverything()");
        }catch(Exception e)
        {
            LOGGER.warn("Error calling Baritone cancelEverything(): {}",
                e.getMessage());
        }

        // Disable features
        CORE.features().disable(InventoryFullFeature.class);
        CORE.features().disable(BaritonePathingFeature.class);

        // Set bot state to idle
        MqttCore.INSTANCE.setBotState(MqttCore.BotState.IDLE);

        // Send success response
        JsonObject response = new JsonObject();
        response.addProperty("status", "success");
        response.addProperty("message", hadActiveRequest
            ? "Cancelled active pathing request"
            : "No active request to cancel");
        response.addProperty("player", playerName);
        response.addProperty("hadActiveRequest", hadActiveRequest);

        if(hadActiveRequest && activeRequest != null)
        {
            response.addProperty("cancelledRequestId",
                activeRequest.getCorrelationIds().requestId());
            response.addProperty("wasInPhase",
                activeRequest.getPhase().toString());
        }

        MessageData responseData = new MessageData(Constants.SERVICE_NAME,
            "cancel", requestId, correlationId, null, response, playerName,
            null);

        EventManager
            .fire(new MqttReplyListener.MqttReplyEvent(playerName, responseData));

        LOGGER.info("Cancel completed: hadActiveRequest={}", hadActiveRequest);
    }
}
