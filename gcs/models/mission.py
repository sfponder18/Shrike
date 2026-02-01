# Mission Model for SwarmDrones GCS
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import json
import copy


class WaypointType(Enum):
    """Types of mission waypoints."""
    TAKEOFF = "TAKEOFF"
    WAYPOINT = "WAYPOINT"
    LOITER = "LOITER"
    LOITER_TIME = "LOITER_TIME"
    LAUNCH_CHICK = "LAUNCH_CHICK"
    RTL = "RTL"
    LAND = "LAND"
    TARGET = "TARGET"  # Mark as target for orb assignment


@dataclass
class Waypoint:
    """A single mission waypoint."""
    id: int
    type: WaypointType
    lat: float
    lon: float
    alt: float  # meters AGL
    param1: float = 0  # Type-specific: loiter time, chick slot, etc.
    param2: float = 0  # Type-specific
    name: str = ""

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.name:
            return self.name
        if self.type == WaypointType.LAUNCH_CHICK:
            return f"Launch CHK{int(self.param1)}"
        return self.type.value

    @property
    def chick_slot(self) -> Optional[int]:
        """Get chick slot for LAUNCH_CHICK waypoints."""
        if self.type == WaypointType.LAUNCH_CHICK:
            return int(self.param1)
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "param1": self.param1,
            "param2": self.param2,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Waypoint":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=WaypointType(data["type"]),
            lat=data["lat"],
            lon=data["lon"],
            alt=data["alt"],
            param1=data.get("param1", 0),
            param2=data.get("param2", 0),
            name=data.get("name", ""),
        )


class Mission:
    """A complete mission plan with undo/redo support."""

    MAX_UNDO_HISTORY = 50

    def __init__(self, name: str = "New Mission", vehicle_id: str = "bird"):
        self.name = name
        self.vehicle_id = vehicle_id
        self.waypoints: List[Waypoint] = []
        self._next_id = 1
        self._undo_stack: List[List[dict]] = []
        self._redo_stack: List[List[dict]] = []

    def _save_state(self):
        """Save current state for undo."""
        state = [wp.to_dict() for wp in self.waypoints]
        self._undo_stack.append(state)
        if len(self._undo_stack) > self.MAX_UNDO_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()  # Clear redo on new action

    def undo(self) -> bool:
        """Undo last action. Returns True if successful."""
        if not self._undo_stack:
            return False

        # Save current state to redo
        current = [wp.to_dict() for wp in self.waypoints]
        self._redo_stack.append(current)

        # Restore previous state
        prev_state = self._undo_stack.pop()
        self.waypoints = [Waypoint.from_dict(d) for d in prev_state]

        # Update next_id
        if self.waypoints:
            self._next_id = max(wp.id for wp in self.waypoints) + 1
        else:
            self._next_id = 1

        return True

    def redo(self) -> bool:
        """Redo last undone action. Returns True if successful."""
        if not self._redo_stack:
            return False

        # Save current state to undo
        current = [wp.to_dict() for wp in self.waypoints]
        self._undo_stack.append(current)

        # Restore redo state
        next_state = self._redo_stack.pop()
        self.waypoints = [Waypoint.from_dict(d) for d in next_state]

        # Update next_id
        if self.waypoints:
            self._next_id = max(wp.id for wp in self.waypoints) + 1
        else:
            self._next_id = 1

        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def add_waypoint(self, wp_type: WaypointType, lat: float, lon: float, alt: float,
                     param1: float = 0, param2: float = 0, name: str = "") -> Waypoint:
        """Add a new waypoint to the mission."""
        self._save_state()
        wp = Waypoint(
            id=self._next_id,
            type=wp_type,
            lat=lat,
            lon=lon,
            alt=alt,
            param1=param1,
            param2=param2,
            name=name,
        )
        self._next_id += 1
        self.waypoints.append(wp)
        return wp

    def add_launch_point(self, lat: float, lon: float, alt: float, chick_id: str) -> Waypoint:
        """Add a chick launch waypoint."""
        return self.add_waypoint(
            WaypointType.LAUNCH_CHICK,
            lat, lon, alt,
            param1=0,  # Will store chick_id as string in name
            name=f"Launch {chick_id.upper()}"
        )

    def add_target(self, lat: float, lon: float, alt: float, name: str = "") -> Waypoint:
        """Add a target waypoint for orb assignment."""
        return self.add_waypoint(
            WaypointType.TARGET,
            lat, lon, alt,
            name=name or "Target"
        )

    def remove_waypoint(self, wp_id: int) -> bool:
        """Remove a waypoint by ID."""
        for i, wp in enumerate(self.waypoints):
            if wp.id == wp_id:
                self._save_state()
                self.waypoints.pop(i)
                return True
        return False

    def get_waypoint(self, wp_id: int) -> Optional[Waypoint]:
        """Get waypoint by ID."""
        for wp in self.waypoints:
            if wp.id == wp_id:
                return wp
        return None

    def get_waypoint_by_index(self, index: int) -> Optional[Waypoint]:
        """Get waypoint by list index (0-based)."""
        if 0 <= index < len(self.waypoints):
            return self.waypoints[index]
        return None

    def update_waypoint(self, wp_id: int, **kwargs) -> bool:
        """Update waypoint properties."""
        wp = self.get_waypoint(wp_id)
        if not wp:
            return False

        self._save_state()
        for key, value in kwargs.items():
            if hasattr(wp, key):
                setattr(wp, key, value)
        return True

    def move_waypoint(self, wp_id: int, new_index: int) -> bool:
        """Move a waypoint to a new position in the list."""
        for i, wp in enumerate(self.waypoints):
            if wp.id == wp_id:
                self._save_state()
                self.waypoints.pop(i)
                self.waypoints.insert(new_index, wp)
                return True
        return False

    def clear(self):
        """Clear all waypoints."""
        if self.waypoints:
            self._save_state()
        self.waypoints.clear()
        self._next_id = 1

    def get_ordered_waypoints(self) -> List[Waypoint]:
        """Get waypoints in mission order (by list position, not ID)."""
        return self.waypoints.copy()

    def to_map_format(self) -> dict:
        """Convert to map display format with sequential ordering."""
        result = {}
        for idx, wp in enumerate(self.waypoints):
            if wp.type != WaypointType.RTL:
                # Use index for ordering, not wp.id
                # Format: (lat, lon, type, id, alt, speed)
                # Speed is stored in param2 (0 = default cruise speed)
                result[idx] = (wp.lat, wp.lon, wp.type.value, wp.id, wp.alt, wp.param2)
        return result

    def to_mavlink_format(self) -> list:
        """Convert to MAVLink upload format."""
        result = []
        for wp in self.waypoints:
            item = {
                "type": wp.type.value,
                "lat": wp.lat,
                "lon": wp.lon,
                "alt": wp.alt,
            }
            if wp.type == WaypointType.LAUNCH_CHICK:
                # Extract chick ID from name
                item["chick_id"] = wp.name.replace("Launch ", "").lower()
            elif wp.type == WaypointType.LOITER_TIME:
                item["time"] = wp.param1
            result.append(item)
        return result

    def to_json(self) -> str:
        """Serialize mission to JSON."""
        return json.dumps({
            "name": self.name,
            "vehicle_id": self.vehicle_id,
            "waypoints": [wp.to_dict() for wp in self.waypoints],
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Mission":
        """Deserialize mission from JSON."""
        data = json.loads(json_str)
        mission = cls(
            name=data.get("name", "Imported Mission"),
            vehicle_id=data.get("vehicle_id", "bird"),
        )
        for wp_data in data.get("waypoints", []):
            wp = Waypoint.from_dict(wp_data)
            mission.waypoints.append(wp)
            if wp.id >= mission._next_id:
                mission._next_id = wp.id + 1
        return mission

    def __len__(self) -> int:
        return len(self.waypoints)

    def __repr__(self) -> str:
        return f"Mission({self.name}, {self.vehicle_id}, {len(self)} waypoints)"
