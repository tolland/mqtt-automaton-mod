package org.limepepper.mqttbot.actions;

import org.limepepper.mqttbot.events.ClientJoinListener;
import org.limepepper.mqttbot.integrations.wurst.WurstService;

import java.util.List;

public class AdHocAction implements ClientJoinListener {
    /**
     * @param event
     *            The Join event details.
     */
    @Override
    public void onClientJoin(ClientJoinEvent event)
    {
        WurstService.INSTANCE.executeCommand("t", List.of("autofarm", "off"));
    }
}
