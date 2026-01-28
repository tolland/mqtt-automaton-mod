"""
World state cache - stores and indexes world entities and blocks.

Raw data from mod is stored and interpreted locally.
Maintains spatial indices for efficient queries.
"""

import time
from typing import Optional

from mqttbot.model.world.block_data import BlockData, ChestLabel, ContainerInfo, SignData
from mqttbot.model.world.entity_data import EntityData, ItemFrameData
from mqttbot.model.world.scan_result import ScanResult


class WorldStateCache:
    """
    Cache of world state (entities, blocks) from mod scans.

    Stores raw data and maintains interpreted indices:
    - Container labels (from item frames or signs)
    - Spatial indices (for radius queries)
    - Type indices (e.g., all chests, all item frames)
    """

    def __init__(self):
        # Raw storage
        self.entities: dict[str, EntityData] = {}  # uuid -> entity
        self.blocks: dict[tuple[int, int, int], BlockData] = {}  # pos -> block

        # Interpreted data
        self.containers: dict[tuple[int, int, int], ContainerInfo] = {}  # pos -> container
        self.item_frames: dict[str, ItemFrameData] = {}  # uuid -> item frame

        # Indices for fast queries
        self.container_labels: dict[tuple[int, int, int], ChestLabel] = {}  # pos -> label
        self.item_to_containers: dict[str, list[tuple[int, int, int]]] = (
            {}
        )  # item_id -> positions

        # Spatial index (chunk-based)
        self.entity_spatial: dict[tuple[int, int], list[str]] = {}  # chunk_pos -> uuids
        self.block_spatial: dict[tuple[int, int], list[tuple]] = {}  # chunk_pos -> positions

    def update_from_scan(self, scan: ScanResult):
        """
        Update cache from mod scan result.
        Stores raw data and rebuilds interpreted indices.
        """
        # Store raw entities
        for entity in scan.entities:
            self.entities[entity.uuid] = entity

            # Update spatial index
            chunk_pos = self._to_chunk_pos(entity.pos[0], entity.pos[2])
            if chunk_pos not in self.entity_spatial:
                self.entity_spatial[chunk_pos] = []
            if entity.uuid not in self.entity_spatial[chunk_pos]:
                self.entity_spatial[chunk_pos].append(entity.uuid)

            # Extract item frames
            if entity.type == "minecraft:item_frame":
                frame = ItemFrameData.from_entity_data(entity)
                if frame:
                    self.item_frames[frame.uuid] = frame

        # Store raw blocks
        for block in scan.blocks:
            self.blocks[block.pos] = block

            # Update spatial index
            chunk_pos = self._to_chunk_pos(block.pos[0], block.pos[2])
            if chunk_pos not in self.block_spatial:
                self.block_spatial[chunk_pos] = []
            if block.pos not in self.block_spatial[chunk_pos]:
                self.block_spatial[chunk_pos].append(block.pos)

            # Extract containers
            if self._is_container(block.type):
                container = ContainerInfo(
                    position=block.pos,
                    type=block.type,
                    label=None,
                    last_seen=scan.timestamp / 1000.0,  # Convert ms to seconds
                    slot_count=block.extra.get("slot_count", 27),
                )
                self.containers[block.pos] = container

        # Interpret relationships
        self._interpret_chest_labels()

    def _is_container(self, block_type: str) -> bool:
        """Check if block type is a container"""
        container_keywords = ["chest", "barrel", "shulker", "hopper", "dispenser", "dropper"]
        return any(keyword in block_type for keyword in container_keywords)

    def _interpret_chest_labels(self):
        """
        Find item frames attached to chests and extract labels.
        Updates container_labels and item_to_containers indices.
        """
        # Clear existing indices
        self.container_labels.clear()
        self.item_to_containers.clear()

        # Find item frames attached to containers
        for uuid, frame in self.item_frames.items():
            if not frame.item_id:
                continue  # Empty frame, skip

            # Calculate which block this frame is attached to
            attached_pos = frame.attached_block_pos()

            # Check if there's a container at that position
            if attached_pos in self.containers:
                # Create or update label
                if attached_pos not in self.container_labels:
                    self.container_labels[attached_pos] = ChestLabel(
                        items=[], mode="inclusive", source="item_frame"
                    )

                label = self.container_labels[attached_pos]
                if frame.item_id not in label.items:
                    label.items.append(frame.item_id)

                # Update container with label
                self.containers[attached_pos].label = label

                # Update reverse index (item -> containers)
                if frame.item_id not in self.item_to_containers:
                    self.item_to_containers[frame.item_id] = []
                if attached_pos not in self.item_to_containers[frame.item_id]:
                    self.item_to_containers[frame.item_id].append(attached_pos)

    def find_containers_for_item(self, item_id: str) -> list[ContainerInfo]:
        """
        Find all containers that should contain this item (based on labels).

        Args:
            item_id: Minecraft item ID (e.g., "minecraft:sugar_cane")

        Returns:
            List of ContainerInfo objects that are labeled for this item
        """
        positions = self.item_to_containers.get(item_id, [])
        return [self.containers[pos] for pos in positions if pos in self.containers]

    def find_containers_in_radius(
        self, center: tuple[float, float, float], radius: float
    ) -> list[ContainerInfo]:
        """
        Find all containers within radius of center point.

        Args:
            center: (x, y, z) center position
            radius: Search radius in blocks

        Returns:
            List of ContainerInfo objects within radius
        """
        cx, cy, cz = center
        chunk_radius = int(radius / 16) + 1
        center_chunk = self._to_chunk_pos(cx, cz)

        results = []

        # Iterate over chunks in radius
        for dx in range(-chunk_radius, chunk_radius + 1):
            for dz in range(-chunk_radius, chunk_radius + 1):
                chunk = (center_chunk[0] + dx, center_chunk[1] + dz)

                if chunk not in self.block_spatial:
                    continue

                # Check each block in this chunk
                for pos in self.block_spatial[chunk]:
                    if pos not in self.containers:
                        continue

                    # Check if within radius
                    dist = self._distance(pos, center)
                    if dist <= radius:
                        results.append(self.containers[pos])

        return results

    def get_container_at(self, pos: tuple[int, int, int]) -> Optional[ContainerInfo]:
        """Get container info at specific position"""
        return self.containers.get(pos)

    def get_all_containers(self) -> list[ContainerInfo]:
        """Get all known containers"""
        return list(self.containers.values())

    def get_all_labeled_containers(self) -> list[ContainerInfo]:
        """Get all containers that have labels"""
        return [c for c in self.containers.values() if c.label is not None]

    def get_item_frame_at(self, pos: tuple[float, float, float]) -> Optional[ItemFrameData]:
        """Find item frame at or near position"""
        for frame in self.item_frames.values():
            if self._distance(frame.pos, pos) < 0.5:  # Within 0.5 blocks
                return frame
        return None

    def clear(self):
        """Clear all cached data"""
        self.entities.clear()
        self.blocks.clear()
        self.containers.clear()
        self.item_frames.clear()
        self.container_labels.clear()
        self.item_to_containers.clear()
        self.entity_spatial.clear()
        self.block_spatial.clear()

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
        return (
            f"WorldStateCache("
            f"entities={len(self.entities)}, "
            f"blocks={len(self.blocks)}, "
            f"containers={len(self.containers)}, "
            f"labeled={len(self.container_labels)})"
        )
