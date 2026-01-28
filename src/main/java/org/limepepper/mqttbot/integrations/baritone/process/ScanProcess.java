/*
 * This file is part of Baritone.
 *
 * Baritone is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Baritone is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Baritone. If not, see <https://www.gnu.org/licenses/>.
 */

package org.limepepper.mqttbot.integrations.baritone.process;

import baritone.Baritone;
import baritone.api.event.listener.AbstractGameEventListener;
import baritone.api.process.PathingCommand;
import baritone.api.process.PathingCommandType;
import baritone.utils.BaritoneProcessHelper;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.Item;
import net.minecraft.world.phys.Vec3;
import org.limepepper.mqttbot.integrations.baritone.api.IScanProcess;

import java.util.ArrayList;
import java.util.List;

public final class ScanProcess extends BaritoneProcessHelper
    implements IScanProcess, AbstractGameEventListener {
    
    private boolean active;
    private List<Item> itemsToCollect;
    private int range;
    private BlockPos startPosition;
    private final List<Vec3> currentTargetItems = new ArrayList<>();
    
    public ScanProcess(Baritone baritone)
    {
        super(baritone);
        baritone.getGameEventHandler().registerEventListener(this);
    }
    
    @Override
    public boolean isActive()
    {
        return active;
    }
    
    @Override
    public void scan(List<Item> items, int range)
    {
        scan(items, range, baritone.getPlayerContext().playerFeet());
    }
    
    @Override
    public void scan(List<Item> items, int range, BlockPos origin)
    {
        if(items == null || items.isEmpty())
        {
            logDirect("No items specified to collect");
            return;
        }
        
        this.itemsToCollect = new ArrayList<>(items);
        this.startPosition = origin;
        this.range = range;
        active = true;
    }
    
    @Override
    public PathingCommand onTick(boolean calcFailed, boolean isSafeToCancel)
    {
        return new PathingCommand(null, PathingCommandType.REQUEST_PAUSE);
    }
    
    @Override
    public void onLostControl()
    {
        active = false;
        itemsToCollect = null;
        currentTargetItems.clear();
    }
    
    @Override
    public String displayName0()
    {
        return "Collecting Items";
    }
}
