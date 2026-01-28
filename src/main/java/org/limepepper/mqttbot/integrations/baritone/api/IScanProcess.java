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

package org.limepepper.mqttbot.integrations.baritone.api;

import baritone.api.process.IBaritoneProcess;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.Item;

import java.util.List;

public interface IScanProcess extends IBaritoneProcess {
    
    void scan(List<Item> items, int range);
    
    void scan(List<Item> items, int range, BlockPos origin);
    
    default void scan(List<Item> items)
    {
        scan(items, 0);
    }
}
