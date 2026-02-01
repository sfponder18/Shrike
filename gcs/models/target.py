# Target Data Model
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class TargetSource(Enum):
    VIDEO = "VIDEO"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    EW = "EW"  # From EW prosecution


@dataclass
class Target:
    """A target coordinate in the queue."""
    id: str
    lat: float
    lon: float
    alt: Optional[float] = None  # Optional altitude
    source: TargetSource = TargetSource.MANUAL
    assigned_orb: Optional[str] = None  # Orb ID if assigned
    timestamp: float = field(default_factory=time.time)
    notes: str = ""
    name: str = ""  # Custom name (optional)
    description: str = ""  # Detailed description
    emitter_id: Optional[str] = None  # EW emitter ID if source is EW

    @property
    def is_ew_target(self) -> bool:
        """Check if this target came from EW prosecution."""
        return self.source == TargetSource.EW or self.emitter_id is not None

    @property
    def coords_str(self) -> str:
        """Format coordinates as string."""
        return f"{self.lat:.4f}, {self.lon:.4f}"

    @property
    def display_id(self) -> str:
        """Display ID with marker."""
        return f"◎{self.id}"

    @property
    def display_name(self) -> str:
        """Display name (custom name or ID)."""
        return self.name if self.name else f"TGT{self.id}"

    def __repr__(self):
        return f"Target({self.id}, {self.coords_str}, {self.source.value})"


class TargetQueue:
    """Manages the queue of targets."""

    def __init__(self):
        self._targets: dict[str, Target] = {}
        self._next_id = 1
        self._selected_id: Optional[str] = None

    def add(self, lat: float, lon: float, source: TargetSource = TargetSource.MANUAL,
            alt: Optional[float] = None, notes: str = "") -> Target:
        """Add a new target to the queue."""
        target_id = str(self._next_id)
        self._next_id += 1
        target = Target(
            id=target_id,
            lat=lat,
            lon=lon,
            alt=alt,
            source=source,
            notes=notes
        )
        self._targets[target_id] = target
        return target

    def remove(self, target_id: str) -> bool:
        """Remove a target from the queue."""
        if target_id in self._targets:
            del self._targets[target_id]
            if self._selected_id == target_id:
                self._selected_id = None
            return True
        return False

    def get(self, target_id: str) -> Optional[Target]:
        """Get a target by ID."""
        return self._targets.get(target_id)

    def get_all(self) -> list[Target]:
        """Get all targets sorted by ID."""
        return sorted(self._targets.values(), key=lambda t: int(t.id))

    def get_unassigned(self) -> list[Target]:
        """Get targets not assigned to an orb."""
        return [t for t in self.get_all() if t.assigned_orb is None]

    def assign_to_orb(self, target_id: str, orb_id: str) -> bool:
        """Assign a target to an orb."""
        target = self._targets.get(target_id)
        if target:
            target.assigned_orb = orb_id
            return True
        return False

    def rename(self, target_id: str, name: str) -> bool:
        """Rename a target."""
        target = self._targets.get(target_id)
        if target:
            target.name = name
            return True
        return False

    def set_description(self, target_id: str, description: str) -> bool:
        """Set target description."""
        target = self._targets.get(target_id)
        if target:
            target.description = description
            return True
        return False

    def unassign_orb(self, orb_id: str):
        """Unassign all targets from an orb."""
        for target in self._targets.values():
            if target.assigned_orb == orb_id:
                target.assigned_orb = None

    @property
    def selected(self) -> Optional[Target]:
        """Get currently selected target."""
        return self._targets.get(self._selected_id) if self._selected_id else None

    @selected.setter
    def selected(self, target_id: Optional[str]):
        """Set selected target by ID."""
        self._selected_id = target_id if target_id in self._targets else None

    def select_next(self) -> Optional[Target]:
        """Select next target in queue, cycling."""
        targets = self.get_all()
        if not targets:
            return None
        if self._selected_id is None:
            self._selected_id = targets[0].id
        else:
            ids = [t.id for t in targets]
            try:
                idx = ids.index(self._selected_id)
                self._selected_id = ids[(idx + 1) % len(ids)]
            except ValueError:
                self._selected_id = targets[0].id
        return self.selected

    def __len__(self):
        return len(self._targets)
