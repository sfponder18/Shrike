# EW Models - Emitter, EPStatus, DFResult
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
import time


class EmitterStatus(Enum):
    """Basic signal status."""
    NEW = "NEW"
    TRACKING = "TRACKING"
    LOST = "LOST"


class ProsecutionState(Enum):
    """Prosecution workflow state machine."""
    NONE = "NONE"           # Not being prosecuted
    QUEUED = "QUEUED"       # In prosecution queue (auto-queued high priority)
    LOCATING = "LOCATING"   # Swarm optimizing formation for DF
    PROSECUTING = "PROSECUTING"  # Vehicle assigned and en route
    RESOLVED = "RESOLVED"   # Action complete


class ProsecutionAction(Enum):
    """Action to take when prosecuting."""
    INVESTIGATE = "INVESTIGATE"      # Send Chick to get eyes on
    MARK_TARGET = "MARK_TARGET"      # Add to target queue for Orb
    CONTINUE_TRACKING = "CONTINUE"   # Keep monitoring without action


class ThreatLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EmitterType(Enum):
    TACTICAL_RADIO = "TACTICAL_RADIO"
    RADAR = "RADAR"
    DATA_LINK = "DATA_LINK"
    JAMMER = "JAMMER"
    BEACON = "BEACON"
    MESH_NODE = "MESH_NODE"
    CELLULAR = "CELLULAR"
    WIFI = "WIFI"
    BROADCAST = "BROADCAST"
    UNKNOWN_SUSPICIOUS = "UNKNOWN_SUSPICIOUS"
    UNKNOWN_BENIGN = "UNKNOWN_BENIGN"
    FRIENDLY = "FRIENDLY"


@dataclass
class DFResult:
    """Direction Finding result for an emitter."""
    lat: float = 0.0
    lon: float = 0.0
    cep_m: float = 999.0  # Circular Error Probable in meters
    method: str = "TDOA"  # TDOA, BEARING, ESTIMATED
    sensors: List[str] = field(default_factory=list)  # Which sensors contributed
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0  # 0-100


@dataclass
class Emitter:
    """Detected RF emitter."""
    id: str
    freq_mhz: float
    bandwidth_khz: float
    power_dbm: float = -80.0

    # Classification
    modulation: str = "Unknown"
    modulation_confidence: float = 0.0
    emitter_type: EmitterType = EmitterType.UNKNOWN_BENIGN
    purpose: str = "UNKNOWN"
    threat_level: str = "NEUTRAL"

    # Library match
    library_match: Optional[str] = None
    library_match_confidence: float = 0.0

    # Criticality (0-100)
    criticality: float = 0.0

    # Signal characteristics
    duty_cycle: float = 1.0  # 0-1
    burst_rate: float = 0.0  # bursts per second
    is_frequency_agile: bool = False

    # Timing
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    update_count: int = 0

    # Status
    status: EmitterStatus = EmitterStatus.NEW

    # Direction Finding
    df_result: Optional[DFResult] = None

    # Prosecution workflow
    prosecution_state: str = "NONE"  # ProsecutionState value as string
    prosecution_action: Optional[str] = None  # ProsecutionAction value as string
    assigned_vehicle: Optional[str] = None  # Vehicle assigned to prosecute
    priority_track: bool = False  # Marked as priority by operator

    # Bearing info (for display before CEP threshold met)
    bearing_from_sensors: Dict[str, float] = field(default_factory=dict)  # sensor_id -> bearing_deg

    # Targeting
    target_id: Optional[str] = None  # If converted to target

    def get_age_seconds(self) -> float:
        """Get seconds since last update."""
        return time.time() - self.last_seen

    def get_criticality_level(self) -> ThreatLevel:
        """Get criticality level based on score."""
        if self.criticality >= 80:
            return ThreatLevel.CRITICAL
        elif self.criticality >= 60:
            return ThreatLevel.HIGH
        elif self.criticality >= 40:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def has_location(self) -> bool:
        """Check if emitter has DF location."""
        return self.df_result is not None and self.df_result.cep_m < 500

    def has_displayable_location(self) -> bool:
        """Check if emitter has location good enough to display on map (CEP < 300m)."""
        return self.df_result is not None and self.df_result.cep_m < 300

    def should_auto_display(self) -> bool:
        """Check if emitter should auto-display on map (HIGH/CRITICAL with location or bearing)."""
        level = self.get_criticality_level()
        if level not in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            return False
        # Display if we have location OR bearing data
        return self.has_displayable_location() or len(self.bearing_from_sensors) > 0

    def is_being_prosecuted(self) -> bool:
        """Check if emitter is actively being prosecuted."""
        return self.prosecution_state in [
            ProsecutionState.QUEUED.value,
            ProsecutionState.LOCATING.value,
            ProsecutionState.PROSECUTING.value
        ]

    def set_prosecution_state(self, state: 'ProsecutionState'):
        """Set prosecution state."""
        self.prosecution_state = state.value

    def set_prosecution_action(self, action: 'ProsecutionAction'):
        """Set prosecution action."""
        self.prosecution_action = action.value

    def get_prosecution_state(self) -> 'ProsecutionState':
        """Get prosecution state as enum."""
        return ProsecutionState(self.prosecution_state)

    def get_prosecution_action(self) -> Optional['ProsecutionAction']:
        """Get prosecution action as enum."""
        if self.prosecution_action:
            return ProsecutionAction(self.prosecution_action)
        return None

    def update(self, power_dbm: float, modulation: str = None,
               modulation_confidence: float = None):
        """Update emitter with new observation."""
        self.power_dbm = power_dbm
        self.last_seen = time.time()
        self.update_count += 1

        if self.status == EmitterStatus.NEW and self.update_count > 3:
            self.status = EmitterStatus.TRACKING

        if modulation:
            self.modulation = modulation
        if modulation_confidence:
            self.modulation_confidence = modulation_confidence


class EmitterList:
    """Manages list of detected emitters."""

    def __init__(self, max_emitters: int = 100):
        self._emitters: Dict[str, Emitter] = {}
        self._next_id = 1
        self._max_emitters = max_emitters
        self._selected_id: Optional[str] = None

    def add(self, freq_mhz: float, bandwidth_khz: float,
            power_dbm: float = -80.0) -> Emitter:
        """Add a new emitter or update existing one at same frequency."""
        # Check if emitter already exists at this frequency (within tolerance)
        for emitter in self._emitters.values():
            if abs(emitter.freq_mhz - freq_mhz) < 0.1:  # 100 kHz tolerance
                emitter.update(power_dbm)
                return emitter

        # Create new emitter
        emitter_id = f"EMT-{self._next_id:04d}"
        self._next_id += 1

        emitter = Emitter(
            id=emitter_id,
            freq_mhz=freq_mhz,
            bandwidth_khz=bandwidth_khz,
            power_dbm=power_dbm
        )

        # Enforce max emitters (remove oldest low-criticality)
        if len(self._emitters) >= self._max_emitters:
            self._prune_oldest()

        self._emitters[emitter_id] = emitter
        return emitter

    def get(self, emitter_id: str) -> Optional[Emitter]:
        """Get emitter by ID."""
        return self._emitters.get(emitter_id)

    def get_all(self) -> List[Emitter]:
        """Get all emitters sorted by criticality (descending)."""
        return sorted(
            self._emitters.values(),
            key=lambda e: e.criticality,
            reverse=True
        )

    def get_by_criticality(self, min_level: ThreatLevel) -> List[Emitter]:
        """Get emitters at or above criticality level."""
        threshold = {
            ThreatLevel.LOW: 0,
            ThreatLevel.MEDIUM: 40,
            ThreatLevel.HIGH: 60,
            ThreatLevel.CRITICAL: 80
        }[min_level]

        return [e for e in self.get_all() if e.criticality >= threshold]

    def get_auto_displayable(self) -> List[Emitter]:
        """Get emitters that should auto-display on map (HIGH/CRITICAL)."""
        return [e for e in self.get_all() if e.should_auto_display()]

    def get_prosecution_queue(self) -> List[Emitter]:
        """Get emitters in prosecution queue (sorted by criticality)."""
        return [e for e in self.get_all() if e.is_being_prosecuted()]

    def get_priority_tracks(self) -> List[Emitter]:
        """Get emitters marked as priority tracks."""
        return [e for e in self.get_all() if e.priority_track]

    def remove(self, emitter_id: str):
        """Remove an emitter."""
        if emitter_id in self._emitters:
            del self._emitters[emitter_id]
            if self._selected_id == emitter_id:
                self._selected_id = None

    def mark_lost(self, timeout_seconds: float = 30.0):
        """Mark emitters as lost if not updated recently."""
        current_time = time.time()
        for emitter in self._emitters.values():
            if current_time - emitter.last_seen > timeout_seconds:
                emitter.status = EmitterStatus.LOST

    def _prune_oldest(self):
        """Remove oldest low-criticality emitter to make room."""
        # Sort by criticality (ascending) then by age (oldest first)
        candidates = sorted(
            self._emitters.values(),
            key=lambda e: (e.criticality, -e.get_age_seconds())
        )
        if candidates:
            self.remove(candidates[0].id)

    @property
    def selected(self) -> Optional[Emitter]:
        """Get selected emitter."""
        return self._emitters.get(self._selected_id)

    @selected.setter
    def selected(self, emitter_id: str):
        """Set selected emitter."""
        self._selected_id = emitter_id

    def count(self) -> int:
        """Get total emitter count."""
        return len(self._emitters)


@dataclass
class HopStatus:
    """Frequency hop status."""
    current_index: int = 0
    total_entries: int = 16
    state: str = "READY"  # READY, PENDING, HOPPING, COMPLETE
    last_hop_time: float = 0.0
    hops_since_start: int = 0


@dataclass
class EPStatus:
    """Electronic Protection status."""
    # Link health
    link_health_pct: float = 100.0
    packet_loss_pct: float = 0.0

    # Threat assessment
    threat_level: ThreatLevel = ThreatLevel.LOW
    active_threats: int = 0

    # Active responses
    active_responses: List[str] = field(default_factory=list)

    # Hop status
    hop_status: HopStatus = field(default_factory=HopStatus)

    # Consensus
    consensus_state: str = "NORMAL"  # NORMAL, DEGRADED, VOTING
    vehicle_health: Dict[str, bool] = field(default_factory=dict)

    def get_threat_level_str(self) -> str:
        """Get threat level as string for display."""
        return self.threat_level.value

    def is_hop_recommended(self) -> bool:
        """Check if frequency hop is recommended."""
        return self.packet_loss_pct >= 50.0

    def update_from_emitters(self, emitters: List[Emitter]):
        """Update EP status based on detected emitters."""
        critical_count = sum(1 for e in emitters if e.criticality >= 80)
        high_count = sum(1 for e in emitters if 60 <= e.criticality < 80)

        self.active_threats = critical_count + high_count

        if critical_count > 0:
            self.threat_level = ThreatLevel.CRITICAL
        elif high_count > 0:
            self.threat_level = ThreatLevel.HIGH
        elif any(e.criticality >= 40 for e in emitters):
            self.threat_level = ThreatLevel.MEDIUM
        else:
            self.threat_level = ThreatLevel.LOW
