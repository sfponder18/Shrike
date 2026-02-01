# EW Manager - Electronic Warfare simulation and management
import random
import math
import time
from typing import Optional, List, Dict
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from ..models.emitter import (
    Emitter, EmitterList, EmitterStatus, EmitterType,
    EPStatus, HopStatus, DFResult, ThreatLevel,
    ProsecutionState, ProsecutionAction
)
from ..config import (
    EW_CRITICALITY_WEIGHTS, EW_SWEEP_BANDS, EW_GUARD_BANDS,
    EW_THREAT_LIBRARY, EW_BENIGN_LIBRARY, EW_MODULATION_TYPES
)


class EWManager(QObject):
    """
    Electronic Warfare Manager.

    Handles:
    - ES: Emitter detection, characterization, criticality scoring
    - EP: Link monitoring, threat assessment, hop coordination
    - DF: Direction finding coordination (simulated)
    - Simulation: Generates fake emitters for testing
    """

    # Signals
    emitter_detected = pyqtSignal(str)  # emitter_id
    emitter_updated = pyqtSignal(str)   # emitter_id
    emitter_lost = pyqtSignal(str)      # emitter_id
    ep_status_changed = pyqtSignal()
    hop_recommended = pyqtSignal()
    hop_initiated = pyqtSignal(int)     # new channel index
    critical_threat = pyqtSignal(str)   # emitter_id
    formation_commanded = pyqtSignal(dict)  # {vehicle_id: (lat, lon, alt)}

    # Prosecution signals
    emitter_queued = pyqtSignal(str)    # emitter_id - auto-queued for prosecution
    prosecution_started = pyqtSignal(str, str)  # emitter_id, vehicle_id
    prosecution_complete = pyqtSignal(str)  # emitter_id
    vehicle_assignment_requested = pyqtSignal(str, str, float, float)  # emitter_id, vehicle_id, lat, lon

    # Map display signals
    priority_tracks_changed = pyqtSignal()  # Notify UI to update map display

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data stores
        self._emitters = EmitterList(max_emitters=50)
        self._ep_status = EPStatus()

        # Simulation state
        self._simulation_mode = False
        self._sim_timer = None
        self._sim_base_lat = 52.0     # UK - matches swarm simulation start
        self._sim_base_lon = -1.5
        self._sim_range_km = 3.0      # Generate emitters within ±3km

        # DF coordination
        self._df_active_emitters: List[str] = []

        # Spectrum data for display
        self._spectrum_data: Dict[str, List[float]] = {}
        self._waterfall_history: List[List[float]] = []

        # Vehicle positions (updated from app)
        self._vehicle_positions: Dict[str, tuple] = {}  # {id: (lat, lon, alt)}

        # Prosecution queue management
        self._prosecution_queue: List[str] = []  # emitter_ids in order

    # ==================== Properties ====================

    @property
    def emitters(self) -> EmitterList:
        """Get emitter list."""
        return self._emitters

    @property
    def ep_status(self) -> EPStatus:
        """Get EP status."""
        return self._ep_status

    @property
    def spectrum_data(self) -> Dict[str, List[float]]:
        """Get current spectrum data for display."""
        return self._spectrum_data

    @property
    def waterfall_history(self) -> List[List[float]]:
        """Get waterfall history."""
        return self._waterfall_history

    # ==================== Simulation ====================

    def start_simulation(self):
        """Start EW simulation mode."""
        print("[EW Manager] Starting simulation...")
        self._simulation_mode = True

        # Initialize EP status
        self._ep_status.link_health_pct = 95.0
        self._ep_status.packet_loss_pct = 5.0
        self._ep_status.vehicle_health = {
            "bird1": True,
            "chick1.1": True,
            "chick1.2": True
        }

        # Start simulation timer (update every 500ms)
        self._sim_timer = QTimer(self)
        self._sim_timer.timeout.connect(self._simulate_update)
        self._sim_timer.start(500)

        # Generate initial emitters
        self._generate_initial_emitters()
        print(f"[EW Manager] Simulation started with {self._emitters.count()} initial emitters")

    def stop_simulation(self):
        """Stop simulation."""
        self._simulation_mode = False
        if self._sim_timer:
            self._sim_timer.stop()
            self._sim_timer = None

    def _simulate_update(self):
        """Periodic simulation update."""
        # Update existing emitters
        for emitter in self._emitters.get_all():
            # Randomly update power (small variation)
            emitter.power_dbm += random.uniform(-2, 2)
            emitter.power_dbm = max(-100, min(-30, emitter.power_dbm))
            emitter.last_seen = time.time()

            # Occasionally update modulation confidence
            if random.random() < 0.1:
                emitter.modulation_confidence = min(100, emitter.modulation_confidence + random.uniform(0, 5))

            # Update DF if tracking
            if emitter.status == EmitterStatus.TRACKING and emitter.df_result:
                # Slowly improve CEP
                if emitter.df_result.cep_m > 30:
                    emitter.df_result.cep_m *= 0.98
                    emitter.df_result.confidence = min(100, emitter.df_result.confidence + 0.5)

        # Randomly add new emitters (low probability)
        if random.random() < 0.05 and self._emitters.count() < 30:
            self._add_random_emitter()

        # Randomly lose an emitter (very low probability)
        if random.random() < 0.02:
            emitters = self._emitters.get_all()
            if emitters:
                candidate = random.choice(emitters)
                if candidate.criticality < 50:  # Don't lose high-crit emitters
                    candidate.status = EmitterStatus.LOST
                    self.emitter_lost.emit(candidate.id)

        # Update EP status
        self._update_ep_status()

        # Generate spectrum data
        self._generate_spectrum_data()

        # Mark old emitters as lost
        self._emitters.mark_lost(timeout_seconds=60)

        # Check for auto-queue
        self.check_auto_queue()

        # Simulate bearing data for emitters without good CEP
        self._simulate_bearing_data()

    def _generate_initial_emitters(self):
        """Generate initial set of emitters for simulation."""
        # Add some known threats
        for i, threat in enumerate(EW_THREAT_LIBRARY[:2]):
            freq = random.uniform(threat["freq_range"][0], threat["freq_range"][1])
            emitter = self._emitters.add(freq, 25.0, random.uniform(-70, -50))
            emitter.modulation = random.choice(threat["modulation"])
            emitter.modulation_confidence = random.uniform(70, 95)
            emitter.emitter_type = EmitterType.TACTICAL_RADIO
            emitter.library_match = threat["name"]
            emitter.library_match_confidence = random.uniform(60, 90)
            emitter.purpose = threat["purpose"]
            emitter.threat_level = threat["threat_level"]
            self._calculate_criticality(emitter)
            self._add_df_result(emitter)
            self.emitter_detected.emit(emitter.id)

        # Add some benign emitters
        for i, benign in enumerate(EW_BENIGN_LIBRARY[:2]):
            freq = random.uniform(benign["freq_range"][0], benign["freq_range"][1])
            emitter = self._emitters.add(freq, 100.0, random.uniform(-80, -60))
            emitter.modulation = random.choice(benign["modulation"])
            emitter.modulation_confidence = random.uniform(80, 98)
            emitter.emitter_type = EmitterType.BROADCAST if "Broadcast" in benign["name"] else EmitterType.WIFI
            emitter.library_match = benign["name"]
            emitter.library_match_confidence = random.uniform(80, 95)
            emitter.purpose = benign["purpose"]
            emitter.threat_level = "NEUTRAL"
            self._calculate_criticality(emitter)
            self.emitter_detected.emit(emitter.id)

        # Add some unknown suspicious
        for i in range(2):
            band = random.choice(EW_SWEEP_BANDS)
            freq = random.uniform(band["start_mhz"], band["end_mhz"])
            emitter = self._emitters.add(freq, random.uniform(10, 50), random.uniform(-75, -55))
            emitter.modulation = random.choice(EW_MODULATION_TYPES[:5])
            emitter.modulation_confidence = random.uniform(40, 70)
            emitter.emitter_type = EmitterType.UNKNOWN_SUSPICIOUS
            emitter.purpose = "UNKNOWN"
            emitter.threat_level = "UNKNOWN"
            self._calculate_criticality(emitter)
            self._add_df_result(emitter)
            self.emitter_detected.emit(emitter.id)

        # Add friendly (our mesh)
        emitter = self._emitters.add(868.5, 125.0, -45.0)
        emitter.modulation = "LoRa"
        emitter.modulation_confidence = 98.0
        emitter.emitter_type = EmitterType.FRIENDLY
        emitter.library_match = "Own Mesh (T-Beam)"
        emitter.library_match_confidence = 100.0
        emitter.purpose = "MESH_NODE"
        emitter.threat_level = "FRIENDLY"
        emitter.criticality = 5.0  # Low criticality for friendlies
        self.emitter_detected.emit(emitter.id)

    def _add_random_emitter(self):
        """Add a random emitter during simulation."""
        band = random.choice(EW_SWEEP_BANDS)
        freq = random.uniform(band["start_mhz"], band["end_mhz"])
        bw = random.uniform(10, 100)
        power = random.uniform(-85, -50)

        emitter = self._emitters.add(freq, bw, power)
        emitter.modulation = random.choice(EW_MODULATION_TYPES)
        emitter.modulation_confidence = random.uniform(30, 80)

        # Randomly classify
        if random.random() < 0.3:
            emitter.emitter_type = EmitterType.UNKNOWN_SUSPICIOUS
            emitter.purpose = "UNKNOWN"
        else:
            emitter.emitter_type = EmitterType.UNKNOWN_BENIGN
            emitter.purpose = "UNKNOWN"

        self._calculate_criticality(emitter)

        if emitter.criticality > 40:
            self._add_df_result(emitter)

        self.emitter_detected.emit(emitter.id)

        if emitter.criticality >= 80:
            self.critical_threat.emit(emitter.id)

    def _add_df_result(self, emitter: Emitter):
        """Add simulated DF result to emitter within range of swarm."""
        # Convert km to degrees (approx: 1 degree lat = 111km, lon varies with lat)
        range_deg_lat = self._sim_range_km / 111.0  # ~0.027 for 3km
        range_deg_lon = self._sim_range_km / (111.0 * math.cos(math.radians(self._sim_base_lat)))

        # Random position within ±3km of swarm base
        lat = self._sim_base_lat + random.uniform(-range_deg_lat, range_deg_lat)
        lon = self._sim_base_lon + random.uniform(-range_deg_lon, range_deg_lon)

        # CEP based on emitter power (stronger = better fix)
        base_cep = 200 - (emitter.power_dbm + 100) * 2  # -50 dBm → 100m, -80 dBm → 160m
        cep = max(30, min(300, base_cep + random.uniform(-30, 30)))

        emitter.df_result = DFResult(
            lat=lat,
            lon=lon,
            cep_m=cep,
            method="TDOA",
            sensors=["chick1.1", "chick1.2"],
            confidence=random.uniform(50, 80)
        )

    def _calculate_criticality(self, emitter: Emitter):
        """Calculate criticality score for emitter."""
        score = 0.0

        # Known signature match (35%)
        if emitter.library_match and "Tactical" in emitter.library_match:
            score += EW_CRITICALITY_WEIGHTS["known_signature"] * 100
        elif emitter.library_match and emitter.threat_level == "HOSTILE":
            score += EW_CRITICALITY_WEIGHTS["known_signature"] * 80

        # Band overlap with own systems (20%)
        for band in EW_GUARD_BANDS:
            if band["start_mhz"] <= emitter.freq_mhz <= band["end_mhz"]:
                score += EW_CRITICALITY_WEIGHTS["band_overlap"] * 100
                break

        # Proximity (15%) - simulated as random for now
        if emitter.df_result and emitter.df_result.cep_m < 150:
            score += EW_CRITICALITY_WEIGHTS["proximity"] * 80

        # Signal strength (10%)
        if emitter.power_dbm > -60:
            score += EW_CRITICALITY_WEIGHTS["signal_strength"] * 100
        elif emitter.power_dbm > -75:
            score += EW_CRITICALITY_WEIGHTS["signal_strength"] * 50

        # New emitter (10%)
        if emitter.status == EmitterStatus.NEW:
            score += EW_CRITICALITY_WEIGHTS["new_emitter"] * 60

        # Rapid change (10%) - not applicable in initial calculation

        # Reduce criticality for known benign
        if emitter.emitter_type in [EmitterType.BROADCAST, EmitterType.WIFI,
                                     EmitterType.CELLULAR, EmitterType.FRIENDLY]:
            score *= 0.3

        emitter.criticality = min(100, max(0, score))

    def _update_ep_status(self):
        """Update EP status based on current emitters."""
        emitters = self._emitters.get_all()
        self._ep_status.update_from_emitters(emitters)

        # Simulate link health variation
        self._ep_status.link_health_pct += random.uniform(-2, 2)
        self._ep_status.link_health_pct = max(50, min(100, self._ep_status.link_health_pct))
        self._ep_status.packet_loss_pct = 100 - self._ep_status.link_health_pct

        # Check if hop recommended
        if self._ep_status.is_hop_recommended():
            self.hop_recommended.emit()

        self.ep_status_changed.emit()

    def _simulate_bearing_data(self):
        """Add simulated bearing data to emitters that don't have good location."""
        for emitter in self._emitters.get_all():
            # Skip emitters with good CEP
            if emitter.has_displayable_location():
                continue

            # Only add bearings for HIGH/CRITICAL
            if emitter.get_criticality_level() not in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                continue

            # Simulate bearing from each vehicle
            for vid, (vlat, vlon, valt) in self._vehicle_positions.items():
                if emitter.df_result:
                    # Calculate true bearing and add some noise
                    dx = emitter.df_result.lon - vlon
                    dy = emitter.df_result.lat - vlat
                    true_bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
                    noisy_bearing = true_bearing + random.uniform(-15, 15)
                    emitter.bearing_from_sensors[vid] = noisy_bearing % 360

    def _generate_spectrum_data(self):
        """Generate spectrum data for display."""
        # Generate FFT-like data for current band
        num_points = 256
        noise_floor = -95
        data = [noise_floor + random.uniform(0, 5) for _ in range(num_points)]

        # Add peaks for known emitters
        for emitter in self._emitters.get_all():
            # Map frequency to bin (assuming 400-500 MHz display)
            if 400 <= emitter.freq_mhz <= 500:
                bin_idx = int((emitter.freq_mhz - 400) / 100 * num_points)
                bin_idx = max(0, min(num_points - 1, bin_idx))

                # Add peak with some width
                for offset in range(-3, 4):
                    idx = bin_idx + offset
                    if 0 <= idx < num_points:
                        peak = emitter.power_dbm - abs(offset) * 3
                        data[idx] = max(data[idx], peak)

        self._spectrum_data["400-500"] = data

        # Update waterfall history
        self._waterfall_history.append(data.copy())
        if len(self._waterfall_history) > 100:
            self._waterfall_history.pop(0)

    # ==================== ES Operations ====================

    def calculate_all_criticality(self):
        """Recalculate criticality for all emitters."""
        for emitter in self._emitters.get_all():
            self._calculate_criticality(emitter)

    def request_df(self, emitter_id: str):
        """Request DF coordination for an emitter."""
        emitter = self._emitters.get(emitter_id)
        if emitter and emitter_id not in self._df_active_emitters:
            self._df_active_emitters.append(emitter_id)
            emitter.status = EmitterStatus.TRACKING

            # In simulation, add DF result after delay
            if self._simulation_mode and not emitter.df_result:
                QTimer.singleShot(2000, lambda: self._add_df_result(emitter))

    def stop_df(self, emitter_id: str):
        """Stop DF coordination for an emitter."""
        if emitter_id in self._df_active_emitters:
            self._df_active_emitters.remove(emitter_id)

    # ==================== EP Operations ====================

    def initiate_hop(self) -> bool:
        """Initiate frequency hop."""
        if self._ep_status.hop_status.state != "READY":
            return False

        self._ep_status.hop_status.state = "HOPPING"
        next_index = (self._ep_status.hop_status.current_index + 1) % \
                     self._ep_status.hop_status.total_entries

        # Simulate hop delay
        QTimer.singleShot(1000, lambda: self._complete_hop(next_index))

        self.hop_initiated.emit(next_index)
        return True

    def _complete_hop(self, new_index: int):
        """Complete frequency hop."""
        self._ep_status.hop_status.current_index = new_index
        self._ep_status.hop_status.state = "READY"
        self._ep_status.hop_status.last_hop_time = time.time()
        self._ep_status.hop_status.hops_since_start += 1

        # Improve link health after hop (simulation)
        if self._simulation_mode:
            self._ep_status.link_health_pct = min(100, self._ep_status.link_health_pct + 20)
            self._ep_status.packet_loss_pct = 100 - self._ep_status.link_health_pct

    # ==================== Target Integration ====================

    def emitter_to_target(self, emitter_id: str) -> Optional[dict]:
        """
        Convert emitter to target data.

        Returns dict with target info if emitter has location.
        """
        emitter = self._emitters.get(emitter_id)
        if not emitter or not emitter.has_location():
            return None

        return {
            "source": "EW_EMITTER",
            "source_id": emitter_id,
            "lat": emitter.df_result.lat,
            "lon": emitter.df_result.lon,
            "cep_m": emitter.df_result.cep_m,
            "emitter_type": emitter.emitter_type.value,
            "freq_mhz": emitter.freq_mhz,
            "criticality": emitter.criticality,
            "auto_update": True
        }

    def update_target_from_emitter(self, emitter_id: str) -> Optional[dict]:
        """Get updated position for target from emitter."""
        emitter = self._emitters.get(emitter_id)
        if not emitter or not emitter.df_result:
            return None

        return {
            "lat": emitter.df_result.lat,
            "lon": emitter.df_result.lon,
            "cep_m": emitter.df_result.cep_m
        }

    # ==================== Configuration ====================

    def set_base_position(self, lat: float, lon: float):
        """Set the base position for emitter generation (from swarm position)."""
        self._sim_base_lat = lat
        self._sim_base_lon = lon

    def set_emitter_range(self, range_km: float):
        """Set the range for emitter generation (km from base)."""
        self._sim_range_km = range_km

    # ==================== DF Geometry Optimization ====================

    def calculate_optimal_df_positions(self, emitter_ids: List[str] = None,
                                        vehicle_positions: Dict[str, tuple] = None) -> Dict[str, tuple]:
        """
        Calculate optimal vehicle positions for DF on selected emitters.

        For good TDOA/AOA geometry, we want vehicles spread out with good
        angular diversity relative to the emitter(s).

        Args:
            emitter_ids: Emitters to optimize for (None = all tracked)
            vehicle_positions: Current positions {id: (lat, lon, alt)}

        Returns:
            Recommended positions {vehicle_id: (lat, lon, alt)}
        """
        # Get emitters to optimize for
        if emitter_ids:
            emitters = [self._emitters.get(eid) for eid in emitter_ids]
            emitters = [e for e in emitters if e and e.df_result]
        else:
            # Use all tracked emitters
            emitters = [e for e in self._emitters.get_all()
                       if e.status == EmitterStatus.TRACKING and e.df_result]

        if not emitters:
            return {}

        # Calculate centroid of emitters
        avg_lat = sum(e.df_result.lat for e in emitters) / len(emitters)
        avg_lon = sum(e.df_result.lon for e in emitters) / len(emitters)

        # Optimal formation: spread vehicles around emitter centroid
        # Triangle formation for 3 vehicles at ~2km radius
        optimal_radius_km = 2.0
        radius_deg_lat = optimal_radius_km / 111.0
        radius_deg_lon = optimal_radius_km / (111.0 * math.cos(math.radians(avg_lat)))

        # Define positions at 120° intervals
        positions = {}

        # Bird: North of target
        positions["bird1"] = (
            avg_lat + radius_deg_lat,
            avg_lon,
            150  # Altitude
        )

        # Chick1: Southwest
        angle_sw = math.radians(210)  # 210° from north
        positions["chick1.1"] = (
            avg_lat + radius_deg_lat * math.cos(angle_sw),
            avg_lon + radius_deg_lon * math.sin(angle_sw),
            120
        )

        # Chick2: Southeast
        angle_se = math.radians(330)  # 330° from north
        positions["chick1.2"] = (
            avg_lat + radius_deg_lat * math.cos(angle_se),
            avg_lon + radius_deg_lon * math.sin(angle_se),
            120
        )

        return positions

    def command_optimal_formation(self, emitter_ids: List[str] = None,
                                   current_positions: Dict[str, tuple] = None) -> bool:
        """
        Command vehicles to optimal DF positions.

        Args:
            emitter_ids: Emitters to optimize for
            current_positions: Current vehicle positions

        Returns:
            True if command was emitted
        """
        optimal = self.calculate_optimal_df_positions(emitter_ids, current_positions)

        if optimal:
            self.formation_commanded.emit(optimal)
            return True

        return False

    def get_df_geometry_quality(self, emitter: Emitter,
                                 vehicle_positions: Dict[str, tuple] = None) -> float:
        """
        Calculate quality score for current DF geometry (0-100).

        Good geometry means:
        - Multiple sensors with good angular separation
        - Reasonable distances (not too close, not too far)
        """
        if not emitter.df_result or not vehicle_positions:
            return 0.0

        if len(vehicle_positions) < 2:
            return 20.0  # Single sensor = poor geometry

        # Calculate angles from emitter to each vehicle
        angles = []
        for vid, (lat, lon, alt) in vehicle_positions.items():
            dx = lon - emitter.df_result.lon
            dy = lat - emitter.df_result.lat
            angle = math.atan2(dx, dy)
            angles.append(angle)

        if len(angles) < 2:
            return 20.0

        # Calculate angular separation
        angles.sort()
        separations = []
        for i in range(len(angles)):
            sep = angles[(i + 1) % len(angles)] - angles[i]
            if sep < 0:
                sep += 2 * math.pi
            separations.append(sep)

        # Ideal: equal separation (120° for 3 sensors)
        ideal_sep = 2 * math.pi / len(angles)
        variance = sum((s - ideal_sep) ** 2 for s in separations) / len(separations)

        # Score: 100 for perfect, decreasing with variance
        score = max(0, 100 - variance * 100)

        return score

    # ==================== Vehicle Position Tracking ====================

    def update_vehicle_position(self, vehicle_id: str, lat: float, lon: float, alt: float):
        """Update tracked vehicle position (called from app on telemetry)."""
        self._vehicle_positions[vehicle_id] = (lat, lon, alt)

    def get_vehicle_positions(self) -> Dict[str, tuple]:
        """Get current vehicle positions."""
        return self._vehicle_positions.copy()

    # ==================== Prosecution Workflow ====================

    def prosecute_emitter(self, emitter_id: str) -> bool:
        """
        Start prosecution workflow for an emitter.
        Called when operator right-clicks "PROSECUTE" on a track.
        """
        emitter = self._emitters.get(emitter_id)
        if not emitter:
            return False

        # Mark as priority and queue
        emitter.priority_track = True
        emitter.set_prosecution_state(ProsecutionState.QUEUED)

        if emitter_id not in self._prosecution_queue:
            self._prosecution_queue.append(emitter_id)

        self.emitter_queued.emit(emitter_id)
        self.priority_tracks_changed.emit()

        print(f"[EW] Emitter {emitter_id} queued for prosecution")
        return True

    def start_locating(self, emitter_id: str) -> bool:
        """
        Start DF optimization phase - command swarm to optimal formation.
        """
        emitter = self._emitters.get(emitter_id)
        if not emitter:
            return False

        emitter.set_prosecution_state(ProsecutionState.LOCATING)
        self.priority_tracks_changed.emit()

        # Command optimal formation
        self.command_optimal_formation([emitter_id], self._vehicle_positions)

        print(f"[EW] Locating emitter {emitter_id} - commanding optimal formation")
        return True

    def assign_prosecution_vehicle(self, emitter_id: str,
                                    action: ProsecutionAction) -> Optional[str]:
        """
        Assign nearest available Chick to prosecute emitter.
        Returns assigned vehicle ID or None.
        """
        emitter = self._emitters.get(emitter_id)
        if not emitter or not emitter.df_result:
            return None

        # Find nearest Chick
        nearest_vehicle = self._find_nearest_chick(
            emitter.df_result.lat,
            emitter.df_result.lon
        )

        if not nearest_vehicle:
            print(f"[EW] No available Chick for prosecution")
            return None

        # Update emitter state
        emitter.set_prosecution_state(ProsecutionState.PROSECUTING)
        emitter.set_prosecution_action(action)
        emitter.assigned_vehicle = nearest_vehicle

        self.prosecution_started.emit(emitter_id, nearest_vehicle)
        self.priority_tracks_changed.emit()

        # Request vehicle assignment (app will confirm with operator)
        self.vehicle_assignment_requested.emit(
            emitter_id,
            nearest_vehicle,
            emitter.df_result.lat,
            emitter.df_result.lon
        )

        print(f"[EW] Assigned {nearest_vehicle} to prosecute {emitter_id} ({action.value})")
        return nearest_vehicle

    def _find_nearest_chick(self, lat: float, lon: float) -> Optional[str]:
        """Find nearest available Chick to a location."""
        min_dist = float('inf')
        nearest = None

        for vid, (vlat, vlon, valt) in self._vehicle_positions.items():
            # Only consider Chicks (not Bird)
            if 'chick' not in vid.lower():
                continue

            # Check if already assigned
            for emitter in self._emitters.get_all():
                if emitter.assigned_vehicle == vid and emitter.is_being_prosecuted():
                    continue  # Skip already assigned

            # Calculate distance
            dist = math.sqrt((lat - vlat) ** 2 + (lon - vlon) ** 2) * 111000  # Approx meters

            if dist < min_dist:
                min_dist = dist
                nearest = vid

        return nearest

    def complete_prosecution(self, emitter_id: str, success: bool = True):
        """Mark prosecution as complete."""
        emitter = self._emitters.get(emitter_id)
        if not emitter:
            return

        emitter.set_prosecution_state(ProsecutionState.RESOLVED)
        emitter.assigned_vehicle = None

        if emitter_id in self._prosecution_queue:
            self._prosecution_queue.remove(emitter_id)

        self.prosecution_complete.emit(emitter_id)
        self.priority_tracks_changed.emit()

        print(f"[EW] Prosecution complete for {emitter_id}")

    def cancel_prosecution(self, emitter_id: str):
        """Cancel prosecution and return to tracking."""
        emitter = self._emitters.get(emitter_id)
        if not emitter:
            return

        emitter.set_prosecution_state(ProsecutionState.NONE)
        emitter.prosecution_action = None
        emitter.assigned_vehicle = None
        emitter.priority_track = False

        if emitter_id in self._prosecution_queue:
            self._prosecution_queue.remove(emitter_id)

        self.priority_tracks_changed.emit()

    def check_auto_queue(self):
        """Check for high-priority emitters that should auto-queue."""
        changed = False
        for emitter in self._emitters.get_all():
            # Auto-queue CRITICAL or HIGH that aren't already being prosecuted
            if (emitter.get_criticality_level() in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]
                and not emitter.is_being_prosecuted()
                and emitter.prosecution_state == ProsecutionState.NONE.value
                and emitter.id not in self._prosecution_queue):

                emitter.set_prosecution_state(ProsecutionState.QUEUED)
                self._prosecution_queue.append(emitter.id)
                self.emitter_queued.emit(emitter.id)
                print(f"[EW] Auto-queued {emitter.id} (criticality: {emitter.criticality:.0f})")
                changed = True

        # Only emit if something changed
        if changed:
            self.priority_tracks_changed.emit()

    def get_prosecution_queue(self) -> List[Emitter]:
        """Get ordered list of emitters in prosecution queue."""
        return [self._emitters.get(eid) for eid in self._prosecution_queue
                if self._emitters.get(eid)]

    # ==================== Map Display Data ====================

    def get_displayable_emitters(self) -> List[dict]:
        """
        Get emitters that should be displayed on map.
        Returns list of dicts with display info.
        """
        result = []

        for emitter in self._emitters.get_all():
            # Check if should display (HIGH/CRITICAL)
            level = emitter.get_criticality_level()
            if level not in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                continue

            display_data = {
                'id': emitter.id,
                'criticality': emitter.criticality,
                'level': level.value,
                'type': emitter.emitter_type.value,
                'priority': emitter.priority_track,
                'prosecution_state': emitter.prosecution_state,
                'assigned_vehicle': emitter.assigned_vehicle,
            }

            # If CEP < 300m, display position
            if emitter.has_displayable_location():
                display_data['lat'] = emitter.df_result.lat
                display_data['lon'] = emitter.df_result.lon
                display_data['cep_m'] = emitter.df_result.cep_m
                display_data['display_type'] = 'position'
            # Otherwise display bearing lines if available
            elif emitter.bearing_from_sensors:
                display_data['bearings'] = emitter.bearing_from_sensors.copy()
                display_data['display_type'] = 'bearing'
            else:
                # Skip if no display data
                continue

            result.append(display_data)

        return result

    def add_bearing_data(self, emitter_id: str, sensor_id: str, bearing_deg: float):
        """Add bearing observation from a sensor."""
        emitter = self._emitters.get(emitter_id)
        if emitter:
            emitter.bearing_from_sensors[sensor_id] = bearing_deg
            self.priority_tracks_changed.emit()
