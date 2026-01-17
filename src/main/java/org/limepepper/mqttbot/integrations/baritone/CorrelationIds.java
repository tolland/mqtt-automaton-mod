package org.limepepper.mqttbot.integrations.baritone;

import org.jetbrains.annotations.NotNull;
import org.limepepper.mqttbot.mqtt.MessageData;

import java.util.Objects;

/**
 * Immutable value object for correlation tracking IDs. Provides type-safe,
 * validated container for requestId and correlationId. This ensures these
 * critical fields are never null or empty, failing fast at construction time
 * rather than allowing bugs to propagate.
 *
 * <p>
 * This replaces the fragile global singleton pattern with proper value-based
 * correlation tracking that can be owned by tasks/handlers.
 * </p>
 *
 * @param requestId
 *            Unique identifier for this specific request (non-null, non-empty)
 * @param correlationId
 *            Identifier linking related requests together (non-null,
 *            non-empty)
 */
public record CorrelationIds(@NotNull String requestId,
    @NotNull String correlationId)
{

    /**
     * Compact constructor with validation. Ensures both IDs are non-null and
     * non-empty.
     *
     * @throws NullPointerException
     *             if either ID is null
     * @throws IllegalArgumentException
     *             if either ID is empty/blank
     */
    public CorrelationIds
    {
        Objects.requireNonNull(requestId,
            "requestId cannot be null - this indicates a protocol violation");
        Objects.requireNonNull(correlationId,
            "correlationId cannot be null - this indicates a protocol violation");

        if(requestId.trim().isEmpty())
        {
            throw new IllegalArgumentException(
                "requestId cannot be empty - this indicates a protocol violation");
        }
        if(correlationId.trim().isEmpty())
        {
            throw new IllegalArgumentException(
                "correlationId cannot be empty - this indicates a protocol violation");
        }
    }

    /**
     * Extracts and validates correlation IDs from an incoming MQTT message.
     * This is the primary factory method for creating CorrelationIds from
     * incoming requests.
     *
     * @param msg
     *            The incoming MQTT message
     * @return Validated CorrelationIds
     * @throws NullPointerException
     *             if msg is null or IDs are null
     * @throws IllegalArgumentException
     *             if IDs are empty/blank
     */
    public static CorrelationIds fromMessage(@NotNull MessageData msg)
    {
        Objects.requireNonNull(msg, "MessageData cannot be null");
        return new CorrelationIds(msg.getRequestId(), msg.getCorrelationId());
    }
}
