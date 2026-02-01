# Mission Planning Panel for SwarmDrones GCS
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QListWidget, QListWidgetItem,
                              QComboBox, QSpinBox, QDoubleSpinBox, QDialog,
                              QFormLayout, QDialogButtonBox, QMessageBox,
                              QFileDialog, QGroupBox, QCheckBox, QLineEdit,
                              QAbstractItemView, QShortcut, QMenu, QAction,
                              QScrollArea, QSizePolicy, QTimeEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTime
from PyQt5.QtGui import QFont, QColor, QKeySequence
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import copy

from ..models.mission import Mission, Waypoint, WaypointType
from ..config import SWARM_CONFIG
import math


@dataclass
class SwarmConfig:
    """Configuration for swarm behavior."""
    formation: str = "none"  # none, line, echelon_r, echelon_l, vee, trail, spread
    spacing: float = 50.0    # meters between vehicles
    alt_offset: float = -10.0  # altitude offset for chicks (negative = lower)
    coord_mode: str = "dynamic"  # dynamic (true swarm), waypoint (pre-planned)
    attack_pattern: str = "sequential"  # sequential, converge, spread


class SwarmCalculator:
    """
    Calculates formation positions and generates chick missions.

    Two supported formations:
    1. LINE ABREAST: All three fly same path, chicks offset left/right
       - Bird in center
       - Chick1 to the LEFT at {spacing} meters
       - Chick2 to the RIGHT at {spacing} meters

    2. TRAIL (Follow the Leader): Chicks follow behind at set spacing
       - Bird leads
       - Chick1 released first, follows at 1x spacing behind
       - Chick2 released second, follows at 2x spacing behind
    """

    @classmethod
    def offset_coordinate(cls, lat: float, lon: float, heading: float,
                          offset_right: float, offset_back: float) -> Tuple[float, float]:
        """
        Calculate new lat/lon given offsets relative to a heading.

        Args:
            lat, lon: Reference position
            heading: Direction of travel in degrees (0=North)
            offset_right: Meters to the right (negative = left)
            offset_back: Meters behind (negative = ahead)

        Returns:
            (new_lat, new_lon)
        """
        heading_rad = math.radians(heading)
        right_bearing = heading_rad + math.pi / 2
        back_bearing = heading_rad + math.pi

        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(lat))

        total_lat_offset = (
            offset_right * math.cos(right_bearing) / meters_per_deg_lat +
            offset_back * math.cos(back_bearing) / meters_per_deg_lat
        )
        total_lon_offset = (
            offset_right * math.sin(right_bearing) / meters_per_deg_lon +
            offset_back * math.sin(back_bearing) / meters_per_deg_lon
        )

        return (lat + total_lat_offset, lon + total_lon_offset)

    @classmethod
    def _bearing_between(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing in degrees from point 1 to point 2."""
        d_lon = math.radians(lon2 - lon1)
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)

        x = math.sin(d_lon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    @classmethod
    def generate_line_abreast(cls, bird_mission: Mission, chick_id: str,
                              chick_index: int, spacing: float, alt_offset: float) -> Mission:
        """
        Generate LINE ABREAST mission.

        All three vehicles fly the same path side by side:
        - Bird in center
        - Chick1 to the LEFT
        - Chick2 to the RIGHT
        """
        chick_mission = Mission(
            name=f"Line Abreast - {chick_id.upper()}",
            vehicle_id=chick_id
        )

        # Chick1 (index 0) = LEFT = negative offset
        # Chick2 (index 1) = RIGHT = positive offset
        right_offset = -spacing if chick_index == 0 else spacing

        wp_id = 1
        for i, wp in enumerate(bird_mission.waypoints):
            if wp.type == WaypointType.LAUNCH_CHICK:
                continue  # Skip launch waypoints

            if wp.type == WaypointType.RTL:
                chick_mission.waypoints.append(Waypoint(
                    id=wp_id, type=WaypointType.RTL,
                    lat=0, lon=0, alt=0, name="RTL"
                ))
                wp_id += 1
                continue

            # Calculate heading to next waypoint
            heading = 0
            for j in range(i + 1, len(bird_mission.waypoints)):
                next_wp = bird_mission.waypoints[j]
                if next_wp.type not in (WaypointType.RTL, WaypointType.LAUNCH_CHICK):
                    heading = cls._bearing_between(wp.lat, wp.lon, next_wp.lat, next_wp.lon)
                    break

            # Apply lateral offset only
            new_lat, new_lon = cls.offset_coordinate(wp.lat, wp.lon, heading, right_offset, 0)

            chick_mission.waypoints.append(Waypoint(
                id=wp_id, type=wp.type,
                lat=new_lat, lon=new_lon,
                alt=wp.alt + alt_offset,
                param1=wp.param1, param2=wp.param2, name=wp.name
            ))
            wp_id += 1

        chick_mission._next_id = wp_id
        return chick_mission

    @classmethod
    def generate_trail(cls, bird_mission: Mission, chick_id: str,
                       chick_index: int, spacing: float, alt_offset: float) -> Mission:
        """
        Generate TRAIL (follow the leader) mission.

        Process:
        1. Find the LAUNCH_CHICK waypoint for this chick
        2. Chick mission starts there
        3. All subsequent waypoints are offset BEHIND the bird's path

        Chick1 trails at 1x spacing, Chick2 at 2x spacing.
        """
        chick_mission = Mission(
            name=f"Trail - {chick_id.upper()}",
            vehicle_id=chick_id
        )

        # Find launch point for this chick
        launch_idx = None
        chick_num = chick_index + 1  # 1 or 2

        for i, wp in enumerate(bird_mission.waypoints):
            if wp.type == WaypointType.LAUNCH_CHICK:
                wp_name = wp.name.lower()
                if (f"chick{chick_num}" in wp_name or
                    f"chk{chick_num}" in wp_name or
                    f"slot {chick_num}" in wp_name):
                    launch_idx = i
                    break

        if launch_idx is None:
            # No launch point - start from beginning
            launch_idx = 0

        # Trail offset: chick1 at 1x, chick2 at 2x
        back_offset = spacing * (chick_index + 1)

        wp_id = 1
        for i in range(launch_idx, len(bird_mission.waypoints)):
            wp = bird_mission.waypoints[i]

            if wp.type == WaypointType.LAUNCH_CHICK:
                # Add takeoff at launch location
                chick_mission.waypoints.append(Waypoint(
                    id=wp_id, type=WaypointType.WAYPOINT,
                    lat=wp.lat, lon=wp.lon, alt=wp.alt + alt_offset,
                    name="Start"
                ))
                wp_id += 1
                continue

            if wp.type == WaypointType.RTL:
                chick_mission.waypoints.append(Waypoint(
                    id=wp_id, type=WaypointType.RTL,
                    lat=0, lon=0, alt=0, name="RTL"
                ))
                wp_id += 1
                continue

            # Calculate heading to next waypoint
            heading = 0
            for j in range(i + 1, len(bird_mission.waypoints)):
                next_wp = bird_mission.waypoints[j]
                if next_wp.type not in (WaypointType.RTL, WaypointType.LAUNCH_CHICK):
                    heading = cls._bearing_between(wp.lat, wp.lon, next_wp.lat, next_wp.lon)
                    break

            # Apply trail (back) offset only
            new_lat, new_lon = cls.offset_coordinate(wp.lat, wp.lon, heading, 0, back_offset)

            chick_mission.waypoints.append(Waypoint(
                id=wp_id, type=wp.type,
                lat=new_lat, lon=new_lon,
                alt=wp.alt + alt_offset,
                param1=wp.param1, param2=wp.param2, name=wp.name
            ))
            wp_id += 1

        chick_mission._next_id = wp_id
        return chick_mission

    @classmethod
    def generate_chick_mission(cls, bird_mission: Mission, chick_id: str,
                               chick_index: int, config: SwarmConfig) -> Mission:
        """Generate chick mission based on formation type."""
        if config.formation == "line":
            return cls.generate_line_abreast(
                bird_mission, chick_id, chick_index,
                config.spacing, config.alt_offset
            )
        elif config.formation == "trail":
            return cls.generate_trail(
                bird_mission, chick_id, chick_index,
                config.spacing, config.alt_offset
            )
        else:
            # No formation - empty mission
            return Mission(name=f"{chick_id} Mission", vehicle_id=chick_id)

    @classmethod
    def calculate_formation_position(cls, bird_lat: float, bird_lon: float,
                                      bird_heading: float, bird_alt: float,
                                      chick_index: int, config: 'SwarmConfig') -> Tuple[float, float, float]:
        """
        Calculate where a chick should be RIGHT NOW based on bird's current position.

        This is the core of TRUE SWARMING - called every telemetry update to
        continuously adjust chick target positions based on bird's actual location.

        Args:
            bird_lat, bird_lon: Bird's current GPS position
            bird_heading: Bird's current heading (degrees)
            bird_alt: Bird's current altitude
            chick_index: 0 for chick1, 1 for chick2
            config: SwarmConfig with formation, spacing, alt_offset

        Returns:
            (target_lat, target_lon, target_alt) - where this chick should fly to
        """
        spacing = config.spacing
        alt_offset = config.alt_offset

        # Calculate offsets based on formation type
        if config.formation == "line":
            # Line Abreast: chicks fly alongside bird
            # Chick1 = LEFT, Chick2 = RIGHT
            right_offset = -spacing if chick_index == 0 else spacing
            back_offset = 0

        elif config.formation == "trail":
            # Trail: chicks follow behind at increasing distances
            # Chick1 = 1x spacing behind, Chick2 = 2x spacing behind
            right_offset = 0
            back_offset = spacing * (chick_index + 1)

        elif config.formation == "echelon_r":
            # Echelon Right: stepped formation to the right
            right_offset = spacing * (chick_index + 1)
            back_offset = spacing * (chick_index + 1) * 0.5

        elif config.formation == "echelon_l":
            # Echelon Left: stepped formation to the left
            right_offset = -spacing * (chick_index + 1)
            back_offset = spacing * (chick_index + 1) * 0.5

        elif config.formation == "vee":
            # V Formation: both chicks behind and to sides
            right_offset = -spacing if chick_index == 0 else spacing
            back_offset = spacing * 0.7  # Both at same distance back

        elif config.formation == "spread":
            # Wide spread: chicks far apart laterally
            right_offset = (-spacing * 2) if chick_index == 0 else (spacing * 2)
            back_offset = spacing * 0.5

        else:
            # No formation - stay at bird position
            return (bird_lat, bird_lon, bird_alt + alt_offset)

        # Apply offsets relative to bird's heading
        target_lat, target_lon = cls.offset_coordinate(
            bird_lat, bird_lon, bird_heading, right_offset, back_offset
        )

        return (target_lat, target_lon, bird_alt + alt_offset)

    @classmethod
    def calculate_attack_positions(cls, targets: List[Tuple[float, float]],
                                    chick_positions: List[Tuple[float, float]],
                                    pattern: str) -> Dict[str, List[Tuple[float, float]]]:
        """
        Calculate approach positions for orb deployment.

        Args:
            targets: List of (lat, lon) target positions
            chick_positions: Current positions of chicks
            pattern: Attack pattern type

        Returns:
            Dict mapping chick_id to list of approach waypoints
        """
        result = {"chick1": [], "chick2": []}

        if pattern == "sequential":
            # Chicks attack targets in order
            for i, target in enumerate(targets):
                chick_idx = i % 2
                chick_id = f"chick{chick_idx + 1}"
                result[chick_id].append(target)

        elif pattern == "converge":
            # All chicks converge on each target
            for target in targets:
                result["chick1"].append(target)
                result["chick2"].append(target)

        elif pattern == "spread":
            # Divide targets between chicks
            for i, target in enumerate(targets):
                if i < len(targets) // 2:
                    result["chick1"].append(target)
                else:
                    result["chick2"].append(target)

        elif pattern == "random":
            # Randomly assign targets
            import random
            for target in targets:
                chick_id = random.choice(["chick1", "chick2"])
                result[chick_id].append(target)

        return result


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


class WaypointDialog(QDialog):
    """Dialog for adding/editing a waypoint."""

    def __init__(self, parent=None, waypoint: Waypoint = None, default_alt: float = 100,
                 default_speed: float = 0, available_chicks: list = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Waypoint" if waypoint else "Add Waypoint")
        self.setMinimumWidth(350)
        self._waypoint = waypoint
        self._default_alt = default_alt
        self._default_speed = default_speed
        self._available_chicks = available_chicks or []
        self._setup_ui()

        if waypoint:
            self._load_waypoint(waypoint)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Waypoint type
        self.type_combo = QComboBox()
        for wt in WaypointType:
            self.type_combo.addItem(wt.value, wt)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Type:", self.type_combo)

        # Name (optional)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional name")
        form.addRow("Name:", self.name_edit)

        # Coordinates
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(6)
        self.lat_spin.setSingleStep(0.0001)
        form.addRow("Latitude:", self.lat_spin)

        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(6)
        self.lon_spin.setSingleStep(0.0001)
        form.addRow("Longitude:", self.lon_spin)

        # Altitude
        self.alt_spin = QSpinBox()
        self.alt_spin.setRange(0, 5000)
        self.alt_spin.setValue(int(self._default_alt))
        self.alt_spin.setSuffix(" m AGL")
        form.addRow("Altitude:", self.alt_spin)

        # Speed (for leg)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 50)
        self.speed_spin.setValue(int(self._default_speed))
        self.speed_spin.setSuffix(" m/s")
        self.speed_spin.setToolTip("Approach speed for this waypoint (0 = default)")
        form.addRow("Speed:", self.speed_spin)

        # Type-specific parameters
        self.param_group = QGroupBox("Parameters")
        param_layout = QFormLayout(self.param_group)

        # Chick selector (for LAUNCH_CHICK)
        self.chick_combo = QComboBox()
        for chick in self._available_chicks:
            self.chick_combo.addItem(chick["name"], chick["id"])
        if not self._available_chicks:
            self.chick_combo.addItem("CHK1", "chick1")
            self.chick_combo.addItem("CHK2", "chick2")
        self.chick_label = QLabel("Launch Chick:")
        param_layout.addRow(self.chick_label, self.chick_combo)

        # Loiter time (for LOITER_TIME)
        self.loiter_time_spin = QSpinBox()
        self.loiter_time_spin.setRange(1, 3600)
        self.loiter_time_spin.setValue(30)
        self.loiter_time_spin.setSuffix(" seconds")
        self.loiter_time_label = QLabel("Loiter Time:")
        param_layout.addRow(self.loiter_time_label, self.loiter_time_spin)

        # Is target checkbox
        self.is_target_check = QCheckBox("Mark as Target (for Orb assignment)")
        param_layout.addRow("", self.is_target_check)

        form.addRow(self.param_group)
        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_type_changed()

    def _on_type_changed(self):
        """Update UI based on waypoint type."""
        wp_type = self.type_combo.currentData()

        # Show/hide coordinate fields
        has_coords = wp_type not in (WaypointType.RTL,)
        self.lat_spin.setEnabled(has_coords)
        self.lon_spin.setEnabled(has_coords)

        # Show/hide parameters
        self.chick_label.setVisible(wp_type == WaypointType.LAUNCH_CHICK)
        self.chick_combo.setVisible(wp_type == WaypointType.LAUNCH_CHICK)
        self.loiter_time_label.setVisible(wp_type == WaypointType.LOITER_TIME)
        self.loiter_time_spin.setVisible(wp_type == WaypointType.LOITER_TIME)
        self.is_target_check.setVisible(wp_type in (WaypointType.WAYPOINT, WaypointType.LOITER))

        has_params = wp_type in (WaypointType.LAUNCH_CHICK, WaypointType.LOITER_TIME,
                                  WaypointType.WAYPOINT, WaypointType.LOITER)
        self.param_group.setVisible(has_params)

    def _load_waypoint(self, wp: Waypoint):
        """Load waypoint data into form."""
        idx = self.type_combo.findData(wp.type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.name_edit.setText(wp.name)
        self.lat_spin.setValue(wp.lat)
        self.lon_spin.setValue(wp.lon)
        self.alt_spin.setValue(int(wp.alt))
        self.speed_spin.setValue(int(wp.param2))  # Speed stored in param2

        if wp.type == WaypointType.LAUNCH_CHICK:
            # Try to find chick by name
            chick_id = wp.name.replace("Launch ", "").lower()
            for i in range(self.chick_combo.count()):
                if self.chick_combo.itemData(i) == chick_id:
                    self.chick_combo.setCurrentIndex(i)
                    break
        elif wp.type == WaypointType.LOITER_TIME:
            self.loiter_time_spin.setValue(int(wp.param1))
        elif wp.type == WaypointType.TARGET:
            self.is_target_check.setChecked(True)

    def get_waypoint_data(self) -> dict:
        """Get waypoint data from form."""
        wp_type = self.type_combo.currentData()

        # Convert to TARGET type if checkbox is checked
        if self.is_target_check.isChecked() and wp_type in (WaypointType.WAYPOINT, WaypointType.LOITER):
            wp_type = WaypointType.TARGET

        data = {
            "type": wp_type,
            "name": self.name_edit.text(),
            "lat": self.lat_spin.value(),
            "lon": self.lon_spin.value(),
            "alt": self.alt_spin.value(),
            "param1": 0,
            "param2": self.speed_spin.value(),  # Speed stored in param2
        }

        if wp_type == WaypointType.LAUNCH_CHICK:
            data["chick_id"] = self.chick_combo.currentData()
            data["name"] = f"Launch {self.chick_combo.currentText()}"
        elif wp_type == WaypointType.LOITER_TIME:
            data["param1"] = self.loiter_time_spin.value()

        return data

    def set_coordinates(self, lat: float, lon: float):
        """Set coordinates from map click."""
        self.lat_spin.setValue(lat)
        self.lon_spin.setValue(lon)


class MissionPanel(QFrame):
    """Panel for mission planning with undo/redo support."""

    # Signals
    mission_changed = pyqtSignal()
    upload_requested = pyqtSignal(str, object)  # vehicle_id, mission
    download_requested = pyqtSignal(str)  # vehicle_id - request to download from vehicle
    waypoint_selected = pyqtSignal(object)  # Waypoint or None
    add_waypoint_from_map = pyqtSignal()
    show_mission_on_map = pyqtSignal(object)  # Mission to display
    waypoint_edit_requested = pyqtSignal(int, float, float)  # wp_id, lat, lon from map
    vehicle_changed = pyqtSignal(str)  # vehicle_id - for updating map leg estimates
    swarm_activated = pyqtSignal(object)  # SwarmConfig - enable dynamic swarm tracking
    swarm_deactivated = pyqtSignal()  # disable swarm tracking

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._mission = Mission()
        self._default_alt = 100
        self._default_speed = 0  # 0 = use default cruise speed
        self._adding_from_map = False
        self._available_chicks = SWARM_CONFIG.get("chicks", [])
        self._available_birds = SWARM_CONFIG.get("birds", [])
        self._setup_ui()
        self._setup_shortcuts()
        self._update_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("MISSION PLANNER")
        title.setObjectName("header")
        header.addWidget(title)
        header.addStretch()

        # Vehicle selector - dynamic from config
        header.addWidget(QLabel("Vehicle:"))
        self.vehicle_combo = QComboBox()
        # Add all birds
        for bird in self._available_birds:
            self.vehicle_combo.addItem(f"{bird['icon']} {bird['name']}", bird["id"])
        # Add all chicks
        for chick in self._available_chicks:
            self.vehicle_combo.addItem(f"{chick['icon']} {chick['name']}", chick["id"])
        self.vehicle_combo.setFixedWidth(100)
        self.vehicle_combo.currentIndexChanged.connect(self._on_vehicle_changed)
        header.addWidget(self.vehicle_combo)

        layout.addLayout(header)

        # Toolbar row 1 - Add waypoints + Map click mode (consolidated)
        toolbar1 = QHBoxLayout()
        toolbar1.setSpacing(2)

        add_wp_btn = QPushButton("+WP")
        add_wp_btn.setToolTip("Add navigation waypoint")
        add_wp_btn.setFixedWidth(35)
        add_wp_btn.clicked.connect(lambda: self._add_waypoint(WaypointType.WAYPOINT))
        toolbar1.addWidget(add_wp_btn)

        add_launch_btn = QPushButton("+LCH")
        add_launch_btn.setToolTip("Add chick launch point")
        add_launch_btn.setFixedWidth(40)
        add_launch_btn.setStyleSheet("QPushButton { background-color: #dc2626; }")
        add_launch_btn.clicked.connect(self._add_launch_point)
        toolbar1.addWidget(add_launch_btn)

        add_target_btn = QPushButton("+TGT")
        add_target_btn.setToolTip("Add target for orb assignment")
        add_target_btn.setFixedWidth(40)
        add_target_btn.setStyleSheet("QPushButton { background-color: #f97316; }")
        add_target_btn.clicked.connect(lambda: self._add_waypoint(WaypointType.TARGET))
        toolbar1.addWidget(add_target_btn)

        add_loiter_btn = QPushButton("+LOI")
        add_loiter_btn.setToolTip("Add loiter point")
        add_loiter_btn.setFixedWidth(35)
        add_loiter_btn.clicked.connect(lambda: self._add_waypoint(WaypointType.LOITER))
        toolbar1.addWidget(add_loiter_btn)

        add_rtl_btn = QPushButton("+RTL")
        add_rtl_btn.setToolTip("Add return to launch")
        add_rtl_btn.setFixedWidth(35)
        add_rtl_btn.clicked.connect(lambda: self._quick_add(WaypointType.RTL))
        toolbar1.addWidget(add_rtl_btn)

        toolbar1.addWidget(self._separator())

        # Map click mode (moved here from row 2)
        self.map_add_btn = QPushButton("Click2Map")
        self.map_add_btn.setCheckable(True)
        self.map_add_btn.setToolTip("Click on map to add waypoints (ESC to cancel)")
        self.map_add_btn.setFixedWidth(62)
        self.map_add_btn.clicked.connect(self._toggle_map_add_mode)
        toolbar1.addWidget(self.map_add_btn)

        self.map_wp_type = QComboBox()
        self.map_wp_type.addItem("WP", ("WAYPOINT", None))
        self.map_wp_type.addItem("TGT", ("TARGET", None))
        for chick in self._available_chicks:
            self.map_wp_type.addItem(f"L{chick['name']}", ("LAUNCH_CHICK", chick["id"]))
        self.map_wp_type.addItem("LOI", ("LOITER", None))
        self.map_wp_type.setFixedWidth(55)
        toolbar1.addWidget(self.map_wp_type)

        toolbar1.addStretch()
        layout.addLayout(toolbar1)

        # Toolbar row 2 - Altitude, Speed, Undo/Redo
        toolbar2 = QHBoxLayout()
        toolbar2.setSpacing(2)

        toolbar2.addWidget(QLabel("Alt:"))
        self.alt_spin = QSpinBox()
        self.alt_spin.setRange(10, 500)
        self.alt_spin.setValue(100)
        self.alt_spin.setSuffix("m")
        self.alt_spin.setFixedWidth(60)
        self.alt_spin.valueChanged.connect(lambda v: setattr(self, '_default_alt', v))
        toolbar2.addWidget(self.alt_spin)

        toolbar2.addWidget(QLabel("Spd:"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 50)
        self.speed_spin.setValue(0)
        self.speed_spin.setSuffix("m/s")
        self.speed_spin.setToolTip("Leg speed (0 = default cruise speed)")
        self.speed_spin.setFixedWidth(65)
        self.speed_spin.valueChanged.connect(lambda v: setattr(self, '_default_speed', v))
        toolbar2.addWidget(self.speed_spin)

        toolbar2.addStretch()

        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setToolTip("Ctrl+Z")
        self.undo_btn.setFixedWidth(45)
        self.undo_btn.clicked.connect(self._undo)
        self.undo_btn.setEnabled(False)
        toolbar2.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("Redo")
        self.redo_btn.setToolTip("Ctrl+Y")
        self.redo_btn.setFixedWidth(45)
        self.redo_btn.clicked.connect(self._redo)
        self.redo_btn.setEnabled(False)
        toolbar2.addWidget(self.redo_btn)

        layout.addLayout(toolbar2)

        # Waypoint list with context menu
        self.wp_list = QListWidget()
        self.wp_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.wp_list.setDefaultDropAction(Qt.MoveAction)
        self.wp_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wp_list.customContextMenuRequested.connect(self._show_context_menu)
        self.wp_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.wp_list.itemDoubleClicked.connect(self._edit_selected)
        self.wp_list.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.wp_list)

        # Stats row
        self.stats_label = QLabel("0 waypoints | 0 km | 0 launch | 0 targets")
        self.stats_label.setStyleSheet("color: #808080; font-size: 10px;")
        layout.addWidget(self.stats_label)

        # Combined action row: Edit/Delete/Dup | Upload/Download | Save/Load
        action_row = QHBoxLayout()
        action_row.setSpacing(2)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(35)
        edit_btn.clicked.connect(self._edit_selected)
        action_row.addWidget(edit_btn)

        delete_btn = QPushButton("Del")
        delete_btn.setFixedWidth(30)
        delete_btn.clicked.connect(self._delete_selected)
        action_row.addWidget(delete_btn)

        dup_btn = QPushButton("Dup")
        dup_btn.setFixedWidth(30)
        dup_btn.setToolTip("Duplicate waypoint")
        dup_btn.clicked.connect(self._duplicate_selected)
        action_row.addWidget(dup_btn)

        action_row.addWidget(self._separator())

        upload_btn = QPushButton("Upload")
        upload_btn.setStyleSheet("QPushButton { background-color: #2563eb; }")
        upload_btn.setFixedWidth(50)
        upload_btn.clicked.connect(self._upload_mission)
        action_row.addWidget(upload_btn)

        download_btn = QPushButton("DL")
        download_btn.setFixedWidth(25)
        download_btn.setToolTip("Download mission from vehicle")
        download_btn.clicked.connect(self._download_mission)
        action_row.addWidget(download_btn)

        action_row.addWidget(self._separator())

        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(38)
        save_btn.clicked.connect(self._save_mission)
        action_row.addWidget(save_btn)

        load_btn = QPushButton("Load")
        load_btn.setFixedWidth(38)
        load_btn.clicked.connect(self._load_mission)
        action_row.addWidget(load_btn)

        action_row.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(40)
        clear_btn.clicked.connect(self._clear_mission)
        action_row.addWidget(clear_btn)

        layout.addLayout(action_row)

        # Swarm Logic Section (expanded)
        self._setup_swarm_section(layout)

    def _separator(self) -> QFrame:
        """Create a vertical separator line."""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #4a4a6a;")
        return sep

    def _setup_swarm_section(self, parent_layout):
        """
        Setup swarm coordination controls.

        Supports two modes:
        1. DYNAMIC (True Swarm): Chicks track bird's position in real-time
        2. WAYPOINT: Pre-planned offset missions (for when comms unreliable)
        """
        swarm_group = QGroupBox("SWARM COORDINATION")
        swarm_group.setCheckable(True)
        swarm_group.setChecked(True)
        swarm_layout = QVBoxLayout(swarm_group)
        swarm_layout.setSpacing(2)
        swarm_layout.setContentsMargins(4, 4, 4, 4)

        # Formation type
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Formation:"))
        self.formation_combo = QComboBox()
        self.formation_combo.addItem("None", "none")
        self.formation_combo.addItem("Line Abreast", "line")
        self.formation_combo.addItem("Echelon Right", "echelon_r")
        self.formation_combo.addItem("Echelon Left", "echelon_l")
        self.formation_combo.addItem("V Formation", "vee")
        self.formation_combo.addItem("Trail", "trail")
        self.formation_combo.addItem("Spread", "spread")
        self.formation_combo.setFixedWidth(110)
        row1.addWidget(self.formation_combo)
        row1.addStretch()
        swarm_layout.addLayout(row1)

        # Spacing and altitude
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Space:"))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(10, 500)
        self.spacing_spin.setValue(50)
        self.spacing_spin.setSuffix("m")
        self.spacing_spin.setFixedWidth(60)
        row2.addWidget(self.spacing_spin)

        row2.addWidget(QLabel("Alt:"))
        self.alt_offset_spin = QSpinBox()
        self.alt_offset_spin.setRange(-100, 100)
        self.alt_offset_spin.setValue(-10)
        self.alt_offset_spin.setSuffix("m")
        self.alt_offset_spin.setFixedWidth(55)
        row2.addWidget(self.alt_offset_spin)
        row2.addStretch()
        swarm_layout.addLayout(row2)

        # Coordination mode
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Mode:"))
        self.coord_combo = QComboBox()
        self.coord_combo.addItem("Dynamic (True Swarm)", "dynamic")
        self.coord_combo.addItem("Waypoint (Pre-planned)", "waypoint")
        self.coord_combo.setToolTip(
            "DYNAMIC: Chicks track bird position in real-time via LoRa\n"
            "WAYPOINT: Generate offset waypoint missions (no live tracking)"
        )
        self.coord_combo.setFixedWidth(140)
        row3.addWidget(self.coord_combo)
        row3.addStretch()
        swarm_layout.addLayout(row3)

        # Attack pattern
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Attack:"))
        self.attack_combo = QComboBox()
        self.attack_combo.addItem("Sequential", "sequential")
        self.attack_combo.addItem("Converge", "converge")
        self.attack_combo.addItem("Spread", "spread")
        self.attack_combo.setFixedWidth(90)
        row4.addWidget(self.attack_combo)
        row4.addStretch()
        swarm_layout.addLayout(row4)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)

        activate_btn = QPushButton("Activate Swarm")
        activate_btn.setStyleSheet("QPushButton { background-color: #dc2626; font-weight: bold; }")
        activate_btn.setToolTip("Enable swarm mode - chicks will track bird position")
        activate_btn.clicked.connect(self._activate_swarm)
        btn_row.addWidget(activate_btn)

        gen_btn = QPushButton("Gen WP Missions")
        gen_btn.setToolTip("Generate waypoint-based missions (for WAYPOINT mode)")
        gen_btn.clicked.connect(self._generate_chick_missions)
        btn_row.addWidget(gen_btn)

        swarm_layout.addLayout(btn_row)

        # Status
        self.swarm_status = QLabel("Swarm: Inactive")
        self.swarm_status.setStyleSheet("color: #808080; font-size: 10px;")
        swarm_layout.addWidget(self.swarm_status)

        # Store state
        self._chick_missions: Dict[str, Mission] = {}
        self._swarm_active = False

        parent_layout.addWidget(swarm_group)

    def _activate_swarm(self):
        """Activate/deactivate swarm mode."""
        config = self._get_swarm_config()

        if config.formation == "none":
            QMessageBox.warning(self, "Swarm", "Select a formation first.")
            return

        self._swarm_active = not self._swarm_active

        if self._swarm_active:
            self.swarm_status.setText(f"Swarm: ACTIVE ({config.formation})")
            self.swarm_status.setStyleSheet("color: #4ade80; font-size: 10px; font-weight: bold;")
            # Emit signal to activate swarm in mavlink manager
            self.swarm_activated.emit(config)
            print(f"[Swarm] Activated: {config.formation}, {config.spacing}m spacing")
        else:
            self.swarm_status.setText("Swarm: Inactive")
            self.swarm_status.setStyleSheet("color: #808080; font-size: 10px;")
            self.swarm_deactivated.emit()
            print("[Swarm] Deactivated")

    def _get_swarm_config(self) -> SwarmConfig:
        """Get current swarm configuration from UI."""
        return SwarmConfig(
            formation=self.formation_combo.currentData(),
            spacing=self.spacing_spin.value(),
            alt_offset=self.alt_offset_spin.value(),
            coord_mode=self.coord_combo.currentData(),
            attack_pattern=self.attack_combo.currentData()
        )

    def _generate_chick_missions(self):
        """
        Generate missions for all chicks based on bird's mission and formation.

        LINE ABREAST: All vehicles fly same path, chicks offset left/right
        TRAIL: Chicks start at LAUNCH_CHICK waypoints, follow behind bird
        """
        if len(self._mission) == 0:
            QMessageBox.warning(
                self, "Generate Chick Missions",
                "Create a Bird mission first.\n\n"
                "Add waypoints for the path you want to fly."
            )
            return

        config = self._get_swarm_config()

        if config.formation == "none":
            QMessageBox.warning(
                self, "No Formation Selected",
                "Select a formation type:\n\n"
                "• LINE ABREAST: All 3 fly side by side\n"
                "• TRAIL: Chicks follow behind bird"
            )
            return

        # For trail formation, check for launch points
        if config.formation == "trail":
            launch_points = [wp for wp in self._mission.waypoints
                            if wp.type == WaypointType.LAUNCH_CHICK]
            if not launch_points:
                reply = QMessageBox.question(
                    self, "No Launch Points",
                    "TRAIL formation works best with LAUNCH_CHICK waypoints.\n\n"
                    "Without them, chicks will follow from the start.\n"
                    "Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

        # Generate mission for each chick
        generated = []
        for chick in self._available_chicks:
            chick_id = chick["id"]
            chick_index = 0 if "1" in chick_id else 1

            chick_mission = SwarmCalculator.generate_chick_mission(
                self._mission, chick_id, chick_index, config
            )

            self._chick_missions[chick_id] = chick_mission
            generated.append(f"  {chick['name']}: {len(chick_mission)} waypoints")

        # Update status
        self.swarm_status.setText(f"Generated: {len(self._chick_missions)} chick missions")
        self.swarm_status.setStyleSheet("color: #4ade80; font-size: 10px; font-weight: bold;")

        # Show summary
        formation_desc = "Side by side" if config.formation == "line" else "Following behind"
        QMessageBox.information(
            self, "Chick Missions Generated",
            f"Formation: {self.formation_combo.currentText()}\n"
            f"  ({formation_desc} at {config.spacing}m spacing)\n\n"
            f"Generated missions:\n"
            + "\n".join(generated) + "\n\n"
            "To view/upload a chick mission:\n"
            "1. Change 'Vehicle' dropdown to CHK1 or CHK2\n"
            "2. The waypoint list will show that mission\n"
            "3. Click 'Upload' to send to vehicle",
            QMessageBox.Ok
        )

        print(f"[Swarm] Generated {len(generated)} chick missions ({config.formation})")


    def get_chick_mission(self, chick_id: str) -> Optional[Mission]:
        """Get a generated chick mission by ID."""
        return self._chick_missions.get(chick_id)

    def load_chick_mission(self, chick_id: str):
        """Load a generated chick mission into the editor."""
        mission = self._chick_missions.get(chick_id)
        if mission:
            self._mission = copy.deepcopy(mission)
            # Update vehicle selector
            idx = self.vehicle_combo.findData(chick_id)
            if idx >= 0:
                self.vehicle_combo.setCurrentIndex(idx)
            self._update_list()
            self.mission_changed.emit()
            print(f"[Swarm] Loaded {chick_id} mission into editor")

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self._redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo)
        QShortcut(QKeySequence("Delete"), self, self._delete_selected)
        QShortcut(QKeySequence("Ctrl+D"), self, self._duplicate_selected)

    def _show_context_menu(self, pos):
        """Show right-click context menu for waypoint list."""
        item = self.wp_list.itemAt(pos)
        if not item:
            return

        wp_id = item.data(Qt.UserRole)
        wp = self._mission.get_waypoint(wp_id)
        if not wp:
            return

        menu = QMenu(self)

        # Edit
        edit_action = QAction("Edit Waypoint...", self)
        edit_action.triggered.connect(self._edit_selected)
        menu.addAction(edit_action)

        menu.addSeparator()

        # Convert to type submenu
        convert_menu = menu.addMenu("Convert to...")
        for wt in WaypointType:
            if wt != wp.type:
                action = QAction(wt.value, self)
                action.triggered.connect(lambda checked, t=wt: self._convert_waypoint(wp_id, t))
                convert_menu.addAction(action)

        menu.addSeparator()

        # Mark as target
        if wp.type != WaypointType.TARGET:
            target_action = QAction("Mark as Target", self)
            target_action.triggered.connect(lambda: self._convert_waypoint(wp_id, WaypointType.TARGET))
            menu.addAction(target_action)

        # Duplicate
        dup_action = QAction("Duplicate", self)
        dup_action.triggered.connect(self._duplicate_selected)
        menu.addAction(dup_action)

        menu.addSeparator()

        # Move
        move_up_action = QAction("Move Up", self)
        move_up_action.triggered.connect(self._move_up)
        menu.addAction(move_up_action)

        move_down_action = QAction("Move Down", self)
        move_down_action.triggered.connect(self._move_down)
        menu.addAction(move_down_action)

        menu.addSeparator()

        # Delete
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)

        menu.exec_(self.wp_list.mapToGlobal(pos))

    def _convert_waypoint(self, wp_id: int, new_type: WaypointType):
        """Convert a waypoint to a different type."""
        wp = self._mission.get_waypoint(wp_id)
        if wp:
            self._mission.update_waypoint(wp_id, type=new_type)
            self._update_list()
            self.mission_changed.emit()

    def _on_vehicle_changed(self):
        """Handle vehicle selection change - load generated chick mission if available."""
        vehicle_id = self.vehicle_combo.currentData()

        # If switching to a chick and we have a generated mission for it, load it
        if vehicle_id in self._chick_missions:
            self._mission = copy.deepcopy(self._chick_missions[vehicle_id])
            self._update_list()
            self.mission_changed.emit()
            print(f"[Swarm] Loaded generated mission for {vehicle_id}")
        else:
            self._mission.vehicle_id = vehicle_id

        self.vehicle_changed.emit(vehicle_id)

    def _update_list(self):
        """Update the waypoint list display."""
        self.wp_list.clear()

        for i, wp in enumerate(self._mission.waypoints):
            # Format: "1. WAYPOINT (52.0000, -1.5000) 100m @15m/s"
            if wp.type == WaypointType.RTL:
                text = f"{i+1}. RTL"
            elif wp.type == WaypointType.LAUNCH_CHICK:
                text = f"{i+1}. {wp.name} ({wp.lat:.4f}, {wp.lon:.4f}) {wp.alt:.0f}m"
            elif wp.type == WaypointType.TARGET:
                text = f"{i+1}. TARGET ({wp.lat:.4f}, {wp.lon:.4f}) {wp.alt:.0f}m"
            else:
                text = f"{i+1}. {wp.type.value} ({wp.lat:.4f}, {wp.lon:.4f}) {wp.alt:.0f}m"

            # Add speed if set (stored in param2)
            if wp.param2 > 0:
                text += f" @{wp.param2:.0f}m/s"

            if wp.name and wp.type not in (WaypointType.LAUNCH_CHICK,):
                text += f" [{wp.name}]"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, wp.id)

            # Color coding
            if wp.type == WaypointType.LAUNCH_CHICK:
                item.setForeground(QColor("#dc2626"))  # Red
            elif wp.type == WaypointType.TARGET:
                item.setForeground(QColor("#f97316"))  # Orange
            elif wp.type == WaypointType.RTL:
                item.setForeground(QColor("#facc15"))  # Yellow
            elif wp.type == WaypointType.LOITER:
                item.setForeground(QColor("#60a5fa"))  # Blue

            self.wp_list.addItem(item)

        self._update_stats()
        self._update_undo_buttons()
        self.show_mission_on_map.emit(self._mission)

    def _update_stats(self):
        """Update mission statistics."""
        total_dist = 0
        launch_points = 0
        target_points = 0

        for i, wp in enumerate(self._mission.waypoints):
            if wp.type == WaypointType.LAUNCH_CHICK:
                launch_points += 1
            if wp.type == WaypointType.TARGET:
                target_points += 1
            if i > 0:
                prev = self._mission.waypoints[i-1]
                if prev.type != WaypointType.RTL and wp.type != WaypointType.RTL:
                    total_dist += haversine_distance(prev.lat, prev.lon, wp.lat, wp.lon)

        dist_km = total_dist / 1000
        self.stats_label.setText(
            f"{len(self._mission)} waypoints | {dist_km:.1f} km | {launch_points} launch | {target_points} targets"
        )

    def _update_undo_buttons(self):
        """Update undo/redo button states."""
        self.undo_btn.setEnabled(self._mission.can_undo)
        self.redo_btn.setEnabled(self._mission.can_redo)

    def _undo(self):
        """Undo last action."""
        if self._mission.undo():
            self._update_list()
            self.mission_changed.emit()
            print("[Mission] Undo")

    def _redo(self):
        """Redo last undone action."""
        if self._mission.redo():
            self._update_list()
            self.mission_changed.emit()
            print("[Mission] Redo")

    def _add_waypoint(self, wp_type: WaypointType):
        """Add a new waypoint via dialog."""
        dialog = WaypointDialog(self, default_alt=self._default_alt,
                                default_speed=self._default_speed,
                                available_chicks=self._available_chicks)
        idx = dialog.type_combo.findData(wp_type)
        if idx >= 0:
            dialog.type_combo.setCurrentIndex(idx)

        if dialog.exec_():
            data = dialog.get_waypoint_data()
            self._mission.add_waypoint(
                data["type"], data["lat"], data["lon"], data["alt"],
                data["param1"], data["param2"], data["name"]
            )
            self._update_list()
            self.mission_changed.emit()

    def _add_launch_point(self):
        """Add a chick launch point."""
        dialog = WaypointDialog(self, default_alt=self._default_alt,
                                default_speed=self._default_speed,
                                available_chicks=self._available_chicks)
        idx = dialog.type_combo.findData(WaypointType.LAUNCH_CHICK)
        if idx >= 0:
            dialog.type_combo.setCurrentIndex(idx)

        if dialog.exec_():
            data = dialog.get_waypoint_data()
            chick_id = data.get("chick_id", "chick1")
            self._mission.add_launch_point(
                data["lat"], data["lon"], data["alt"], chick_id
            )
            self._update_list()
            self.mission_changed.emit()

    def _quick_add(self, wp_type: WaypointType):
        """Quickly add a waypoint without dialog."""
        if wp_type == WaypointType.RTL:
            self._mission.add_waypoint(WaypointType.RTL, 0, 0, 0)
            self._update_list()
            self.mission_changed.emit()

    def _toggle_map_add_mode(self):
        """Toggle adding waypoints from map clicks."""
        self._adding_from_map = self.map_add_btn.isChecked()
        if self._adding_from_map:
            self.map_add_btn.setStyleSheet("QPushButton { background-color: #16a34a; }")
            self.add_waypoint_from_map.emit()
        else:
            self.map_add_btn.setStyleSheet("")

    def add_waypoint_at(self, lat: float, lon: float):
        """Add a waypoint at the given coordinates (from map click)."""
        if not self._adding_from_map:
            return

        wp_type_str, chick_id = self.map_wp_type.currentData()

        if wp_type_str == "LAUNCH_CHICK" and chick_id:
            self._mission.add_launch_point(lat, lon, self._default_alt, chick_id)
        elif wp_type_str == "TARGET":
            self._mission.add_target(lat, lon, self._default_alt)
        else:
            wp_type = WaypointType(wp_type_str)
            # Pass speed in param2
            self._mission.add_waypoint(
                wp_type, lat, lon, self._default_alt,
                param1=0, param2=self._default_speed
            )

        self._update_list()
        self.mission_changed.emit()

    def cancel_map_add_mode(self):
        """Cancel map add mode."""
        self._adding_from_map = False
        self.map_add_btn.setChecked(False)
        self.map_add_btn.setStyleSheet("")

    @property
    def is_adding_from_map(self) -> bool:
        return self._adding_from_map

    def _edit_selected(self):
        """Edit the selected waypoint."""
        item = self.wp_list.currentItem()
        if not item:
            return

        wp_id = item.data(Qt.UserRole)
        wp = self._mission.get_waypoint(wp_id)
        if not wp:
            return

        dialog = WaypointDialog(self, waypoint=wp, default_alt=self._default_alt,
                                default_speed=self._default_speed,
                                available_chicks=self._available_chicks)
        if dialog.exec_():
            data = dialog.get_waypoint_data()
            self._mission.update_waypoint(
                wp_id,
                type=data["type"],
                name=data["name"],
                lat=data["lat"],
                lon=data["lon"],
                alt=data["alt"],
                param1=data["param1"],
                param2=data["param2"]
            )
            self._update_list()
            self.mission_changed.emit()

    def _delete_selected(self):
        """Delete the selected waypoint."""
        item = self.wp_list.currentItem()
        if not item:
            return

        wp_id = item.data(Qt.UserRole)
        self._mission.remove_waypoint(wp_id)
        self._update_list()
        self.mission_changed.emit()

    def _duplicate_selected(self):
        """Duplicate the selected waypoint."""
        item = self.wp_list.currentItem()
        if not item:
            return

        wp_id = item.data(Qt.UserRole)
        wp = self._mission.get_waypoint(wp_id)
        if not wp:
            return

        # Add duplicate with slightly offset position
        self._mission.add_waypoint(
            wp.type,
            wp.lat + 0.0001,
            wp.lon + 0.0001,
            wp.alt,
            wp.param1,
            wp.param2,
            f"{wp.name} (copy)" if wp.name else ""
        )
        self._update_list()
        self.mission_changed.emit()

    def _move_up(self):
        """Move selected waypoint up."""
        row = self.wp_list.currentRow()
        if row <= 0:
            return

        wp_id = self.wp_list.item(row).data(Qt.UserRole)
        self._mission.move_waypoint(wp_id, row - 1)
        self._update_list()
        self.wp_list.setCurrentRow(row - 1)
        self.mission_changed.emit()

    def _move_down(self):
        """Move selected waypoint down."""
        row = self.wp_list.currentRow()
        if row < 0 or row >= len(self._mission) - 1:
            return

        wp_id = self.wp_list.item(row).data(Qt.UserRole)
        self._mission.move_waypoint(wp_id, row + 1)
        self._update_list()
        self.wp_list.setCurrentRow(row + 1)
        self.mission_changed.emit()

    def _on_rows_moved(self):
        """Handle drag-drop reorder."""
        new_order = []
        for i in range(self.wp_list.count()):
            wp_id = self.wp_list.item(i).data(Qt.UserRole)
            wp = self._mission.get_waypoint(wp_id)
            if wp:
                new_order.append(wp)

        self._mission._save_state()
        self._mission.waypoints = new_order
        self._update_list()
        self.mission_changed.emit()

    def _on_selection_changed(self):
        """Handle waypoint selection."""
        item = self.wp_list.currentItem()
        if item:
            wp_id = item.data(Qt.UserRole)
            wp = self._mission.get_waypoint(wp_id)
            self.waypoint_selected.emit(wp)
        else:
            self.waypoint_selected.emit(None)

    def _upload_mission(self):
        """Upload mission to vehicle."""
        if len(self._mission) == 0:
            QMessageBox.warning(self, "Empty Mission", "Add waypoints before uploading.")
            return

        vehicle_id = self.vehicle_combo.currentData()
        reply = QMessageBox.question(
            self, "Upload Mission",
            f"Upload {len(self._mission)} waypoints to {vehicle_id.upper()}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.upload_requested.emit(vehicle_id, self._mission)

    def _download_mission(self):
        """Download mission from vehicle."""
        vehicle_id = self.vehicle_combo.currentData()
        reply = QMessageBox.question(
            self, "Download Mission",
            f"Download mission from {vehicle_id.upper()}?\n\n"
            "This will replace the current mission in the editor.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.download_requested.emit(vehicle_id)

    def load_mission(self, mission: Mission):
        """Load a mission into the editor (called after download)."""
        self._mission = copy.deepcopy(mission)
        # Update vehicle selector
        idx = self.vehicle_combo.findData(mission.vehicle_id)
        if idx >= 0:
            self.vehicle_combo.setCurrentIndex(idx)
        self._update_list()
        self.mission_changed.emit()
        print(f"[Mission] Loaded {len(mission)} waypoints")

    def _clear_mission(self):
        """Clear all waypoints."""
        if len(self._mission) == 0:
            return

        reply = QMessageBox.question(
            self, "Clear Mission",
            "Clear all waypoints?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._mission.clear()
            self._update_list()
            self.mission_changed.emit()

    def _reverse_mission(self):
        """Reverse waypoint order."""
        if len(self._mission) < 2:
            return
        self._mission._save_state()
        self._mission.waypoints.reverse()
        self._update_list()
        self.mission_changed.emit()

    def _save_mission(self):
        """Save mission to file."""
        if len(self._mission) == 0:
            QMessageBox.warning(self, "Empty Mission", "Add waypoints before saving.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Mission", "", "Mission Files (*.json);;All Files (*)"
        )

        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            try:
                with open(filename, 'w') as f:
                    f.write(self._mission.to_json())
                print(f"[Mission] Saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def _load_mission(self):
        """Load mission from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Mission", "", "Mission Files (*.json);;All Files (*)"
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    self._mission = Mission.from_json(f.read())
                # Update vehicle selector
                idx = self.vehicle_combo.findData(self._mission.vehicle_id)
                if idx >= 0:
                    self.vehicle_combo.setCurrentIndex(idx)
                self._update_list()
                self.mission_changed.emit()
                print(f"[Mission] Loaded {len(self._mission)} waypoints from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", str(e))

    def edit_waypoint_at(self, wp_id: int):
        """Edit a specific waypoint by ID (called from map click)."""
        wp = self._mission.get_waypoint(wp_id)
        if not wp:
            return

        dialog = WaypointDialog(self, waypoint=wp, default_alt=self._default_alt,
                                default_speed=self._default_speed,
                                available_chicks=self._available_chicks)
        if dialog.exec_():
            data = dialog.get_waypoint_data()
            self._mission.update_waypoint(
                wp_id,
                type=data["type"],
                name=data["name"],
                lat=data["lat"],
                lon=data["lon"],
                alt=data["alt"],
                param1=data["param1"],
                param2=data["param2"]
            )
            self._update_list()
            self.mission_changed.emit()

    @property
    def mission(self) -> Mission:
        return self._mission
