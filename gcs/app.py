# SwarmDrones GCS Main Application
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTabWidget, QLabel, QPushButton, QSplitter,
                              QFrame, QMessageBox, QShortcut, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence
import time

from .styles import DARK_STYLE
from .widgets import (MapWidget, VideoWidget, VehiclePanel, TargetQueueWidget,
                      OrbPanel, StatusBar, ModePanel, MissionPanel)
from .widgets.target_queue import ManualCoordDialog
from .models import Vehicle, VehicleType, VehicleState, ChickState
from .models.target import TargetQueue, TargetSource
from .models.orb import OrbManager, OrbState
from .comms import MAVLinkManager, LoRaManager, VideoManager


class GCSMainWindow(QMainWindow):
    """Main GCS window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SWARM GCS")
        self.setMinimumSize(1280, 720)
        self.resize(1920, 1080)

        # Communications managers
        self._mavlink = MAVLinkManager(self)
        self._lora = LoRaManager(self)
        self._video = VideoManager(self)

        # Data models
        self._selected_vehicle = None  # Will be set by _init_vehicles
        self._vehicles = self._init_vehicles()
        self._targets = TargetQueue()
        self._orbs = OrbManager()
        self._current_tab = "FLIGHT"

        # Store uploaded/downloaded missions per vehicle
        self._vehicle_missions = {}  # vehicle_id -> Mission

        # Connect comms signals
        self._connect_comms_signals()

        # Apply dark style
        self.setStyleSheet(DARK_STYLE)

        # Setup UI
        self._setup_ui()
        self._setup_shortcuts()

        # Start simulation mode for development
        self._start_simulation()

        # Select first bird by default
        if self._selected_vehicle:
            self._on_vehicle_selected(self._selected_vehicle)

    def _init_vehicles(self) -> dict:
        """Initialize vehicle objects from config with carrier relationships."""
        from .config import SWARM_CONFIG

        vehicles = {}

        # Create birds
        for bird_cfg in SWARM_CONFIG["birds"]:
            vtype = VehicleType.PLANE if bird_cfg.get("type") == "plane" else VehicleType.COPTER
            vehicles[bird_cfg["id"]] = Vehicle(
                bird_cfg["id"],
                bird_cfg["name"],
                vtype,
                bird_cfg.get("icon", "✈")
            )

        # Create chicks (attached to their carriers)
        for chick_cfg in SWARM_CONFIG["chicks"]:
            vtype = VehicleType.COPTER if chick_cfg.get("type") == "copter" else VehicleType.PLANE
            vehicles[chick_cfg["id"]] = Vehicle(
                chick_cfg["id"],
                chick_cfg["name"],
                vtype,
                chick_cfg.get("icon", "⬡"),
                carrier=chick_cfg.get("carrier"),
                slot=chick_cfg.get("slot", 1)
            )

        # Set default selected vehicle to first bird
        if SWARM_CONFIG["birds"]:
            self._selected_vehicle = SWARM_CONFIG["birds"][0]["id"]

        return vehicles

    def _connect_comms_signals(self):
        """Connect communication manager signals."""
        # MAVLink telemetry
        self._mavlink.telemetry_received.connect(self._on_telemetry_received)
        self._mavlink.connection_changed.connect(self._on_mavlink_connection_changed)
        self._mavlink.mode_changed.connect(self._on_mode_changed)

        # Mission events (for hardware: these trigger actual mechanisms)
        self._mavlink.chick_launch_triggered.connect(self._on_auto_chick_launch)
        self._mavlink.waypoint_reached.connect(self._on_waypoint_reached)

        # LoRa mesh
        self._lora.node_status_updated.connect(self._on_mesh_status_updated)

        # Video
        self._video.frame_received.connect(self._on_video_frame)

    def _start_simulation(self):
        """Start all simulations for development."""
        self._mavlink.start_simulation()
        self._lora.start_simulation()
        self._video.start_simulation()
        # Start video stream for first bird
        if self._selected_vehicle:
            self._video.start_stream(self._selected_vehicle)

    def _setup_ui(self):
        """Setup the main UI layout with adjustable splitters."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Header with tabs
        header = self._create_header()
        main_layout.addWidget(header)

        # Main content - horizontal splitter (left/right)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(6)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3a3a5a;
            }
            QSplitter::handle:hover {
                background-color: #5a5a8a;
            }
        """)

        # LEFT SIDE - vertical splitter (map / mode+targets)
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setHandleWidth(6)
        left_splitter.setStyleSheet(self.main_splitter.styleSheet())

        # Map widget
        self.map_widget = MapWidget()
        self.map_widget.target_added.connect(self._on_map_target_added)
        self.map_widget.investigate_requested.connect(self._on_investigate_requested)
        self.map_widget.mission_waypoint_clicked.connect(self._on_map_click_for_mission)
        self.map_widget.waypoint_edit_requested.connect(self._on_waypoint_edit_from_map)
        self.map_widget.view_vehicle_mission.connect(self._on_view_vehicle_mission)
        left_splitter.addWidget(self.map_widget)

        # Bottom left panel (mode + targets)
        bottom_left = QWidget()
        bottom_left_layout = QVBoxLayout(bottom_left)
        bottom_left_layout.setContentsMargins(0, 0, 0, 0)
        bottom_left_layout.setSpacing(4)

        # Mode panel
        self.mode_panel = ModePanel()
        self.mode_panel.mode_selected.connect(self._on_mode_button_clicked)
        self.mode_panel.launch_requested.connect(self._on_launch_chick)
        self.mode_panel.arm_requested.connect(self._on_arm_requested)
        self.mode_panel.takeoff_requested.connect(self._on_takeoff_requested)
        self.mode_panel.land_requested.connect(self._on_land_requested)
        bottom_left_layout.addWidget(self.mode_panel)

        # Target queue (shown in FLIGHT tab)
        self.target_queue = TargetQueueWidget()
        self.target_queue.target_selected.connect(self._on_target_selected)
        self.target_queue.manual_entry_requested.connect(self._on_manual_entry)
        self.target_queue.target_removed.connect(self._on_target_removed)
        self.target_queue.target_renamed.connect(self._on_target_renamed)
        self.target_queue.target_description_changed.connect(self._on_target_description_changed)
        bottom_left_layout.addWidget(self.target_queue)

        # Mission panel (shown in MISSION tab)
        self.mission_panel = MissionPanel()
        self.mission_panel.upload_requested.connect(self._on_mission_upload)
        self.mission_panel.download_requested.connect(self._on_mission_download)
        self.mission_panel.add_waypoint_from_map.connect(self._on_mission_map_mode)
        self.mission_panel.show_mission_on_map.connect(self._on_show_mission)
        self.mission_panel.vehicle_changed.connect(self.map_widget.set_mission_vehicle)
        # Connect swarm signals for dynamic tracking
        self.mission_panel.swarm_activated.connect(self._mavlink.activate_swarm)
        self.mission_panel.swarm_deactivated.connect(self._mavlink.deactivate_swarm)
        self.mission_panel.hide()  # Hidden by default (FLIGHT tab active)
        bottom_left_layout.addWidget(self.mission_panel)

        left_splitter.addWidget(bottom_left)
        left_splitter.setSizes([500, 250])  # Initial sizes

        self.main_splitter.addWidget(left_splitter)

        # RIGHT SIDE - vertical splitter (video / vehicles+orbs)
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(6)
        right_splitter.setStyleSheet(self.main_splitter.styleSheet())

        # Video feed
        self.video_widget = VideoWidget()
        self.video_widget.source_changed.connect(self._on_video_source_changed)
        self.video_widget.fullscreen_toggled.connect(self._toggle_video_fullscreen)
        right_splitter.addWidget(self.video_widget)

        # Bottom right panel (vehicles + orbs)
        bottom_right = QWidget()
        bottom_right_layout = QVBoxLayout(bottom_right)
        bottom_right_layout.setContentsMargins(0, 0, 0, 0)
        bottom_right_layout.setSpacing(4)

        # Vehicle panel
        self.vehicle_panel = VehiclePanel()
        self.vehicle_panel.vehicle_selected.connect(self._on_vehicle_selected)
        bottom_right_layout.addWidget(self.vehicle_panel)

        # Orb panel
        self.orb_panel = OrbPanel()
        self.orb_panel.orb_selected.connect(self._on_orb_selected)
        self.orb_panel.assign_requested.connect(self._on_assign_target)
        self.orb_panel.arm_requested.connect(self._on_arm_orb)
        self.orb_panel.disarm_requested.connect(self._on_disarm_orb)
        self.orb_panel.release_requested.connect(self._on_release_orb)
        bottom_right_layout.addWidget(self.orb_panel)

        right_splitter.addWidget(bottom_right)
        right_splitter.setSizes([300, 350])  # Initial sizes

        self.main_splitter.addWidget(right_splitter)

        # Set main splitter proportions (60/40)
        self.main_splitter.setSizes([700, 400])

        main_layout.addWidget(self.main_splitter, 1)

        # Status bar
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        # Initial UI updates
        self._update_orb_display()

    def _create_header(self) -> QWidget:
        """Create header with tabs and controls."""
        header = QFrame()
        header.setObjectName("panel")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 4, 8, 4)

        # Title
        title = QLabel("SWARM GCS")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        layout.addSpacing(20)

        # Tab buttons
        self.tab_buttons = {}
        tabs = ["FLIGHT", "MISSION", "ISR", "EW"]
        for i, tab in enumerate(tabs):
            btn = QPushButton(tab)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setEnabled(i <= 1)  # FLIGHT and MISSION enabled
            if i > 1:
                btn.setToolTip("Coming in future version")
            btn.clicked.connect(lambda checked, t=tab: self._on_tab_clicked(t))
            self.tab_buttons[tab] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Connection status indicator
        self.conn_label = QLabel("SIM MODE")
        self.conn_label.setStyleSheet("color: #facc15; font-weight: bold;")
        layout.addWidget(self.conn_label)

        layout.addSpacing(10)

        # Pre-flight button
        preflight_btn = QPushButton("PRE-FLIGHT")
        preflight_btn.setObjectName("preflight_button")
        preflight_btn.clicked.connect(self._on_preflight)
        layout.addWidget(preflight_btn)

        # Connect button
        connect_btn = QPushButton("CONNECT")
        connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(connect_btn)

        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedWidth(40)
        settings_btn.clicked.connect(self._on_settings)
        layout.addWidget(settings_btn)

        return header

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Vehicle selection - dynamically create shortcuts for all vehicles
        vehicle_ids = list(self._vehicles.keys())
        for i, vid in enumerate(vehicle_ids[:9]):  # Ctrl+1 through Ctrl+9
            # Use default argument to capture vid in closure
            QShortcut(QKeySequence(f"Ctrl+{i+1}"), self,
                      lambda v=vid: self._on_vehicle_selected(v))

        # Mode cycle
        QShortcut(QKeySequence("M"), self, self._cycle_mode)

        # Video
        QShortcut(QKeySequence("V"), self, self._toggle_video_fullscreen)
        QShortcut(QKeySequence("Tab"), self, self._cycle_video_source)

        # Targets
        QShortcut(QKeySequence("Space"), self, self._capture_coordinate)
        QShortcut(QKeySequence("T"), self, self.target_queue.select_next)

        # Orbs
        QShortcut(QKeySequence("A"), self, self._on_assign_target)

        # Launch chick
        QShortcut(QKeySequence("L"), self, self._on_launch_chick)

        # RTL all
        QShortcut(QKeySequence("Ctrl+R"), self, self._rtl_all)

        # Center map on selected vehicle
        QShortcut(QKeySequence("C"), self, self._center_map_on_selected)

        # Quick fly (SITL testing) - GUIDED, ARM, TAKEOFF
        QShortcut(QKeySequence("F"), self, self._quick_fly_selected)

        # Escape
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    # ==================== Comms Event Handlers ====================

    def _on_telemetry_received(self, vehicle_id: str, telemetry):
        """Handle telemetry from MAVLink manager."""
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return

        # Update vehicle state
        vehicle.state.lat = telemetry.lat
        vehicle.state.lon = telemetry.lon
        vehicle.state.alt = telemetry.alt
        vehicle.state.heading = telemetry.heading
        vehicle.state.groundspeed = telemetry.groundspeed
        vehicle.state.battery_pct = telemetry.battery_pct
        vehicle.state.mode = telemetry.mode
        vehicle.state.armed = telemetry.armed
        vehicle.connected = True

        # If this is a carrier bird, update attached Chicks to match its position
        from .config import get_chicks_for_bird
        chicks = get_chicks_for_bird(vehicle_id)
        if chicks:
            self._sync_attached_chicks(vehicle_id)

        # Update UI
        chick_state_str = None
        if vehicle.chick_state:
            chick_state_str = vehicle.chick_state.value

        self.vehicle_panel.update_vehicle(
            vehicle_id,
            telemetry.mode,
            telemetry.alt,
            telemetry.battery_pct,
            True,
            speed=telemetry.groundspeed,
            heading=telemetry.heading,
            gps_sats=telemetry.gps_sats,
            chick_state=chick_state_str
        )

        if vehicle_id == self._selected_vehicle:
            self.mode_panel.set_current_mode(telemetry.mode)
            self.mode_panel.set_armed(telemetry.armed)
            self._update_mode_panel_for_chick()

        self._update_map()

    def _sync_attached_chicks(self, carrier_id: str):
        """Synchronize attached Chicks to their carrier's position."""
        from .config import get_chicks_for_bird

        carrier = self._vehicles.get(carrier_id)
        if not carrier:
            return

        for chick_id in get_chicks_for_bird(carrier_id):
            chick = self._vehicles.get(chick_id)
            if chick and chick.is_attached:
                # Attached chicks inherit carrier's position
                chick.state.lat = carrier.state.lat
                chick.state.lon = carrier.state.lon
                chick.state.alt = carrier.state.alt
                chick.state.heading = carrier.state.heading
                chick.state.groundspeed = carrier.state.groundspeed

    def _update_mode_panel_for_chick(self):
        """Update mode panel to show launch button if Chick is selected and attached."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if vehicle and vehicle.chick_state:
            self.mode_panel.set_chick_state(
                vehicle.chick_state.value,
                vehicle.can_launch
            )

    def _on_mavlink_connection_changed(self, vehicle_id: str, connected: bool):
        """Handle MAVLink connection state change."""
        vehicle = self._vehicles.get(vehicle_id)
        if vehicle:
            vehicle.connected = connected

    def _on_mode_changed(self, vehicle_id: str, mode: str):
        """Handle mode change confirmation from vehicle."""
        if vehicle_id == self._selected_vehicle:
            self.mode_panel.set_current_mode(mode)

    def _on_mesh_status_updated(self, node_name: str, status):
        """Handle mesh node status update."""
        from .config import SWARM_CONFIG

        # Map vehicle IDs to status bar slots
        # First bird -> bird slot, chicks -> c1, c2 slots
        birds = [b["id"] for b in SWARM_CONFIG["birds"]]
        chicks = [c["id"] for c in SWARM_CONFIG["chicks"]]

        if node_name in birds:
            self.status_bar.update_mesh(bird=(status.is_connected, status.rssi))
        elif node_name in chicks:
            # Find chick index
            idx = chicks.index(node_name)
            if idx == 0:
                self.status_bar.update_mesh(c1=(status.is_connected, status.rssi))
            elif idx == 1:
                self.status_bar.update_mesh(c2=(status.is_connected, status.rssi))

        self.status_bar.update_time(time.strftime("%H:%M:%S"))

    def _on_video_frame(self, source_id: str, frame):
        """Handle video frame from video manager."""
        self.video_widget.set_frame(frame)

    # ==================== UI Event Handlers ====================

    def _on_tab_clicked(self, tab: str):
        """Handle tab button click."""
        for name, btn in self.tab_buttons.items():
            btn.setChecked(name == tab)

        # Switch panel visibility based on tab
        if tab == "FLIGHT":
            self.target_queue.show()
            self.mission_panel.hide()
            self.mission_panel.cancel_map_add_mode()
            self.map_widget.set_mission_click_mode(False)
            # Keep mission visible if one is uploaded for selected vehicle
            if self._selected_vehicle in self._vehicle_missions:
                mission = self._vehicle_missions[self._selected_vehicle]
                self.map_widget.set_mission_waypoints(mission.to_map_format())
            else:
                self.map_widget.set_mission_waypoints({})
        elif tab == "MISSION":
            self.target_queue.hide()
            self.mission_panel.show()

        self._current_tab = tab

    def _on_vehicle_selected(self, vehicle_id: str):
        """Handle vehicle selection."""
        if vehicle_id not in self._vehicles:
            print(f"[GCS] Unknown vehicle: {vehicle_id}")
            return

        self._selected_vehicle = vehicle_id
        self.vehicle_panel.select_vehicle(vehicle_id, emit_signal=False)

        vehicle = self._vehicles[vehicle_id]
        self.mode_panel.set_vehicle(
            vehicle_id,
            vehicle.name,
            vehicle.type.value
        )
        self.mode_panel.set_current_mode(vehicle.state.mode)

        # Update chick-specific UI
        if vehicle.chick_state:
            self.mode_panel.set_chick_state(
                vehicle.chick_state.value,
                vehicle.can_launch
            )
        else:
            self.mode_panel.set_chick_state(None, False)

    def _on_mode_button_clicked(self, mode: str):
        """Handle mode button click - send command via MAVLink."""
        # Map short names to full names
        mode_map = {"LOIT": "LOITER", "GUIDE": "GUIDED"}
        full_mode = mode_map.get(mode, mode)

        self._mavlink.set_mode(self._selected_vehicle, full_mode)

    def _on_video_source_changed(self, source: str):
        """Handle video source change."""
        self._video.switch_stream(source)

    def _cycle_video_source(self):
        """Cycle to next video source."""
        self.video_widget.cycle_source()

    def _toggle_video_fullscreen(self):
        """Toggle video fullscreen mode."""
        # TODO: Implement fullscreen video overlay
        print("Video fullscreen toggle - TODO")

    def _on_map_target_added(self, lat: float, lon: float):
        """Handle target added from map right-click."""
        target = self._targets.add(lat, lon, TargetSource.MANUAL)
        self._update_target_queue()
        self._update_map()
        print(f"[Target] Added from map: {target}")

    def _on_investigate_requested(self, lat: float, lon: float):
        """Handle investigate request - send selected vehicle to location."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        # Get current altitude for the goto command
        alt = vehicle.state.alt if vehicle.state.alt > 10 else 50  # Default 50m if too low

        # Confirm with user
        reply = QMessageBox.question(
            self, "Investigate Point",
            f"Send {vehicle.name} to investigate?\n\n"
            f"Location: {lat:.5f}, {lon:.5f}\n"
            f"Altitude: {alt:.0f}m\n\n"
            "Vehicle will switch to GUIDED mode and fly to this point.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Set mode to GUIDED and send goto command
            self._mavlink.set_mode(self._selected_vehicle, "GUIDED")
            # Small delay for mode change to take effect
            QTimer.singleShot(500, lambda: self._mavlink.goto(self._selected_vehicle, lat, lon, alt))
            print(f"[Investigate] {vehicle.name} -> ({lat:.5f}, {lon:.5f}) @ {alt:.0f}m")

    def _on_arm_requested(self, arm: bool):
        """Handle arm/disarm request from mode panel."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        action = "Arm" if arm else "Disarm"

        # For arming copters, set to GUIDED mode first
        if arm and vehicle.type.value == "copter":
            print(f"[Arm] Setting {vehicle.name} to GUIDED mode before arming...")
            self._mavlink.set_mode(self._selected_vehicle, "GUIDED")

        # Confirm arm/disarm
        if arm:
            msg = (f"Arm {vehicle.name}?\n\n"
                   f"Mode: {vehicle.state.mode}\n"
                   f"WARNING: Motors will spin!")
        else:
            msg = f"Disarm {vehicle.name}?"

        reply = QMessageBox.question(
            self, f"{action} Vehicle", msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No if arm else QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Send arm command
            self._mavlink.arm(self._selected_vehicle, arm)
            print(f"[{action}] Command sent to {vehicle.name}")

            # For SITL: if arm fails, offer force arm
            if arm:
                QTimer.singleShot(2000, lambda: self._check_arm_status(vehicle))

    def _check_arm_status(self, vehicle):
        """Check if arm succeeded, offer force arm if not."""
        if vehicle.state.armed:
            return  # Already armed, success

        reply = QMessageBox.question(
            self, "Arm Failed",
            f"{vehicle.name} did not arm.\n\n"
            "Pre-arm checks may have failed.\n\n"
            "Force arm? (bypasses safety checks - SITL only!)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._mavlink.arm(vehicle.id, True, force=True)
            print(f"[Arm] Force arm sent to {vehicle.name}")

    def _on_takeoff_requested(self, altitude: float):
        """Handle takeoff request from mode panel."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        # Check if armed
        if not vehicle.state.armed:
            QMessageBox.warning(self, "Not Armed",
                f"{vehicle.name} is not armed.\n\nArm the vehicle first before takeoff.")
            return

        # Confirm takeoff
        reply = QMessageBox.question(
            self, "Confirm Takeoff",
            f"Takeoff {vehicle.name}?\n\n"
            f"Target altitude: {altitude:.0f}m\n\n"
            "Vehicle will climb to target altitude and hover.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # For copters: use GUIDED mode and send takeoff command
            # For planes: use TAKEOFF mode or AUTO with takeoff waypoint
            if vehicle.type.value == "copter":
                self._mavlink.set_mode(self._selected_vehicle, "GUIDED")
                QTimer.singleShot(500, lambda: self._mavlink.takeoff(self._selected_vehicle, altitude))
            else:
                # For planes, switch to TAKEOFF mode
                self._mavlink.set_mode(self._selected_vehicle, "TAKEOFF")
            print(f"[Takeoff] {vehicle.name} -> {altitude:.0f}m")

    def _on_land_requested(self):
        """Handle land request from mode panel."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        reply = QMessageBox.question(
            self, "Confirm Land",
            f"Land {vehicle.name} now?\n\n"
            "Vehicle will descend and land at current position.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._mavlink.set_mode(self._selected_vehicle, "LAND")
            print(f"[Land] {vehicle.name}")

    def _on_target_selected(self, target_id: str):
        """Handle target selection."""
        self._targets.selected = target_id
        self._update_orb_display()

    def _on_target_removed(self, target_id: str):
        """Handle target removal."""
        self._targets.remove(target_id)
        self._update_target_queue()
        self._update_map()

    def _on_target_renamed(self, target_id: str, new_name: str):
        """Handle target rename."""
        self._targets.rename(target_id, new_name)
        self._update_target_queue()
        print(f"[Target] Renamed {target_id} to '{new_name}'")

    def _on_target_description_changed(self, target_id: str, description: str):
        """Handle target description change."""
        self._targets.set_description(target_id, description)
        print(f"[Target] Updated description for {target_id}")

    def _on_manual_entry(self):
        """Show manual coordinate entry dialog."""
        dialog = ManualCoordDialog(self)
        if dialog.exec_():
            lat, lon, name, description = dialog.get_coordinates()
            if lat is not None and lon is not None:
                target = self._targets.add(lat, lon, TargetSource.MANUAL)
                if name:
                    self._targets.rename(target.id, name)
                if description:
                    self._targets.set_description(target.id, description)
                self._update_target_queue()
                self._update_map()
                print(f"[Target] Manual entry: {target}")

    def _on_orb_selected(self, orb_id: str):
        """Handle orb selection."""
        self._orbs.selected = orb_id
        self._update_orb_display()

    def _on_assign_target(self):
        """Assign selected target to selected orb."""
        orb = self._orbs.selected
        target = self._targets.selected
        if orb and target:
            orb.assign_target(target.id)
            self._targets.assign_to_orb(target.id, orb.id)

            # Send target to Chick via LoRa
            from .comms.lora_manager import TargetCoordinate
            target_coord = TargetCoordinate(
                target_id=target.id,
                lat=target.lat,
                lon=target.lon
            )
            self._lora.send_target_to_chick(orb.carrier, target_coord)

            self._update_orb_display()
            self._update_target_queue()
            print(f"[Orb] Assigned target {target.id} to ORB{orb.id}")

    def _on_arm_orb(self):
        """Arm selected orb."""
        orb = self._orbs.selected
        if orb and orb.arm():
            # Send arm command via LoRa
            self._lora.send_arm_command(orb.carrier, orb.slot)
            self._update_orb_display()
            print(f"[Orb] Armed ORB{orb.id}")

    def _on_disarm_orb(self):
        """Disarm selected orb."""
        orb = self._orbs.selected
        if orb and orb.disarm():
            # Send disarm command via LoRa
            self._lora.send_disarm_command(orb.carrier, orb.slot)
            self._update_orb_display()
            print(f"[Orb] Disarmed ORB{orb.id}")

    def _on_release_orb(self):
        """Release selected orb."""
        orb = self._orbs.selected
        if orb and orb.release():
            # Send release command via LoRa
            self._lora.send_release_command(orb.carrier, orb.slot)
            self._update_orb_display()
            print(f"[Orb] Released ORB{orb.id}")

    def _on_launch_chick(self):
        """Launch the currently selected Chick from Bird."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle or not vehicle.can_launch:
            return

        # Confirm launch
        carrier_name = self._vehicles[vehicle.carrier].name if vehicle.carrier else "carrier"
        reply = QMessageBox.question(
            self, "Confirm Launch",
            f"Launch {vehicle.name} from {carrier_name}?\n\n"
            f"The Chick will detach and begin autonomous flight.\n"
            f"Current altitude: {vehicle.state.alt:.0f}m",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Get carrier's current position for chick release point
            carrier = self._vehicles.get(vehicle.carrier) if vehicle.carrier else None
            if carrier:
                # Set chick position to carrier's current position (simulation)
                self._mavlink.set_vehicle_position(
                    vehicle.id,
                    carrier.state.lat,
                    carrier.state.lon,
                    carrier.state.alt,
                    carrier.state.heading
                )

            if vehicle.launch():
                # Send launch command via LoRa
                self._lora.send_launch_chick_command(vehicle.slot)
                print(f"[Launch] {vehicle.name} launching from {vehicle.carrier} (slot {vehicle.slot})")

                # In simulation, immediately mark as launched
                # In real operation, wait for confirmation from Bird
                QTimer.singleShot(1000, lambda v=vehicle: self._complete_chick_launch(v.id))

    def _complete_chick_launch(self, vehicle_id: str):
        """Complete chick launch sequence (called after confirmation)."""
        vehicle = self._vehicles.get(vehicle_id)
        if vehicle and vehicle.chick_state == ChickState.LAUNCHING:
            vehicle.set_launched()
            print(f"[Launch] {vehicle.name} now flying independently")

            # Mark chick as released for swarm tracking
            self._mavlink.mark_chick_released(vehicle_id)

            # Auto-enter AUTO mode so chick will follow swarm formation
            # or execute its uploaded mission
            self._mavlink.set_mode(vehicle_id, "AUTO")
            print(f"[Launch] {vehicle.name} entering AUTO mode")

            # Update UI
            self.vehicle_panel.update_vehicle(
                vehicle_id,
                "AUTO",  # Show the new mode
                vehicle.state.alt,
                vehicle.state.battery_pct,
                True,
                chick_state="launched"
            )
            self._update_mode_panel_for_chick()

    def _on_auto_chick_launch(self, carrier_id: str, chick_id: str):
        """
        Handle automatic chick launch from mission waypoint.

        Hardware integration point:
            - This is called when the carrier reaches a LAUNCH_CHICK waypoint
            - In hardware: triggers LoRa command to release mechanism
            - Servo/actuator on Bird releases the Chick
            - Chick's autopilot takes over once released
        """
        print(f"[AUTO LAUNCH] {carrier_id} releasing {chick_id}")

        vehicle = self._vehicles.get(chick_id)
        if not vehicle:
            print(f"[AUTO LAUNCH] Error: {chick_id} not found")
            return

        if not vehicle.is_attached:
            print(f"[AUTO LAUNCH] {chick_id} already launched")
            return

        # Get carrier's current position for chick release point
        carrier = self._vehicles.get(carrier_id)
        if carrier:
            # Set chick position to carrier's current position (simulation)
            self._mavlink.set_vehicle_position(
                chick_id,
                carrier.state.lat,
                carrier.state.lon,
                carrier.state.alt,
                carrier.state.heading
            )
            print(f"[AUTO LAUNCH] {chick_id} released at ({carrier.state.lat:.5f}, {carrier.state.lon:.5f})")

        # Execute launch sequence
        if vehicle.launch():
            # Send hardware command via LoRa
            # For hardware: This triggers the physical release mechanism
            self._lora.send_launch_chick_command(vehicle.slot)

            # In simulation, complete launch after brief delay
            QTimer.singleShot(500, lambda v=vehicle: self._complete_chick_launch(v.id))

            # Log for hardware debugging
            print(f"[HARDWARE] Would send release command for slot {vehicle.slot}")

    def _on_waypoint_reached(self, vehicle_id: str, wp_index: int, waypoint: dict):
        """
        Handle waypoint reached event.

        Hardware integration point:
            - Called when any vehicle reaches a mission waypoint
            - Can be used to trigger actions, log progress, etc.
            - In hardware: confirms autopilot mission progress
        """
        wp_type = waypoint.get("type", "WAYPOINT")
        print(f"[MISSION] {vehicle_id} reached WP{wp_index + 1}: {wp_type}")

        # Update status bar or mission panel progress indicator
        # This could trigger UI updates showing mission progress

    # ==================== Mission Handlers ====================

    def _on_mission_upload(self, vehicle_id: str, mission):
        """Handle mission upload request."""
        import copy
        waypoints = mission.to_mavlink_format()
        success = self._mavlink.upload_mission(vehicle_id, waypoints)

        if success:
            # Store mission for this vehicle
            self._vehicle_missions[vehicle_id] = copy.deepcopy(mission)
            QMessageBox.information(
                self, "Mission Uploaded",
                f"Successfully uploaded {len(waypoints)} waypoints to {vehicle_id.upper()}."
            )
        else:
            QMessageBox.warning(
                self, "Upload Failed",
                f"Failed to upload mission to {vehicle_id.upper()}."
            )

    def _on_mission_download(self, vehicle_id: str):
        """Handle mission download request."""
        mission = self._mavlink.download_mission(vehicle_id)
        if mission:
            self._vehicle_missions[vehicle_id] = mission
            self.mission_panel.load_mission(mission)
            QMessageBox.information(
                self, "Mission Downloaded",
                f"Downloaded {len(mission)} waypoints from {vehicle_id.upper()}."
            )
        else:
            # In simulation, create mission from current position
            if self._mavlink._simulation_mode:
                from .models.mission import Mission, WaypointType
                vehicle = self._vehicles.get(vehicle_id)
                if vehicle:
                    mission = Mission(name=f"{vehicle_id} Mission", vehicle_id=vehicle_id)
                    mission.add_waypoint(
                        WaypointType.WAYPOINT,
                        vehicle.state.lat, vehicle.state.lon, vehicle.state.alt,
                        param1=0, param2=0, name="Current Position"
                    )
                    self._vehicle_missions[vehicle_id] = mission
                    self.mission_panel.load_mission(mission)
                    QMessageBox.information(
                        self, "Simulation Mode",
                        f"Created mission at {vehicle_id.upper()}'s current position.\n\n"
                        "In real operation, this downloads the active mission from the autopilot."
                    )
            else:
                QMessageBox.warning(
                    self, "Download Failed",
                    f"Failed to download mission from {vehicle_id.upper()}."
                )

    def _on_view_vehicle_mission(self, vehicle_id: str):
        """Show a vehicle's uploaded mission on the map."""
        if vehicle_id in self._vehicle_missions:
            mission = self._vehicle_missions[vehicle_id]
            self.map_widget.set_mission_waypoints(mission.to_map_format())
            self.map_widget.set_mission_vehicle(vehicle_id)
            print(f"[Map] Showing {vehicle_id} mission path ({len(mission)} waypoints)")
        else:
            QMessageBox.information(
                self, "No Mission",
                f"No mission has been uploaded to {vehicle_id.upper()} yet.\n\n"
                "Upload a mission first, or download from the vehicle."
            )

    def _on_mission_map_mode(self):
        """Handle mission panel requesting map click mode."""
        self.map_widget.set_mission_click_mode(True)
        print("[Mission] Map click mode enabled - click map to add waypoints")

    def _on_show_mission(self, mission):
        """Show mission waypoints on map."""
        # Use to_map_format for correct ordering
        self.map_widget.set_mission_waypoints(mission.to_map_format())

    def _on_map_click_for_mission(self, lat: float, lon: float):
        """Handle map click when in mission add mode."""
        if hasattr(self, '_current_tab') and self._current_tab == "MISSION":
            if self.mission_panel.is_adding_from_map:
                self.mission_panel.add_waypoint_at(lat, lon)

    def _on_waypoint_edit_from_map(self, wp_id: int):
        """Handle waypoint edit request from map right-click."""
        if hasattr(self, '_current_tab') and self._current_tab == "MISSION":
            self.mission_panel.edit_waypoint_at(wp_id)

    def _capture_coordinate(self):
        """Capture coordinate from selected vehicle's current position (Space key)."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if vehicle and vehicle.connected:
            target = self._targets.add(
                vehicle.state.lat,
                vehicle.state.lon,
                TargetSource.VIDEO
            )
            self._update_target_queue()
            self._update_map()
            print(f"[Target] Captured from {vehicle.name}: {target}")

    def _cycle_mode(self):
        """Cycle through flight modes for selected vehicle."""
        vehicle = self._vehicles[self._selected_vehicle]
        modes = vehicle.get_modes()
        try:
            idx = modes.index(vehicle.state.mode)
            new_mode = modes[(idx + 1) % len(modes)]
        except ValueError:
            new_mode = modes[0]

        self._mavlink.set_mode(self._selected_vehicle, new_mode)

    def _rtl_all(self):
        """Set all vehicles to RTL mode."""
        reply = QMessageBox.warning(
            self, "Confirm RTL All",
            "Set ALL vehicles to RTL mode?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._mavlink.rtl_all()
            print("[Command] RTL ALL sent")

    def _center_map_on_selected(self):
        """Center map on the selected vehicle (C key)."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if vehicle and vehicle.state.lat != 0:
            self.map_widget.center_on(vehicle.state.lat, vehicle.state.lon)
            print(f"[Map] Centered on {vehicle.name}")

    def _quick_fly_selected(self):
        """Quick fly the selected vehicle (F key) - GUIDED, ARM, TAKEOFF."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        reply = QMessageBox.question(
            self, "Quick Fly",
            f"Quick fly {vehicle.name}?\n\n"
            "This will:\n"
            "1. Set GUIDED mode\n"
            "2. Force ARM (bypass checks)\n"
            "3. Takeoff to 50m (copters)\n\n"
            "Use for SITL testing only!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._mavlink.quick_fly(self._selected_vehicle, 50)
            print(f"[Quick Fly] {vehicle.name}")

    def _on_preflight(self):
        """Show pre-flight check dialog."""
        from .config import SWARM_CONFIG

        # Gather status
        mesh_status = self._lora.get_all_nodes()
        lines = [
            "Pre-Flight Check Results:",
            "=" * 40,
            "",
            "MESH (T-Beam LoRa):"
        ]

        # Check all vehicles from config
        all_vehicle_ids = [b["id"] for b in SWARM_CONFIG["birds"]] + [c["id"] for c in SWARM_CONFIG["chicks"]]
        for vid in all_vehicle_ids:
            status = mesh_status.get(vid)
            if status and status.is_connected:
                lines.append(f"  ✓ {vid.upper()}: {status.rssi} dBm")
            else:
                lines.append(f"  ✗ {vid.upper()}: NOT CONNECTED")

        lines.extend([
            "",
            "MLRS (MAVLink):"
        ])

        for vid in all_vehicle_ids:
            connected = self._mavlink.is_connected(vid)
            if connected:
                telem = self._mavlink.get_telemetry(vid)
                lines.append(f"  ✓ {vid.upper()}: Mode={telem.mode}, Batt={telem.battery_pct}%")
            else:
                lines.append(f"  ✗ {vid.upper()}: NOT CONNECTED")

        lines.extend([
            "",
            "CHICK STATUS:"
        ])

        for chick_cfg in SWARM_CONFIG["chicks"]:
            chick = self._vehicles.get(chick_cfg["id"])
            if chick and chick.chick_state:
                state = chick.chick_state.value.upper()
                carrier = f"on {chick.carrier.upper()}" if chick.is_attached else "independent"
                lines.append(f"  {chick.name}: {state} ({carrier})")

        lines.extend([
            "",
            "VIDEO:",
            f"  Active source: {self._video.active_source or 'None'}",
            "",
            "ORBS:",
        ])

        for orb in self._orbs.get_all():
            lines.append(f"  ORB{orb.id} ({orb.carrier}): {orb.state.value}")

        QMessageBox.information(self, "Pre-Flight Check", "\n".join(lines))

    def _on_connect_clicked(self):
        """Show connection dialog."""
        items = ["Simulation Mode", "SITL (ArduPilot)", "MLRS Serial", "UDP (Tailscale)"]
        item, ok = QInputDialog.getItem(
            self, "Connect", "Select connection type:", items, 0, False
        )

        if ok:
            if item == "Simulation Mode":
                self._start_simulation()
                self.conn_label.setText("SIM MODE")
                self.conn_label.setStyleSheet("color: #facc15; font-weight: bold;")

            elif item == "SITL (ArduPilot)":
                from .config import SITL_CONNECTIONS, SITL_CONNECTIONS_UDP, SITL_USE_TCP
                self._mavlink.stop_simulation()

                # Use TCP or UDP config based on setting
                connections = SITL_CONNECTIONS if SITL_USE_TCP else SITL_CONNECTIONS_UDP
                proto = "TCP" if SITL_USE_TCP else "UDP"

                # Build connection summary
                conn_summary = "\n".join([f"  {vid}: {addr}" for vid, addr in connections.items()])

                # Show info about SITL setup
                if SITL_USE_TCP:
                    setup_info = (
                        f"Run tools\\start_sitl.py to launch 3 SITLs, or:\n"
                        f"  MP #1: Start ArduPlane (Instance 0, port 5760)\n"
                        f"  MP #2: Start ArduCopter (Instance 1, port 5770)\n"
                        f"  MP #3: Start ArduCopter (Instance 2, port 5780)"
                    )
                else:
                    setup_info = (
                        f"Run sim_vehicle.py instances:\n"
                        f"  sim_vehicle.py -v ArduPlane -I 0\n"
                        f"  sim_vehicle.py -v ArduCopter -I 1\n"
                        f"  sim_vehicle.py -v ArduCopter -I 2"
                    )

                reply = QMessageBox.question(
                    self, "SITL Connection",
                    f"Connect to ArduPilot SITL instances? ({proto})\n\n"
                    f"Connections:\n{conn_summary}\n\n"
                    f"{setup_info}\n\n"
                    "Continue?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Reset auto-center so map will center on first telemetry
                    self.map_widget._has_auto_centered = False

                    if self._mavlink.connect_sitl(connections):
                        # Count connected vehicles
                        connected = len(self._mavlink._connections)
                        self.conn_label.setText(f"SITL ({connected})")
                        self.conn_label.setStyleSheet("color: #4ade80; font-weight: bold;")
                        QMessageBox.information(self, "Connected",
                            f"Connected to {connected} SITL instance(s)!\n\n"
                            "Telemetry should now show real data from ArduPilot.\n\n"
                            "Press 'C' to center map on selected vehicle.")
                    else:
                        QMessageBox.warning(self, "Connection Failed",
                            f"Could not connect to any SITL instance.\n\n"
                            "Make sure SITL is running:\n"
                            f"{conn_summary}\n\n"
                            "Each SITL needs a different Instance number (-I flag).")

            elif item == "MLRS Serial":
                port, ok = QInputDialog.getText(
                    self, "MLRS Port", "Enter serial port (e.g., COM4):", text="COM4"
                )
                if ok and port:
                    self._mavlink.stop_simulation()
                    if self._mavlink.connect_mlrs(port):
                        self.conn_label.setText("MLRS")
                        self.conn_label.setStyleSheet("color: #4ade80; font-weight: bold;")
                    else:
                        QMessageBox.warning(self, "Connection Failed",
                                          f"Could not connect to {port}")

            elif item == "UDP (Tailscale)":
                host, ok = QInputDialog.getText(
                    self, "Tailscale IP", "Enter Bird's Tailscale IP:", text="100.64.0.1"
                )
                if ok and host:
                    self._mavlink.stop_simulation()
                    if self._mavlink.connect_backup(host):
                        self.conn_label.setText("4G")
                        self.conn_label.setStyleSheet("color: #4ade80; font-weight: bold;")
                    else:
                        QMessageBox.warning(self, "Connection Failed",
                                          f"Could not connect to {host}")

    def _on_settings(self):
        """Show settings dialog."""
        QMessageBox.information(
            self, "Settings",
            "Settings:\n\n"
            "• MLRS Port: COM4 (configure)\n"
            "• T-Beam Port: COM3 (configure)\n"
            "• Tailscale IP: 100.64.0.1 (configure)\n"
            "• Video RTSP: rtsp://<ip>:8554/<source>\n\n"
            "Configuration file: gcs/config.py"
        )

    def _on_escape(self):
        """Handle escape key."""
        pass

    # ==================== Update Methods ====================

    def _update_map(self):
        """Update map display."""
        vehicles = {}
        for vid, vehicle in self._vehicles.items():
            # Include attachment state for proper rendering
            is_attached = vehicle.is_attached if vehicle.chick_state else False
            vehicles[vid] = (
                vehicle.state.lat,
                vehicle.state.lon,
                vehicle.state.heading,
                vehicle.icon,
                vehicle.name,
                vid == self._selected_vehicle,
                vehicle.state.alt,
                vehicle.state.groundspeed,
                is_attached  # New: whether vehicle is attached to carrier
            )
        self.map_widget.set_vehicles(vehicles)

        targets = {}
        for target in self._targets.get_all():
            targets[target.id] = (target.lat, target.lon, target.assigned_orb)
        self.map_widget.set_targets(targets)

    def _update_target_queue(self):
        """Update target queue display."""
        targets = [
            (t.id, t.lat, t.lon, t.source.value, t.assigned_orb, t.name, t.description)
            for t in self._targets.get_all()
        ]
        self.target_queue.update_targets(targets)

    def _update_orb_display(self):
        """Update orb panel display."""
        for orb in self._orbs.get_all():
            has_target = orb.target_id is not None
            self.orb_panel.update_orb(orb.id, orb.state.value, has_target)

        selected = self._orbs.selected
        if selected:
            self.orb_panel.update_selected_info(selected.id, selected.target_id)
            self.orb_panel.update_buttons(
                can_assign=self._targets.selected is not None and selected.state == OrbState.LOADED,
                can_arm=selected.can_arm,
                can_release=selected.can_release,
                is_armed=selected.state == OrbState.ARMED
            )
        else:
            self.orb_panel.update_selected_info(None)
            self.orb_panel.update_buttons(False, False, False, False)

    def closeEvent(self, event):
        """Clean up on close."""
        self._mavlink.stop_simulation()
        self._lora.stop_simulation()
        self._video.stop_simulation()
        event.accept()
