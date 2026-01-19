package org.limepepper.mqttbot.mqtt;

public class MessageEnvelope {
    
    private String sender;
    private String receiver;
    private ServiceMessage serviceMessage;
    private String timestamp; // ISO 8601 format
    
    public MessageEnvelope(String sender, String receiver,
        ServiceMessage serviceMessage, String timestamp)
    {
        this.sender = sender;
        this.receiver = receiver;
        this.serviceMessage = serviceMessage;
        this.timestamp = timestamp;
    }
    
    public String getSender()
    {
        return sender;
    }
    
    public void setSender(String sender)
    {
        this.sender = sender;
        
    }
    
    public String getReceiver()
    {
        return receiver;
    }
    
    public void setReceiver(String receiver)
    {
        this.receiver = receiver;
    }
    
    public ServiceMessage getServiceMessage()
    {
        return serviceMessage;
    }
    
    public void setServiceMessage(ServiceMessage serviceMessage)
    {
        this.serviceMessage = serviceMessage;
    }
}
