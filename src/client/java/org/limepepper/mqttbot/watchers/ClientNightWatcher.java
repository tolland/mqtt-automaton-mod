package org.limepepper.mqttbot.watchers;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import org.limepepper.mqttbot.event.EventManager;
import org.limepepper.mqttbot.events.DayNightListener;
import net.minecraft.client.Minecraft;
import net.minecraft.world.World;

public final class ClientNightWatcher {
    private static final long DAY_TICKS = 24_000L;
    private static final long NIGHT_START = 13_000L;
    private static final long NIGHT_END   = 23_000L;
    private static boolean wasNight = false;

    public static void init() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client.world == null) return;
            World w = client.world;

            if (w.getRegistryKey() != World.OVERWORLD) return;
            if (!w.getDimension().hasSkyLight() || w.getDimension().hasFixedTime()) return;

            long tod = w.getTimeOfDay() % DAY_TICKS;
            boolean nightByTime = (tod >= NIGHT_START && tod < NIGHT_END);
            boolean isNightish  = nightByTime || w.isThundering();

            if (!wasNight && isNightish) {
                onNightStart(client);
            } else if (wasNight && !isNightish) {
                onDayStart(client);
            }
            wasNight = isNightish;
        });
    }

    private static void onNightStart(Minecraft client) {
        // e.g., send MQTT, notify UI, start a route, etc.
        System.out.println("[ClientNightWatcher] Night started");
        EventManager.fire(DayNightListener.NightStartEvent.INSTANCE);
    }

    private static void onDayStart(Minecraft client) {
        System.out.println("[ClientNightWatcher] Day started");
        EventManager.fire(DayNightListener.DayStartEvent.INSTANCE);
    }

    private ClientNightWatcher() {}
}
