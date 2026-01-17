package org.limepepper.mqttbot.mixin;

import com.llamalad7.mixinextras.sugar.Local;
import com.llamalad7.mixinextras.sugar.ref.LocalRef;
import net.minecraft.client.GuiMessage;
import net.minecraft.client.GuiMessageTag;
import net.minecraft.client.gui.components.ChatComponent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MessageSignature;
import org.jetbrains.annotations.Nullable;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.ChatMessageListener;
import org.limepepper.mqttbot.util.MqttBotLogger;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.List;

/**
 * try and hook this
 * Minecraft.getInstance().gui.getChat().addMessage(msg, null, tag);
 */
@Mixin(ChatComponent.class)
public class ChatHudMixin {
    
    @Unique
    private static final MqttBotLogger LOGGER =
        new MqttBotLogger(ChatHudMixin.class);
    
    @Shadow
    @Final
    private List<GuiMessage.Line> trimmedMessages;
    
    @Inject(at = @At("HEAD"),
        method = "addMessage(Lnet/minecraft/network/chat/Component;Lnet/minecraft/network/chat/MessageSignature;Lnet/minecraft/client/GuiMessageTag;)V",
        cancellable = false)
    private void onAddMessage(Component messageDontUse,
        @Nullable MessageSignature signature,
        @Nullable GuiMessageTag indicatorDontUse, CallbackInfo ci,
        @Local(argsOnly = true) LocalRef<Component> message,
        @Local(argsOnly = true) LocalRef<GuiMessageTag> indicator)
    {
        String messageText = message.get().getString();
        LOGGER.debug("ChatHudMixin onAddMessage: " + messageText);
        
        EventManager
            .fire(new ChatMessageListener.ChatMessageEvent(messageText));
    }
}
