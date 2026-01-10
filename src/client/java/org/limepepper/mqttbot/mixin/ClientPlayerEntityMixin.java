package org.limepepper.mqttbot.mixin;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.player.LocalPlayer;
import org.spongepowered.asm.mixin.Mixin;

@Environment(EnvType.CLIENT)
@Mixin(LocalPlayer.class)
public abstract class ClientPlayerEntityMixin {
    
    // @Inject(at = @At("RETURN"), method = "hurt")
    // private void onHurt(DamageSource source, float amount,
    // CallbackInfoReturnable<Boolean> cir) {
    // if (cir.getReturnValue()) {
    // System.out.println("The player received damage from: " +
    // source.getMsgId());
    // EventManager.fire(DamageListener.DamageEvent.INSTANCE);
    // }
    // }
}
