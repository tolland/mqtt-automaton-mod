package org.limepepper.mqttbot.mixin;


import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.damagesource.DamageSource;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DamageListener;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Environment(EnvType.CLIENT)
@Mixin(LocalPlayer.class)
public abstract class ClientPlayerEntityMixin {

//    @Inject(at = @At("RETURN"), method = "hurt")
//    private void onHurt(DamageSource source, float amount, CallbackInfoReturnable<Boolean> cir) {
//        if (cir.getReturnValue()) {
//            System.out.println("The player received damage from: " + source.getMsgId());
//            EventManager.fire(DamageListener.DamageEvent.INSTANCE);
//        }
//    }
}
