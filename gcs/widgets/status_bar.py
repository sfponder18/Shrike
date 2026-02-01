# Link Status Bar for SwarmDrones GCS
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class StatusIndicator(QWidget):
    """Individual status indicator with label and icon."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.label = QLabel(label)
        self.label.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(self.label)

        self.indicator = QLabel("○")
        self.indicator.setStyleSheet("color: #404060;")
        layout.addWidget(self.indicator)

    def set_status(self, connected: bool, rssi: int = None):
        """Update status. rssi is optional signal strength."""
        if connected:
            self.indicator.setText("●")
            self.indicator.setStyleSheet("color: #4ade80;")
            if rssi is not None:
                self.label.setStyleSheet("color: #e0e0e0;")
        else:
            self.indicator.setText("●")
            self.indicator.setStyleSheet("color: #f87171;")
            self.label.setStyleSheet("color: #a0a0a0;")

    def set_rssi(self, rssi: int):
        """Update with RSSI value."""
        self.label.setText(f"{self.label.text().split()[0]} {rssi}")


class MeshIndicator(QWidget):
    """Mesh network status indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.mesh_label = QLabel("MESH:")
        self.mesh_label.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(self.mesh_label)

        # Individual node indicators
        self.nodes = {}
        for name in ["Bird", "C1", "C2"]:
            node_layout = QHBoxLayout()
            node_layout.setSpacing(2)

            label = QLabel(name)
            label.setStyleSheet("color: #808080;")
            node_layout.addWidget(label)

            rssi = QLabel("--")
            rssi.setStyleSheet("color: #808080;")
            node_layout.addWidget(rssi)

            indicator = QLabel("○")
            indicator.setStyleSheet("color: #404060;")
            node_layout.addWidget(indicator)

            self.nodes[name] = {"label": label, "rssi": rssi, "indicator": indicator}
            layout.addLayout(node_layout)

    def update_node(self, name: str, connected: bool, rssi: int = None):
        """Update a node's status."""
        if name not in self.nodes:
            return

        node = self.nodes[name]
        if connected:
            node["indicator"].setText("●")
            node["indicator"].setStyleSheet("color: #4ade80;")
            node["label"].setStyleSheet("color: #e0e0e0;")
            if rssi is not None:
                node["rssi"].setText(str(rssi))
                node["rssi"].setStyleSheet("color: #a0a0a0;")
        else:
            node["indicator"].setText("●")
            node["indicator"].setStyleSheet("color: #f87171;")
            node["label"].setStyleSheet("color: #808080;")
            node["rssi"].setText("--")
            node["rssi"].setStyleSheet("color: #808080;")


class StatusBar(QFrame):
    """Full status bar with all link indicators."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setFixedHeight(32)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(24)

        # Mesh status
        self.mesh = MeshIndicator()
        layout.addWidget(self.mesh)

        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #3a3a5a;")
        layout.addWidget(sep1)

        # MLRS status
        self.mlrs = StatusIndicator("MLRS:")
        layout.addWidget(self.mlrs)

        # 4G status
        self.lte = StatusIndicator("4G:")
        layout.addWidget(self.lte)

        # ELRS status
        self.elrs = StatusIndicator("ELRS:")
        layout.addWidget(self.elrs)

        layout.addStretch()

        # Time
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.time_label)

    def update_mesh(self, bird: tuple = None, c1: tuple = None, c2: tuple = None):
        """Update mesh status. Each tuple is (connected, rssi)."""
        if bird:
            self.mesh.update_node("Bird", bird[0], bird[1] if len(bird) > 1 else None)
        if c1:
            self.mesh.update_node("C1", c1[0], c1[1] if len(c1) > 1 else None)
        if c2:
            self.mesh.update_node("C2", c2[0], c2[1] if len(c2) > 1 else None)

    def update_links(self, mlrs: bool, lte: bool, elrs: bool):
        """Update link status indicators."""
        self.mlrs.set_status(mlrs)
        self.lte.set_status(lte)
        self.elrs.set_status(elrs)

    def update_time(self, time_str: str):
        """Update time display."""
        self.time_label.setText(time_str)
