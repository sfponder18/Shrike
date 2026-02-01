# Orb Management Panel for SwarmDrones GCS
# Profile-based employment system with target-drone pairing
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QPushButton, QGridLayout, QMessageBox,
                              QButtonGroup, QRadioButton, QComboBox, QScrollArea,
                              QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from enum import Enum


class EmploymentProfile(Enum):
    """Orb employment profiles."""
    SINGLE = "single"   # Drop 1 orb
    DUAL = "dual"       # Drop 2 orbs
    SALVO = "salvo"     # Drop all available


class OrbStatusWidget(QFrame):
    """Compact orb status indicator with click support."""

    clicked = pyqtSignal(str)  # orb_id

    def __init__(self, orb_id: str, parent=None):
        super().__init__(parent)
        self.orb_id = orb_id
        self._state = "loaded"
        self._has_target = False
        self._target_id = None
        self._selected_for_employment = False
        self._range_info = None  # {in_range, time_to_range, current_dist}

        self.setFixedSize(70, 70)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.id_label = QLabel(f"ORB{self.orb_id}")
        self.id_label.setAlignment(Qt.AlignCenter)
        self.id_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(self.id_label)

        self.status_label = QLabel("●")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.status_label)

        # Target indicator
        self.target_label = QLabel("")
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setStyleSheet("font-size: 8px; color: #9ca3af;")
        layout.addWidget(self.target_label)

        self._update_style()

    def mousePressEvent(self, event):
        """Handle click to select this orb."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.orb_id)
        super().mousePressEvent(event)

    def set_state(self, state: str, has_target: bool = False,
                  target_id: str = None, selected: bool = False):
        """Update orb state display."""
        self._state = state
        self._has_target = has_target
        self._target_id = target_id
        self._selected_for_employment = selected
        self._update_style()

    def set_range_info(self, in_range: bool = None, time_to_range: float = None,
                       current_dist: float = None):
        """Set range information for this orb."""
        if in_range is None:
            self._range_info = None
        else:
            self._range_info = {
                "in_range": in_range,
                "time_to_range": time_to_range,
                "current_dist": current_dist
            }

    def get_range_text(self) -> str:
        """Get range status text."""
        if not self._range_info or not self._has_target:
            return ""

        info = self._range_info
        if info["in_range"]:
            return f"IN RANGE"
        elif info["time_to_range"] and info["time_to_range"] > 0:
            return f"ETA: {info['time_to_range']:.0f}s"
        elif info["current_dist"]:
            return f"{info['current_dist']:.0f}m"
        return "OUT OF RANGE"

    def _update_style(self):
        # Update target label
        if self._target_id:
            self.target_label.setText(f"TGT:{self._target_id[:6]}")
        else:
            self.target_label.setText("NO TGT")

        if self._state == "empty":
            self.status_label.setText("○")
            self.status_label.setStyleSheet("color: #404060; font-size: 18px;")
            self.setStyleSheet("background-color: #1a1a2e; border-radius: 4px;")
        elif self._state == "released":
            self.status_label.setText("◌")
            self.status_label.setStyleSheet("color: #f97316; font-size: 18px;")
            self.setStyleSheet("background-color: #1a1a2e; border-radius: 4px;")
        elif self._state == "armed":
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #ef4444; font-size: 18px;")
            border = "2px solid #ef4444" if self._selected_for_employment else "none"
            self.setStyleSheet(f"background-color: #4a1a1a; border-radius: 4px; border: {border};")
        elif self._has_target:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #4ade80; font-size: 18px;")
            border = "2px solid #4ade80" if self._selected_for_employment else "none"
            self.setStyleSheet(f"background-color: #1a3a1a; border-radius: 4px; border: {border};")
        else:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #60a5fa; font-size: 18px;")
            border = "2px solid #60a5fa" if self._selected_for_employment else "none"
            self.setStyleSheet(f"background-color: #1a1a3a; border-radius: 4px; border: {border};")


class TargetRowWidget(QFrame):
    """Widget for a single target in the target list."""

    drone_assigned = pyqtSignal(str, str)  # target_id, drone_id (or "" for unassigned)

    def __init__(self, target_id: str, target_name: str, parent=None):
        super().__init__(parent)
        self.target_id = target_id
        self._setup_ui(target_name)

    def _setup_ui(self, target_name: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Target name
        self.name_label = QLabel(target_name)
        self.name_label.setStyleSheet("color: #f87171; font-weight: bold; min-width: 80px;")
        layout.addWidget(self.name_label)

        # Weapon type (fixed to ORB for now)
        self.weapon_label = QLabel("ORB")
        self.weapon_label.setStyleSheet("color: #9ca3af; font-size: 10px;")
        layout.addWidget(self.weapon_label)

        # Drone assignment dropdown
        self.drone_combo = QComboBox()
        self.drone_combo.addItem("-- Unassigned --", "")
        self.drone_combo.addItem("Chick 1.1", "chick1.1")
        self.drone_combo.addItem("Chick 1.2", "chick1.2")
        self.drone_combo.setFixedWidth(110)
        self.drone_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: white;
                border: 1px solid #374151;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView {
                background-color: #1f2937;
                color: white;
                selection-background-color: #374151;
            }
        """)
        self.drone_combo.currentIndexChanged.connect(self._on_drone_changed)
        layout.addWidget(self.drone_combo)

        layout.addStretch()

        self.setStyleSheet("background-color: #1a1a2e; border-radius: 4px; margin: 1px;")

    def _on_drone_changed(self, index):
        drone_id = self.drone_combo.currentData()
        self.drone_assigned.emit(self.target_id, drone_id)

    def set_assigned_drone(self, drone_id: str):
        """Set the assigned drone in the dropdown."""
        index = self.drone_combo.findData(drone_id)
        if index >= 0:
            self.drone_combo.blockSignals(True)
            self.drone_combo.setCurrentIndex(index)
            self.drone_combo.blockSignals(False)


class DroneColumnWidget(QFrame):
    """Column widget showing a drone and its orbs."""

    orb_clicked = pyqtSignal(str)  # orb_id

    def __init__(self, drone_id: str, drone_name: str, orb_ids: list, parent=None):
        super().__init__(parent)
        self.drone_id = drone_id
        self.drone_name = drone_name
        self._orb_widgets: dict[str, OrbStatusWidget] = {}
        self._setup_ui(orb_ids)

    def _setup_ui(self, orb_ids: list):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)

        # Drone header
        header = QLabel(self.drone_name)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #60a5fa; font-weight: bold; font-size: 11px;")
        layout.addWidget(header)

        # Orbs stacked vertically
        for orb_id in orb_ids:
            widget = OrbStatusWidget(orb_id)
            widget.clicked.connect(self.orb_clicked.emit)
            self._orb_widgets[orb_id] = widget
            layout.addWidget(widget, alignment=Qt.AlignCenter)

        # Range countdown label (under orbs)
        self.range_label = QLabel("")
        self.range_label.setAlignment(Qt.AlignCenter)
        self.range_label.setStyleSheet("color: #fbbf24; font-size: 10px;")
        self.range_label.setWordWrap(True)
        layout.addWidget(self.range_label)

        layout.addStretch()

        self.setStyleSheet("background-color: #0f0f1a; border-radius: 6px;")
        self.setMinimumWidth(90)

    def get_orb_widget(self, orb_id: str) -> OrbStatusWidget:
        return self._orb_widgets.get(orb_id)

    def update_range_display(self):
        """Update range display from orb widgets."""
        range_texts = []
        for orb_id, widget in self._orb_widgets.items():
            text = widget.get_range_text()
            if text:
                range_texts.append(f"O{orb_id}: {text}")

        if range_texts:
            self.range_label.setText("\n".join(range_texts))
        else:
            self.range_label.setText("")


class OrbPanel(QFrame):
    """Panel for profile-based orb management with target-drone pairing."""

    # Signals
    profile_selected = pyqtSignal(str)  # profile name
    orb_clicked = pyqtSignal(str)  # orb_id clicked for assignment
    target_drone_assigned = pyqtSignal(str, str)  # target_id, drone_id
    arm_requested = pyqtSignal(list)  # list of orb_ids to arm
    disarm_requested = pyqtSignal(list)  # list of orb_ids to disarm
    release_requested = pyqtSignal(list)  # list of orb_ids to release

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._drone_columns: dict[str, DroneColumnWidget] = {}
        self._target_rows: dict[str, TargetRowWidget] = {}
        self._current_profile = EmploymentProfile.SINGLE
        self._employment_orbs = []  # Orbs selected for current employment
        self._orb_states = {}  # orb_id -> {state, has_target, target_id, carrier}
        self._is_armed = False
        self._release_timer = None
        self._release_countdown = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Header
        title = QLabel("STORES MANAGEMENT")
        title.setObjectName("header")
        layout.addWidget(title)

        # Main content: Drone columns on left (under vehicles), target list on right
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)

        # === Left side: Drone columns (aligned under vehicle cards) ===
        drones_frame = QFrame()
        drones_layout = QHBoxLayout(drones_frame)
        drones_layout.setContentsMargins(0, 0, 0, 0)
        drones_layout.setSpacing(4)

        # Chick 1.1 column (orbs 1, 2)
        chick1_col = DroneColumnWidget("chick1.1", "CHICK 1.1", ["1", "2"])
        chick1_col.orb_clicked.connect(self._on_orb_clicked)
        self._drone_columns["chick1.1"] = chick1_col
        drones_layout.addWidget(chick1_col)

        # Chick 1.2 column (orbs 3, 4)
        chick2_col = DroneColumnWidget("chick1.2", "CHICK 1.2", ["3", "4"])
        chick2_col.orb_clicked.connect(self._on_orb_clicked)
        self._drone_columns["chick1.2"] = chick2_col
        drones_layout.addWidget(chick2_col)

        content_layout.addWidget(drones_frame)

        # === Right side: Target list ===
        target_frame = QFrame()
        target_frame.setStyleSheet("background-color: #0f0f1a; border-radius: 6px;")
        target_layout = QVBoxLayout(target_frame)
        target_layout.setContentsMargins(4, 4, 4, 4)
        target_layout.setSpacing(4)

        target_header = QLabel("TARGETS")
        target_header.setStyleSheet("color: #f87171; font-weight: bold; font-size: 11px;")
        target_layout.addWidget(target_header)

        # Scrollable target list
        self.target_scroll = QScrollArea()
        self.target_scroll.setWidgetResizable(True)
        self.target_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.target_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.target_container = QWidget()
        self.target_list_layout = QVBoxLayout(self.target_container)
        self.target_list_layout.setContentsMargins(0, 0, 0, 0)
        self.target_list_layout.setSpacing(2)
        self.target_list_layout.addStretch()

        self.target_scroll.setWidget(self.target_container)
        target_layout.addWidget(self.target_scroll)

        # No targets label
        self.no_targets_label = QLabel("No active targets")
        self.no_targets_label.setStyleSheet("color: #4b5563; font-style: italic;")
        self.no_targets_label.setAlignment(Qt.AlignCenter)
        target_layout.addWidget(self.no_targets_label)

        content_layout.addWidget(target_frame, stretch=1)

        layout.addLayout(content_layout)

        # Employment profile selector
        profile_layout = QHBoxLayout()
        profile_label = QLabel("PROFILE:")
        profile_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        profile_layout.addWidget(profile_label)

        self._profile_group = QButtonGroup(self)
        profile_btn_style = """
            QRadioButton {
                color: white;
                font-weight: bold;
                padding: 4px 8px;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
            }
            QRadioButton::indicator:checked {
                background-color: #4ade80;
                border: 2px solid #22c55e;
                border-radius: 6px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #374151;
                border: 2px solid #4b5563;
                border-radius: 6px;
            }
        """

        self.single_btn = QRadioButton("SINGLE")
        self.single_btn.setStyleSheet(profile_btn_style)
        self.single_btn.setChecked(True)
        self.single_btn.toggled.connect(lambda c: self._on_profile_changed(EmploymentProfile.SINGLE) if c else None)
        self._profile_group.addButton(self.single_btn)
        profile_layout.addWidget(self.single_btn)

        self.dual_btn = QRadioButton("DUAL")
        self.dual_btn.setStyleSheet(profile_btn_style)
        self.dual_btn.toggled.connect(lambda c: self._on_profile_changed(EmploymentProfile.DUAL) if c else None)
        self._profile_group.addButton(self.dual_btn)
        profile_layout.addWidget(self.dual_btn)

        self.salvo_btn = QRadioButton("SALVO")
        self.salvo_btn.setStyleSheet(profile_btn_style)
        self.salvo_btn.toggled.connect(lambda c: self._on_profile_changed(EmploymentProfile.SALVO) if c else None)
        self._profile_group.addButton(self.salvo_btn)
        profile_layout.addWidget(self.salvo_btn)

        profile_layout.addStretch()
        layout.addLayout(profile_layout)

        # Employment info
        self.employment_label = QLabel("SELECT TARGET TO CUE")
        self.employment_label.setStyleSheet("color: #9ca3af;")
        layout.addWidget(self.employment_label)

        # Impact time (shown when orbs released)
        self.impact_label = QLabel("")
        self.impact_label.setStyleSheet("color: #f87171; font-weight: bold;")
        self.impact_label.hide()
        layout.addWidget(self.impact_label)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.arm_btn = QPushButton("ARM")
        self.arm_btn.setObjectName("arm_button")
        self.arm_btn.clicked.connect(self._on_arm_clicked)
        self.arm_btn.setEnabled(False)
        self.arm_btn.setStyleSheet("""
            QPushButton#arm_button {
                background-color: #374151;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#arm_button:hover { background-color: #4b5563; }
            QPushButton#arm_button:disabled { background-color: #1f2937; color: #4b5563; }
        """)
        btn_layout.addWidget(self.arm_btn)

        self.release_btn = QPushButton("RELEASE")
        self.release_btn.setObjectName("release_button")
        self.release_btn.pressed.connect(self._on_release_pressed)
        self.release_btn.released.connect(self._on_release_released)
        self.release_btn.setEnabled(False)
        self.release_btn.setStyleSheet("""
            QPushButton#release_button {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton#release_button:hover { background-color: #ef4444; }
            QPushButton#release_button:disabled { background-color: #1f2937; color: #4b5563; }
        """)
        btn_layout.addWidget(self.release_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _on_orb_clicked(self, orb_id: str):
        """Handle orb click for assignment."""
        self.orb_clicked.emit(orb_id)

    def _on_profile_changed(self, profile: EmploymentProfile):
        """Handle profile selection change."""
        self._current_profile = profile
        self.profile_selected.emit(profile.value)
        self._update_employment_selection()

    def _on_arm_clicked(self):
        """Handle arm/disarm toggle."""
        if self._is_armed:
            self.disarm_requested.emit(self._employment_orbs.copy())
        else:
            self.arm_requested.emit(self._employment_orbs.copy())

    def _on_release_pressed(self):
        """Start release hold timer (2 second hold required)."""
        if not self._employment_orbs:
            return
        self._release_countdown = 20  # 2 seconds at 100ms intervals
        self._release_timer = QTimer()
        self._release_timer.timeout.connect(self._release_tick)
        self._release_timer.start(100)
        self.release_btn.setText("HOLD 2s")

    def _release_tick(self):
        """Tick for release countdown."""
        self._release_countdown -= 1
        remaining = self._release_countdown / 10
        self.release_btn.setText(f"HOLD {remaining:.1f}s")

        if self._release_countdown <= 0:
            self._release_timer.stop()
            self._confirm_release()

    def _on_release_released(self):
        """Cancel release if button released early."""
        if self._release_timer:
            self._release_timer.stop()
            self._release_timer = None
        self.release_btn.setText("RELEASE")

    def _confirm_release(self):
        """Execute release."""
        self._release_timer = None
        self.release_btn.setText("RELEASE")

        orb_list = ", ".join([f"ORB{o}" for o in self._employment_orbs])
        reply = QMessageBox.warning(
            self, "Confirm Release",
            f"Release {orb_list}?\n\n"
            f"Profile: {self._current_profile.value.upper()}\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.release_requested.emit(self._employment_orbs.copy())

    def _update_employment_selection(self):
        """Update which orbs are selected for employment based on profile and targets."""
        # Get orbs with targets, grouped by carrier
        orbs_by_carrier = {}
        for orb_id, state in self._orb_states.items():
            if state.get("state") in ["loaded", "armed"] and state.get("has_target"):
                carrier = state.get("carrier", "")
                if carrier not in orbs_by_carrier:
                    orbs_by_carrier[carrier] = []
                orbs_by_carrier[carrier].append(orb_id)

        # For each carrier, select orbs based on profile
        self._employment_orbs = []
        for carrier, orb_ids in orbs_by_carrier.items():
            orb_ids.sort()
            if self._current_profile == EmploymentProfile.SINGLE:
                self._employment_orbs.extend(orb_ids[:1])
            elif self._current_profile == EmploymentProfile.DUAL:
                self._employment_orbs.extend(orb_ids[:2])
            else:  # SALVO
                self._employment_orbs.extend(orb_ids)

        # Update display
        self._update_orb_displays()
        self._update_employment_info()
        self._update_buttons()

    def _update_orb_displays(self):
        """Update all orb status widgets."""
        for drone_id, column in self._drone_columns.items():
            for orb_id in ["1", "2"] if drone_id == "chick1.1" else ["3", "4"]:
                widget = column.get_orb_widget(orb_id)
                if widget:
                    state = self._orb_states.get(orb_id, {})
                    widget.set_state(
                        state.get("state", "loaded"),
                        state.get("has_target", False),
                        state.get("target_id"),
                        orb_id in self._employment_orbs
                    )
            column.update_range_display()

    def _update_employment_info(self):
        """Update employment info label."""
        if not self._employment_orbs:
            self.employment_label.setText("SELECT TARGET TO CUE")
            self.employment_label.setStyleSheet("color: #9ca3af;")
        else:
            orb_list = ", ".join([f"ORB{o}" for o in self._employment_orbs])
            profile = self._current_profile.value.upper()
            if self._is_armed:
                self.employment_label.setText(f"ARMED: {orb_list} [{profile}]")
                self.employment_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            else:
                self.employment_label.setText(f"CUED: {orb_list} [{profile}]")
                self.employment_label.setStyleSheet("color: #4ade80; font-weight: bold;")

    def _update_buttons(self):
        """Update button enabled states."""
        has_employment = len(self._employment_orbs) > 0
        self.arm_btn.setEnabled(has_employment)
        self.release_btn.setEnabled(has_employment and self._is_armed)

        if self._is_armed:
            self.arm_btn.setText("DISARM")
            self.arm_btn.setStyleSheet("""
                QPushButton#arm_button {
                    background-color: #dc2626;
                    color: white;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QPushButton#arm_button:hover { background-color: #ef4444; }
            """)
        else:
            self.arm_btn.setText("ARM")
            self.arm_btn.setStyleSheet("""
                QPushButton#arm_button {
                    background-color: #374151;
                    color: white;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                QPushButton#arm_button:hover { background-color: #4b5563; }
                QPushButton#arm_button:disabled { background-color: #1f2937; color: #4b5563; }
            """)

    # ==================== Public API ====================

    def add_target(self, target_id: str, target_name: str):
        """Add a target to the list."""
        if target_id in self._target_rows:
            return  # Already exists

        row = TargetRowWidget(target_id, target_name)
        row.drone_assigned.connect(self._on_target_drone_assigned)
        self._target_rows[target_id] = row

        # Insert before the stretch
        self.target_list_layout.insertWidget(
            self.target_list_layout.count() - 1, row
        )
        self.no_targets_label.hide()

    def remove_target(self, target_id: str):
        """Remove a target from the list."""
        if target_id in self._target_rows:
            row = self._target_rows.pop(target_id)
            self.target_list_layout.removeWidget(row)
            row.deleteLater()

        if not self._target_rows:
            self.no_targets_label.show()

    def clear_targets(self):
        """Clear all targets from the list."""
        for row in self._target_rows.values():
            self.target_list_layout.removeWidget(row)
            row.deleteLater()
        self._target_rows.clear()
        self.no_targets_label.show()

    def _on_target_drone_assigned(self, target_id: str, drone_id: str):
        """Handle target-drone assignment from dropdown."""
        self.target_drone_assigned.emit(target_id, drone_id)

    def set_target_drone(self, target_id: str, drone_id: str):
        """Set the assigned drone for a target."""
        if target_id in self._target_rows:
            self._target_rows[target_id].set_assigned_drone(drone_id)

    def update_orb(self, orb_id: str, state: str, has_target: bool = False,
                   target_id: str = None, carrier: str = None):
        """Update orb state."""
        self._orb_states[orb_id] = {
            "state": state,
            "has_target": has_target,
            "target_id": target_id,
            "carrier": carrier
        }
        self._update_employment_selection()

    def set_armed(self, armed: bool):
        """Set armed state for current employment."""
        self._is_armed = armed
        self._update_employment_info()
        self._update_buttons()
        self._update_orb_displays()

    def update_orb_range(self, orb_id: str, in_range: bool = None,
                         time_to_range: float = None,
                         current_dist: float = None):
        """Update range status for a specific orb."""
        # Find the orb widget and update it
        for drone_id, column in self._drone_columns.items():
            widget = column.get_orb_widget(orb_id)
            if widget:
                widget.set_range_info(in_range, time_to_range, current_dist)
                column.update_range_display()
                break

    def update_impact_time(self, orb_id: str, time_to_impact: float = None):
        """Update impact time display."""
        if time_to_impact is not None and time_to_impact > 0:
            self.impact_label.setText(f"ORB{orb_id} IMPACT: {time_to_impact:.1f}s")
            self.impact_label.show()
        elif time_to_impact is not None and time_to_impact <= 0:
            self.impact_label.setText(f"ORB{orb_id} IMPACT: NOW")
            self.impact_label.show()
        else:
            self.impact_label.hide()

    def get_employment_orbs(self) -> list:
        """Get list of orbs currently selected for employment."""
        return self._employment_orbs.copy()

    def get_current_profile(self) -> str:
        """Get current employment profile."""
        return self._current_profile.value

    def get_orbs_for_carrier(self, carrier_id: str) -> list:
        """Get orb IDs for a specific carrier based on current profile."""
        if carrier_id == "chick1.1":
            orb_ids = ["1", "2"]
        elif carrier_id == "chick1.2":
            orb_ids = ["3", "4"]
        else:
            return []

        # Filter to available orbs
        available = [oid for oid in orb_ids
                     if self._orb_states.get(oid, {}).get("state") in ["loaded", "armed", None]]

        if self._current_profile == EmploymentProfile.SINGLE:
            return available[:1]
        elif self._current_profile == EmploymentProfile.DUAL:
            return available[:2]
        else:  # SALVO
            return available

    @property
    def selected_id(self) -> str:
        """Get first orb in employment selection (for backwards compatibility)."""
        return self._employment_orbs[0] if self._employment_orbs else None
