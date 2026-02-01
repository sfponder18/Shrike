# Vehicle State Model
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class VehicleType(Enum):
    PLANE = "plane"
    COPTER = "copter"


class ChickState(Enum):
    """Attachment state for Chick drones carried by Bird."""
    ATTACHED = "attached"    # Mounted on Bird, not yet launched
    LAUNCHING = "launching"  # Launch sequence initiated
    LAUNCHED = "launched"    # Flying independently
    RECOVERED = "recovered"  # Back on Bird (future capability)


@dataclass
class VehicleState:
    """Current state of a vehicle."""
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0  # meters AGL
    heading: float = 0.0  # degrees
    groundspeed: float = 0.0  # m/s
    airspeed: float = 0.0  # m/s
    battery_pct: int = 100
    battery_voltage: float = 16.8
    mode: str = "LOITER"
    armed: bool = False
    gps_fix: int = 3  # 0=no fix, 2=2D, 3=3D
    gps_satellites: int = 12
    last_heartbeat: float = field(default_factory=time.time)

    @property
    def is_connected(self) -> bool:
        return (time.time() - self.last_heartbeat) < 5.0


class Vehicle:
    """Represents a vehicle in the swarm."""

    def __init__(self, vehicle_id: str, name: str, vehicle_type: VehicleType, icon: str,
                 carrier: Optional[str] = None, slot: Optional[int] = None):
        self.id = vehicle_id
        self.name = name
        self.type = vehicle_type
        self.icon = icon
        self.state = VehicleState()
        self.connected = False

        # Carrier relationship (for Chicks attached to Bird)
        self.carrier = carrier  # Vehicle ID of carrier (e.g., "bird")
        self.slot = slot        # Slot number on carrier (1 or 2)
        self._chick_state = ChickState.ATTACHED if carrier else None

    @property
    def chick_state(self) -> Optional[ChickState]:
        """Get attachment state (only for Chicks)."""
        return self._chick_state

    @property
    def is_attached(self) -> bool:
        """Check if this vehicle is currently attached to a carrier."""
        return self._chick_state == ChickState.ATTACHED

    @property
    def is_launched(self) -> bool:
        """Check if this vehicle has been launched."""
        return self._chick_state in (ChickState.LAUNCHED, ChickState.LAUNCHING)

    @property
    def can_launch(self) -> bool:
        """Check if this vehicle can be launched from carrier."""
        return self._chick_state == ChickState.ATTACHED

    def launch(self) -> bool:
        """
        Launch this vehicle from carrier.
        Returns True if launch initiated successfully.
        """
        if self.can_launch:
            self._chick_state = ChickState.LAUNCHING
            return True
        return False

    def set_launched(self):
        """Mark vehicle as fully launched (after confirmation)."""
        if self._chick_state == ChickState.LAUNCHING:
            self._chick_state = ChickState.LAUNCHED

    def recover(self) -> bool:
        """Mark vehicle as recovered/reattached (future capability)."""
        if self._chick_state == ChickState.LAUNCHED:
            self._chick_state = ChickState.RECOVERED
            return True
        return False

    def update_from_mavlink(self, msg):
        """Update state from MAVLink message. To be implemented with real MAVLink."""
        pass

    def get_modes(self) -> list[str]:
        """Get available flight modes for this vehicle type."""
        if self.type == VehicleType.PLANE:
            return ["MANUAL", "FBWA", "FBWB", "AUTO", "RTL", "LOITER", "GUIDED", "LAND"]
        else:
            return ["STABILIZE", "ALT_HOLD", "LOITER", "AUTO", "RTL", "GUIDED", "LAND"]

    def __repr__(self):
        return f"Vehicle({self.id}, {self.name}, {self.type.value})"
