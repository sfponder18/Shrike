# Video Feed Widget for SwarmDrones GCS
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QFrame, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont
import time


class VideoDisplay(QLabel):
    """Video display area with overlay support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 180)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #0a0a1a; border: 1px solid #3a3a5a;")

        # Overlay info
        self.vehicle_name = "BIRD"
        self.recording = False
        self.timestamp = ""

        # Placeholder
        self._draw_placeholder()

    def _draw_placeholder(self):
        """Draw placeholder when no video."""
        pixmap = QPixmap(640, 360)
        pixmap.fill(QColor("#0a0a1a"))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#404060"))

        # Center text
        font = QFont("Consolas", 14)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "NO VIDEO FEED")

        # Border
        painter.drawRect(0, 0, pixmap.width()-1, pixmap.height()-1)

        # Crosshair
        cx, cy = pixmap.width()//2, pixmap.height()//2
        painter.drawLine(cx-20, cy, cx+20, cy)
        painter.drawLine(cx, cy-20, cx, cy+20)

        painter.end()
        self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_frame(self, frame: QImage):
        """Set video frame."""
        if frame:
            pixmap = QPixmap.fromImage(frame)
            self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self._draw_placeholder()

    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        if self.pixmap():
            self._draw_placeholder()


class VideoWidget(QFrame):
    """Video feed widget with source selection."""

    source_changed = pyqtSignal(str)  # vehicle_id
    fullscreen_toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._current_source = "bird"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header with source selector
        header = QHBoxLayout()

        title = QLabel("VIDEO FEED")
        title.setObjectName("header")
        header.addWidget(title)

        self.source_combo = QComboBox()
        self.source_combo.addItems(["Bird", "Chick 1", "Chick 2"])
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        header.addWidget(self.source_combo)

        layout.addLayout(header)

        # Video display
        self.display = VideoDisplay()
        layout.addWidget(self.display, 1)

        # Controls
        ctrl_layout = QHBoxLayout()

        expand_btn = QPushButton("Expand (V)")
        expand_btn.clicked.connect(self.fullscreen_toggled.emit)
        ctrl_layout.addWidget(expand_btn)

        ctrl_layout.addStretch()

        self.status_label = QLabel("Waiting for stream...")
        self.status_label.setStyleSheet("color: #808080;")
        ctrl_layout.addWidget(self.status_label)

        layout.addLayout(ctrl_layout)

    def _on_source_changed(self, text: str):
        """Handle source selection change."""
        source_map = {"Bird": "bird", "Chick 1": "chick1", "Chick 2": "chick2"}
        source = source_map.get(text, "bird")
        self._current_source = source
        self.source_changed.emit(source)
        self.display._draw_placeholder()
        self.status_label.setText(f"Switching to {text}...")

    def cycle_source(self):
        """Cycle to next video source."""
        current = self.source_combo.currentIndex()
        next_idx = (current + 1) % self.source_combo.count()
        self.source_combo.setCurrentIndex(next_idx)

    def set_frame(self, frame: QImage):
        """Update video frame."""
        self.display.set_frame(frame)
        self.status_label.setText("Live")
        self.status_label.setStyleSheet("color: #4ade80;")

    def set_disconnected(self):
        """Show disconnected state."""
        self.display._draw_placeholder()
        self.status_label.setText("No signal")
        self.status_label.setStyleSheet("color: #f87171;")
