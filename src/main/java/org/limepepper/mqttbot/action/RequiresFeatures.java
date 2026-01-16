package org.limepepper.mqttbot.action;

import java.util.Set;

public interface RequiresFeatures {
    Set<Class<? extends Feature>> requiredFeatures();
}
