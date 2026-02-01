# EW Panel Widget - Electronic Warfare Display
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QProgressBar, QComboBox,
    QAbstractItemView, QGroupBox, QScrollArea, QMenu, QAction,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

from ..models.emitter import (
    Emitter, EmitterList, EPStatus, ThreatLevel, EmitterType,
    ProsecutionState, ProsecutionAction
)


class SpectrumDisplay(QFrame):
    """Real-time spectrum display widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("spectrum_display")
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self._data = []
        self._freq_start = 400  # MHz
        self._freq_end = 500    # MHz
        self._db_min = -100
        self._db_max = -30

    def set_data(self, data: list, freq_start: float = 400, freq_end: float = 500):
        """Set spectrum data to display."""
        self._data = data
        self._freq_start = freq_start
        self._freq_end = freq_end
        self.update()

    def paintEvent(self, event):
        """Draw spectrum."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#0a0a1a"))

        if not self._data:
            # Draw placeholder
            painter.setPen(QColor("#4a4a6a"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No spectrum data")
            return

        # Draw grid
        painter.setPen(QPen(QColor("#2a2a4a"), 1))
        w, h = self.width(), self.height()

        # Horizontal grid lines (dB)
        for db in range(-90, -30, 10):
            y = self._db_to_y(db, h)
            painter.drawLine(0, y, w, y)

        # Vertical grid lines (freq)
        freq_step = (self._freq_end - self._freq_start) / 5
        for i in range(6):
            x = int(i * w / 5)
            painter.drawLine(x, 0, x, h)

        # Draw spectrum trace
        if len(self._data) > 1:
            painter.setPen(QPen(QColor("#4ade80"), 2))
            points = []
            for i, val in enumerate(self._data):
                x = int(i * w / len(self._data))
                y = self._db_to_y(val, h)
                points.append((x, y))

            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1],
                               points[i+1][0], points[i+1][1])

        # Draw labels
        painter.setPen(QColor("#6a6a8a"))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(5, 12, f"{self._db_max} dBm")
        painter.drawText(5, h - 5, f"{self._db_min} dBm")
        painter.drawText(5, h - 18, f"{self._freq_start} MHz")
        painter.drawText(w - 60, h - 18, f"{self._freq_end} MHz")

    def _db_to_y(self, db: float, height: int) -> int:
        """Convert dB value to Y coordinate."""
        db = max(self._db_min, min(self._db_max, db))
        ratio = (db - self._db_min) / (self._db_max - self._db_min)
        return int(height * (1 - ratio))


class WaterfallDisplay(QFrame):
    """Waterfall/spectrogram display widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("waterfall_display")
        self.setMinimumHeight(50)
        self.setMaximumHeight(70)
        self._history = []

    def set_history(self, history: list):
        """Set waterfall history data."""
        self._history = history[-50:]  # Keep last 50 rows
        self.update()

    def paintEvent(self, event):
        """Draw waterfall."""
        painter = QPainter(self)

        # Background
        painter.fillRect(self.rect(), QColor("#0a0a1a"))

        if not self._history:
            painter.setPen(QColor("#4a4a6a"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No history")
            return

        w, h = self.width(), self.height()
        row_height = max(1, h // len(self._history))

        for row_idx, row_data in enumerate(self._history):
            y = row_idx * row_height
            if not row_data:
                continue

            col_width = max(1, w // len(row_data))
            for col_idx, val in enumerate(row_data):
                x = col_idx * col_width
                # Map dB to color (blue -> green -> yellow -> red)
                intensity = max(0, min(1, (val + 100) / 70))
                color = self._intensity_to_color(intensity)
                painter.fillRect(x, y, col_width + 1, row_height + 1, color)

    def _intensity_to_color(self, intensity: float) -> QColor:
        """Convert intensity (0-1) to color."""
        if intensity < 0.33:
            # Blue to cyan
            r = 0
            g = int(intensity * 3 * 150)
            b = 100 + int(intensity * 3 * 100)
        elif intensity < 0.66:
            # Cyan to yellow
            t = (intensity - 0.33) * 3
            r = int(t * 255)
            g = 150 + int(t * 105)
            b = int(200 * (1 - t))
        else:
            # Yellow to red
            t = (intensity - 0.66) * 3
            r = 255
            g = int(255 * (1 - t))
            b = 0
        return QColor(r, g, b)


class EPStatusPanel(QFrame):
    """Electronic Protection status panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ep_status_panel")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Title
        title = QLabel("EP STATUS")
        title.setObjectName("header")
        layout.addWidget(title)

        # Link health
        health_layout = QHBoxLayout()
        health_layout.addWidget(QLabel("Link Health:"))
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(95)
        self.health_bar.setTextVisible(True)
        self.health_bar.setFormat("%v%")
        health_layout.addWidget(self.health_bar)
        layout.addLayout(health_layout)

        # Threat level
        threat_layout = QHBoxLayout()
        threat_layout.addWidget(QLabel("Threat Level:"))
        self.threat_label = QLabel("LOW")
        self.threat_label.setObjectName("threat_low")
        threat_layout.addWidget(self.threat_label)
        threat_layout.addStretch()
        layout.addLayout(threat_layout)

        # Active responses
        layout.addWidget(QLabel("Active Responses:"))
        self.responses_label = QLabel("  (none)")
        self.responses_label.setStyleSheet("color: #6b7280;")
        layout.addWidget(self.responses_label)

        # Hop status
        hop_layout = QHBoxLayout()
        hop_layout.addWidget(QLabel("Hop Status:"))
        self.hop_label = QLabel("3/16 | Ready")
        self.hop_label.setObjectName("hop_ready")
        hop_layout.addWidget(self.hop_label)
        hop_layout.addStretch()
        layout.addLayout(hop_layout)

        # Consensus
        layout.addWidget(QLabel("Consensus:"))
        self.consensus_layout = QHBoxLayout()
        self.vehicle_indicators = {}
        for vid in ["Bird", "Chick1", "Chick2"]:
            indicator = QLabel(f"● {vid}")
            indicator.setStyleSheet("color: #4ade80;")
            self.vehicle_indicators[vid] = indicator
            self.consensus_layout.addWidget(indicator)
        self.consensus_layout.addStretch()
        layout.addLayout(self.consensus_layout)

        layout.addStretch()

    def update_status(self, status: EPStatus):
        """Update display from EP status."""
        try:
            # Link health
            self.health_bar.setValue(int(status.link_health_pct))
            if status.link_health_pct > 80:
                self.health_bar.setStyleSheet("QProgressBar::chunk { background-color: #4ade80; }")
            elif status.link_health_pct > 50:
                self.health_bar.setStyleSheet("QProgressBar::chunk { background-color: #facc15; }")
            else:
                self.health_bar.setStyleSheet("QProgressBar::chunk { background-color: #f87171; }")

            # Threat level
            level = status.threat_level.value
            self.threat_label.setText(level)
            colors = {
                "LOW": "#4ade80",
                "MEDIUM": "#facc15",
                "HIGH": "#fb923c",
                "CRITICAL": "#f87171"
            }
            self.threat_label.setStyleSheet(f"color: {colors.get(level, '#e0e0e0')}; font-weight: bold;")

            # Active responses
            if status.active_responses:
                self.responses_label.setText("  " + ", ".join(status.active_responses))
                self.responses_label.setStyleSheet("color: #fb923c;")
            else:
                self.responses_label.setText("  (none)")
                self.responses_label.setStyleSheet("color: #6b7280;")

            # Hop status
            hop = status.hop_status
            self.hop_label.setText(f"{hop.current_index + 1}/{hop.total_entries} | {hop.state}")

            # Consensus
            for vid, healthy in status.vehicle_health.items():
                short_name = vid.replace("bird", "Bird").replace("chick", "Chick").replace("1.", "")
                if short_name in self.vehicle_indicators:
                    color = "#4ade80" if healthy else "#f87171"
                    self.vehicle_indicators[short_name].setStyleSheet(f"color: {color};")
        except Exception as e:
            print(f"[EW] EP status update error: {e}")


class ProsecutionQueuePanel(QFrame):
    """Panel showing tracks in prosecution queue."""

    item_selected = pyqtSignal(str)  # emitter_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prosecution_queue_panel")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Header
        header = QLabel("PROSECUTION QUEUE")
        header.setObjectName("header")
        header.setStyleSheet("font-weight: bold; color: #f87171;")
        layout.addWidget(header)

        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(100)
        self.queue_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.queue_list)

    def update_queue(self, emitters: list):
        """Update queue display with list of emitters."""
        self.queue_list.clear()

        for emitter in emitters:
            # Create item with state icon and info
            state = emitter.prosecution_state
            state_icons = {
                ProsecutionState.QUEUED.value: "⌛",
                ProsecutionState.LOCATING.value: "◎",
                ProsecutionState.PROSECUTING.value: "▶",
            }
            icon = state_icons.get(state, "?")

            # Build display text
            cep_text = f"CEP:{emitter.df_result.cep_m:.0f}m" if emitter.df_result else "No DF"
            vehicle_text = f"→{emitter.assigned_vehicle}" if emitter.assigned_vehicle else ""

            text = f"{icon} {emitter.id} | {emitter.freq_mhz:.1f}MHz | {cep_text} {vehicle_text}"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, emitter.id)

            # Color by state
            if state == ProsecutionState.PROSECUTING.value:
                item.setForeground(QColor("#f87171"))
            elif state == ProsecutionState.LOCATING.value:
                item.setForeground(QColor("#60a5fa"))
            else:
                item.setForeground(QColor("#facc15"))

            self.queue_list.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle queue item click."""
        emitter_id = item.data(Qt.UserRole)
        if emitter_id:
            self.item_selected.emit(emitter_id)


class DFGeometryPanel(QFrame):
    """Direction Finding geometry visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("df_geometry_panel")
        self.setMinimumSize(120, 120)
        self.setMaximumHeight(140)
        self._vehicles = {}  # {name: (x, y)}
        self._emitters = []  # [(x, y, cep, id), ...]

    def set_geometry(self, vehicles: dict, emitters: list = None):
        """Set DF geometry data. emitters is list of (x, y, cep, id) tuples."""
        self._vehicles = vehicles
        self._emitters = emitters or []
        self.update()

    def paintEvent(self, event):
        """Draw DF geometry."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#1e1e3a"))

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # Draw compass
        painter.setPen(QPen(QColor("#3a3a5a"), 1))
        painter.drawLine(cx, 10, cx, h - 10)  # N-S
        painter.drawLine(10, cy, w - 10, cy)  # E-W

        painter.setPen(QColor("#6a6a8a"))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(cx - 3, 12, "N")

        # Draw vehicles
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        for name, (x, y) in self._vehicles.items():
            # Map normalized coords to widget
            px = int(cx + x * (w / 3))
            py = int(cy - y * (h / 3))

            # Draw vehicle marker
            painter.setPen(QPen(QColor("#4ade80"), 2))
            painter.setBrush(QBrush(QColor("#4ade80")))
            painter.drawEllipse(px - 5, py - 5, 10, 10)

            # Label
            painter.setPen(QColor("#4ade80"))
            painter.drawText(px + 8, py + 4, name[0])  # First letter

        # Draw all emitters with CEP
        for i, emitter_data in enumerate(self._emitters):
            if len(emitter_data) >= 3:
                ex, ey, cep = emitter_data[:3]
                emitter_id = emitter_data[3] if len(emitter_data) > 3 else f"E{i}"

                px = int(cx + ex * (w / 3))
                py = int(cy - ey * (h / 3))

                # CEP circle (scaled)
                cep_radius = max(5, min(50, cep / 5))

                # Different colors for different emitters
                colors = ["#f87171", "#fb923c", "#facc15", "#4ade80", "#60a5fa"]
                color = QColor(colors[i % len(colors)])

                painter.setPen(QPen(color, 1, Qt.DashLine))
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 50)))
                painter.drawEllipse(int(px - cep_radius), int(py - cep_radius),
                                  int(cep_radius * 2), int(cep_radius * 2))

                # Emitter marker
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(px - 4, py - 4, 8, 8)

                # Label
                painter.setPen(color)
                painter.drawText(px + 8, py + 4, emitter_id[-4:])  # Last 4 chars


class EmitterDetailPanel(QFrame):
    """Detailed view of selected emitter(s)."""

    target_requested = pyqtSignal(str)  # emitter_id
    investigate_requested = pyqtSignal(str)  # emitter_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("emitter_detail_panel")
        self._current_emitters = []  # List of emitters
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header
        self.header_label = QLabel("SELECTED EMITTERS (0)")
        self.header_label.setObjectName("header")
        layout.addWidget(self.header_label)

        # Scroll area for multiple emitters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)  # Compact to give more room to emitter table

        self.detail_container = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(8)

        scroll.setWidget(self.detail_container)
        layout.addWidget(scroll)

        # Action buttons (for primary selected)
        btn_layout = QHBoxLayout()

        self.investigate_btn = QPushButton("INVESTIGATE")
        self.investigate_btn.setObjectName("ew_investigate_btn")
        self.investigate_btn.clicked.connect(self._on_investigate)
        self.investigate_btn.setEnabled(False)
        btn_layout.addWidget(self.investigate_btn)

        self.target_btn = QPushButton("ADD TO TARGETS")
        self.target_btn.setObjectName("ew_target_btn")
        self.target_btn.clicked.connect(self._on_target)
        self.target_btn.setEnabled(False)
        btn_layout.addWidget(self.target_btn)

        layout.addLayout(btn_layout)

    def set_emitters(self, emitters: list):
        """Update display for multiple emitters."""
        self._current_emitters = emitters or []

        # Clear existing details
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.header_label.setText(f"SELECTED EMITTERS ({len(self._current_emitters)})")

        if not self._current_emitters:
            self.investigate_btn.setEnabled(False)
            self.target_btn.setEnabled(False)
            placeholder = QLabel("No emitters selected")
            placeholder.setStyleSheet("color: #6b7280;")
            self.detail_layout.addWidget(placeholder)
            return

        # Add detail for each emitter
        for emitter in self._current_emitters:
            frame = self._create_emitter_detail_frame(emitter)
            self.detail_layout.addWidget(frame)

        self.detail_layout.addStretch()

        # Enable buttons based on primary (first) emitter
        primary = self._current_emitters[0]
        self.investigate_btn.setEnabled(True)
        self.target_btn.setEnabled(primary.has_location())

    def _create_emitter_detail_frame(self, emitter: Emitter) -> QFrame:
        """Create a detail frame for one emitter."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #2a2a4a; border-radius: 4px; padding: 4px; }")

        layout = QGridLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Row 0: ID and Type
        id_label = QLabel(f"<b>{emitter.id}</b>")
        id_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(id_label, 0, 0)

        type_label = QLabel(emitter.emitter_type.value)
        type_colors = {
            EmitterType.TACTICAL_RADIO: "#fb923c",
            EmitterType.UNKNOWN_SUSPICIOUS: "#facc15",
            EmitterType.FRIENDLY: "#4ade80",
        }
        type_label.setStyleSheet(f"color: {type_colors.get(emitter.emitter_type, '#6b7280')};")
        layout.addWidget(type_label, 0, 1)

        # Criticality bar
        crit_bar = QProgressBar()
        crit_bar.setRange(0, 100)
        crit_bar.setValue(int(emitter.criticality))
        crit_bar.setFixedWidth(60)
        crit_bar.setTextVisible(False)
        level = emitter.get_criticality_level()
        colors = {
            ThreatLevel.LOW: "#4a6a4a",
            ThreatLevel.MEDIUM: "#6a6a4a",
            ThreatLevel.HIGH: "#8a6a4a",
            ThreatLevel.CRITICAL: "#8a4a4a"
        }
        crit_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {colors[level]}; }}")
        layout.addWidget(crit_bar, 0, 2)

        # Row 1: Freq, Mod, CEP
        layout.addWidget(QLabel(f"{emitter.freq_mhz:.3f} MHz"), 1, 0)
        layout.addWidget(QLabel(f"{emitter.modulation}"), 1, 1)

        if emitter.df_result:
            cep_text = f"CEP: {emitter.df_result.cep_m:.0f}m"
            cep_color = "#4ade80" if emitter.df_result.cep_m < 50 else \
                        "#facc15" if emitter.df_result.cep_m < 150 else "#f87171"
        else:
            cep_text = "No DF"
            cep_color = "#6b7280"
        cep_label = QLabel(cep_text)
        cep_label.setStyleSheet(f"color: {cep_color};")
        layout.addWidget(cep_label, 1, 2)

        return frame

    def _on_investigate(self):
        """Investigate the primary (first) selected emitter."""
        if self._current_emitters:
            self.investigate_requested.emit(self._current_emitters[0].id)

    def _on_target(self):
        """Add primary (first) selected emitter to targets."""
        if self._current_emitters:
            self.target_requested.emit(self._current_emitters[0].id)


class EWPanel(QFrame):
    """
    Main Electronic Warfare Panel.

    Provides:
    - Spectrum display with waterfall
    - EP status monitoring
    - DF geometry visualization
    - Emitter list with criticality (multi-select)
    - Emitter detail view (multiple)
    - Target integration
    - Map display of selected emitters
    """

    target_requested = pyqtSignal(float, float, str)  # lat, lon, emitter_id
    investigate_requested = pyqtSignal(str)  # emitter_id
    emitters_selected_for_map = pyqtSignal(list)  # list of (lat, lon, id, cep) tuples
    optimize_geometry_requested = pyqtSignal(list)  # list of emitter_ids to optimize for

    # Prosecution signals
    prosecute_requested = pyqtSignal(str)  # emitter_id - right-click prosecute
    prosecution_action_selected = pyqtSignal(str, str)  # emitter_id, action (INVESTIGATE/MARK_TARGET/CONTINUE)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ew_panel")
        self._ew_manager = None
        self._setup_ui()

        # Update timer for age display
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(1000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Main horizontal splitter: Left (spectrum/table) | Right (queue/status/waterfall)
        main_splitter = QSplitter(Qt.Horizontal)

        # ========== LEFT SIDE: Spectrum + Table ==========
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Spectrum section (compact)
        spectrum_widget = QWidget()
        spectrum_layout = QVBoxLayout(spectrum_widget)
        spectrum_layout.setContentsMargins(0, 0, 0, 0)
        spectrum_layout.setSpacing(2)

        # Band selector
        band_layout = QHBoxLayout()
        band_layout.addWidget(QLabel("Band:"))
        self.band_combo = QComboBox()
        self.band_combo.addItems(["UHF (400-500 MHz)", "VHF (136-174 MHz)",
                                  "ISM (860-930 MHz)", "L-Band (1200-1400 MHz)"])
        band_layout.addWidget(self.band_combo)
        band_layout.addStretch()
        spectrum_layout.addLayout(band_layout)

        # Spectrum display
        self.spectrum_display = SpectrumDisplay()
        spectrum_layout.addWidget(self.spectrum_display)

        left_layout.addWidget(spectrum_widget, 0)

        # Emitter table - main focus
        self._create_emitter_table()
        self.emitter_table.setMinimumHeight(180)
        left_layout.addWidget(self.emitter_table, 1)

        # Emitter detail panel
        self.emitter_detail = EmitterDetailPanel()
        self.emitter_detail.target_requested.connect(self._on_target_requested)
        self.emitter_detail.investigate_requested.connect(self._on_investigate_requested)
        self.emitter_detail.setMaximumHeight(150)
        left_layout.addWidget(self.emitter_detail, 0)

        main_splitter.addWidget(left_widget)

        # ========== RIGHT SIDE: Queue + Status + Waterfall ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Prosecution Queue (top priority display)
        self.prosecution_queue_panel = ProsecutionQueuePanel()
        self.prosecution_queue_panel.item_selected.connect(self._on_queue_item_selected)
        right_layout.addWidget(self.prosecution_queue_panel)

        # EP Status panel
        self.ep_status_panel = EPStatusPanel()
        right_layout.addWidget(self.ep_status_panel)

        # DF Geometry panel
        self.df_geometry_panel = DFGeometryPanel()
        right_layout.addWidget(self.df_geometry_panel)

        # Optimize button
        self.optimize_btn = QPushButton("Optimize DF Formation")
        self.optimize_btn.setToolTip("Command vehicles to optimal positions for DF on selected emitters")
        self.optimize_btn.clicked.connect(self._on_optimize_geometry)
        right_layout.addWidget(self.optimize_btn)

        # Waterfall display (moved here - replaces camera view)
        waterfall_label = QLabel("WATERFALL")
        waterfall_label.setStyleSheet("font-weight: bold; color: #60a5fa;")
        right_layout.addWidget(waterfall_label)

        self.waterfall_display = WaterfallDisplay()
        self.waterfall_display.setMinimumHeight(80)
        self.waterfall_display.setMaximumHeight(120)
        right_layout.addWidget(self.waterfall_display)

        right_layout.addStretch()

        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([600, 300])

        layout.addWidget(main_splitter, 1)

    def _create_emitter_table(self):
        """Create emitter list table with multi-selection and context menu."""
        self.emitter_table = QTableWidget()
        self.emitter_table.setColumnCount(7)
        self.emitter_table.setHorizontalHeaderLabels([
            "ID", "Freq", "Type", "Crit", "CEP", "State", "Age"
        ])

        # Configure table
        header = self.emitter_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)           # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Freq
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Crit
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # CEP
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # State
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Age

        self.emitter_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.emitter_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.emitter_table.setAlternatingRowColors(True)
        self.emitter_table.verticalHeader().setVisible(False)
        self.emitter_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Connect signals
        self.emitter_table.itemSelectionChanged.connect(self._on_emitter_selected)

        # Right-click context menu
        self.emitter_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.emitter_table.customContextMenuRequested.connect(self._on_table_right_click)

        # Track selected emitter IDs for map display
        self._selected_emitter_ids = set()

    def set_ew_manager(self, manager):
        """Set the EW manager for data."""
        self._ew_manager = manager
        if manager:
            manager.emitter_detected.connect(self._on_emitter_detected)
            manager.emitter_updated.connect(self._on_emitter_updated)
            manager.ep_status_changed.connect(self._on_ep_status_changed)
            print(f"[EW Panel] Manager connected, current emitters: {manager.emitters.count()}")

    def refresh(self):
        """Force refresh of all panel data."""
        print("[EW Panel] Force refresh called")
        self._refresh_emitter_table()
        self._update_prosecution_queue()
        if self._ew_manager:
            self.ep_status_panel.update_status(self._ew_manager.ep_status)

    def _update_display(self):
        """Periodic display update."""
        if not self._ew_manager:
            return

        try:
            # Update spectrum
            if self._ew_manager.spectrum_data:
                data = self._ew_manager.spectrum_data.get("400-500", [])
                self.spectrum_display.set_data(data, 400, 500)

            # Update waterfall
            self.waterfall_display.set_history(self._ew_manager.waterfall_history)

            # Update emitter ages in table
            self._update_emitter_ages()

            # Update DF geometry with selected emitters
            self._update_df_geometry()

            # Update prosecution queue
            self._update_prosecution_queue()
        except Exception as e:
            print(f"[EW] Display update error: {e}")

    def _update_prosecution_queue(self):
        """Update the prosecution queue panel."""
        if not self._ew_manager:
            return

        try:
            queue = self._ew_manager.get_prosecution_queue()
            self.prosecution_queue_panel.update_queue(queue)
        except Exception as e:
            print(f"[EW] Queue update error: {e}")

    def _on_queue_item_selected(self, emitter_id: str):
        """Handle selection of item in prosecution queue."""
        try:
            # Find and select the emitter in the table
            for row in range(self.emitter_table.rowCount()):
                id_item = self.emitter_table.item(row, 0)  # ID is column 0
                if id_item:
                    item_id = id_item.text().replace("★ ", "")
                    if item_id == emitter_id:
                        self.emitter_table.selectRow(row)
                        break
        except Exception as e:
            print(f"[EW] Queue selection error: {e}")

    def _on_emitter_detected(self, emitter_id: str):
        """Handle new emitter detection."""
        print(f"[EW Panel] Emitter detected: {emitter_id}")
        self._refresh_emitter_table()

    def _on_emitter_updated(self, emitter_id: str):
        """Handle emitter update."""
        self._refresh_emitter_table()

    def _on_ep_status_changed(self):
        """Handle EP status change."""
        if self._ew_manager:
            self.ep_status_panel.update_status(self._ew_manager.ep_status)

    def _refresh_emitter_table(self):
        """Refresh emitter table from manager."""
        if not self._ew_manager:
            return

        try:
            emitters = self._ew_manager.emitters.get_all()

            # Block signals during update
            self.emitter_table.blockSignals(True)

            # Remember selection
            selected_ids = self._selected_emitter_ids.copy()

            self.emitter_table.setRowCount(len(emitters))

            for row, emitter in enumerate(emitters):
                # ID (with priority marker)
                id_text = f"★ {emitter.id}" if emitter.priority_track else emitter.id
                id_item = QTableWidgetItem(id_text)
                if emitter.priority_track:
                    id_item.setForeground(QColor("#f87171"))
                self.emitter_table.setItem(row, 0, id_item)

                # Frequency
                freq_item = QTableWidgetItem(f"{emitter.freq_mhz:.1f}")
                self.emitter_table.setItem(row, 1, freq_item)

                # Type - show library match if known, otherwise UNK
                if emitter.library_match:
                    # Shorten known classifications for table display
                    type_text = emitter.library_match
                    # Truncate long names
                    if len(type_text) > 12:
                        type_text = type_text[:10] + ".."
                    # Color based on threat level
                    if emitter.threat_level in ["HOSTILE", "UNKNOWN"]:
                        type_color = "#fb923c"  # Orange for hostile/unknown
                    elif emitter.threat_level == "FRIENDLY":
                        type_color = "#4ade80"  # Green for friendly
                    else:
                        type_color = "#6b7280"  # Gray for neutral
                else:
                    type_text = "UNK"
                    type_color = "#facc15"  # Yellow for unknown

                type_item = QTableWidgetItem(type_text)
                type_item.setForeground(QColor(type_color))
                type_item.setToolTip(emitter.library_match or "Unknown - no library match")
                self.emitter_table.setItem(row, 2, type_item)

                # Criticality
                level = emitter.get_criticality_level()
                crit_item = QTableWidgetItem(f"{emitter.criticality:.0f}")
                crit_colors = {
                    ThreatLevel.LOW: "#4ade80",
                    ThreatLevel.MEDIUM: "#facc15",
                    ThreatLevel.HIGH: "#fb923c",
                    ThreatLevel.CRITICAL: "#f87171"
                }
                crit_item.setForeground(QColor(crit_colors[level]))
                self.emitter_table.setItem(row, 3, crit_item)

                # CEP
                if emitter.df_result:
                    cep_text = f"{emitter.df_result.cep_m:.0f}m"
                    cep_color = "#4ade80" if emitter.df_result.cep_m < 100 else "#facc15"
                else:
                    cep_text = "-"
                    cep_color = "#6b7280"
                cep_item = QTableWidgetItem(cep_text)
                cep_item.setForeground(QColor(cep_color))
                self.emitter_table.setItem(row, 4, cep_item)

                # State
                state_map = {
                    "NONE": "-",
                    "QUEUED": "QUE",
                    "LOCATING": "LOC",
                    "PROSECUTING": "PRO",
                    "RESOLVED": "RES",
                }
                state_text = state_map.get(emitter.prosecution_state, "-")
                state_item = QTableWidgetItem(state_text)
                if emitter.prosecution_state == "PROSECUTING":
                    state_item.setForeground(QColor("#f87171"))
                elif emitter.prosecution_state == "LOCATING":
                    state_item.setForeground(QColor("#60a5fa"))
                self.emitter_table.setItem(row, 5, state_item)

                # Age
                age_item = QTableWidgetItem(f"{emitter.get_age_seconds():.0f}s")
                self.emitter_table.setItem(row, 6, age_item)

                # Restore selection
                if emitter.id in selected_ids:
                    self.emitter_table.selectRow(row)

            self.emitter_table.blockSignals(False)

        except Exception as e:
            self.emitter_table.blockSignals(False)
            print(f"[EW] Table refresh error: {e}")

    def _update_emitter_ages(self):
        """Update just the age column."""
        if not self._ew_manager:
            return

        try:
            for row in range(self.emitter_table.rowCount()):
                id_item = self.emitter_table.item(row, 0)  # ID is column 0
                if id_item:
                    emitter_id = id_item.text().replace("★ ", "")
                    emitter = self._ew_manager.emitters.get(emitter_id)
                    if emitter:
                        age_item = self.emitter_table.item(row, 6)  # Age is column 6
                        if age_item:
                            age_item.setText(f"{emitter.get_age_seconds():.0f}s")
        except Exception as e:
            print(f"[EW] Age update error: {e}")

    def _on_table_right_click(self, pos):
        """Handle right-click on emitter table."""
        item = self.emitter_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        id_item = self.emitter_table.item(row, 0)  # ID is column 0
        if not id_item:
            return

        emitter_id = id_item.text().replace("★ ", "")
        emitter = self._ew_manager.emitters.get(emitter_id) if self._ew_manager else None
        if not emitter:
            return

        # Select this row
        self.emitter_table.selectRow(row)

        menu = QMenu(self)

        # PROSECUTE - main action
        prosecute = menu.addAction("PROSECUTE")
        prosecute.triggered.connect(lambda: self._do_prosecute(emitter_id))

        menu.addSeparator()

        # Show on map
        if emitter.df_result:
            show_map = menu.addAction("Show on Map")
            show_map.triggered.connect(lambda: self._do_show_on_map(emitter))

        # Request DF
        request_df = menu.addAction("Request DF")
        request_df.triggered.connect(lambda: self._do_request_df(emitter_id))

        # If prosecuting, add action options
        if emitter.prosecution_state in ["LOCATING", "PROSECUTING"]:
            menu.addSeparator()
            investigate = menu.addAction("Investigate (send Chick)")
            investigate.triggered.connect(lambda: self._do_action(emitter_id, "INVESTIGATE"))

            mark_target = menu.addAction("Mark as Target")
            mark_target.triggered.connect(lambda: self._do_action(emitter_id, "MARK_TARGET"))

            cancel = menu.addAction("Cancel Prosecution")
            cancel.triggered.connect(lambda: self._do_cancel(emitter_id))

        menu.exec_(self.emitter_table.viewport().mapToGlobal(pos))

    def _do_prosecute(self, emitter_id: str):
        """Start prosecution for emitter."""
        self.prosecute_requested.emit(emitter_id)

    def _do_show_on_map(self, emitter):
        """Show emitter on map."""
        if emitter.df_result:
            self.emitters_selected_for_map.emit([
                (emitter.df_result.lat, emitter.df_result.lon, emitter.id,
                 emitter.df_result.cep_m, emitter.priority_track, emitter.prosecution_state, True)
            ])

    def _do_request_df(self, emitter_id: str):
        """Request DF for emitter."""
        if self._ew_manager:
            self._ew_manager.request_df(emitter_id)
        self.investigate_requested.emit(emitter_id)

    def _do_action(self, emitter_id: str, action: str):
        """Execute prosecution action."""
        self.prosecution_action_selected.emit(emitter_id, action)

    def _do_cancel(self, emitter_id: str):
        """Cancel prosecution."""
        if self._ew_manager:
            self._ew_manager.cancel_prosecution(emitter_id)
        self._refresh_emitter_table()

    def _update_df_geometry(self):
        """Update DF geometry panel with all selected emitters."""
        # Simulated vehicle positions (normalized -1 to 1)
        vehicles = {
            "Bird": (0, 0.5),
            "C1": (-0.4, -0.3),
            "C2": (0.4, -0.3)
        }

        # Get all selected emitters with positions
        emitter_positions = []
        if self._ew_manager:
            selected_emitters = self._get_selected_emitters()
            for i, emitter in enumerate(selected_emitters):
                if emitter.df_result:
                    # Normalize to display coords (rough approximation)
                    # Offset each emitter slightly so they don't overlap
                    x_offset = (i % 3 - 1) * 0.15
                    y_offset = (i // 3) * 0.15
                    emitter_positions.append((
                        0.1 + x_offset,
                        -0.1 + y_offset,
                        emitter.df_result.cep_m,
                        emitter.id
                    ))

        self.df_geometry_panel.set_geometry(vehicles, emitter_positions)

    def _get_selected_emitters(self) -> list:
        """Get list of selected Emitter objects."""
        if not self._ew_manager:
            return []

        selected_emitters = []
        selected_rows = set()

        for item in self.emitter_table.selectedItems():
            selected_rows.add(item.row())

        for row in sorted(selected_rows):
            id_item = self.emitter_table.item(row, 0)  # ID is column 0
            if id_item:
                emitter_id = id_item.text().replace("★ ", "")
                emitter = self._ew_manager.emitters.get(emitter_id)
                if emitter:
                    selected_emitters.append(emitter)

        return selected_emitters

    def _on_emitter_selected(self):
        """Handle emitter selection in table (multi-select)."""
        try:
            selected_emitters = self._get_selected_emitters()

            # Track selected IDs
            self._selected_emitter_ids = {e.id for e in selected_emitters}

            # Update detail panel with all selected
            self.emitter_detail.set_emitters(selected_emitters)

            # Update DF geometry
            self._update_df_geometry()

            # Emit signal for map display with extended data
            map_data = []
            for emitter in selected_emitters:
                if emitter.df_result:
                    map_data.append((
                        emitter.df_result.lat,
                        emitter.df_result.lon,
                        emitter.id,
                        emitter.df_result.cep_m,
                        emitter.priority_track,
                        emitter.prosecution_state,
                        True  # is_selected flag
                    ))

            self.emitters_selected_for_map.emit(map_data)
        except Exception as e:
            print(f"[EW] Selection error: {e}")

    def _on_target_requested(self, emitter_id: str):
        """Handle target request from detail panel."""
        if not self._ew_manager:
            return

        try:
            target_data = self._ew_manager.emitter_to_target(emitter_id)
            if target_data:
                self.target_requested.emit(
                    target_data["lat"],
                    target_data["lon"],
                    emitter_id
                )
        except Exception as e:
            print(f"[EW] Target request error: {e}")

    def _on_investigate_requested(self, emitter_id: str):
        """Handle investigate request from detail panel."""
        try:
            if self._ew_manager:
                self._ew_manager.request_df(emitter_id)
            self.investigate_requested.emit(emitter_id)
        except Exception as e:
            print(f"[EW] Investigate request error: {e}")

    def _on_optimize_geometry(self):
        """Handle optimize geometry button - command formation positions."""
        try:
            if not self._ew_manager:
                return

            # Get selected emitter IDs
            selected_emitters = self._get_selected_emitters()
            emitter_ids = [e.id for e in selected_emitters if e.df_result]

            if not emitter_ids:
                # No specific selection - optimize for all tracked
                emitter_ids = None

            # Command optimal formation through EW manager
            success = self._ew_manager.command_optimal_formation(emitter_ids)

            if success:
                print(f"[EW] Formation optimization commanded for {len(emitter_ids) if emitter_ids else 'all tracked'} emitters")
            else:
                print("[EW] No emitters with location data for optimization")

        except Exception as e:
            print(f"[EW] Optimize geometry error: {e}")
