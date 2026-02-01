# Orb State Model
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrbState(Enum):
    LOADED = "loaded"      # On carrier, not armed
    ARMED = "armed"        # On carrier, armed
    RELEASED = "released"  # Released, in flight
    EXPENDED = "expended"  # Mission complete
    EMPTY = "empty"        # Slot empty


@dataclass
class Orb:
    """Represents a glide munition."""
    id: str
    carrier: str  # Vehicle ID (chick1 or chick2)
    slot: int     # 1 or 2
    state: OrbState = OrbState.LOADED
    target_id: Optional[str] = None
    battery_pct: int = 100
    gps_fix: bool = True

    # Release tracking for time-of-fall estimation
    release_time: Optional[float] = None  # Unix timestamp when released
    release_alt: Optional[float] = None   # Altitude (m) at release
    target_alt: Optional[float] = None    # Target altitude (m), defaults to ground level

    @property
    def display_id(self) -> str:
        """Display ID for UI."""
        return f"ORB{self.id}"

    def get_estimated_impact_time(self) -> Optional[float]:
        """
        Calculate estimated time to impact in seconds.
        Based on typical glide munition descent rate of ~15-20 m/s.
        Returns None if not released or missing data.
        """
        if self.state != OrbState.RELEASED or self.release_alt is None:
            return None

        target_alt = self.target_alt or 0  # Default to ground level
        altitude_diff = self.release_alt - target_alt

        if altitude_diff <= 0:
            return 0  # Already at or below target

        # Typical glide munition descent rate: 15-20 m/s average
        # Using 18 m/s as average descent rate
        DESCENT_RATE_MS = 18.0
        return altitude_diff / DESCENT_RATE_MS

    def get_time_to_impact(self) -> Optional[float]:
        """
        Get remaining time to impact in seconds.
        Returns None if not released or impact occurred.
        """
        if self.release_time is None:
            return None

        import time
        estimated_total = self.get_estimated_impact_time()
        if estimated_total is None:
            return None

        elapsed = time.time() - self.release_time
        remaining = estimated_total - elapsed
        return max(0, remaining)

    @property
    def is_ready(self) -> bool:
        """Check if orb is ready for operations."""
        return self.state == OrbState.LOADED and self.gps_fix and self.battery_pct > 10

    @property
    def can_arm(self) -> bool:
        """Check if orb can be armed."""
        return self.state == OrbState.LOADED and self.target_id is not None

    @property
    def can_release(self) -> bool:
        """Check if orb can be released."""
        return self.state == OrbState.ARMED

    def assign_target(self, target_id: str):
        """Assign a target to this orb."""
        if self.state == OrbState.LOADED:
            self.target_id = target_id

    def clear_target(self):
        """Clear the assigned target."""
        if self.state == OrbState.LOADED:
            self.target_id = None

    def arm(self) -> bool:
        """Arm the orb. Returns True if successful."""
        if self.can_arm:
            self.state = OrbState.ARMED
            return True
        return False

    def disarm(self) -> bool:
        """Disarm the orb. Returns True if successful."""
        if self.state == OrbState.ARMED:
            self.state = OrbState.LOADED
            return True
        return False

    def release(self, release_alt: float = None, target_alt: float = 0) -> bool:
        """
        Release the orb. Returns True if successful.

        Args:
            release_alt: Altitude (m) at release
            target_alt: Target altitude (m), defaults to ground level
        """
        import time
        if self.can_release:
            self.state = OrbState.RELEASED
            self.release_time = time.time()
            self.release_alt = release_alt
            self.target_alt = target_alt
            return True
        return False

    def __repr__(self):
        return f"Orb({self.id}, {self.carrier}, slot={self.slot}, {self.state.value})"


class OrbManager:
    """Manages all orbs in the swarm."""

    def __init__(self):
        self._orbs: dict[str, Orb] = {}
        self._selected_id: Optional[str] = None
        self._init_orbs()

    def _init_orbs(self):
        """Initialize default orb configuration."""
        # 2 orbs per chick (chick1.1 and chick1.2 for bird1)
        self._orbs["1"] = Orb(id="1", carrier="chick1.1", slot=1)
        self._orbs["2"] = Orb(id="2", carrier="chick1.1", slot=2)
        self._orbs["3"] = Orb(id="3", carrier="chick1.2", slot=1)
        self._orbs["4"] = Orb(id="4", carrier="chick1.2", slot=2)

    def get(self, orb_id: str) -> Optional[Orb]:
        """Get an orb by ID."""
        return self._orbs.get(orb_id)

    def get_all(self) -> list[Orb]:
        """Get all orbs."""
        return list(self._orbs.values())

    def get_by_carrier(self, carrier_id: str) -> list[Orb]:
        """Get orbs carried by a specific vehicle."""
        return [o for o in self._orbs.values() if o.carrier == carrier_id]

    def get_by_target(self, target_id: str) -> Optional[Orb]:
        """Get the orb assigned to a specific target (if any)."""
        for orb in self._orbs.values():
            if orb.target_id == target_id:
                return orb
        return None

    def is_target_assigned(self, target_id: str) -> bool:
        """Check if a target is already assigned to any orb."""
        return self.get_by_target(target_id) is not None

    def clear_orb_with_target(self, target_id: str) -> Optional[str]:
        """
        Clear any orb that has this target assigned.
        Returns the orb ID that was cleared, or None.
        """
        orb = self.get_by_target(target_id)
        if orb:
            orb.clear_target()
            return orb.id
        return None

    @property
    def selected(self) -> Optional[Orb]:
        """Get currently selected orb."""
        return self._orbs.get(self._selected_id) if self._selected_id else None

    @selected.setter
    def selected(self, orb_id: Optional[str]):
        """Set selected orb by ID."""
        self._selected_id = orb_id if orb_id in self._orbs else None

    def select_next(self) -> Optional[Orb]:
        """Select next available orb."""
        available = [o for o in self._orbs.values() if o.state in (OrbState.LOADED, OrbState.ARMED)]
        if not available:
            return None
        if self._selected_id is None:
            self._selected_id = available[0].id
        else:
            ids = [o.id for o in available]
            try:
                idx = ids.index(self._selected_id)
                self._selected_id = ids[(idx + 1) % len(ids)]
            except ValueError:
                self._selected_id = available[0].id
        return self.selected
