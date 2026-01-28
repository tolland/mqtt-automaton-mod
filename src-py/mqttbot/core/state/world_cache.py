"""
World state cache - stores and indexes world entities and blocks.

Raw data from mod is stored and interpreted locally.
Maintains spatial indices for efficient queries.
Organized by server/dimension like Baritone's cache structure.
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from mqttbot.model.world.block_data import BlockData, ChestLabel, ContainerInfo, SignData
from mqttbot.model.world.entity_data import EntityData, ItemFrameData
from mqttbot.model.world.scan_result import ScanResult


@dataclass
class WorldData:
    """
    Data for a single world/dimension.
    Organized like Baritone: server/minecraft/dimension_seed/
    """

    server: str  # Server address or world name
    dimension: str  # minecraft:overworld, minecraft:the_nether, etc.
    seed: int = 0  # World seed for disambiguation

    # Raw storage
    entities: dict[str, EntityData] = field(default_factory=dict)  # uuid -> entity
    blocks: dict[tuple[int, int, int], BlockData] = field(
        default_factory=dict
    )  # pos -> block

    # Interpreted data
    containers: dict[tuple[int, int, int], ContainerInfo] = field(
        default_factory=dict
    )  # pos -> container
    item_frames: dict[str, ItemFrameData] = field(default_factory=dict)  # uuid -> item frame

    # Indices for fast queries
    container_labels: dict[tuple[int, int, int], ChestLabel] = field(
        default_factory=dict
    )  # pos -> label
    item_to_containers: dict[str, list[tuple[int, int, int]]] = field(
        default_factory=dict
    )  # item_id -> positions

    # Spatial index (chunk-based)
    entity_spatial: dict[tuple[int, int], list[str]] = field(
        default_factory=dict
    )  # chunk_pos -> uuids
    block_spatial: dict[tuple[int, int], list[tuple]] = field(
        default_factory=dict
    )  # chunk_pos -> positions

    def world_key(self) -> tuple[str, str]:
        """Get key for this world (server, dimension)"""
        return (self.server, self.dimension)


class WorldStateCache:
    """
    Cache of world state (entities, blocks) from mod scans.

    Stores raw data and maintains interpreted indices:
    - Container labels (from item frames or signs)
    - Spatial indices (for radius queries)
    - Type indices (e.g., all chests, all item frames)

    Organized by server/dimension for multi-world support.
    """

    def __init__(self):
        # Multi-world storage: (server, dimension) -> WorldData
        self.worlds: dict[tuple[str, str], WorldData] = {}

        # Track current world context
        self.current_world: Optional[tuple[str, str]] = None

    def update_from_scan(self, scan: ScanResult):
        """
        Update cache from mod scan result.
        Stores raw data and rebuilds interpreted indices.
        Organized by server/dimension.
        """
        # Get or create WorldData for this server/dimension
        world_key = (scan.server, scan.dimension)
        if world_key not in self.worlds:
            self.worlds[world_key] = WorldData(
                server=scan.server, dimension=scan.dimension, seed=scan.seed
            )

        world = self.worlds[world_key]
        self.current_world = world_key

        # Store raw entities
        for entity in scan.entities:
            world.entities[entity.uuid] = entity

            # Update spatial index
            chunk_pos = self._to_chunk_pos(entity.pos[0], entity.pos[2])
            if chunk_pos not in world.entity_spatial:
                world.entity_spatial[chunk_pos] = []
            if entity.uuid not in world.entity_spatial[chunk_pos]:
                world.entity_spatial[chunk_pos].append(entity.uuid)

            # Extract item frames
            if entity.type == "minecraft:item_frame":
                frame = ItemFrameData.from_entity_data(entity)
                if frame:
                    world.item_frames[frame.uuid] = frame

        # Store raw blocks
        for block in scan.blocks:
            world.blocks[block.pos] = block

            # Update spatial index
            chunk_pos = self._to_chunk_pos(block.pos[0], block.pos[2])
            if chunk_pos not in world.block_spatial:
                world.block_spatial[chunk_pos] = []
            if block.pos not in world.block_spatial[chunk_pos]:
                world.block_spatial[chunk_pos].append(block.pos)

            # Extract containers
            if self._is_container(block.type):
                container = ContainerInfo(
                    position=block.pos,
                    type=block.type,
                    label=None,
                    last_seen=scan.timestamp / 1000.0,  # Convert ms to seconds
                    dimension=scan.dimension,
                    slot_count=block.extra.get("slot_count", 27),
                )
                world.containers[block.pos] = container

        # Interpret relationships for this world
        self._interpret_chest_labels(world)

    def _is_container(self, block_type: str) -> bool:
        """Check if block type is a container"""
        container_keywords = ["chest", "barrel", "shulker", "hopper", "dispenser", "dropper"]
        return any(keyword in block_type for keyword in container_keywords)

    def _interpret_chest_labels(self, world: WorldData):
        """
        Find item frames attached to chests and extract labels.
        Updates container_labels and item_to_containers indices for given world.
        """
        # Clear existing indices for this world
        world.container_labels.clear()
        world.item_to_containers.clear()

        # Find item frames attached to containers
        for uuid, frame in world.item_frames.items():
            if not frame.item_id:
                continue  # Empty frame, skip

            # Calculate which block this frame is attached to
            attached_pos = frame.attached_block_pos()

            # Check if there's a container at that position
            if attached_pos in world.containers:
                # Create or update label
                if attached_pos not in world.container_labels:
                    world.container_labels[attached_pos] = ChestLabel(
                        items=[], mode="inclusive", source="item_frame"
                    )

                label = world.container_labels[attached_pos]
                if frame.item_id not in label.items:
                    label.items.append(frame.item_id)

                # Update container with label
                world.containers[attached_pos].label = label

                # Update reverse index (item -> containers)
                if frame.item_id not in world.item_to_containers:
                    world.item_to_containers[frame.item_id] = []
                if attached_pos not in world.item_to_containers[frame.item_id]:
                    world.item_to_containers[frame.item_id].append(attached_pos)

    def find_containers_for_item(
        self, item_id: str, world_key: Optional[tuple[str, str]] = None
    ) -> list[ContainerInfo]:
        """
        Find all containers that should contain this item (based on labels).

        Args:
            item_id: Minecraft item ID (e.g., "minecraft:sugar_cane")
            world_key: Optional (server, dimension) tuple; defaults to current world

        Returns:
            List of ContainerInfo objects that are labeled for this item
        """
        world = self._get_world(world_key)
        if not world:
            return []

        positions = world.item_to_containers.get(item_id, [])
        return [world.containers[pos] for pos in positions if pos in world.containers]

    def find_containers_in_radius(
        self,
        center: tuple[float, float, float],
        radius: float,
        world_key: Optional[tuple[str, str]] = None,
    ) -> list[ContainerInfo]:
        """
        Find all containers within radius of center point.

        Args:
            center: (x, y, z) center position
            radius: Search radius in blocks
            world_key: Optional (server, dimension) tuple; defaults to current world

        Returns:
            List of ContainerInfo objects within radius
        """
        world = self._get_world(world_key)
        if not world:
            return []

        cx, cy, cz = center
        chunk_radius = int(radius / 16) + 1
        center_chunk = self._to_chunk_pos(cx, cz)

        results = []

        # Iterate over chunks in radius
        for dx in range(-chunk_radius, chunk_radius + 1):
            for dz in range(-chunk_radius, chunk_radius + 1):
                chunk = (center_chunk[0] + dx, center_chunk[1] + dz)

                if chunk not in world.block_spatial:
                    continue

                # Check each block in this chunk
                for pos in world.block_spatial[chunk]:
                    if pos not in world.containers:
                        continue

                    # Check if within radius
                    dist = self._distance(pos, center)
                    if dist <= radius:
                        results.append(world.containers[pos])

        return results

    def get_container_at(
        self, pos: tuple[int, int, int], world_key: Optional[tuple[str, str]] = None
    ) -> Optional[ContainerInfo]:
        """Get container info at specific position"""
        world = self._get_world(world_key)
        if not world:
            return None
        return world.containers.get(pos)

    def get_all_containers(
        self, world_key: Optional[tuple[str, str]] = None
    ) -> list[ContainerInfo]:
        """Get all known containers"""
        world = self._get_world(world_key)
        if not world:
            return []
        return list(world.containers.values())

    def get_all_labeled_containers(
        self, world_key: Optional[tuple[str, str]] = None
    ) -> list[ContainerInfo]:
        """Get all containers that have labels"""
        world = self._get_world(world_key)
        if not world:
            return []
        return [c for c in world.containers.values() if c.label is not None]

    def get_item_frame_at(
        self, pos: tuple[float, float, float], world_key: Optional[tuple[str, str]] = None
    ) -> Optional[ItemFrameData]:
        """Find item frame at or near position"""
        world = self._get_world(world_key)
        if not world:
            return None
        for frame in world.item_frames.values():
            if self._distance(frame.pos, pos) < 0.5:  # Within 0.5 blocks
                return frame
        return None

    def get_world_list(self) -> list[tuple[str, str]]:
        """Get list of all known worlds (server, dimension)"""
        return list(self.worlds.keys())

    def clear(self, world_key: Optional[tuple[str, str]] = None):
        """
        Clear cached data.

        Args:
            world_key: If provided, clear only that world; otherwise clear all
        """
        if world_key:
            if world_key in self.worlds:
                del self.worlds[world_key]
                if self.current_world == world_key:
                    self.current_world = None
        else:
            self.worlds.clear()
            self.current_world = None

    def _get_world(self, world_key: Optional[tuple[str, str]] = None) -> Optional[WorldData]:
        """
        Get WorldData for specified world or current world.

        Args:
            world_key: Optional (server, dimension) tuple

        Returns:
            WorldData or None if not found
        """
        if world_key is None:
            world_key = self.current_world

        if world_key is None:
            return None

        return self.worlds.get(world_key)

    def _to_chunk_pos(self, x: float, z: float) -> tuple[int, int]:
        """Convert world coordinates to chunk coordinates"""
        return (int(x) >> 4, int(z) >> 4)

    def _distance(
        self, pos1: tuple[float, float, float], pos2: tuple[float, float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        dz = pos1[2] - pos2[2]
        return (dx * dx + dy * dy + dz * dz) ** 0.5

    def __repr__(self) -> str:
        total_entities = sum(len(w.entities) for w in self.worlds.values())
        total_blocks = sum(len(w.blocks) for w in self.worlds.values())
        total_containers = sum(len(w.containers) for w in self.worlds.values())
        total_labeled = sum(len(w.container_labels) for w in self.worlds.values())

        return (
            f"WorldStateCache("
            f"worlds={len(self.worlds)}, "
            f"entities={total_entities}, "
            f"blocks={total_blocks}, "
            f"containers={total_containers}, "
            f"labeled={total_labeled})"
        )
