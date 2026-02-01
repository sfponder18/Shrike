# Video Stream Manager
# Handles video feeds from Bird and Chicks via 4G
#
# Integration points:
#   - Bird: Pi 5 → 4G → GCS (RTSP or WebRTC)
#   - Chicks: Pi Zero 2W → WiFi → Bird → 4G → GCS
#
# Dependencies (install when ready):
#   pip install opencv-python
#   pip install av  # For RTSP

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QImage
from dataclasses import dataclass
from typing import Optional, Dict
import time


@dataclass
class StreamConfig:
    """Configuration for a video stream."""
    url: str                    # RTSP URL or other stream source
    name: str                   # Display name
    resolution: tuple = (1920, 1080)
    fps: int = 30


class VideoManager(QObject):
    """
    Manages video streams from swarm vehicles.

    Stream paths:
        Bird:   Pi 5 camera → GStreamer → RTSP → 4G → GCS
        Chick1: Pi camera → WiFi → Bird Pi 5 → relay → 4G → GCS
        Chick2: Pi camera → WiFi → Bird Pi 5 → relay → 4G → GCS

    Expected RTSP URLs (configure in Bird's Pi 5):
        Bird:   rtsp://<tailscale_ip>:8554/bird
        Chick1: rtsp://<tailscale_ip>:8554/chick1
        Chick2: rtsp://<tailscale_ip>:8554/chick2

    Usage:
        manager = VideoManager()
        manager.frame_received.connect(on_frame)
        manager.configure_stream("bird", "rtsp://100.x.x.x:8554/bird")
        manager.start_stream("bird")
    """

    # Signals
    frame_received = pyqtSignal(str, object)    # source_id, QImage
    stream_started = pyqtSignal(str)            # source_id
    stream_stopped = pyqtSignal(str)            # source_id
    stream_error = pyqtSignal(str, str)         # source_id, error message

    def __init__(self, parent=None):
        super().__init__(parent)

        self._streams: Dict[str, StreamConfig] = {}
        self._active_stream: Optional[str] = None
        self._capture = None  # cv2.VideoCapture

        # Simulation
        self._simulation_mode = True
        self._sim_timer = QTimer()
        self._sim_timer.timeout.connect(self._simulate_frame)
        self._frame_count = 0

    # ==================== Configuration ====================

    def configure_stream(self, source_id: str, url: str, name: str = None):
        """
        Configure a video stream source.

        Args:
            source_id: "bird", "chick1", or "chick2"
            url: RTSP URL or stream path
            name: Display name (defaults to source_id)
        """
        self._streams[source_id] = StreamConfig(
            url=url,
            name=name or source_id.upper()
        )
        print(f"[Video] Configured stream: {source_id} -> {url}")

    def configure_defaults(self, tailscale_ip: str):
        """
        Configure default streams using Tailscale IP.

        Args:
            tailscale_ip: Bird's Tailscale IP (e.g., "100.64.0.1")
        """
        from ..config import SWARM_CONFIG

        # Configure streams for all birds (only birds have cameras for now)
        for bird in SWARM_CONFIG["birds"]:
            vid = bird["id"]
            name = bird["name"]
            self.configure_stream(vid, f"rtsp://{tailscale_ip}:8554/{vid}", name)

    # ==================== Stream Control ====================

    def start_stream(self, source_id: str) -> bool:
        """
        Start receiving video from a source.

        Args:
            source_id: Stream to start

        TODO: Implement with OpenCV
            import cv2
            config = self._streams[source_id]
            self._capture = cv2.VideoCapture(config.url)
            # Start capture thread
        """
        if source_id not in self._streams:
            print(f"[Video] Unknown source: {source_id}")
            return False

        print(f"[Video] Start stream: {source_id}")
        self._active_stream = source_id

        if self._simulation_mode:
            self._sim_timer.start(33)  # ~30 fps
            self.stream_started.emit(source_id)
            return True

        # TODO: Real implementation
        return False

    def stop_stream(self, source_id: str = None):
        """Stop video stream."""
        source_id = source_id or self._active_stream
        print(f"[Video] Stop stream: {source_id}")

        if self._capture:
            self._capture.release()
            self._capture = None

        self._sim_timer.stop()
        self._active_stream = None

        if source_id:
            self.stream_stopped.emit(source_id)

    def switch_stream(self, source_id: str) -> bool:
        """Switch to a different video source."""
        if self._active_stream:
            self.stop_stream()
        return self.start_stream(source_id)

    # ==================== Status ====================

    @property
    def active_source(self) -> Optional[str]:
        """Get currently active stream source."""
        return self._active_stream

    def is_streaming(self) -> bool:
        """Check if actively receiving video."""
        return self._active_stream is not None

    def get_stream_info(self, source_id: str) -> Optional[StreamConfig]:
        """Get stream configuration."""
        return self._streams.get(source_id)

    # ==================== Simulation ====================

    def start_simulation(self):
        """Start simulated video for development."""
        from ..config import SWARM_CONFIG

        self._simulation_mode = True

        # Configure simulated streams for all birds
        for bird in SWARM_CONFIG["birds"]:
            vid = bird["id"]
            name = bird["name"]
            self.configure_stream(vid, f"sim://{vid}", f"{name} (Sim)")

    def stop_simulation(self):
        """Stop video simulation."""
        self._sim_timer.stop()
        self._simulation_mode = False

    def _simulate_frame(self):
        """Generate simulated video frame."""
        if not self._active_stream:
            return

        self._frame_count += 1

        # Create a simple test pattern image
        width, height = 640, 360

        # Create QImage with test pattern
        from PyQt5.QtGui import QImage, QPainter, QColor, QFont
        from PyQt5.QtCore import Qt

        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(QColor(10, 10, 30))

        painter = QPainter(image)
        painter.setPen(QColor(64, 64, 96))

        # Grid
        for x in range(0, width, 40):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, 40):
            painter.drawLine(0, y, width, y)

        # Center crosshair
        painter.setPen(QColor(100, 200, 100))
        cx, cy = width // 2, height // 2
        painter.drawLine(cx - 30, cy, cx + 30, cy)
        painter.drawLine(cx, cy - 30, cx, cy + 30)
        painter.drawEllipse(cx - 50, cy - 50, 100, 100)

        # Text overlay
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Consolas", 12))
        painter.drawText(10, 25, f"{self._active_stream.upper()} - SIMULATED")
        painter.drawText(10, 45, f"Frame: {self._frame_count}")
        painter.drawText(10, height - 10, "NO SIGNAL - Connect video source")

        painter.end()

        self.frame_received.emit(self._active_stream, image)
