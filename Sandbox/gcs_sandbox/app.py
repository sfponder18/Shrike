# SwarmDrones Sandbox GCS Main Application
# Modified from main GCS to enable EW panel

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTabWidget, QLabel, QPushButton, QSplitter,
                              QFrame, QMessageBox, QShortcut, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence
import time
import math

from .styles import SANDBOX_STYLE
from .widgets import (MapWidget, VideoWidget, VehiclePanel, TargetQueueWidget,
                      OrbPanel, StatusBar, ModePanel, MissionPanel, EWPanel)
from gcs.widgets.target_queue import ManualCoordDialog
from .models import (Vehicle, VehicleType, VehicleState, ChickState,
                     TargetQueue, TargetSource, OrbManager, OrbState)
from .models.emitter import ProsecutionState
from .comms import MAVLinkManager, LoRaManager, VideoManager, EWManager


class GCSSandboxWindow(QMainWindow):
    """Sandbox GCS window with EW Panel enabled."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SWARM GCS [SANDBOX - EW EXPERIMENTAL]")
        self.setMinimumSize(1280, 720)
        self.resize(1920, 1080)

        # Communications managers
        self._mavlink = MAVLinkManager(self)
        self._lora = LoRaManager(self)
        self._video = VideoManager(self)
        self._ew = EWManager(self)  # NEW: EW Manager

        # Data models
        self._selected_vehicle = None
        self._vehicles = self._init_vehicles()
        self._targets = TargetQueue()
        self._orbs = OrbManager()
        self._current_tab = "FLIGHT"

        # EW map display state - track user-selected emitters separately from auto-display
        self._ew_user_selected_emitters = []  # User selection takes priority

        # Prosecution/attack state - track vehicles actively prosecuting
        self._active_prosecutions = {}  # {vehicle_id: emitter_id}
        self._prosecution_arrived = set()  # Track which prosecutions have arrived

        # Swarm formation - store last known good formation for reform
        self._last_swarm_formation = {}  # {vehicle_id: (lat, lon, alt)}

        # Formation state tracking
        self._formation_members = {}  # {vehicle_id: "in_formation" | "on_task" | "returning"}
        self._pending_reintegrations = []  # Vehicles waiting to rejoin formation

        # Store uploaded/downloaded missions per vehicle
        self._vehicle_missions = {}

        # Connect comms signals
        self._connect_comms_signals()

        # Apply sandbox style (includes EW styles)
        self.setStyleSheet(SANDBOX_STYLE)

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

        # Mission events
        self._mavlink.chick_launch_triggered.connect(self._on_auto_chick_launch)
        self._mavlink.waypoint_reached.connect(self._on_waypoint_reached)

        # LoRa mesh
        self._lora.node_status_updated.connect(self._on_mesh_status_updated)

        # Video
        self._video.frame_received.connect(self._on_video_frame)

        # EW signals
        self._ew.critical_threat.connect(self._on_critical_threat)
        self._ew.hop_recommended.connect(self._on_hop_recommended)
        self._ew.formation_commanded.connect(self._on_ew_formation_commanded)
        self._ew.vehicle_assignment_requested.connect(self._on_ew_vehicle_assignment)
        self._ew.priority_tracks_changed.connect(self._on_priority_tracks_changed)
        self._ew.prosecution_complete.connect(self._on_ew_prosecution_complete)

    def _start_simulation(self):
        """Start all simulations for development."""
        self._mavlink.start_simulation()
        self._lora.start_simulation()
        self._video.start_simulation()

        # Set EW manager base position to match swarm simulation start
        # Swarm starts at (52.0, -1.5) - see mavlink_manager.py
        self._ew.set_base_position(52.0, -1.5)
        self._ew.set_emitter_range(3.0)  # Emitters within ±3km
        self._ew.start_simulation()

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
        # Entity context menu actions
        self.map_widget.vehicle_action_requested.connect(self._on_map_vehicle_action)
        self.map_widget.target_action_requested.connect(self._on_map_target_action)
        self.map_widget.emitter_action_requested.connect(self._on_map_emitter_action)
        self.map_widget.view_vehicle_mission.connect(self._on_view_vehicle_mission)
        left_splitter.addWidget(self.map_widget)

        # Bottom left panel (mode + targets/mission/ew)
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
        self.mode_panel.reform_swarm_requested.connect(self._on_reform_swarm)
        self.mode_panel.altitude_change_requested.connect(self._on_altitude_change)
        self.mode_panel.prosecution_complete_requested.connect(self._on_prosecution_complete)
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
        self.mission_panel.swarm_activated.connect(self._mavlink.activate_swarm)
        self.mission_panel.swarm_deactivated.connect(self._mavlink.deactivate_swarm)
        self.mission_panel.hide()
        bottom_left_layout.addWidget(self.mission_panel)

        # EW Panel (shown in EW tab) - NEW
        self.ew_panel = EWPanel()
        self.ew_panel.set_ew_manager(self._ew)
        self.ew_panel.target_requested.connect(self._on_ew_target_requested)
        self.ew_panel.investigate_requested.connect(self._on_ew_investigate)
        self.ew_panel.emitters_selected_for_map.connect(self._on_ew_emitters_for_map)
        self.ew_panel.prosecute_requested.connect(self._on_ew_prosecute)
        self.ew_panel.prosecution_action_selected.connect(self._on_ew_prosecution_action)
        self.ew_panel.hide()
        bottom_left_layout.addWidget(self.ew_panel)

        left_splitter.addWidget(bottom_left)
        left_splitter.setSizes([500, 250])

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

        # Orb panel (profile-based employment system)
        self.orb_panel = OrbPanel()
        self.orb_panel.orb_clicked.connect(self._on_orb_clicked)
        self.orb_panel.target_drone_assigned.connect(self._on_target_drone_assigned)
        self.orb_panel.arm_requested.connect(self._on_arm_orbs)
        self.orb_panel.disarm_requested.connect(self._on_disarm_orbs)
        self.orb_panel.release_requested.connect(self._on_release_orbs)
        bottom_right_layout.addWidget(self.orb_panel)

        right_splitter.addWidget(bottom_right)
        right_splitter.setSizes([300, 350])

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

        # Title with sandbox indicator
        title = QLabel("SWARM GCS")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Sandbox badge
        sandbox_badge = QLabel("[SANDBOX]")
        sandbox_badge.setStyleSheet("font-size: 12px; font-weight: bold; color: #facc15; margin-left: 8px;")
        layout.addWidget(sandbox_badge)

        layout.addSpacing(20)

        # Tab buttons - ALL ENABLED including EW
        self.tab_buttons = {}
        tabs = ["FLIGHT", "MISSION", "ISR", "EW"]
        for i, tab in enumerate(tabs):
            btn = QPushButton(tab)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            # Enable all tabs except ISR (EW is enabled!)
            btn.setEnabled(tab != "ISR")
            if tab == "ISR":
                btn.setToolTip("Coming in future version")
            elif tab == "EW":
                btn.setToolTip("Electronic Warfare Panel (Experimental)")
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
        # Vehicle selection
        vehicle_ids = list(self._vehicles.keys())
        for i, vid in enumerate(vehicle_ids[:9]):
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

        # Launch chick
        QShortcut(QKeySequence("L"), self, self._on_launch_chick)

        # RTL all
        QShortcut(QKeySequence("Ctrl+R"), self, self._rtl_all)

        # Center map on selected vehicle
        QShortcut(QKeySequence("C"), self, self._center_map_on_selected)

        # Quick fly
        QShortcut(QKeySequence("F"), self, self._quick_fly_selected)

        # EW Tab shortcut
        QShortcut(QKeySequence("E"), self, lambda: self._on_tab_clicked("EW"))

        # Escape
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    # ==================== Tab Switching ====================

    def _on_tab_clicked(self, tab: str):
        """Handle tab button click."""
        for name, btn in self.tab_buttons.items():
            btn.setChecked(name == tab)

        # Switch panel visibility based on tab
        if tab == "FLIGHT":
            self.target_queue.show()
            self.mission_panel.hide()
            self.ew_panel.hide()
            self.mission_panel.cancel_map_add_mode()
            self.map_widget.set_mission_click_mode(False)
            self.map_widget.clear_ew_emitters()  # Clear EW markers
            self._ew_user_selected_emitters = []  # Clear EW selection state
            if self._selected_vehicle in self._vehicle_missions:
                mission = self._vehicle_missions[self._selected_vehicle]
                self.map_widget.set_mission_waypoints(mission.to_map_format())
            else:
                self.map_widget.set_mission_waypoints({})

        elif tab == "MISSION":
            self.target_queue.hide()
            self.mission_panel.show()
            self.ew_panel.hide()
            self.map_widget.clear_ew_emitters()  # Clear EW markers
            self._ew_user_selected_emitters = []  # Clear EW selection state

        elif tab == "EW":
            print("[App] Switching to EW tab")
            self.target_queue.hide()
            self.mission_panel.hide()
            self.ew_panel.show()
            self.mission_panel.cancel_map_add_mode()
            self.map_widget.set_mission_click_mode(False)
            # Refresh EW panel data
            self.ew_panel.refresh()
            # Show priority tracks on map
            self._on_priority_tracks_changed()

        self._current_tab = tab

    # ==================== EW Event Handlers ====================

    def _on_critical_threat(self, emitter_id: str):
        """Handle critical threat detected."""
        # Show alert
        self.status_bar.show_alert(f"CRITICAL THREAT: {emitter_id}")

        # Auto-switch to EW tab if not already there
        if self._current_tab != "EW":
            # Flash EW tab button
            ew_btn = self.tab_buttons.get("EW")
            if ew_btn:
                ew_btn.setStyleSheet("background-color: #8a4a4a;")
                QTimer.singleShot(500, lambda: ew_btn.setStyleSheet(""))

    def _on_hop_recommended(self):
        """Handle hop recommendation from EP."""
        # This could show a dialog or update status
        print("[EP] Frequency hop recommended due to interference")

    def _on_ew_target_requested(self, lat: float, lon: float, emitter_id: str):
        """Handle target creation from EW panel."""
        # Add to target queue
        target = self._targets.add(lat, lon, TargetSource.MANUAL)
        self._targets.rename(target.id, f"EW-{emitter_id}")
        self._targets.set_description(target.id, f"From emitter {emitter_id}")

        # Add to orb panel target list
        self.orb_panel.add_target(target.id, f"EW-{emitter_id}")

        self._update_target_queue()
        self._update_map()

        # Show confirmation
        QMessageBox.information(
            self, "Target Added",
            f"Target created from emitter {emitter_id}\n\n"
            f"Position: {lat:.5f}, {lon:.5f}\n"
            f"Added to target queue as {target.id}"
        )

        # Switch to FLIGHT tab to see target
        self._on_tab_clicked("FLIGHT")

    def _on_ew_investigate(self, emitter_id: str):
        """Handle investigate request from EW panel."""
        try:
            # Get emitter position
            target_data = self._ew.emitter_to_target(emitter_id)
            if not target_data:
                QMessageBox.warning(
                    self, "Cannot Investigate",
                    f"Emitter {emitter_id} does not have a position estimate yet.\n\n"
                    "Wait for DF to provide location."
                )
                return

            # Center map on emitter location
            self.map_widget.center_on(target_data['lat'], target_data['lon'])

            # Send chick to investigate
            # For now, just show info - could auto-send selected chick
            QMessageBox.information(
                self, "Investigate Emitter",
                f"Investigating {emitter_id}\n\n"
                f"Estimated position: {target_data['lat']:.5f}, {target_data['lon']:.5f}\n"
                f"CEP: {target_data['cep_m']:.0f}m\n\n"
                "Use right-click on map to send vehicle to investigate."
            )
        except Exception as e:
            print(f"[EW] Error investigating emitter: {e}")
            QMessageBox.warning(
                self, "Error",
                f"Error investigating emitter {emitter_id}:\n{str(e)}"
            )

    def _on_ew_emitters_for_map(self, emitter_data: list):
        """Display selected EW emitters on the map (user selection)."""
        try:
            # Store user selection - this takes priority over auto-display
            self._ew_user_selected_emitters = emitter_data if emitter_data else []

            # Merge user selection with auto-displayable priority tracks
            self._update_ew_map_display()

            # Center on first emitter if single selection
            if emitter_data and len(emitter_data) == 1:
                lat, lon = emitter_data[0][0], emitter_data[0][1]
                self.map_widget.center_on(lat, lon)
        except Exception as e:
            print(f"[EW] Error displaying emitters on map: {e}")

    def _on_ew_formation_commanded(self, positions: dict):
        """Handle EW formation optimization command."""
        try:
            if not positions:
                return

            # Filter out vehicles that are on prosecution tasks
            available_positions = {}
            excluded = []
            for vid, (lat, lon, alt) in positions.items():
                if vid in self._active_prosecutions:
                    excluded.append(vid)
                else:
                    available_positions[vid] = (lat, lon, alt)

            if not available_positions:
                if excluded:
                    QMessageBox.information(
                        self, "Formation Skipped",
                        f"All vehicles are on prosecution tasks:\n{', '.join(excluded)}\n\n"
                        "Formation optimization skipped."
                    )
                return

            # Build message for confirmation
            pos_lines = []
            for vid, (lat, lon, alt) in available_positions.items():
                vehicle = self._vehicles.get(vid)
                name = vehicle.name if vehicle else vid
                pos_lines.append(f"  {name}: {lat:.5f}, {lon:.5f} @ {alt:.0f}m")

            excluded_msg = ""
            if excluded:
                excluded_names = [self._vehicles.get(v).name if self._vehicles.get(v) else v for v in excluded]
                excluded_msg = f"\n\nExcluded (on prosecution): {', '.join(excluded_names)}"

            reply = QMessageBox.question(
                self, "Optimize DF Formation",
                "Command vehicles to optimal DF positions?\n\n"
                "Recommended positions:\n" + "\n".join(pos_lines) + excluded_msg + "\n\n"
                "This will set GUIDED mode and fly vehicles to these positions.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Command each available vehicle to its optimal position
                for vid, (lat, lon, alt) in available_positions.items():
                    vehicle = self._vehicles.get(vid)
                    if vehicle and vehicle.connected:
                        self._mavlink.set_mode(vid, "GUIDED")
                        QTimer.singleShot(500, lambda v=vid, la=lat, lo=lon, a=alt:
                                         self._mavlink.goto(v, la, lo, a))
                        print(f"[EW] Commanding {vid} to ({lat:.5f}, {lon:.5f}) @ {alt:.0f}m")

                print("[EW] DF formation optimization in progress")

        except Exception as e:
            print(f"[EW] Formation command error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to command formation:\n{str(e)}")

    def _on_ew_prosecute(self, emitter_id: str):
        """Handle prosecute request from EW panel right-click menu."""
        try:
            emitter = self._ew.emitters.get(emitter_id)
            if not emitter:
                print(f"[EW] Emitter {emitter_id} not found")
                return

            # Check if emitter has a valid position
            if not emitter.df_result or emitter.df_result.cep_m > 500:
                QMessageBox.warning(
                    self, "Position Inaccurate",
                    f"Emitter position CEP is too large ({emitter.df_result.cep_m if emitter.df_result else 'N/A'}m).\n"
                    "Continue tracking to improve accuracy before prosecuting."
                )
                return

            # Show vehicle selection dialog
            selected_vehicle = self._show_prosecution_vehicle_dialog(emitter_id, emitter)
            if not selected_vehicle:
                return  # User cancelled

            # Start prosecution workflow in EW manager
            success = self._ew.prosecute_emitter(emitter_id)
            if not success:
                return

            # Add emitter to target queue for employment management
            short_id = emitter_id[-8:] if len(emitter_id) > 8 else emitter_id
            target = self._targets.add(
                emitter.df_result.lat,
                emitter.df_result.lon,
                TargetSource.EW,
                notes=f"EW Track: {emitter_id}"
            )
            # Store emitter reference for EW symbol display
            target.emitter_id = emitter_id
            # Name it with EW prefix
            target_name = f"EW-{short_id}"
            if emitter.library_match:
                # Include classification if known
                match_short = emitter.library_match[:12] if len(emitter.library_match) > 12 else emitter.library_match
                target_name = f"EW-{match_short}"
            self._targets.rename(target.id, target_name)

            # Store the link between emitter and target
            emitter.target_id = target.id

            # Add target to orb panel's target list
            self.orb_panel.add_target(target.id, target_name)

            # Track this prosecution and mark vehicle as on task
            self._active_prosecutions[selected_vehicle] = emitter_id
            self._formation_members[selected_vehicle] = "on_task"

            # Auto-assign orbs from prosecuting vehicle
            # The prosecuting vehicle (chick) carries the orbs
            self.orb_panel.set_target_drone(target.id, selected_vehicle)
            self._auto_assign_orbs_for_target(target.id, selected_vehicle)

            # Command the selected vehicle to the target
            vehicle = self._vehicles.get(selected_vehicle)
            vehicle_name = vehicle.name if vehicle else selected_vehicle

            if vehicle and vehicle.connected and emitter.df_result:
                target_lat = emitter.df_result.lat
                target_lon = emitter.df_result.lon
                target_alt = vehicle.state.alt if vehicle.state.alt > 10 else 100

                print(f"[EW] Commanding {vehicle_name} to ({target_lat:.6f}, {target_lon:.6f}, {target_alt:.0f}m)")

                self._mavlink.set_mode(selected_vehicle, "GUIDED")
                # Capture values in lambda to avoid closure issues
                QTimer.singleShot(500, lambda vid=selected_vehicle, lat=target_lat, lon=target_lon, alt=target_alt:
                    self._mavlink.goto(vid, lat, lon, alt))

                print(f"[EW] {vehicle_name} commanded to prosecute {emitter_id}")
                print(f"[EW] Vehicle flying DIRECTLY to target at ({target_lat:.6f}, {target_lon:.6f})")
            else:
                print(f"[EW] WARNING: Could not command {vehicle_name} - vehicle not ready")

            # Set emitter to PROSECUTING state (not LOCATING - we're going directly)
            emitter.set_prosecution_state(ProsecutionState.PROSECUTING)
            emitter.assigned_vehicle = selected_vehicle

            # Update displays
            self._update_target_queue()
            self._update_map()

            # Switch to FLIGHT tab for employment management
            self._on_tab_clicked("FLIGHT")

            # Select the new target
            self._targets.selected = target.id
            self._update_target_queue()
            self.target_queue.select_target(target.id)

            print(f"[EW] Prosecution started: {vehicle_name} -> {emitter_id} -> Target {target.id}")

        except Exception as e:
            import traceback
            print(f"[EW] Prosecute error: {e}")
            traceback.print_exc()

    def _show_prosecution_vehicle_dialog(self, emitter_id: str, emitter) -> str:
        """Show dialog to select which formation member will prosecute the target."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QButtonGroup, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Prosecution Vehicle")
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)

        # Header info
        short_id = emitter_id[-8:] if len(emitter_id) > 8 else emitter_id
        header = QLabel(f"<b>Prosecute Emitter: {short_id}</b>")
        layout.addWidget(header)

        if emitter.library_match:
            type_label = QLabel(f"Type: {emitter.library_match}")
            layout.addWidget(type_label)

        if emitter.df_result:
            pos_label = QLabel(f"Position: {emitter.df_result.lat:.5f}, {emitter.df_result.lon:.5f}")
            layout.addWidget(pos_label)
            cep_label = QLabel(f"CEP: {emitter.df_result.cep_m:.0f}m")
            layout.addWidget(cep_label)

        layout.addSpacing(10)
        layout.addWidget(QLabel("<b>Select formation member to assign:</b>"))

        # Create radio buttons for available vehicles
        button_group = QButtonGroup(dialog)
        available_vehicles = []

        for vid, vehicle in self._vehicles.items():
            # Skip vehicles that aren't available
            if not vehicle.connected:
                continue
            if vehicle.chick_state and vehicle.is_attached:
                continue

            # Calculate distance to emitter
            dist = 0
            if emitter.df_result:
                from gcs.widgets.map_widget import haversine_distance
                dist = haversine_distance(
                    vehicle.state.lat, vehicle.state.lon,
                    emitter.df_result.lat, emitter.df_result.lon
                )

            # Check if already on task
            status = ""
            if vid in self._active_prosecutions:
                status = " [BUSY - prosecuting]"
            elif self._formation_members.get(vid) == "on_task":
                status = " [BUSY - on task]"

            radio = QRadioButton(f"{vehicle.name} - {dist/1000:.1f}km away{status}")
            radio.setProperty("vehicle_id", vid)

            # Disable if busy
            if status:
                radio.setEnabled(False)
            else:
                available_vehicles.append((vid, dist))

            button_group.addButton(radio)
            layout.addWidget(radio)

        # Pre-select closest available vehicle
        if available_vehicles:
            available_vehicles.sort(key=lambda x: x[1])
            closest_vid = available_vehicles[0][0]
            for btn in button_group.buttons():
                if btn.property("vehicle_id") == closest_vid:
                    btn.setChecked(True)
                    break

        layout.addSpacing(10)

        # Note about formation
        note = QLabel("<i>Other formation members will continue the mission.</i>")
        note.setStyleSheet("color: #9ca3af;")
        layout.addWidget(note)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            # Find selected vehicle
            for btn in button_group.buttons():
                if btn.isChecked():
                    return btn.property("vehicle_id")

        return None

    def _on_ew_prosecution_action(self, emitter_id: str, action: str):
        """Handle prosecution action selection (INVESTIGATE/MARK_TARGET/CONTINUE)."""
        try:
            from .models import ProsecutionAction

            action_enum = ProsecutionAction(action)

            # Assign vehicle for the action
            assigned = self._ew.assign_prosecution_vehicle(emitter_id, action_enum)

            if assigned:
                print(f"[EW] Prosecution action {action} assigned to {assigned} for {emitter_id}")
            else:
                QMessageBox.warning(
                    self, "No Vehicle Available",
                    f"No Chick available to prosecute {emitter_id}.\n\n"
                    "Ensure at least one Chick is deployed and not already assigned."
                )
        except Exception as e:
            print(f"[EW] Prosecution action error: {e}")

    def _on_ew_vehicle_assignment(self, emitter_id: str, vehicle_id: str, lat: float, lon: float):
        """Handle vehicle assignment request from EW manager."""
        try:
            vehicle = self._vehicles.get(vehicle_id)
            vehicle_name = vehicle.name if vehicle else vehicle_id

            # Check if vehicle is already prosecuting
            if vehicle_id in self._active_prosecutions:
                current_target = self._active_prosecutions[vehicle_id]
                reply = QMessageBox.warning(
                    self, "Vehicle Busy",
                    f"{vehicle_name} is currently prosecuting {current_target}.\n\n"
                    f"Abort current prosecution and reassign to {emitter_id}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                # Cancel old prosecution
                self._ew.cancel_prosecution(current_target)

            emitter = self._ew.emitters.get(emitter_id)
            action_str = emitter.prosecution_action if emitter else "INVESTIGATE"

            reply = QMessageBox.question(
                self, "Confirm Vehicle Assignment",
                f"Assign {vehicle_name} to {action_str} emitter {emitter_id}?\n\n"
                f"Target position: {lat:.5f}, {lon:.5f}\n\n"
                "This will command the vehicle to the target location.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                # Track this prosecution
                self._active_prosecutions[vehicle_id] = emitter_id

                # Command vehicle to target
                if vehicle and vehicle.connected:
                    # Use vehicle's current altitude or default to 100m
                    target_alt = vehicle.state.alt if vehicle.state.alt > 10 else 100

                    self._mavlink.set_mode(vehicle_id, "GUIDED")
                    # Capture values in lambda to avoid closure issues
                    QTimer.singleShot(500, lambda vid=vehicle_id, la=lat, lo=lon, alt=target_alt:
                                     self._mavlink.goto(vid, la, lo, alt))
                    print(f"[EW] {vehicle_id} commanded to prosecute {emitter_id} @ {target_alt:.0f}m")

                    # Show on map
                    self.map_widget.center_on(lat, lon)
            else:
                # Cancel the assignment
                self._ew.cancel_prosecution(emitter_id)

        except Exception as e:
            print(f"[EW] Vehicle assignment error: {e}")

    def _on_priority_tracks_changed(self):
        """Handle priority tracks changed - update map with auto-displayable emitters."""
        try:
            if self._current_tab == "EW":
                # Merge auto-displayable emitters with user selection
                self._update_ew_map_display()
        except Exception as e:
            print(f"[EW] Priority tracks update error: {e}")

    def _on_ew_prosecution_complete(self, emitter_id: str):
        """Handle prosecution complete - clear tracking and queue for reintegration."""
        try:
            # Clean up arrival tracking
            if hasattr(self, '_prosecution_arrived') and emitter_id in self._prosecution_arrived:
                self._prosecution_arrived.discard(emitter_id)

            # Find and clear the vehicle that was prosecuting this emitter
            vehicle_to_clear = None
            for vid, eid in self._active_prosecutions.items():
                if eid == emitter_id:
                    vehicle_to_clear = vid
                    break

            if vehicle_to_clear:
                del self._active_prosecutions[vehicle_to_clear]
                vehicle = self._vehicles.get(vehicle_to_clear)
                vehicle_name = vehicle.name if vehicle else vehicle_to_clear

                # Mark for reintegration
                self._formation_members[vehicle_to_clear] = "returning"
                self._pending_reintegrations.append(vehicle_to_clear)

                print(f"[EW] Prosecution complete: {vehicle_name} finished with {emitter_id}")
                print(f"[FORMATION] {vehicle_name} queued for reintegration")

                # Prompt for reintegration
                self._prompt_reintegration(vehicle_to_clear)

        except Exception as e:
            print(f"[EW] Prosecution complete error: {e}")

    def _prompt_reintegration(self, vehicle_id: str):
        """Prompt to reintegrate a vehicle back into formation."""
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return

        reply = QMessageBox.question(
            self, "Reintegrate to Formation",
            f"{vehicle.name} has completed its task.\n\n"
            "Reintegrate into formation sweep?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._reintegrate_vehicle(vehicle_id)
        else:
            # Leave in returning state, can be manually reintegrated later
            print(f"[FORMATION] {vehicle.name} standing by for manual reintegration")

    def _reintegrate_vehicle(self, vehicle_id: str):
        """Reintegrate a vehicle back into the formation."""
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return

        # Calculate formation position
        formation_pos = self._calculate_reintegration_position(vehicle_id)
        if formation_pos:
            lat, lon, alt = formation_pos
            self._mavlink.set_mode(vehicle_id, "AUTO")
            # Capture values in lambda to avoid closure issues
            QTimer.singleShot(500, lambda vid=vehicle_id, la=lat, lo=lon, a=alt:
                self._mavlink.goto(vid, la, lo, a))
            print(f"[FORMATION] {vehicle.name} reintegrating to ({lat:.5f}, {lon:.5f})")

        # Update state
        self._formation_members[vehicle_id] = "in_formation"
        if vehicle_id in self._pending_reintegrations:
            self._pending_reintegrations.remove(vehicle_id)

    def _calculate_reintegration_position(self, vehicle_id: str) -> tuple:
        """Calculate where a vehicle should rejoin the formation."""
        # If we have a stored formation, use that
        if vehicle_id in self._last_swarm_formation:
            return self._last_swarm_formation[vehicle_id]

        # Otherwise calculate based on Bird position
        bird = self._vehicles.get("bird1")
        if not bird:
            return None

        # Default offset behind Bird
        offset_lat = -0.002  # ~220m behind
        offset_lon = 0.001 if "chick1" in vehicle_id else -0.001  # Left/right offset

        return (
            bird.state.lat + offset_lat,
            bird.state.lon + offset_lon,
            bird.state.alt - 20  # Slightly lower than Bird
        )

    def _update_ew_map_display(self):
        """
        Update map with merged EW emitters: user selection + auto-displayable priority tracks.
        User selection takes priority (marked as selected).
        """
        try:
            # Get user-selected emitter IDs
            user_selected_ids = set()
            for data in self._ew_user_selected_emitters:
                if len(data) >= 3:
                    user_selected_ids.add(data[2])  # ID is at index 2

            # Start with user-selected emitters (they're already marked as selected)
            merged_emitters = list(self._ew_user_selected_emitters)

            # Get auto-displayable priority tracks
            display_data = self._ew.get_displayable_emitters()

            # Add priority tracks that aren't already selected
            for data in display_data:
                if data.get('display_type') == 'position':
                    emitter_id = data['id']
                    if emitter_id not in user_selected_ids:
                        # Add as non-selected priority track
                        merged_emitters.append((
                            data['lat'],
                            data['lon'],
                            emitter_id,
                            data['cep_m'],
                            data.get('priority', False),
                            data.get('prosecution_state'),
                            False  # Not selected by user
                        ))

            # Update map with merged data
            if merged_emitters:
                self.map_widget.set_ew_emitters(merged_emitters)
            else:
                self.map_widget.clear_ew_emitters()
        except Exception as e:
            print(f"[EW] Map update error: {e}")

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

        # If carrier bird, sync chicks
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
            self.mode_panel.set_altitude(telemetry.alt)
            self._update_mode_panel_for_chick()

        # Update EW manager with vehicle position for proximity calculations
        self._ew.update_vehicle_position(vehicle_id, telemetry.lat, telemetry.lon, telemetry.alt)

        # Check if prosecuting vehicle has arrived at target
        try:
            self._check_prosecution_arrival(vehicle_id, telemetry.lat, telemetry.lon, telemetry.alt)
        except Exception as e:
            print(f"[ERROR] Prosecution arrival check failed: {e}")

        # Update orb range calculations
        try:
            self._update_orb_range_status(vehicle_id, telemetry.lat, telemetry.lon, telemetry.alt)
        except Exception as e:
            print(f"[ERROR] Orb range status update failed: {e}")

        self._update_map()

    def _check_prosecution_arrival(self, vehicle_id: str, lat: float, lon: float, alt: float):
        """Check if a prosecuting vehicle has arrived at its target."""
        if vehicle_id not in self._active_prosecutions:
            return

        emitter_id = self._active_prosecutions[vehicle_id]
        emitter = self._ew.emitters.get(emitter_id) if self._ew else None
        if not emitter or not emitter.df_result:
            return

        # Calculate distance to target
        target_lat = emitter.df_result.lat
        target_lon = emitter.df_result.lon
        dist = self._calculate_distance(lat, lon, target_lat, target_lon)

        # Consider arrived if within 50m
        arrival_threshold = 50  # meters
        if dist < arrival_threshold:
            vehicle = self._vehicles.get(vehicle_id)
            vehicle_name = vehicle.name if vehicle else vehicle_id

            # Only notify once per prosecution
            if emitter_id not in self._prosecution_arrived:
                self._prosecution_arrived.add(emitter_id)

                print(f"[PROSECUTE] {vehicle_name} ARRIVED at target {emitter_id} (dist: {dist:.0f}m)")

                # Update emitter state
                emitter.set_prosecution_state(ProsecutionState.RESOLVED)

                # Show notification
                self.statusBar().showMessage(
                    f"{vehicle_name} arrived at prosecution target - {dist:.0f}m from emitter", 5000
                )

                # Update EW panel
                self._ew.priority_tracks_changed.emit()

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters."""
        d_lat = (lat2 - lat1) * 111000
        d_lon = (lon2 - lon1) * 111000 * math.cos(math.radians(lat1))
        return math.sqrt(d_lat**2 + d_lon**2)

    def _update_orb_range_status(self, vehicle_id: str, lat: float, lon: float, alt: float):
        """Update orb range status based on vehicle position relative to assigned targets."""
        # Only calculate for chicks that carry orbs
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle or vehicle.type != VehicleType.COPTER:
            return

        # Get orbs on this vehicle
        vehicle_orbs = [o for o in self._orbs.get_all() if o.carrier == vehicle_id]
        if not vehicle_orbs:
            return

        # Calculate range for EACH orb on this vehicle that has a target
        for orb in vehicle_orbs:
            if not orb.target_id:
                # Clear range info for orbs without targets
                self.orb_panel.update_orb_range(orb.id, None, None, None)
                continue

            # Get the target for this orb
            target = self._targets.get(orb.target_id)
            if not target:
                self.orb_panel.update_orb_range(orb.id, None, None, None)
                continue

            # Calculate distance to the orb's assigned target
            horiz_dist = self._calculate_distance(lat, lon, target.lat, target.lon)

            # Calculate max range based on altitude and glide characteristics
            max_range = self._calculate_orb_max_range(alt, orb)
            in_range = horiz_dist <= max_range
            time_to_range = self._calculate_time_to_range(
                vehicle, horiz_dist, max_range
            ) if not in_range else 0

            # Update range info for this specific orb
            self.orb_panel.update_orb_range(orb.id, in_range, time_to_range, horiz_dist)

    def _calculate_orb_max_range(self, release_alt: float, orb) -> float:
        """
        Calculate maximum horizontal range for an orb based on release altitude.

        Uses kinematic model for guided glide munition:
        - Assumes low glide ratio (L/D ~2-4 for compact guided munition)
        - Accounts for initial acceleration and terminal guidance phase

        Args:
            release_alt: Release altitude in meters AGL
            orb: Orb object

        Returns:
            Maximum horizontal range in meters
        """
        # Orb kinematic parameters (conservative estimates for guided drop)
        GLIDE_RATIO = 2.5          # L/D ratio (horizontal:vertical distance)
        MIN_GUIDANCE_ALT = 30      # Minimum altitude for terminal guidance (m)
        TERMINAL_RANGE = 50        # Additional range from terminal phase (m)

        # Effective altitude for glide calculation
        effective_alt = max(0, release_alt - MIN_GUIDANCE_ALT)

        # Basic glide range
        glide_range = effective_alt * GLIDE_RATIO

        # Add terminal guidance capability
        total_range = glide_range + TERMINAL_RANGE

        # Safety margin (80% of theoretical max)
        return total_range * 0.8

    def _calculate_time_to_range(self, vehicle, current_dist: float, max_range: float) -> float:
        """
        Calculate estimated time until vehicle is in orb range of target.

        Args:
            vehicle: Vehicle object
            current_dist: Current distance to target in meters
            max_range: Maximum orb range in meters

        Returns:
            Time in seconds until in range, or -1 if moving away
        """
        if current_dist <= max_range:
            return 0

        # Use vehicle's current speed
        speed = vehicle.state.groundspeed if vehicle.state.groundspeed > 1 else 20  # Default 20 m/s

        # Distance to close
        dist_to_close = current_dist - max_range

        # Time estimate (assuming direct approach)
        return dist_to_close / speed

    def _sync_attached_chicks(self, carrier_id: str):
        """Synchronize attached Chicks to their carrier's position."""
        from .config import get_chicks_for_bird

        carrier = self._vehicles.get(carrier_id)
        if not carrier:
            return

        for chick_id in get_chicks_for_bird(carrier_id):
            chick = self._vehicles.get(chick_id)
            if chick and chick.is_attached:
                chick.state.lat = carrier.state.lat
                chick.state.lon = carrier.state.lon
                chick.state.alt = carrier.state.alt
                chick.state.heading = carrier.state.heading
                chick.state.groundspeed = carrier.state.groundspeed

    def _update_mode_panel_for_chick(self):
        """Update mode panel to show launch button if Chick is selected."""
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
        """Handle mode change confirmation."""
        if vehicle_id == self._selected_vehicle:
            self.mode_panel.set_current_mode(mode)

    def _on_mesh_status_updated(self, node_name: str, status):
        """Handle mesh node status update."""
        from .config import SWARM_CONFIG

        birds = [b["id"] for b in SWARM_CONFIG["birds"]]
        chicks = [c["id"] for c in SWARM_CONFIG["chicks"]]

        if node_name in birds:
            self.status_bar.update_mesh(bird=(status.is_connected, status.rssi))
        elif node_name in chicks:
            idx = chicks.index(node_name)
            if idx == 0:
                self.status_bar.update_mesh(c1=(status.is_connected, status.rssi))
            elif idx == 1:
                self.status_bar.update_mesh(c2=(status.is_connected, status.rssi))

        self.status_bar.update_time(time.strftime("%H:%M:%S"))

    def _on_video_frame(self, source_id: str, frame):
        """Handle video frame."""
        self.video_widget.set_frame(frame)

    # ==================== UI Event Handlers ====================

    def _on_vehicle_selected(self, vehicle_id: str):
        """Handle vehicle selection."""
        if vehicle_id not in self._vehicles:
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

        if vehicle.chick_state:
            self.mode_panel.set_chick_state(
                vehicle.chick_state.value,
                vehicle.can_launch
            )
        else:
            self.mode_panel.set_chick_state(None, False)

        # Update prosecution state (show/hide complete button)
        if vehicle_id in self._active_prosecutions:
            emitter_id = self._active_prosecutions[vehicle_id]
            self.mode_panel.set_prosecution_state(True, emitter_id)
        else:
            self.mode_panel.set_prosecution_state(False)

    def _on_mode_button_clicked(self, mode: str):
        """Handle mode button click."""
        # Check if selected vehicle is actively prosecuting
        if self._selected_vehicle in self._active_prosecutions:
            emitter_id = self._active_prosecutions[self._selected_vehicle]
            reply = QMessageBox.warning(
                self, "Active Prosecution",
                f"This vehicle is actively prosecuting {emitter_id}.\n\n"
                "Changing mode will abort the prosecution. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            # Clear the prosecution
            del self._active_prosecutions[self._selected_vehicle]
            self._ew.cancel_prosecution(emitter_id)

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
        pass

    def _on_map_target_added(self, lat: float, lon: float):
        """Handle target added from map."""
        target = self._targets.add(lat, lon, TargetSource.MANUAL)
        # Add to orb panel target list
        self.orb_panel.add_target(target.id, target.name or target.id)
        self._update_target_queue()
        self._update_map()

    def _on_investigate_requested(self, lat: float, lon: float):
        """Handle investigate request from map."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        alt = vehicle.state.alt if vehicle.state.alt > 10 else 50

        reply = QMessageBox.question(
            self, "Investigate Point",
            f"Send {vehicle.name} to investigate?\n\n"
            f"Location: {lat:.5f}, {lon:.5f}\n"
            f"Altitude: {alt:.0f}m",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._mavlink.set_mode(self._selected_vehicle, "GUIDED")
            # Capture values in lambda to avoid closure issues
            QTimer.singleShot(500, lambda vid=self._selected_vehicle, la=lat, lo=lon, a=alt:
                self._mavlink.goto(vid, la, lo, a))

    def _on_map_vehicle_action(self, vehicle_id: str, action: str):
        """Handle vehicle context menu actions from map."""
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return

        if action == "select":
            self._on_vehicle_selected(vehicle_id)
        elif action == "rtl":
            reply = QMessageBox.question(
                self, "Confirm RTL",
                f"Command {vehicle.name} to Return To Launch?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._mavlink.set_mode(vehicle_id, "RTL")
        elif action == "loiter":
            self._mavlink.set_mode(vehicle_id, "LOITER")

    def _on_map_target_action(self, target_id: str, action: str):
        """Handle target context menu actions from map."""
        target = self._targets.get(target_id)
        if not target:
            return

        if action == "fly_to":
            # Fly selected vehicle to target
            vehicle = self._vehicles.get(self._selected_vehicle)
            if not vehicle:
                QMessageBox.warning(self, "No Vehicle", "No vehicle selected.")
                return

            alt = vehicle.state.alt if vehicle.state.alt > 10 else 50
            reply = QMessageBox.question(
                self, "Fly to Target",
                f"Send {vehicle.name} to Target {target_id}?\n\n"
                f"Location: {target.lat:.5f}, {target.lon:.5f}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._mavlink.set_mode(self._selected_vehicle, "GUIDED")
                # Capture values in lambda to avoid closure issues
                QTimer.singleShot(500, lambda vid=self._selected_vehicle, la=target.lat, lo=target.lon, a=alt:
                    self._mavlink.goto(vid, la, lo, a))

        elif action == "assign_orb":
            # Select this target - user will click an orb or use dropdown to assign
            self._targets.selected = target_id
            self._update_target_queue()
            # Ensure target is in orb panel
            target = self._targets.get(target_id)
            if target:
                self.orb_panel.add_target(target_id, target.name or target_id)
            QMessageBox.information(
                self, "Assign Orb",
                "Target selected. Use the Stores panel to:\n\n"
                "1. Select a drone from the target dropdown, or\n"
                "2. Click an orb to assign it to this target."
            )

        elif action == "unassign_orb":
            # Clear all orbs assigned to this target
            for orb in self._orbs.get_all():
                if orb.target_id == target_id:
                    orb.clear_target()
            target.assigned_orb = None
            # Update orb panel drone assignment
            self.orb_panel.set_target_drone(target_id, "")
            self._update_orb_display()
            self._update_target_queue()

        elif action == "remove":
            reply = QMessageBox.question(
                self, "Remove Target",
                f"Remove Target {target_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._targets.remove(target_id)
                self.orb_panel.remove_target(target_id)
                self._update_target_queue()
                self._update_map()

    def _on_map_emitter_action(self, emitter_id: str, action: str):
        """Handle EW emitter context menu actions from map."""
        emitter = self._ew.emitters.get(emitter_id) if self._ew else None
        if not emitter:
            return

        if action == "prosecute":
            # Start prosecution workflow
            self._on_ew_prosecute(emitter_id)

        elif action == "investigate":
            # Quick investigate without full prosecution
            if emitter.df_result:
                lat, lon = emitter.df_result.lat, emitter.df_result.lon
                vehicle = self._vehicles.get(self._selected_vehicle)
                if vehicle:
                    alt = vehicle.state.alt if vehicle.state.alt > 10 else 100
                    reply = QMessageBox.question(
                        self, "Investigate Emitter",
                        f"Send {vehicle.name} to investigate emitter?\n\n"
                        f"Location: {lat:.5f}, {lon:.5f}",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        self._mavlink.set_mode(self._selected_vehicle, "GUIDED")
                        # Capture values in lambda to avoid closure issues
                        QTimer.singleShot(500, lambda vid=self._selected_vehicle, la=lat, lo=lon, a=alt:
                            self._mavlink.goto(vid, la, lo, a))

        elif action == "add_target":
            # Add emitter position to target queue
            if emitter.df_result and emitter.df_result.cep_m < 300:
                target = self._targets.add(
                    emitter.df_result.lat,
                    emitter.df_result.lon,
                    TargetSource.MANUAL
                )
                short_id = emitter_id[-8:] if len(emitter_id) > 8 else emitter_id
                self._targets.rename(target.id, f"EM-{short_id}")
                # Add to orb panel target list
                self.orb_panel.add_target(target.id, f"EM-{short_id}")
                self._update_target_queue()
                self._update_map()
                print(f"[EW] Added emitter {emitter_id} to target queue as Target {target.id}")
            else:
                QMessageBox.warning(
                    self, "Cannot Add Target",
                    "Emitter position not accurate enough (CEP > 300m).\n"
                    "Continue tracking to improve accuracy."
                )

    def _on_arm_requested(self, arm: bool):
        """Handle arm/disarm request."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        if arm and vehicle.type.value == "copter":
            self._mavlink.set_mode(self._selected_vehicle, "GUIDED")

        action = "Arm" if arm else "Disarm"
        if arm:
            msg = f"Arm {vehicle.name}?\n\nWARNING: Motors will spin!"
        else:
            msg = f"Disarm {vehicle.name}?"

        reply = QMessageBox.question(
            self, f"{action} Vehicle", msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No if arm else QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._mavlink.arm(self._selected_vehicle, arm)

    def _on_takeoff_requested(self, altitude: float):
        """Handle takeoff request."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle or not vehicle.state.armed:
            return

        reply = QMessageBox.question(
            self, "Confirm Takeoff",
            f"Takeoff {vehicle.name} to {altitude:.0f}m?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if vehicle.type.value == "copter":
                self._mavlink.set_mode(self._selected_vehicle, "GUIDED")
                # Capture values in lambda to avoid closure issues
                QTimer.singleShot(500, lambda vid=self._selected_vehicle, alt=altitude:
                    self._mavlink.takeoff(vid, alt))
            else:
                self._mavlink.set_mode(self._selected_vehicle, "TAKEOFF")

    def _on_land_requested(self):
        """Handle land request."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        reply = QMessageBox.question(
            self, "Confirm Land",
            f"Land {vehicle.name} now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._mavlink.set_mode(self._selected_vehicle, "LAND")

    def _on_altitude_change(self, vehicle_id: str, new_altitude: float):
        """Handle altitude change request from mode panel."""
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle or not vehicle.connected:
            return

        # Use dedicated altitude change - doesn't change flight mode
        self._mavlink.change_altitude(vehicle_id, new_altitude)
        print(f"[ALT] {vehicle.name} altitude change to {new_altitude:.0f}m")

    def _on_prosecution_complete(self, vehicle_id: str):
        """Handle prosecution complete request from mode panel."""
        if vehicle_id not in self._active_prosecutions:
            return

        emitter_id = self._active_prosecutions[vehicle_id]
        vehicle = self._vehicles.get(vehicle_id)
        vehicle_name = vehicle.name if vehicle else vehicle_id

        # Clear prosecution tracking
        del self._active_prosecutions[vehicle_id]
        if emitter_id in self._prosecution_arrived:
            self._prosecution_arrived.discard(emitter_id)

        # Update emitter state
        emitter = self._ew.emitters.get(emitter_id) if self._ew else None
        if emitter:
            emitter.set_prosecution_state(ProsecutionState.RESOLVED)
            emitter.assigned_vehicle = None

        # Mark vehicle for reintegration
        self._formation_members[vehicle_id] = "returning"
        self._pending_reintegrations.append(vehicle_id)

        # Update mode panel to hide complete button
        self.mode_panel.set_prosecution_state(False)

        # Update displays
        self._ew.priority_tracks_changed.emit()
        self._update_map()

        print(f"[PROSECUTE] {vehicle_name} prosecution of {emitter_id} marked COMPLETE")
        self.statusBar().showMessage(f"{vehicle_name} prosecution complete - queued for reintegration", 5000)

    def _on_target_selected(self, target_id: str):
        """Handle target selection."""
        self._targets.selected = target_id
        self._update_orb_display()

    def _on_target_removed(self, target_id: str):
        """Handle target removal."""
        self._targets.remove(target_id)
        self.orb_panel.remove_target(target_id)
        self._update_target_queue()
        self._update_map()

    def _on_target_renamed(self, target_id: str, new_name: str):
        """Handle target rename."""
        self._targets.rename(target_id, new_name)
        self._update_target_queue()

    def _on_target_description_changed(self, target_id: str, description: str):
        """Handle target description change."""
        self._targets.set_description(target_id, description)

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
                # Add to orb panel target list
                display_name = name if name else target.id
                self.orb_panel.add_target(target.id, display_name)
                self._update_target_queue()
                self._update_map()

    def _on_orb_clicked(self, orb_id: str):
        """Handle click on orb widget - assign currently selected target to this orb."""
        target = self._targets.selected
        if not target:
            QMessageBox.warning(self, "No Target", "Select a target first, then click an orb to assign.")
            return

        orb = self._orbs.get(orb_id)
        if not orb:
            return

        if orb.state.value not in ["loaded", "armed"]:
            QMessageBox.warning(self, "Orb Not Available",
                              f"ORB{orb_id} is not available for assignment (state: {orb.state.value}).")
            return

        # If orb already has a target, ask to reassign
        if orb.target_id:
            reply = QMessageBox.question(
                self, "Orb Has Target",
                f"ORB{orb_id} already has target {orb.target_id} assigned.\n\n"
                f"Reassign to {target.name or target.id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            # Clear old target assignment
            old_target = self._targets.get(orb.target_id)
            if old_target:
                old_target.assigned_orb = None
            orb.clear_target()

        # Perform the assignment
        orb.assign_target(target.id)
        self._targets.assign_to_orb(target.id, orb_id)

        from gcs.comms.lora_manager import TargetCoordinate
        target_coord = TargetCoordinate(
            target_id=target.id,
            lat=target.lat,
            lon=target.lon
        )
        self._lora.send_target_to_chick(orb.carrier, target_coord)

        print(f"[STORES] ORB{orb_id} assigned to target {target.id}")
        self._update_orb_display()
        self._update_target_queue()

    def _on_target_drone_assigned(self, target_id: str, drone_id: str):
        """Handle target-drone pairing from orb panel dropdown."""
        target = self._targets.get(target_id)
        if not target:
            return

        if not drone_id:
            # Unassigned - clear any orb assignments for this target
            for orb in self._orbs.get_all():
                if orb.target_id == target_id:
                    orb.clear_target()
            target.assigned_orb = None
            print(f"[STORES] Target {target_id} unassigned from drone")
            self._update_orb_display()
            self._update_target_queue()
            return

        # Auto-assign orbs from this drone based on profile
        self._auto_assign_orbs_for_target(target_id, drone_id)

    def _auto_assign_orbs_for_target(self, target_id: str, drone_id: str):
        """Auto-assign orbs from a specific drone to a target based on current profile."""
        target = self._targets.get(target_id)
        if not target:
            return

        # Get orbs to assign based on profile
        orb_ids_to_assign = self.orb_panel.get_orbs_for_carrier(drone_id)

        if not orb_ids_to_assign:
            QMessageBox.warning(self, "No Orbs Available",
                              f"No available orbs on {drone_id}.")
            return

        # Clear any existing assignments to this target first
        for orb in self._orbs.get_all():
            if orb.target_id == target_id:
                orb.clear_target()

        # Assign each orb
        from gcs.comms.lora_manager import TargetCoordinate
        target_coord = TargetCoordinate(
            target_id=target_id,
            lat=target.lat,
            lon=target.lon
        )

        assigned_orbs = []
        for orb_id in orb_ids_to_assign:
            orb = self._orbs.get(orb_id)
            if orb and orb.state.value in ["loaded", "armed"]:
                # Clear orb's previous target if any
                if orb.target_id and orb.target_id != target_id:
                    old_tgt = self._targets.get(orb.target_id)
                    if old_tgt:
                        old_tgt.assigned_orb = None

                orb.assign_target(target_id)
                assigned_orbs.append(orb_id)
                self._lora.send_target_to_chick(orb.carrier, target_coord)

        if assigned_orbs:
            # Track first assigned orb in target
            target.assigned_orb = assigned_orbs[0]
            orb_list = ", ".join([f"ORB{o}" for o in assigned_orbs])
            print(f"[STORES] {orb_list} assigned to target {target_id} on {drone_id}")

        self._update_orb_display()
        self._update_target_queue()

    def _on_arm_orbs(self, orb_ids: list):
        """Arm orbs for employment."""
        for orb_id in orb_ids:
            orb = self._orbs.get(orb_id)
            if orb and orb.arm():
                self._lora.send_arm_command(orb.carrier, orb.slot)
                print(f"[STORES] ORB{orb_id} ARMED")

        self.orb_panel.set_armed(True)
        self._update_orb_display()

    def _on_disarm_orbs(self, orb_ids: list):
        """Disarm orbs."""
        for orb_id in orb_ids:
            orb = self._orbs.get(orb_id)
            if orb and orb.disarm():
                self._lora.send_disarm_command(orb.carrier, orb.slot)
                print(f"[STORES] ORB{orb_id} DISARMED")

        self.orb_panel.set_armed(False)
        self._update_orb_display()

    def _on_release_orbs(self, orb_ids: list):
        """Release orbs based on employment profile."""
        for orb_id in orb_ids:
            orb = self._orbs.get(orb_id)
            if not orb:
                continue

            # Get carrier vehicle altitude for time-of-fall calculation
            carrier = self._vehicles.get(orb.carrier)
            release_alt = carrier.state.alt if carrier else 100  # Default 100m if unknown

            # Get target altitude (default to ground level)
            target_alt = 0
            if orb.target_id:
                target = self._targets.get(orb.target_id)
                if target and target.alt:
                    target_alt = target.alt

            if orb.release(release_alt=release_alt, target_alt=target_alt):
                self._lora.send_release_command(orb.carrier, orb.slot)
                print(f"[STORES] ORB{orb_id} RELEASED")

                # Start impact timer update
                self._start_orb_impact_timer(orb.id)

        self.orb_panel.set_armed(False)
        self._update_orb_display()

    def _start_orb_impact_timer(self, orb_id: str):
        """Start a timer to update orb impact countdown."""
        def update_impact():
            orb = self._orbs.get(orb_id)
            if orb and orb.state.value == "released":
                time_to_impact = orb.get_time_to_impact()
                self.orb_panel.update_impact_time(orb_id, time_to_impact)

                if time_to_impact is not None and time_to_impact > 0:
                    # Continue updating
                    QTimer.singleShot(100, update_impact)
                elif time_to_impact is not None and time_to_impact <= 0:
                    # Impact occurred - mark expended after short delay
                    # Capture orb_id in lambda to avoid closure issues
                    QTimer.singleShot(2000, lambda oid=orb_id: self._on_orb_impact(oid))
            else:
                self.orb_panel.update_impact_time(orb_id, None)

        # Start the update loop
        update_impact()

    def _on_orb_impact(self, orb_id: str):
        """Handle orb impact (end of flight)."""
        orb = self._orbs.get(orb_id)
        if orb:
            orb.state = OrbState.EXPENDED
            self.orb_panel.update_impact_time(orb_id, None)
            self._update_orb_display()
            print(f"[ORB] ORB{orb_id} impact - mission complete")

    def _on_reform_swarm(self):
        """Reform swarm to last known good configuration."""
        # Check for active prosecutions
        if self._active_prosecutions:
            active_names = []
            for vid in self._active_prosecutions.keys():
                v = self._vehicles.get(vid)
                active_names.append(v.name if v else vid)

            reply = QMessageBox.question(
                self, "Active Prosecutions",
                f"The following vehicles are on task:\n{', '.join(active_names)}\n\n"
                "Reform available vehicles only? (Busy vehicles will rejoin after completing their task)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return

        # Get all launched chicks and bird (skip those on active tasks)
        vehicles_to_reform = []
        busy_vehicles = []
        for vid, vehicle in self._vehicles.items():
            if vehicle.connected:
                # Skip attached chicks
                if vehicle.chick_state and vehicle.is_attached:
                    continue
                # Skip vehicles on active prosecution
                if vid in self._active_prosecutions:
                    busy_vehicles.append(vehicle.name)
                    continue
                vehicles_to_reform.append(vid)

        if not vehicles_to_reform:
            QMessageBox.information(
                self, "No Vehicles",
                "No vehicles available to reform."
            )
            return

        # Check for stored formation or calculate default
        if self._last_swarm_formation:
            formation = self._last_swarm_formation
            msg = "Reform available vehicles to last saved configuration?"
        else:
            # Calculate default formation around Bird
            formation = self._calculate_default_formation()
            msg = "Reform available vehicles to default formation?"

        # Add note about busy vehicles
        if busy_vehicles:
            msg += f"\n\n(Busy: {', '.join(busy_vehicles)} - will rejoin after task)"

        if not formation:
            QMessageBox.warning(
                self, "No Formation",
                "Cannot calculate formation - no valid vehicle positions."
            )
            return

        # Build confirmation message
        pos_lines = []
        for vid, (lat, lon, alt) in formation.items():
            vehicle = self._vehicles.get(vid)
            name = vehicle.name if vehicle else vid
            pos_lines.append(f"  {name}: {lat:.5f}, {lon:.5f} @ {alt:.0f}m")

        reply = QMessageBox.question(
            self, "Reform Swarm",
            f"{msg}\n\n" + "\n".join(pos_lines),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Command each available vehicle to its formation position
            reformed_count = 0
            for vid, (lat, lon, alt) in formation.items():
                # Skip vehicles not in the reform list (busy)
                if vid not in vehicles_to_reform:
                    continue

                vehicle = self._vehicles.get(vid)
                if vehicle and vehicle.connected:
                    self._mavlink.set_mode(vid, "AUTO")
                    # Use guided goto for immediate positioning
                    QTimer.singleShot(500, lambda v=vid, la=lat, lo=lon, a=alt:
                                     self._mavlink.goto(v, la, lo, a))
                    # Mark as in formation
                    self._formation_members[vid] = "in_formation"
                    reformed_count += 1
                    print(f"[SWARM] Commanding {vid} to reform position ({lat:.5f}, {lon:.5f})")

            print(f"[SWARM] Reform swarm initiated - {reformed_count} vehicles")

    def _calculate_default_formation(self) -> dict:
        """Calculate default swarm formation positions around Bird."""
        # Get Bird position as reference
        bird = self._vehicles.get("bird1")
        if not bird or bird.state.lat == 0:
            return {}

        bird_lat = bird.state.lat
        bird_lon = bird.state.lon
        bird_alt = bird.state.alt if bird.state.alt > 50 else 100

        # Formation: Bird in front, Chicks behind in V-formation
        # Offset in degrees (approximately 200m spacing)
        offset_lat = 0.002  # ~220m
        offset_lon = 0.002  # ~150m at 52° latitude

        formation = {
            "bird1": (bird_lat, bird_lon, bird_alt),
            "chick1.1": (bird_lat - offset_lat, bird_lon - offset_lon, bird_alt - 20),
            "chick1.2": (bird_lat - offset_lat, bird_lon + offset_lon, bird_alt - 20),
        }

        return formation

    def _save_current_formation(self):
        """Save current vehicle positions as the last good formation."""
        self._last_swarm_formation = {}
        for vid, vehicle in self._vehicles.items():
            if vehicle.connected and vehicle.state.lat != 0:
                # Skip attached chicks
                if vehicle.chick_state and vehicle.is_attached:
                    continue
                self._last_swarm_formation[vid] = (
                    vehicle.state.lat,
                    vehicle.state.lon,
                    vehicle.state.alt
                )
        if self._last_swarm_formation:
            print(f"[SWARM] Formation saved: {list(self._last_swarm_formation.keys())}")

    def _on_launch_chick(self):
        """Launch selected Chick."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle or not vehicle.can_launch:
            return

        carrier_name = self._vehicles[vehicle.carrier].name if vehicle.carrier else "carrier"
        reply = QMessageBox.question(
            self, "Confirm Launch",
            f"Launch {vehicle.name} from {carrier_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            carrier = self._vehicles.get(vehicle.carrier) if vehicle.carrier else None
            if carrier:
                self._mavlink.set_vehicle_position(
                    vehicle.id,
                    carrier.state.lat,
                    carrier.state.lon,
                    carrier.state.alt,
                    carrier.state.heading
                )

            if vehicle.launch():
                self._lora.send_launch_chick_command(vehicle.slot)
                QTimer.singleShot(1000, lambda v=vehicle: self._complete_chick_launch(v.id))

    def _complete_chick_launch(self, vehicle_id: str):
        """Complete chick launch sequence."""
        vehicle = self._vehicles.get(vehicle_id)
        if vehicle and vehicle.chick_state == ChickState.LAUNCHING:
            vehicle.set_launched()
            self._mavlink.mark_chick_released(vehicle_id)
            self._mavlink.set_mode(vehicle_id, "AUTO")
            self.vehicle_panel.update_vehicle(
                vehicle_id,
                "AUTO",
                vehicle.state.alt,
                vehicle.state.battery_pct,
                True,
                chick_state="launched"
            )
            self._update_mode_panel_for_chick()

    def _on_auto_chick_launch(self, carrier_id: str, chick_id: str):
        """Handle automatic chick launch from mission waypoint."""
        vehicle = self._vehicles.get(chick_id)
        if not vehicle or not vehicle.is_attached:
            return

        carrier = self._vehicles.get(carrier_id)
        if carrier:
            self._mavlink.set_vehicle_position(
                chick_id,
                carrier.state.lat,
                carrier.state.lon,
                carrier.state.alt,
                carrier.state.heading
            )

        if vehicle.launch():
            self._lora.send_launch_chick_command(vehicle.slot)
            QTimer.singleShot(500, lambda v=vehicle: self._complete_chick_launch(v.id))

    def _on_waypoint_reached(self, vehicle_id: str, wp_index: int, waypoint: dict):
        """Handle waypoint reached event."""
        wp_type = waypoint.get("type", "WAYPOINT")
        print(f"[MISSION] {vehicle_id} reached WP{wp_index + 1}: {wp_type}")

    # ==================== Mission Handlers ====================

    def _on_mission_upload(self, vehicle_id: str, mission):
        """Handle mission upload request."""
        import copy
        waypoints = mission.to_mavlink_format()
        success = self._mavlink.upload_mission(vehicle_id, waypoints)

        if success:
            self._vehicle_missions[vehicle_id] = copy.deepcopy(mission)
            QMessageBox.information(
                self, "Mission Uploaded",
                f"Successfully uploaded {len(waypoints)} waypoints to {vehicle_id.upper()}."
            )

    def _on_mission_download(self, vehicle_id: str):
        """Handle mission download request."""
        mission = self._mavlink.download_mission(vehicle_id)
        if mission:
            self._vehicle_missions[vehicle_id] = mission
            self.mission_panel.load_mission(mission)

    def _on_view_vehicle_mission(self, vehicle_id: str):
        """Show a vehicle's uploaded mission on the map."""
        if vehicle_id in self._vehicle_missions:
            mission = self._vehicle_missions[vehicle_id]
            self.map_widget.set_mission_waypoints(mission.to_map_format())
            self.map_widget.set_mission_vehicle(vehicle_id)

    def _on_mission_map_mode(self):
        """Handle mission panel requesting map click mode."""
        self.map_widget.set_mission_click_mode(True)

    def _on_show_mission(self, mission):
        """Show mission waypoints on map."""
        self.map_widget.set_mission_waypoints(mission.to_map_format())

    def _on_map_click_for_mission(self, lat: float, lon: float):
        """Handle map click when in mission add mode."""
        if hasattr(self, '_current_tab') and self._current_tab == "MISSION":
            if self.mission_panel.is_adding_from_map:
                self.mission_panel.add_waypoint_at(lat, lon)

    def _on_waypoint_edit_from_map(self, wp_id: int):
        """Handle waypoint edit request from map."""
        if hasattr(self, '_current_tab') and self._current_tab == "MISSION":
            self.mission_panel.edit_waypoint_at(wp_id)

    def _capture_coordinate(self):
        """Capture coordinate from selected vehicle's current position."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if vehicle and vehicle.connected:
            target = self._targets.add(
                vehicle.state.lat,
                vehicle.state.lon,
                TargetSource.VIDEO
            )
            # Add to orb panel target list
            self.orb_panel.add_target(target.id, target.name or target.id)
            self._update_target_queue()
            self._update_map()

    def _cycle_mode(self):
        """Cycle through flight modes."""
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

    def _center_map_on_selected(self):
        """Center map on the selected vehicle."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if vehicle and vehicle.state.lat != 0:
            self.map_widget.center_on(vehicle.state.lat, vehicle.state.lon)

    def _quick_fly_selected(self):
        """Quick fly the selected vehicle."""
        vehicle = self._vehicles.get(self._selected_vehicle)
        if not vehicle:
            return

        reply = QMessageBox.question(
            self, "Quick Fly",
            f"Quick fly {vehicle.name}?\n\n"
            "This will set GUIDED mode, force ARM, and takeoff to 50m.\n"
            "Use for SITL testing only!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._mavlink.quick_fly(self._selected_vehicle, 50)

    def _on_preflight(self):
        """Show pre-flight check dialog."""
        from .config import SWARM_CONFIG

        mesh_status = self._lora.get_all_nodes()
        lines = [
            "Pre-Flight Check Results:",
            "=" * 40,
            "",
            "MESH (T-Beam LoRa):"
        ]

        all_vehicle_ids = [b["id"] for b in SWARM_CONFIG["birds"]] + [c["id"] for c in SWARM_CONFIG["chicks"]]
        for vid in all_vehicle_ids:
            status = mesh_status.get(vid)
            if status and status.is_connected:
                lines.append(f"  ✓ {vid.upper()}: {status.rssi} dBm")
            else:
                lines.append(f"  ✗ {vid.upper()}: NOT CONNECTED")

        lines.extend([
            "",
            "EW SYSTEM:",
            f"  Emitters tracked: {self._ew.emitters.count()}",
            f"  Threat level: {self._ew.ep_status.threat_level.value}",
            f"  Link health: {self._ew.ep_status.link_health_pct:.0f}%",
        ])

        QMessageBox.information(self, "Pre-Flight Check", "\n".join(lines))

    def _on_connect_clicked(self):
        """Show connection dialog."""
        items = ["Simulation Mode", "SITL (ArduPilot)"]
        item, ok = QInputDialog.getItem(
            self, "Connect", "Select connection type:", items, 0, False
        )

        if ok:
            if item == "Simulation Mode":
                self._start_simulation()
                self.conn_label.setText("SIM MODE")
                self.conn_label.setStyleSheet("color: #facc15; font-weight: bold;")
            elif item == "SITL (ArduPilot)":
                from .config import SITL_CONNECTIONS, SITL_USE_TCP
                self._mavlink.stop_simulation()

                if self._mavlink.connect_sitl(SITL_CONNECTIONS):
                    connected = len(self._mavlink._connections)
                    self.conn_label.setText(f"SITL ({connected})")
                    self.conn_label.setStyleSheet("color: #4ade80; font-weight: bold;")

    def _on_settings(self):
        """Show settings dialog."""
        QMessageBox.information(
            self, "Settings",
            "Sandbox Settings:\n\n"
            "• EW Panel: ENABLED\n"
            "• Simulation: Active\n"
            "• Config: sandbox/gcs_sandbox/config.py"
        )

    def _on_escape(self):
        """Handle escape key."""
        pass

    # ==================== Update Methods ====================

    def _update_map(self):
        """Update map display."""
        vehicles = {}
        for vid, vehicle in self._vehicles.items():
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
                is_attached
            )
        self.map_widget.set_vehicles(vehicles)

        targets = {}
        for target in self._targets.get_all():
            # Include EW flag for special symbology
            is_ew = target.is_ew_target if hasattr(target, 'is_ew_target') else False
            targets[target.id] = (target.lat, target.lon, target.assigned_orb, is_ew)
        self.map_widget.set_targets(targets)

    def _update_target_queue(self):
        """Update target queue display."""
        targets = [
            (t.id, t.lat, t.lon, t.source.value, t.assigned_orb, t.name, t.description)
            for t in self._targets.get_all()
        ]
        self.target_queue.update_targets(targets)

    def _update_orb_display(self):
        """Update orb panel display with current orb states."""
        for orb in self._orbs.get_all():
            has_target = orb.target_id is not None
            self.orb_panel.update_orb(orb.id, orb.state.value, has_target, orb.target_id, orb.carrier)

    def closeEvent(self, event):
        """Clean up on close."""
        self._mavlink.stop_simulation()
        self._lora.stop_simulation()
        self._video.stop_simulation()
        self._ew.stop_simulation()
        event.accept()
