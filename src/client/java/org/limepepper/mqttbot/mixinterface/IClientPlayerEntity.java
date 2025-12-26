package org.limepepper.mqttbot.mixinterface;

import net.minecraft.world.phys.Vec3;

public interface IClientPlayerEntity
{
    public void setNoClip(boolean noClip);

    public float getLastYaw();

    public float getLastPitch();

    public void setMovementMultiplier(Vec3 movementMultiplier);

    public boolean isTouchingWaterBypass();
}
