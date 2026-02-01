# Flight Mode Panel for SwarmDrones GCS
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QPushButton, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ModePanel(QFrame):
    """Panel for flight mode selection."""

    mode_selected = pyqtSignal(str)  # mode name
    launch_requested = pyqtSignal()  # chick launch requested
    arm_requested = pyqtSignal(bool)  # True=arm, False=disarm
    takeoff_requested = pyqtSignal(float)  # altitude in meters
    land_requested = pyqtSignal()  # land at current position
    reform_swarm_requested = pyqtSignal()  # reform swarm to last configuration
    altitude_change_requested = pyqtSignal(str, float)  # vehicle_id, new_altitude
    prosecution_complete_requested = pyqtSignal(str)  # vehicle_id - mark prosecution as complete

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._buttons: dict[str, QPushButton] = {}
        self._current_mode = None
        self._vehicle_type = "copter"
        self._selected_vehicle = None
        self._chick_state = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header with selected vehicle
        header_layout = QHBoxLayout()
        self.header_label = QLabel("SELECTED: --")
        self.header_label.setObjectName("header")
        header_layout.addWidget(self.header_label)

        # Chick state label (shown when chick is selected)
        self.chick_state_label = QLabel("")
        self.chick_state_label.setObjectName("chick_state")
        self.chick_state_label.setStyleSheet("color: #facc15; font-weight: bold;")
        self.chick_state_label.hide()
        header_layout.addWidget(self.chick_state_label)

        header_layout.addStretch()

        # Launch button (shown when chick is attached)
        self.launch_btn = QPushButton("LAUNCH")
        self.launch_btn.setObjectName("launch_button")
        self.launch_btn.setStyleSheet("""
            QPushButton#launch_button {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 4px 16px;
                border-radius: 4px;
            }
            QPushButton#launch_button:hover {
                background-color: #ef4444;
            }
            QPushButton#launch_button:disabled {
                background-color: #4a4a6a;
                color: #808080;
            }
        """)
        self.launch_btn.clicked.connect(self._on_launch_clicked)
        self.launch_btn.hide()
        header_layout.addWidget(self.launch_btn)

        layout.addLayout(header_layout)

        # Mode buttons
        self.modes_layout = QHBoxLayout()
        self.modes_layout.setSpacing(4)

        # Placeholder buttons - will be updated based on vehicle type
        modes = ["LOIT", "RTL", "AUTO", "LAND", "GUIDE"]
        for mode in modes:
            btn = QPushButton(mode)
            btn.setObjectName("mode_button")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_mode_clicked(m))
            self._buttons[mode] = btn
            self.modes_layout.addWidget(btn)

        # Separator
        sep_label = QLabel("|")
        sep_label.setStyleSheet("color: #4a4a6a; font-weight: bold;")
        self.modes_layout.addWidget(sep_label)

        # Arm/Disarm button
        self.arm_btn = QPushButton("ARM")
        self.arm_btn.setObjectName("arm_button")
        self.arm_btn.setCheckable(True)
        self.arm_btn.setStyleSheet("""
            QPushButton#arm_button {
                background-color: #4a4a6a;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#arm_button:checked {
                background-color: #dc2626;
            }
            QPushButton#arm_button:hover {
                background-color: #5a5a8a;
            }
            QPushButton#arm_button:checked:hover {
                background-color: #ef4444;
            }
        """)
        self.arm_btn.clicked.connect(self._on_arm_clicked)
        self.modes_layout.addWidget(self.arm_btn)

        # Takeoff button
        self.takeoff_btn = QPushButton("TKOFF")
        self.takeoff_btn.setObjectName("takeoff_button")
        self.takeoff_btn.setStyleSheet("""
            QPushButton#takeoff_button {
                background-color: #059669;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#takeoff_button:hover {
                background-color: #10b981;
            }
            QPushButton#takeoff_button:disabled {
                background-color: #4a4a6a;
                color: #808080;
            }
        """)
        self.takeoff_btn.clicked.connect(self._on_takeoff_clicked)
        self.modes_layout.addWidget(self.takeoff_btn)

        # Land button (action, not mode)
        self.land_btn = QPushButton("LND")
        self.land_btn.setObjectName("land_button")
        self.land_btn.setStyleSheet("""
            QPushButton#land_button {
                background-color: #d97706;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#land_button:hover {
                background-color: #f59e0b;
            }
        """)
        self.land_btn.clicked.connect(self._on_land_clicked)
        self.modes_layout.addWidget(self.land_btn)

        # Reform swarm button
        self.reform_btn = QPushButton("REFORM")
        self.reform_btn.setObjectName("reform_button")
        self.reform_btn.setToolTip("Reform swarm to last configuration")
        self.reform_btn.setStyleSheet("""
            QPushButton#reform_button {
                background-color: #7c3aed;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#reform_button:hover {
                background-color: #8b5cf6;
            }
            QPushButton#reform_button:disabled {
                background-color: #4a4a6a;
                color: #808080;
            }
        """)
        self.reform_btn.clicked.connect(self._on_reform_clicked)
        self.modes_layout.addWidget(self.reform_btn)

        # Complete prosecution button (hidden by default)
        self.complete_btn = QPushButton("COMPLETE")
        self.complete_btn.setObjectName("complete_button")
        self.complete_btn.setToolTip("Mark prosecution task as complete")
        self.complete_btn.setStyleSheet("""
            QPushButton#complete_button {
                background-color: #059669;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#complete_button:hover {
                background-color: #10b981;
            }
        """)
        self.complete_btn.clicked.connect(self._on_complete_clicked)
        self.complete_btn.hide()
        self.modes_layout.addWidget(self.complete_btn)

        self.modes_layout.addStretch()
        layout.addLayout(self.modes_layout)

        # Altitude control row
        alt_layout = QHBoxLayout()
        alt_layout.setSpacing(4)

        alt_label = QLabel("ALT:")
        alt_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        alt_layout.addWidget(alt_label)

        # Current altitude display
        self.alt_display = QLabel("--m")
        self.alt_display.setStyleSheet("color: #4ade80; font-weight: bold; min-width: 50px;")
        alt_layout.addWidget(self.alt_display)

        # Quick altitude buttons
        alt_btn_style = """
            QPushButton {
                background-color: #374151;
                color: white;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
                min-width: 35px;
            }
            QPushButton:hover { background-color: #4b5563; }
            QPushButton:pressed { background-color: #1f2937; }
        """

        self.alt_down_50 = QPushButton("-50")
        self.alt_down_50.setStyleSheet(alt_btn_style)
        self.alt_down_50.clicked.connect(lambda: self._change_altitude(-50))
        alt_layout.addWidget(self.alt_down_50)

        self.alt_down_10 = QPushButton("-10")
        self.alt_down_10.setStyleSheet(alt_btn_style)
        self.alt_down_10.clicked.connect(lambda: self._change_altitude(-10))
        alt_layout.addWidget(self.alt_down_10)

        self.alt_up_10 = QPushButton("+10")
        self.alt_up_10.setStyleSheet(alt_btn_style)
        self.alt_up_10.clicked.connect(lambda: self._change_altitude(10))
        alt_layout.addWidget(self.alt_up_10)

        self.alt_up_50 = QPushButton("+50")
        self.alt_up_50.setStyleSheet(alt_btn_style)
        self.alt_up_50.clicked.connect(lambda: self._change_altitude(50))
        alt_layout.addWidget(self.alt_up_50)

        # Altitude input spinner
        self.alt_spinner = QSpinBox()
        self.alt_spinner.setRange(10, 500)
        self.alt_spinner.setValue(100)
        self.alt_spinner.setSuffix("m")
        self.alt_spinner.setFixedWidth(70)
        self.alt_spinner.setStyleSheet("""
            QSpinBox {
                background-color: #1f2937;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        alt_layout.addWidget(self.alt_spinner)

        # Go to altitude button
        self.alt_go_btn = QPushButton("GO")
        self.alt_go_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-weight: bold;
                padding: 2px 10px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #10b981; }
        """)
        self.alt_go_btn.clicked.connect(self._go_to_altitude)
        alt_layout.addWidget(self.alt_go_btn)

        alt_layout.addStretch()
        layout.addLayout(alt_layout)

        # Track state
        self._is_armed = False
        self._current_alt = 0

    def _on_mode_clicked(self, mode: str):
        """Handle mode button click."""
        self.mode_selected.emit(mode)

    def _on_launch_clicked(self):
        """Handle launch button click."""
        self.launch_requested.emit()

    def _on_arm_clicked(self):
        """Handle arm/disarm button click."""
        # Toggle armed state
        new_state = not self._is_armed
        self.arm_requested.emit(new_state)

    def _on_takeoff_clicked(self):
        """Handle takeoff button click."""
        # Default takeoff altitude
        self.takeoff_requested.emit(50.0)  # 50 meters

    def _on_land_clicked(self):
        """Handle land button click."""
        self.land_requested.emit()

    def _on_reform_clicked(self):
        """Handle reform swarm button click."""
        self.reform_swarm_requested.emit()

    def _on_complete_clicked(self):
        """Handle complete prosecution button click."""
        if self._selected_vehicle:
            self.prosecution_complete_requested.emit(self._selected_vehicle)

    def _change_altitude(self, delta: float):
        """Change altitude by delta meters."""
        if self._selected_vehicle:
            new_alt = max(10, self._current_alt + delta)
            self.altitude_change_requested.emit(self._selected_vehicle, new_alt)

    def _go_to_altitude(self):
        """Go to the altitude in the spinner."""
        if self._selected_vehicle:
            new_alt = self.alt_spinner.value()
            self.altitude_change_requested.emit(self._selected_vehicle, new_alt)

    def set_altitude(self, altitude: float):
        """Update the altitude display."""
        self._current_alt = altitude
        self.alt_display.setText(f"{altitude:.0f}m")
        # Update spinner to nearby value
        self.alt_spinner.setValue(int(altitude))

    def set_armed(self, armed: bool):
        """Update armed state display."""
        self._is_armed = armed
        self.arm_btn.setChecked(armed)
        self.arm_btn.setText("DISARM" if armed else "ARM")

    def set_vehicle(self, vehicle_id: str, vehicle_name: str, vehicle_type: str):
        """Set the selected vehicle and update mode buttons."""
        self._selected_vehicle = vehicle_id
        self._vehicle_type = vehicle_type

        # Update header
        icon = "✈" if vehicle_type == "plane" else "⬡"
        self.header_label.setText(f"SELECTED: {icon} {vehicle_name}")

        # Clear existing mode buttons
        for btn in self._buttons.values():
            self.modes_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()

        # Add appropriate mode buttons
        if vehicle_type == "plane":
            modes = ["LOIT", "RTL", "AUTO", "LAND", "GUIDE"]
        else:
            modes = ["LOIT", "RTL", "AUTO", "LAND", "GUIDE"]

        # Insert mode buttons at the beginning (before separator and action buttons)
        for i, mode in enumerate(modes):
            btn = QPushButton(mode)
            btn.setObjectName("mode_button")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_mode_clicked(m))
            self._buttons[mode] = btn
            self.modes_layout.insertWidget(i, btn)

    def set_current_mode(self, mode: str):
        """Update the current mode display."""
        self._current_mode = mode

        # Map full mode names to short names
        mode_map = {
            "LOITER": "LOIT",
            "GUIDED": "GUIDE",
        }
        short_mode = mode_map.get(mode, mode)

        # Update button states
        for btn_mode, btn in self._buttons.items():
            btn.setChecked(btn_mode == short_mode)

    def set_chick_state(self, state: str, can_launch: bool):
        """
        Update chick-specific UI elements.

        Args:
            state: ChickState value ("attached", "launching", "launched") or None for Bird
            can_launch: Whether the launch button should be enabled
        """
        self._chick_state = state

        if state is None:
            # Not a chick (Bird selected)
            self.chick_state_label.hide()
            self.launch_btn.hide()
            # Enable all mode buttons
            for btn in self._buttons.values():
                btn.setEnabled(True)
        else:
            # Chick selected - show state
            state_display = {
                "attached": "ATTACHED",
                "launching": "LAUNCHING...",
                "launched": "LAUNCHED",
                "recovered": "RECOVERED"
            }
            self.chick_state_label.setText(f"[{state_display.get(state, state.upper())}]")

            # Color coding for state
            state_colors = {
                "attached": "#facc15",   # Yellow
                "launching": "#f97316",  # Orange
                "launched": "#4ade80",   # Green
                "recovered": "#60a5fa"   # Blue
            }
            color = state_colors.get(state, "#ffffff")
            self.chick_state_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.chick_state_label.show()

            # Show/enable launch button based on state
            if state == "attached":
                self.launch_btn.show()
                self.launch_btn.setEnabled(can_launch)
                # Disable mode buttons when attached (can't control)
                for btn in self._buttons.values():
                    btn.setEnabled(False)
            else:
                self.launch_btn.hide()
                # Enable mode buttons when launched
                for btn in self._buttons.values():
                    btn.setEnabled(state == "launched")

    def set_prosecution_state(self, is_prosecuting: bool, target_name: str = None):
        """
        Update prosecution state display.

        Args:
            is_prosecuting: True if vehicle is on a prosecution task
            target_name: Name of target being prosecuted (for tooltip)
        """
        if is_prosecuting:
            self.complete_btn.show()
            if target_name:
                self.complete_btn.setToolTip(f"Complete prosecution of {target_name}")
        else:
            self.complete_btn.hide()
