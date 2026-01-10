/*
 * Copyright (c) 2014-2022 Wurst-Imperium and contributors.
 *
 * This source code is subject to the terms of the GNU General Public
 * License, version 3. If a copy of the GPL was not distributed with this
 * file, You can obtain one at: https://www.gnu.org/licenses/gpl-3.0.txt
 */
package org.limepepper.mqttbot.mixin;

import org.limepepper.mqttbot.MqttCore;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DeathListener;
import net.minecraft.client.gui.screens.DeathScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(DeathScreen.class)
public abstract class DeathScreenMixin extends Screen {
    private DeathScreenMixin(MqttCore client, Component text_1)
    {
        super(text_1);
    }
    
    @Inject(at = {@At(value = "TAIL")}, method = {"tick()V"})
    private void onTick(CallbackInfo ci)
    {
        EventManager.fire(DeathListener.DeathEvent.INSTANCE);
    }
}
