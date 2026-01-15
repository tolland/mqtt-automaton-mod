package org.limepepper.mqttbot.util;

import com.google.gson.JsonObject;
import org.limepepper.mqttbot.mqtt.MessageData;

public enum MsgUtils {
    INSTANCE;

    public static String formatMessage(String botId, String method, String params) {
        return String.format("{\"botId\": \"%s\", \"method\": \"%s\", \"params\": \"%s\"}", botId, method, params);
    }

    public static MessageData msgData(
            String service,
            String method,
            JsonObject params
    ) {
        MessageData msgData = new MessageData();
        msgData.setService(service);
        msgData.setMethod(method);
        msgData.setParams(params);
        return msgData;
    }
}
