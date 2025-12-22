package org.limepepper.mqttbot.mqtt;

public class MessageEnvelope {

    private String sender;
    private String receiver;
    private MessageData messageData;
    private String timestamp; // ISO 8601 format

    public MessageEnvelope(String sender, String receiver, MessageData messageData, String timestamp) {
        this.sender = sender;
        this.receiver = receiver;
        this.messageData = messageData;
        this.timestamp = timestamp;
    }

    public String getSender() {
        return sender;
    }

    public void setSender(String sender) {
        this.sender = sender;

    }

    public String getReceiver() {
        return receiver;
    }

    public void setReceiver(String receiver) {
        this.receiver = receiver;
    }

    public MessageData getMessageData() {
        return messageData;
    }

    public void setMessageData(MessageData messageData) {
        this.messageData = messageData;
    }
}
