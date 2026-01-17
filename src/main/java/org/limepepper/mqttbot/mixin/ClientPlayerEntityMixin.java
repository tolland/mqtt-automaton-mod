package org.limepepper.mqttbot.mixin;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.player.LocalPlayer;
import net.wurstclient.event.EventManager;
import net.wurstclient.events.PostMotionListener;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Environment(EnvType.CLIENT)
@Mixin(LocalPlayer.class)
public abstract class ClientPlayerEntityMixin {
    
    // @Inject(at = @At("RETURN"), method = "hurt")
    // private void onHurt(DamageSource source, float amount,
    // CallbackInfoReturnable<Boolean> cir) {
    // if (cir.getReturnValue()) {
    // LOGGER.debug("The player received damage from: " +
    // source.getMsgId());
    // EventManager.fire(DamageListener.DamageEvent.INSTANCE);
    // }
    // }
    
    @Inject(at = @At("TAIL"), method = "sendPosition()V")
    private void onSendMovementPacketsTAIL(CallbackInfo ci)
    {
        EventManager.fire(PostMotionListener.PostMotionEvent.INSTANCE);
    }
}
