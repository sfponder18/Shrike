# Vehicle Status Card Widget for SwarmDrones GCS
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QProgressBar, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class VehicleHUD(QFrame):
    """HUD showing detailed parameters of selected vehicle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setMinimumWidth(140)
        self.setMaximumWidth(180)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # Vehicle name/icon
        self.name_label = QLabel("✈ BIRD")
        self.name_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.name_label.setStyleSheet("color: #4ade80;")
        layout.addWidget(self.name_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #3a3a5a;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Parameters grid
        self.params = {}
        param_list = [
            ("MODE", "---"),
            ("STATE", "---"),  # Chick attachment state
            ("ALT", "-- m"),
            ("SPD", "-- m/s"),
            ("HDG", "---°"),
            ("GPS", "-- sats"),
            ("BATT", "--%"),
        ]

        for name, default in param_list:
            row = QHBoxLayout()
            row.setSpacing(4)

            label = QLabel(name)
            label.setStyleSheet("color: #808080; font-size: 9px;")
            label.setFixedWidth(35)
            row.addWidget(label)

            value = QLabel(default)
            value.setStyleSheet("color: #e0e0e0; font-size: 10px;")
            value.setAlignment(Qt.AlignRight)
            row.addWidget(value)

            self.params[name] = value
            layout.addLayout(row)

        layout.addStretch()

    def update_vehicle(self, name: str, icon: str, mode: str, alt: float,
                       speed: float, heading: float, gps_sats: int,
                       battery: int, connected: bool, chick_state: str = None):
        """Update HUD with vehicle data."""
        self.name_label.setText(f"{icon} {name}")

        if connected:
            self.name_label.setStyleSheet("color: #4ade80;")
            self.params["MODE"].setText(mode)
            self.params["MODE"].setStyleSheet(self._mode_color(mode))

            # Chick state display
            if chick_state:
                state_display = {
                    "attached": "ATTACHED",
                    "launching": "LAUNCHING",
                    "launched": "LAUNCHED",
                    "recovered": "RECOVERED"
                }
                state_colors = {
                    "attached": "color: #facc15;",   # Yellow
                    "launching": "color: #f97316;",  # Orange
                    "launched": "color: #4ade80;",   # Green
                    "recovered": "color: #60a5fa;"   # Blue
                }
                self.params["STATE"].setText(state_display.get(chick_state, chick_state.upper()))
                self.params["STATE"].setStyleSheet(state_colors.get(chick_state, "color: #e0e0e0;"))
            else:
                self.params["STATE"].setText("N/A")
                self.params["STATE"].setStyleSheet("color: #606080;")

            self.params["ALT"].setText(f"{alt:.0f} m")
            self.params["SPD"].setText(f"{speed:.1f} m/s")
            self.params["HDG"].setText(f"{heading:.0f}°")
            self.params["GPS"].setText(f"{gps_sats} sats")
            self.params["GPS"].setStyleSheet(
                "color: #4ade80;" if gps_sats >= 6 else "color: #facc15;"
            )
            self.params["BATT"].setText(f"{battery:.2f}%")
            self.params["BATT"].setStyleSheet(self._batt_color(battery))
        else:
            self.name_label.setStyleSheet("color: #f87171;")
            for key in self.params:
                self.params[key].setText("---")
                self.params[key].setStyleSheet("color: #808080;")

    def _mode_color(self, mode: str) -> str:
        if mode in ("RTL", "LAND"):
            return "color: #facc15;"
        elif mode in ("AUTO", "GUIDED"):
            return "color: #4ade80;"
        else:
            return "color: #60a5fa;"

    def _batt_color(self, pct: int) -> str:
        if pct > 50:
            return "color: #4ade80;"
        elif pct > 20:
            return "color: #facc15;"
        else:
            return "color: #f87171;"


class VehicleCard(QFrame):
    """Individual vehicle status card."""

    clicked = pyqtSignal(str)  # vehicle_id

    def __init__(self, vehicle_id: str, name: str, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.name = name
        self._selected = False
        self._setup_ui()
        self.update_selection(False)

    def _setup_ui(self):
        self.setFixedWidth(100)
        self.setMinimumHeight(90)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Name
        self.name_label = QLabel(self.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("Consolas", 11, QFont.Bold))
        self.name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.name_label)

        # Mode
        self.mode_label = QLabel("---")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("color: #60a5fa;")
        self.mode_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.mode_label)

        # Altitude
        self.alt_label = QLabel("-- m")
        self.alt_label.setAlignment(Qt.AlignCenter)
        self.alt_label.setStyleSheet("color: #a0a0a0;")
        self.alt_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.alt_label)

        # Battery bar
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)
        self.battery_bar.setTextVisible(True)
        self.battery_bar.setFormat("%p%")
        self.battery_bar.setFixedHeight(18)
        self.battery_bar.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.battery_bar)

    def update_selection(self, selected: bool):
        """Update selection state."""
        self._selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2a3a5a;
                    border: 2px solid #4a8aba;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2a2a4a;
                    border: 2px solid #3a3a5a;
                    border-radius: 6px;
                }
            """)

    def update_state(self, mode: str, alt: float, battery: int, connected: bool,
                     chick_state: str = None):
        """Update displayed state."""
        # Display mode or chick state
        if chick_state == "attached":
            self.mode_label.setText("ATTACHED")
            self.mode_label.setStyleSheet("color: #facc15;")  # Yellow
        elif chick_state == "launching":
            self.mode_label.setText("LAUNCHING")
            self.mode_label.setStyleSheet("color: #f97316;")  # Orange
        else:
            self.mode_label.setText(mode if connected else "---")
            # Mode color
            if not connected:
                self.mode_label.setStyleSheet("color: #808080;")
            elif mode in ("RTL", "LAND"):
                self.mode_label.setStyleSheet("color: #facc15;")
            elif mode in ("AUTO", "GUIDED"):
                self.mode_label.setStyleSheet("color: #4ade80;")
            else:
                self.mode_label.setStyleSheet("color: #60a5fa;")

        self.alt_label.setText(f"{alt:.0f}m" if connected else "-- m")
        self.battery_bar.setValue(int(battery) if connected else 0)

        # Battery color
        if battery > 50:
            self.battery_bar.setStyleSheet("QProgressBar::chunk { background-color: #4ade80; }")
        elif battery > 20:
            self.battery_bar.setStyleSheet("QProgressBar::chunk { background-color: #facc15; }")
        else:
            self.battery_bar.setStyleSheet("QProgressBar::chunk { background-color: #f87171; }")

    def mousePressEvent(self, event):
        """Handle click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.vehicle_id)


class VehiclePanel(QFrame):
    """Panel containing HUD and vehicle cards."""

    vehicle_selected = pyqtSignal(str)  # vehicle_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._cards: dict[str, VehicleCard] = {}
        self._selected_id = None
        self._vehicle_data = {}  # Store full vehicle data for HUD
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        title = QLabel("VEHICLES")
        title.setObjectName("header")
        header.addWidget(title)

        shortcut = QLabel("[Ctrl+1/2/3]")
        shortcut.setStyleSheet("color: #606080; font-size: 10px;")
        header.addWidget(shortcut)
        header.addStretch()

        layout.addLayout(header)

        # Main content: HUD + Cards
        content = QHBoxLayout()
        content.setSpacing(8)

        # HUD on the left
        self.hud = VehicleHUD()
        content.addWidget(self.hud)

        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)

        # Create cards from config
        from ..config import get_all_vehicles
        vehicles = get_all_vehicles()

        for vid, info in vehicles.items():
            name = info.get("name", vid)
            icon = info.get("icon", "?")
            card = VehicleCard(vid, name)
            card.clicked.connect(self._on_card_clicked)
            self._cards[vid] = card
            self._vehicle_data[vid] = {"name": name, "icon": icon}
            cards_layout.addWidget(card)

        content.addLayout(cards_layout)
        content.addStretch()

        layout.addLayout(content)

    def _on_card_clicked(self, vehicle_id: str):
        """Handle card click."""
        self.select_vehicle(vehicle_id)

    def select_vehicle(self, vehicle_id: str, emit_signal: bool = True):
        """Select a vehicle."""
        if vehicle_id not in self._cards:
            return

        # Skip if already selected
        if self._selected_id == vehicle_id:
            return

        # Deselect previous
        if self._selected_id and self._selected_id in self._cards:
            self._cards[self._selected_id].update_selection(False)

        # Select new
        self._selected_id = vehicle_id
        self._cards[vehicle_id].update_selection(True)

        # Update HUD
        self._update_hud(vehicle_id)

        if emit_signal:
            self.vehicle_selected.emit(vehicle_id)

    def update_vehicle(self, vehicle_id: str, mode: str, alt: float, battery: int,
                       connected: bool, speed: float = 0, heading: float = 0,
                       gps_sats: int = 0, chick_state: str = None):
        """Update a vehicle's displayed state."""
        if vehicle_id in self._cards:
            self._cards[vehicle_id].update_state(mode, alt, battery, connected, chick_state)

        # Store data for HUD
        if vehicle_id in self._vehicle_data:
            self._vehicle_data[vehicle_id].update({
                "mode": mode,
                "alt": alt,
                "battery": battery,
                "connected": connected,
                "speed": speed,
                "heading": heading,
                "gps_sats": gps_sats,
                "chick_state": chick_state,
            })

        # Update HUD if this is the selected vehicle
        if vehicle_id == self._selected_id:
            self._update_hud(vehicle_id)

    def _update_hud(self, vehicle_id: str):
        """Update the HUD with data from specified vehicle."""
        data = self._vehicle_data.get(vehicle_id, {})
        self.hud.update_vehicle(
            name=data.get("name", "---"),
            icon=data.get("icon", "?"),
            mode=data.get("mode", "---"),
            alt=data.get("alt", 0),
            speed=data.get("speed", 0),
            heading=data.get("heading", 0),
            gps_sats=data.get("gps_sats", 0),
            battery=data.get("battery", 0),
            connected=data.get("connected", False),
            chick_state=data.get("chick_state"),
        )

    @property
    def selected_id(self) -> str:
        return self._selected_id
