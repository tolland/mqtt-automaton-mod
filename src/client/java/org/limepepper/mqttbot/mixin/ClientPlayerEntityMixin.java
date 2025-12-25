package org.limepepper.mqttbot.mixin;


import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.text.Text;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Environment(EnvType.CLIENT)
@Mixin(ClientPlayerEntity.class)
public abstract class ClientPlayerEntityMixin {


    @Shadow
    public abstract void sendMessage(Text message, boolean overlay);

    //    @Inject(at = @At("RETURN"), method = "damage")
//    private void onDamage(DamageSource source, float amount, CallbackInfoReturnable info) {
//        System.out.println("The player received damage!");
//        EventManager.fire(DamageListener.DamageEvent.INSTANCE);
//    }
    @Inject(method = "handleStatus", at = @At("HEAD"))
    private void onHandleStatus(byte status, CallbackInfo ci) {
        if (status == 2) { // 2 is the status code for "Entity Hurt"
            // Trigger your logic here
            System.out.println("The player received damage!");
        }
    }
}
