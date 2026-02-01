# Map Widget for SwarmDrones GCS
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def bearing_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing in degrees from point 1 to point 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


class MapCanvas(QWidget):
    """Canvas for drawing the map and vehicle positions."""

    target_added = pyqtSignal(float, float)  # lat, lon
    bullseye_set = pyqtSignal(float, float)  # lat, lon
    investigate_requested = pyqtSignal(float, float)  # lat, lon - send vehicle here
    mission_click = pyqtSignal(float, float)  # lat, lon - for mission waypoint add
    waypoint_right_clicked = pyqtSignal(int, float, float)  # wp_id, lat, lon
    view_mission_requested = pyqtSignal(str)  # vehicle_id - request to show vehicle's mission

    # Entity-specific signals
    vehicle_action_requested = pyqtSignal(str, str)  # vehicle_id, action (fly_to, select, center)
    target_action_requested = pyqtSignal(str, str)  # target_id, action (fly_to, remove, assign_orb)
    emitter_action_requested = pyqtSignal(str, str)  # emitter_id, action (prosecute, add_target, investigate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setFocusPolicy(Qt.StrongFocus)

        # View state
        self.center_lat = 52.0
        self.center_lon = -1.5
        self.zoom = 15

        # Data
        self.vehicles = {}      # id -> (lat, lon, heading, icon, name, selected, alt, speed, is_attached)
        self.targets = {}       # id -> (lat, lon, assigned_orb)
        self.mission_waypoints = {}  # id -> (lat, lon, type)
        self.ew_emitters = {}   # id -> (lat, lon, cep_m) - EW emitter positions

        # Bullseye
        self.bullseye_lat = None
        self.bullseye_lon = None
        self.bullseye_name = "BULLSEYE"

        # Interaction
        self.dragging = False
        self.last_mouse_pos = None
        self._right_click_pos = None

        # Mouse tracking for cursor BRAA
        self._mouse_lat = None
        self._mouse_lon = None

        # Measure tool
        self._measure_start = None  # (lat, lon) or None
        self._measuring = False

        # Mission click mode
        self._mission_mode = False

        # Leg hover info
        self._hovered_leg = None  # (leg_idx, wp1_data, wp2_data) or None
        self._mission_vehicle_id = "bird"  # Vehicle for leg estimates

    def set_vehicles(self, vehicles: dict):
        """Update vehicle positions. vehicles: {id: (lat, lon, heading, icon, name, selected, alt, speed)}"""
        self.vehicles = vehicles
        self.update()

    def set_targets(self, targets: dict):
        """Update target positions."""
        self.targets = targets
        self.update()

    def set_mission_waypoints(self, waypoints: dict):
        """Update mission waypoint positions. waypoints: {id: (lat, lon, type)}"""
        self.mission_waypoints = waypoints
        self.update()

    def set_ew_emitters(self, emitters: list):
        """Update EW emitter positions.

        emitters: [(lat, lon, id, cep_m), ...] or
                  [(lat, lon, id, cep_m, priority, state, selected), ...]
        """
        self.ew_emitters = {}
        for emitter_data in emitters:
            if len(emitter_data) >= 4:
                lat, lon, emitter_id, cep_m = emitter_data[:4]
                priority = emitter_data[4] if len(emitter_data) > 4 else False
                state = emitter_data[5] if len(emitter_data) > 5 else None
                selected = emitter_data[6] if len(emitter_data) > 6 else False
                self.ew_emitters[emitter_id] = (lat, lon, cep_m, priority, state, selected)
        self.update()

    def clear_ew_emitters(self):
        """Clear all EW emitter markers."""
        self.ew_emitters = {}
        self.update()

    def set_mission_vehicle(self, vehicle_id: str):
        """Set the vehicle ID for mission leg estimates."""
        self._mission_vehicle_id = vehicle_id

    def set_mission_mode(self, enabled: bool):
        """Enable/disable mission waypoint click mode."""
        self._mission_mode = enabled
        if enabled:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def set_bullseye(self, lat: float, lon: float, name: str = "BULLSEYE"):
        """Set the bullseye reference point."""
        self.bullseye_lat = lat
        self.bullseye_lon = lon
        self.bullseye_name = name
        self.update()

    def clear_bullseye(self):
        """Clear the bullseye."""
        self.bullseye_lat = None
        self.bullseye_lon = None
        self.update()

    def center_on(self, lat: float, lon: float):
        """Center map on coordinates."""
        self.center_lat = lat
        self.center_lon = lon
        self.update()

    def center_on_vehicle(self, vehicle_id: str = None):
        """Center map on a vehicle. If vehicle_id is None, center on selected vehicle."""
        for vid, data in self.vehicles.items():
            if len(data) >= 6:
                lat, lon = data[0], data[1]
                selected = data[5] if len(data) > 5 else False

                # Center on specific vehicle or selected vehicle
                if vehicle_id is None and selected:
                    self.center_on(lat, lon)
                    return True
                elif vehicle_id == vid:
                    self.center_on(lat, lon)
                    return True
        return False

    def center_on_all_vehicles(self):
        """Center map to show all vehicles."""
        if not self.vehicles:
            return

        lats = []
        lons = []
        for vid, data in self.vehicles.items():
            if len(data) >= 2:
                lats.append(data[0])
                lons.append(data[1])

        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            self.center_on(center_lat, center_lon)

    def zoom_in(self):
        self.zoom = min(20, self.zoom + 1)
        self.update()

    def zoom_out(self):
        self.zoom = max(5, self.zoom - 1)
        self.update()

    def lat_lon_to_screen(self, lat: float, lon: float) -> QPointF:
        """Convert lat/lon to screen coordinates."""
        scale = 2 ** self.zoom * 10
        x = self.width() / 2 + (lon - self.center_lon) * scale
        y = self.height() / 2 - (lat - self.center_lat) * scale
        return QPointF(x, y)

    def screen_to_lat_lon(self, x: float, y: float) -> tuple[float, float]:
        """Convert screen coordinates to lat/lon."""
        scale = 2 ** self.zoom * 10
        lon = self.center_lon + (x - self.width() / 2) / scale
        lat = self.center_lat - (y - self.height() / 2) / scale
        return lat, lon

    def get_selected_vehicle_braa(self) -> tuple:
        """Get BRAA from selected vehicle to bullseye. Returns (bearing, range_m, alt, aspect) or None."""
        if self.bullseye_lat is None:
            return None

        for vid, data in self.vehicles.items():
            if len(data) >= 9:
                lat, lon, heading, icon, name, selected, alt, speed, is_attached = data
            elif len(data) >= 8:
                lat, lon, heading, icon, name, selected, alt, speed = data[:8]
            else:
                lat, lon, heading, icon, name, selected = data[:6]
                alt, speed = 0, 0

            if selected:
                bearing = bearing_between(lat, lon, self.bullseye_lat, self.bullseye_lon)
                range_m = haversine_distance(lat, lon, self.bullseye_lat, self.bullseye_lon)
                return (bearing, range_m, alt, heading)

        return None

    def get_cursor_braa(self) -> tuple:
        """Get BRAA from bullseye to cursor. Returns (bearing, range_m) or None."""
        if self.bullseye_lat is None or self._mouse_lat is None:
            return None

        bearing = bearing_between(self.bullseye_lat, self.bullseye_lon, self._mouse_lat, self._mouse_lon)
        range_m = haversine_distance(self.bullseye_lat, self.bullseye_lon, self._mouse_lat, self._mouse_lon)
        return (bearing, range_m)

    def paintEvent(self, event):
        """Draw the map."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#1a1a2e"))

        # Grid
        self._draw_grid(painter)

        # Bullseye
        self._draw_bullseye(painter)

        # Mission waypoints
        self._draw_mission(painter)

        # EW Emitters
        self._draw_ew_emitters(painter)

        # Targets
        self._draw_targets(painter)

        # Vehicles
        self._draw_vehicles(painter)

        # Measure line
        self._draw_measure(painter)

        # Scale indicator
        self._draw_scale(painter)

        # BRAA display
        self._draw_braa(painter)

        # Leg info tooltip (when hovering over mission leg)
        self._draw_leg_info(painter)

    def _draw_grid(self, painter: QPainter):
        """Draw coordinate grid."""
        painter.setPen(QPen(QColor("#2a2a4a"), 1))

        grid_spacing = 0.01 / (2 ** (self.zoom - 10))

        lon_start = self.center_lon - 0.1
        lon_end = self.center_lon + 0.1
        lon = round(lon_start / grid_spacing) * grid_spacing
        while lon < lon_end:
            pt = self.lat_lon_to_screen(self.center_lat, lon)
            if 0 <= pt.x() <= self.width():
                painter.drawLine(int(pt.x()), 0, int(pt.x()), self.height())
            lon += grid_spacing

        lat_start = self.center_lat - 0.1
        lat_end = self.center_lat + 0.1
        lat = round(lat_start / grid_spacing) * grid_spacing
        while lat < lat_end:
            pt = self.lat_lon_to_screen(lat, self.center_lon)
            if 0 <= pt.y() <= self.height():
                painter.drawLine(0, int(pt.y()), self.width(), int(pt.y()))
            lat += grid_spacing

    def _draw_bullseye(self, painter: QPainter):
        """Draw bullseye reference point."""
        if self.bullseye_lat is None:
            return

        pt = self.lat_lon_to_screen(self.bullseye_lat, self.bullseye_lon)
        color = QColor("#ff00ff")  # Magenta

        # Draw concentric rings
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.NoBrush)
        for radius in [10, 25, 45]:
            painter.drawEllipse(pt, radius, radius)

        # Draw crosshair
        painter.drawLine(int(pt.x()) - 50, int(pt.y()), int(pt.x()) + 50, int(pt.y()))
        painter.drawLine(int(pt.x()), int(pt.y()) - 50, int(pt.x()), int(pt.y()) + 50)

        # Label
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.setPen(QPen(color, 1))
        painter.drawText(int(pt.x()) + 55, int(pt.y()) + 4, self.bullseye_name)

    def _draw_ew_emitters(self, painter: QPainter):
        """Draw EW emitter markers - clean diamond symbology."""
        if not self.ew_emitters:
            return

        font = QFont("Consolas", 9, QFont.Bold)
        painter.setFont(font)

        for emitter_id, emitter_data in self.ew_emitters.items():
            # Unpack data: (lat, lon, cep_m, priority, state, selected)
            lat = emitter_data[0]
            lon = emitter_data[1]
            cep_m = emitter_data[2]
            priority = emitter_data[3] if len(emitter_data) > 3 else False
            state = emitter_data[4] if len(emitter_data) > 4 else None
            is_selected = emitter_data[5] if len(emitter_data) > 5 else False

            pt = self.lat_lon_to_screen(lat, lon)

            # Color scheme - red for hostile, orange for unknown
            if state == "PROSECUTING":
                color = QColor("#ef4444")  # Red
            elif priority or state in ["LOCATING", "QUEUED"]:
                color = QColor("#f97316")  # Orange
            else:
                color = QColor("#eab308")  # Yellow

            # Draw CEP circle
            if cep_m > 0:
                scale = 2 ** self.zoom * 10
                cep_degrees = cep_m / 111000.0
                cep_pixels = max(15, cep_degrees * scale)

                painter.setPen(QPen(color, 1, Qt.DashLine))
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 30)))
                painter.drawEllipse(pt, int(cep_pixels), int(cep_pixels))

            # Draw diamond marker (hostile symbol)
            size = 8
            diamond = [
                (pt.x(), pt.y() - size),      # Top
                (pt.x() + size, pt.y()),      # Right
                (pt.x(), pt.y() + size),      # Bottom
                (pt.x() - size, pt.y()),      # Left
            ]

            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 100)))

            from PyQt5.QtGui import QPolygonF
            from PyQt5.QtCore import QPointF
            poly = QPolygonF([QPointF(x, y) for x, y in diamond])
            painter.drawPolygon(poly)

            # Selection ring if selected
            if is_selected:
                painter.setPen(QPen(QColor("#ffffff"), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(pt, 14, 14)
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(pt, 14, 14)

            # Label
            metrics = painter.fontMetrics()
            label_text = emitter_id[-8:]  # Last 8 chars
            if priority:
                label_text = "! " + label_text

            label_x = int(pt.x()) + 12
            label_y = int(pt.y()) + 4

            # Background
            text_width = metrics.horizontalAdvance(label_text)
            painter.fillRect(label_x - 2, label_y - metrics.height() + 2,
                           text_width + 4, metrics.height() + 2,
                           QColor(0, 0, 0, 180))
            painter.setPen(QPen(color, 1))
            painter.drawText(label_x, label_y, label_text)

            # CEP below label
            if cep_m > 0 and cep_m < 500:
                cep_text = f"{cep_m:.0f}m"
                painter.setPen(QPen(QColor("#9ca3af"), 1))
                painter.drawText(label_x, label_y + metrics.height(), cep_text)

    def _draw_mission(self, painter: QPainter):
        """Draw mission waypoints and connecting lines."""
        if not self.mission_waypoints:
            return

        font = QFont("Consolas", 9)
        painter.setFont(font)

        # Sort by key (which is the list index) for correct order
        sorted_wps = sorted(self.mission_waypoints.items(), key=lambda x: x[0])
        points = []
        self._wp_positions = {}  # Store positions for click detection

        for idx, wp_data in sorted_wps:
            # Handle formats: (lat, lon, type, id), (lat, lon, type, id, alt), (lat, lon, type, id, alt, speed)
            if len(wp_data) >= 6:
                lat, lon, wp_type, wp_id, alt, speed = wp_data[:6]
            elif len(wp_data) >= 5:
                lat, lon, wp_type, wp_id, alt = wp_data[:5]
                speed = 0
            else:
                lat, lon, wp_type, wp_id = wp_data[:4]
                alt, speed = 0, 0
            pt = self.lat_lon_to_screen(lat, lon)
            points.append((pt, wp_id))
            self._wp_positions[wp_id] = pt

            # Color based on waypoint type
            if wp_type == "LAUNCH_CHICK":
                color = QColor("#dc2626")  # Red for launch
                size = 12
            elif wp_type == "TARGET":
                color = QColor("#f97316")  # Orange for target
                size = 10
            elif wp_type == "LOITER" or wp_type == "LOITER_TIME":
                color = QColor("#60a5fa")  # Blue
                size = 8
            elif wp_type == "RTL":
                color = QColor("#facc15")  # Yellow
                size = 8
            else:
                color = QColor("#22c55e")  # Green
                size = 8

            # Draw waypoint marker
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color.darker(150)))

            if wp_type == "LAUNCH_CHICK":
                # Draw star for launch points
                self._draw_star(painter, pt, size, color)
            elif wp_type == "TARGET":
                # Draw crosshair for targets
                painter.drawEllipse(pt, size, size)
                painter.drawLine(int(pt.x()) - size - 3, int(pt.y()),
                               int(pt.x()) + size + 3, int(pt.y()))
                painter.drawLine(int(pt.x()), int(pt.y()) - size - 3,
                               int(pt.x()), int(pt.y()) + size + 3)
            else:
                # Draw diamond for regular waypoints
                diamond = QPolygonF([
                    QPointF(pt.x(), pt.y() - size),
                    QPointF(pt.x() + size, pt.y()),
                    QPointF(pt.x(), pt.y() + size),
                    QPointF(pt.x() - size, pt.y()),
                ])
                painter.drawPolygon(diamond)

            # Draw waypoint number (1-based display)
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawText(int(pt.x()) + size + 4, int(pt.y()) + 4, str(idx + 1))

        # Draw connecting lines and store leg data for hover
        self._leg_data = []  # [(p1, p2, leg_idx, wp1_data, wp2_data), ...]
        if len(points) >= 2:
            painter.setPen(QPen(QColor("#22c55e"), 2, Qt.DashLine))
            for i in range(len(points) - 1):
                p1, wp1_id = points[i]
                p2, wp2_id = points[i+1]
                painter.drawLine(
                    int(p1.x()), int(p1.y()),
                    int(p2.x()), int(p2.y())
                )
                # Store leg info for hover detection
                # wp_data format: (lat, lon, type, id, alt) or (lat, lon, type, id)
                wp1_data = sorted_wps[i][1]
                wp2_data = sorted_wps[i+1][1]
                self._leg_data.append((p1, p2, i, wp1_data, wp2_data))

    def get_waypoint_at(self, x: float, y: float, threshold: float = 15) -> int:
        """Get waypoint ID at screen position, or -1 if none."""
        if not hasattr(self, '_wp_positions'):
            return -1

        for wp_id, pt in self._wp_positions.items():
            dist = ((pt.x() - x) ** 2 + (pt.y() - y) ** 2) ** 0.5
            if dist < threshold:
                return wp_id
        return -1

    def get_leg_at(self, x: float, y: float, threshold: float = 10) -> tuple:
        """
        Get mission leg at screen position.

        Returns:
            (leg_index, wp1_data, wp2_data) or None if not hovering over a leg
        """
        if not hasattr(self, '_leg_data') or not self._leg_data:
            return None

        for p1, p2, leg_idx, wp1_data, wp2_data in self._leg_data:
            # Calculate distance from point to line segment
            dist = self._point_to_line_dist(x, y, p1.x(), p1.y(), p2.x(), p2.y())
            if dist < threshold:
                return (leg_idx, wp1_data, wp2_data)
        return None

    def _point_to_line_dist(self, px: float, py: float,
                            x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate perpendicular distance from point to line segment."""
        # Vector from p1 to p2
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            # p1 and p2 are the same point
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # Parameter t for closest point on line
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))

        # Closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    def _draw_star(self, painter: QPainter, center: QPointF, size: float, color: QColor):
        """Draw a star shape for launch waypoints."""
        import math
        points = []
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            r = size if i % 2 == 0 else size / 2
            x = center.x() + r * math.cos(angle)
            y = center.y() + r * math.sin(angle)
            points.append(QPointF(x, y))

        star = QPolygonF(points)
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color.darker(150)))
        painter.drawPolygon(star)

    def _draw_targets(self, painter: QPainter):
        """Draw target markers."""
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)

        for tid, target_data in self.targets.items():
            # Handle both old (lat, lon, assigned) and new (lat, lon, assigned, is_ew) formats
            if len(target_data) >= 4:
                lat, lon, assigned, is_ew = target_data[:4]
            else:
                lat, lon, assigned = target_data[:3]
                is_ew = False

            pt = self.lat_lon_to_screen(lat, lon)

            if assigned:
                color = QColor("#f97316")  # Orange - assigned
            elif is_ew:
                color = QColor("#a855f7")  # Purple - EW target
            else:
                color = QColor("#ef4444")  # Red - unassigned

            # Draw EW diamond symbol for EW targets
            if is_ew:
                # Draw diamond (EW symbol)
                size = 10
                diamond = [
                    (pt.x(), pt.y() - size),      # Top
                    (pt.x() + size, pt.y()),      # Right
                    (pt.x(), pt.y() + size),      # Bottom
                    (pt.x() - size, pt.y()),      # Left
                ]
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 100)))
                poly = QPolygonF([QPointF(x, y) for x, y in diamond])
                painter.drawPolygon(poly)

                # Draw inner target circle
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color.darker(150)))
                painter.drawEllipse(pt, 5, 5)

                # Label with EW indicator
                painter.setPen(QPen(QColor("#ffffff"), 1))
                painter.drawText(int(pt.x()) + 14, int(pt.y()) + 4, f"EW◎{tid}")
            else:
                # Standard target circle
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color.darker(150)))
                painter.drawEllipse(pt, 8, 8)

                painter.setPen(QPen(QColor("#ffffff"), 1))
                painter.drawText(int(pt.x()) + 12, int(pt.y()) + 4, f"◎{tid}")

    def _draw_vehicles(self, painter: QPainter):
        """Draw vehicle icons with altitude/speed labels."""
        # First pass: draw launched/independent vehicles
        # Second pass: draw attached indicators on Bird
        attached_to_bird = []

        for vid, data in self.vehicles.items():
            # Unpack data (handle both old and new format)
            if len(data) >= 9:
                lat, lon, heading, icon, name, selected, alt, speed, is_attached = data
            elif len(data) >= 8:
                lat, lon, heading, icon, name, selected, alt, speed = data
                is_attached = False
            else:
                lat, lon, heading, icon, name, selected = data[:6]
                alt, speed = 0, 0
                is_attached = False

            # Skip attached chicks in main drawing - we'll draw indicators later
            if is_attached:
                attached_to_bird.append((vid, name, selected))
                continue

            pt = self.lat_lon_to_screen(lat, lon)

            # Color and size based on selection
            if selected:
                color = QColor("#4ade80")  # Green
                size = 14
            else:
                color = QColor("#60a5fa")  # Blue
                size = 12

            # Draw altitude/speed label ABOVE the aircraft
            painter.setFont(QFont("Consolas", 8))
            label_text = f"{alt:.0f}m {speed:.0f}m/s"
            painter.setPen(QPen(QColor("#ffffff"), 1))

            # Background for readability
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(label_text)
            text_height = metrics.height()
            label_x = int(pt.x()) - text_width // 2
            label_y = int(pt.y()) - size - 18

            painter.fillRect(label_x - 2, label_y - text_height + 2, text_width + 4, text_height + 2,
                           QColor(26, 26, 46, 200))
            painter.drawText(label_x, label_y, label_text)

            # Draw direction indicator (triangle)
            painter.save()
            painter.translate(pt)
            painter.rotate(heading)

            triangle = QPolygonF([
                QPointF(0, -size),
                QPointF(-size/2, size/2),
                QPointF(size/2, size/2),
            ])

            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color.darker(150)))
            painter.drawPolygon(triangle)
            painter.restore()

            # Name label to the right
            painter.setFont(QFont("Consolas", 9))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawText(int(pt.x()) + 15, int(pt.y()) + 4, name)

            # Draw attached chick indicators near Bird
            if vid == "bird" and attached_to_bird:
                self._draw_attached_indicators(painter, pt, attached_to_bird)

    def _draw_attached_indicators(self, painter: QPainter, bird_pt: QPointF,
                                   attached: list):
        """Draw small indicators for attached chicks near the Bird icon."""
        painter.setFont(QFont("Consolas", 7))

        for i, (chick_id, name, selected) in enumerate(attached):
            # Position indicators to the left of Bird
            offset_x = -30 - (i * 25)
            offset_y = 5

            ix = int(bird_pt.x()) + offset_x
            iy = int(bird_pt.y()) + offset_y

            # Draw small hexagon indicator
            if selected:
                color = QColor("#facc15")  # Yellow when selected
            else:
                color = QColor("#808080")  # Gray when not selected

            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color.darker(150)))

            # Small hexagon
            hex_size = 6
            hexagon = QPolygonF([
                QPointF(ix + hex_size, iy),
                QPointF(ix + hex_size/2, iy - hex_size*0.866),
                QPointF(ix - hex_size/2, iy - hex_size*0.866),
                QPointF(ix - hex_size, iy),
                QPointF(ix - hex_size/2, iy + hex_size*0.866),
                QPointF(ix + hex_size/2, iy + hex_size*0.866),
            ])
            painter.drawPolygon(hexagon)

            # Label
            painter.setPen(QPen(color, 1))
            painter.drawText(ix - 8, iy + 18, name)

    def _draw_measure(self, painter: QPainter):
        """Draw measure line from start point to cursor."""
        if not self._measuring or self._measure_start is None:
            return
        if self._mouse_lat is None:
            return

        start_lat, start_lon = self._measure_start
        start_pt = self.lat_lon_to_screen(start_lat, start_lon)
        end_pt = self.lat_lon_to_screen(self._mouse_lat, self._mouse_lon)

        # Draw line
        painter.setPen(QPen(QColor("#00ffff"), 2, Qt.DashLine))
        painter.drawLine(int(start_pt.x()), int(start_pt.y()), int(end_pt.x()), int(end_pt.y()))

        # Draw endpoints
        painter.setBrush(QBrush(QColor("#00ffff")))
        painter.drawEllipse(start_pt, 5, 5)
        painter.drawEllipse(end_pt, 5, 5)

        # Calculate and display measurement
        bearing = bearing_between(start_lat, start_lon, self._mouse_lat, self._mouse_lon)
        distance = haversine_distance(start_lat, start_lon, self._mouse_lat, self._mouse_lon)

        if distance > 1000:
            dist_str = f"{distance/1000:.2f} km"
        else:
            dist_str = f"{distance:.0f} m"

        measure_text = f"{bearing:03.0f}° / {dist_str}"

        # Draw label at midpoint
        mid_x = (start_pt.x() + end_pt.x()) / 2
        mid_y = (start_pt.y() + end_pt.y()) / 2

        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(measure_text)

        # Background
        painter.fillRect(int(mid_x) - text_width//2 - 4, int(mid_y) - 20,
                        text_width + 8, 18, QColor(0, 40, 40, 220))

        painter.setPen(QPen(QColor("#00ffff"), 1))
        painter.drawText(int(mid_x) - text_width//2, int(mid_y) - 6, measure_text)

        # Instructions
        painter.setFont(QFont("Consolas", 9))
        painter.setPen(QPen(QColor("#00ffff"), 1))
        hint = "Click to finish measuring, ESC to cancel"
        painter.drawText(10, self.height() - 10, hint)

    def _draw_scale(self, painter: QPainter):
        """Draw scale bar."""
        painter.setPen(QPen(QColor("#808080"), 1))
        painter.setFont(QFont("Consolas", 8))

        scale_pixels = 100
        scale = 2 ** self.zoom * 10
        scale_meters = scale_pixels / scale * 111000

        x, y = 20, self.height() - 30
        painter.drawLine(x, y, x + scale_pixels, y)
        painter.drawLine(x, y - 5, x, y + 5)
        painter.drawLine(x + scale_pixels, y - 5, x + scale_pixels, y + 5)

        if scale_meters > 1000:
            label = f"{scale_meters/1000:.1f} km"
        else:
            label = f"{scale_meters:.0f} m"
        painter.drawText(x, y - 10, label)

    def _draw_braa(self, painter: QPainter):
        """Draw BRAA displays - vehicle to bullseye and cursor from bullseye."""
        if self.bullseye_lat is None:
            return

        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        metrics = painter.fontMetrics()
        line_height = metrics.height() + 4

        lines = []

        # Vehicle BRAA (from selected vehicle to bullseye)
        vehicle_braa = self.get_selected_vehicle_braa()
        if vehicle_braa:
            bearing, range_m, alt, heading = vehicle_braa
            if range_m > 1000:
                range_str = f"{range_m/1000:.1f}km"
            else:
                range_str = f"{range_m:.0f}m"
            lines.append(("AIRCRAFT", f"{bearing:03.0f}° / {range_str}", "#4ade80"))

        # Cursor BRAA (from bullseye to cursor)
        cursor_braa = self.get_cursor_braa()
        if cursor_braa:
            bearing, range_m = cursor_braa
            if range_m > 1000:
                range_str = f"{range_m/1000:.1f}km"
            else:
                range_str = f"{range_m:.0f}m"
            lines.append(("CURSOR", f"{bearing:03.0f}° / {range_str}", "#ff00ff"))

        if not lines:
            return

        # Calculate box size
        max_width = 0
        for label, value, _ in lines:
            text = f"{label}: {value}"
            max_width = max(max_width, metrics.horizontalAdvance(text))

        box_height = len(lines) * line_height + 8
        box_width = max_width + 20

        x = self.width() - box_width - 10
        y = 10

        # Title (no background)
        painter.setPen(QPen(QColor("#ff00ff"), 1))
        painter.drawText(x + 5, y + line_height - 2, "BULLSEYE REF")

        # Lines
        for i, (label, value, color) in enumerate(lines):
            ty = y + (i + 2) * line_height - 2
            painter.setPen(QPen(QColor("#808080"), 1))
            painter.drawText(x + 10, ty, f"{label}:")
            painter.setPen(QPen(QColor(color), 1))
            painter.drawText(x + 80, ty, value)

    def _draw_leg_info(self, painter: QPainter):
        """Draw leg information tooltip when hovering over a mission leg."""
        if self._hovered_leg is None:
            return

        leg_idx, wp1_data, wp2_data = self._hovered_leg

        # Import config functions
        try:
            from ..config import get_vehicle_performance, estimate_leg_time, estimate_leg_battery
        except ImportError:
            return

        # Extract waypoint data (handle formats with alt and speed)
        if len(wp1_data) >= 6:
            lat1, lon1, type1, id1, alt1, speed1 = wp1_data[:6]
        elif len(wp1_data) >= 5:
            lat1, lon1, type1, id1, alt1 = wp1_data[:5]
            speed1 = 0
        else:
            lat1, lon1, type1, id1 = wp1_data[:4]
            alt1, speed1 = 0, 0

        if len(wp2_data) >= 6:
            lat2, lon2, type2, id2, alt2, speed2 = wp2_data[:6]
        elif len(wp2_data) >= 5:
            lat2, lon2, type2, id2, alt2 = wp2_data[:5]
            speed2 = 0
        else:
            lat2, lon2, type2, id2 = wp2_data[:4]
            alt2, speed2 = 0, 0

        # Calculate leg metrics
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        alt_change = alt2 - alt1  # Positive = climbing, negative = descending

        # Use custom speed if set on the destination waypoint, otherwise use defaults
        custom_speed = speed2 if speed2 > 0 else None

        time_sec = estimate_leg_time(self._mission_vehicle_id, distance, alt_change)
        battery_pct = estimate_leg_battery(self._mission_vehicle_id, time_sec)

        # Get vehicle performance for speed info
        perf = get_vehicle_performance(self._mission_vehicle_id)

        # Format display strings
        if distance > 1000:
            dist_str = f"{distance/1000:.2f} km"
        else:
            dist_str = f"{distance:.0f} m"

        time_min = time_sec / 60
        if time_min >= 1:
            time_str = f"{time_min:.1f} min"
        else:
            time_str = f"{time_sec:.0f} sec"

        # Bearing
        bearing = bearing_between(lat1, lon1, lat2, lon2)

        # Build info text
        lines = [
            f"LEG {leg_idx + 1} → {leg_idx + 2}",
            f"Dist: {dist_str}",
            f"Brng: {bearing:.0f}°",
        ]

        # Add altitude change if significant
        if abs(alt_change) > 1:
            if alt_change > 0:
                lines.append(f"Alt: ↑{alt_change:.0f}m")
            else:
                lines.append(f"Alt: ↓{abs(alt_change):.0f}m")

        # If custom speed is set, recalculate time with that speed
        if custom_speed:
            time_sec = distance / custom_speed
            time_min = time_sec / 60
            if time_min >= 1:
                time_str = f"{time_min:.1f} min"
            else:
                time_str = f"{time_sec:.0f} sec"
            battery_pct = estimate_leg_battery(self._mission_vehicle_id, time_sec)
            speed_str = f"Spd: {custom_speed:.0f} m/s (custom)"
        else:
            speed_str = f"Spd: {perf['cruise_speed_ms']:.0f} m/s"

        lines.extend([
            f"Time: {time_str}",
            f"Batt: ~{battery_pct:.1f}%",
            speed_str,
        ])

        # Draw tooltip near cursor
        painter.setFont(QFont("Consolas", 9))
        metrics = painter.fontMetrics()
        line_height = metrics.height() + 2

        max_width = max(metrics.horizontalAdvance(line) for line in lines)
        box_width = max_width + 16
        box_height = len(lines) * line_height + 8

        # Position tooltip near mouse but within screen
        if self._mouse_lat is not None:
            cursor_screen = self.lat_lon_to_screen(self._mouse_lat, self._mouse_lon)
            x = int(cursor_screen.x()) + 15
            y = int(cursor_screen.y()) - box_height // 2
        else:
            x = 100
            y = 100

        # Keep within screen bounds
        x = min(x, self.width() - box_width - 10)
        y = max(10, min(y, self.height() - box_height - 10))

        # Draw background
        painter.fillRect(x, y, box_width, box_height, QColor(26, 26, 46, 240))
        painter.setPen(QPen(QColor("#4ade80"), 1))
        painter.drawRect(x, y, box_width, box_height)

        # Draw lines
        for i, line in enumerate(lines):
            ty = y + 12 + i * line_height
            if i == 0:
                painter.setPen(QPen(QColor("#4ade80"), 1))  # Green header
            else:
                painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawText(x + 8, ty, line)

    def get_vehicle_at(self, x: float, y: float, threshold: float = 20) -> str:
        """Get vehicle ID at screen position, or None if none."""
        for vid, data in self.vehicles.items():
            # Skip attached vehicles (they're shown as indicators, not main icons)
            if len(data) >= 9 and data[8]:  # is_attached
                continue
            lat, lon = data[0], data[1]
            pt = self.lat_lon_to_screen(lat, lon)
            dist = ((pt.x() - x) ** 2 + (pt.y() - y) ** 2) ** 0.5
            if dist < threshold:
                return vid
        return None

    def get_target_at(self, x: float, y: float, threshold: float = 15) -> str:
        """Get target ID at screen position, or None if none."""
        for tid, target_data in self.targets.items():
            lat, lon = target_data[0], target_data[1]
            pt = self.lat_lon_to_screen(lat, lon)
            dist = ((pt.x() - x) ** 2 + (pt.y() - y) ** 2) ** 0.5
            if dist < threshold:
                return tid
        return None

    def get_emitter_at(self, x: float, y: float, threshold: float = 15) -> str:
        """Get EW emitter ID at screen position, or None if none."""
        for eid, emitter_data in self.ew_emitters.items():
            lat, lon = emitter_data[0], emitter_data[1]
            pt = self.lat_lon_to_screen(lat, lon)
            dist = ((pt.x() - x) ** 2 + (pt.y() - y) ** 2) ** 0.5
            if dist < threshold:
                return eid
        return None

    def get_entity_at(self, x: float, y: float) -> tuple:
        """
        Get the entity at screen position with priority ordering.
        Returns: (entity_type, entity_id) or (None, None)
        Priority: vehicle > target > emitter > waypoint
        """
        # Check vehicle first (highest priority)
        vid = self.get_vehicle_at(x, y)
        if vid:
            return ("vehicle", vid)

        # Check target
        tid = self.get_target_at(x, y)
        if tid:
            return ("target", tid)

        # Check emitter
        eid = self.get_emitter_at(x, y)
        if eid:
            return ("emitter", eid)

        # Check waypoint
        wp_id = self.get_waypoint_at(x, y)
        if wp_id >= 0:
            return ("waypoint", wp_id)

        return (None, None)

    def _show_context_menu(self, pos):
        """Show right-click context menu with entity snap detection."""
        # Don't show menu if measuring
        if self._measuring:
            self._cancel_measure()
            return

        self._right_click_pos = pos

        # Use unified entity detection with priority ordering
        entity_type, entity_id = self.get_entity_at(pos.x(), pos.y())

        if entity_type == "vehicle":
            self._show_vehicle_context_menu(pos, entity_id)
            return
        elif entity_type == "target":
            self._show_target_context_menu(pos, entity_id)
            return
        elif entity_type == "emitter":
            self._show_emitter_context_menu(pos, entity_id)
            return
        elif entity_type == "waypoint":
            self._show_waypoint_context_menu(pos, entity_id)
            return

        # No entity clicked - show general menu
        menu = QMenu(self)

        # Investigate (send vehicle here)
        investigate = QAction("Investigate Here", self)
        investigate.triggered.connect(self._investigate_at_click)
        menu.addAction(investigate)

        menu.addSeparator()

        # Target
        add_target = QAction("Add Target Here", self)
        add_target.triggered.connect(self._add_target_at_click)
        menu.addAction(add_target)

        menu.addSeparator()

        # Measure
        measure = QAction("Measure From Here", self)
        measure.triggered.connect(self._start_measure_at_click)
        menu.addAction(measure)

        menu.addSeparator()

        # Bullseye
        set_bullseye = QAction("Set Bullseye Here", self)
        set_bullseye.triggered.connect(self._set_bullseye_at_click)
        menu.addAction(set_bullseye)

        if self.bullseye_lat is not None:
            clear_bullseye = QAction("Clear Bullseye", self)
            clear_bullseye.triggered.connect(self.clear_bullseye)
            menu.addAction(clear_bullseye)

        menu.addSeparator()

        # View
        center_here = QAction("Center Map Here", self)
        center_here.triggered.connect(self._center_at_click)
        menu.addAction(center_here)

        menu.exec_(self.mapToGlobal(pos))

    def _show_vehicle_context_menu(self, pos, vehicle_id: str):
        """Show context menu for a vehicle."""
        menu = QMenu(self)

        # Get vehicle data
        vehicle_data = self.vehicles.get(vehicle_id, {})
        vehicle_name = vehicle_data[4] if len(vehicle_data) > 4 else vehicle_id.upper()
        lat = vehicle_data[0] if len(vehicle_data) > 0 else 0
        lon = vehicle_data[1] if len(vehicle_data) > 1 else 0
        is_selected = vehicle_data[5] if len(vehicle_data) > 5 else False
        is_attached = vehicle_data[8] if len(vehicle_data) > 8 else False

        # Header
        header = QAction(f"{vehicle_name}", self)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        # Select vehicle (if not already selected)
        if not is_selected:
            select_action = QAction(f"Select {vehicle_name}", self)
            select_action.triggered.connect(lambda: self.vehicle_action_requested.emit(vehicle_id, "select"))
            menu.addAction(select_action)

        # View mission path
        view_mission = QAction(f"View Mission Path", self)
        view_mission.triggered.connect(lambda: self.view_mission_requested.emit(vehicle_id))
        menu.addAction(view_mission)

        menu.addSeparator()

        # Fly another vehicle here
        fly_here = QAction("Fly Selected Vehicle Here", self)
        fly_here.triggered.connect(self._investigate_at_click)
        menu.addAction(fly_here)

        # Commands (only for launched/active vehicles)
        if not is_attached:
            menu.addSeparator()

            # RTL
            rtl_action = QAction("Command RTL", self)
            rtl_action.triggered.connect(lambda: self.vehicle_action_requested.emit(vehicle_id, "rtl"))
            menu.addAction(rtl_action)

            # Loiter
            loiter_action = QAction("Command Loiter Here", self)
            loiter_action.triggered.connect(lambda: self.vehicle_action_requested.emit(vehicle_id, "loiter"))
            menu.addAction(loiter_action)

        menu.addSeparator()

        # Center on vehicle
        center_action = QAction(f"Center on {vehicle_name}", self)
        center_action.triggered.connect(lambda: self._center_on_vehicle(vehicle_id))
        menu.addAction(center_action)

        menu.exec_(self.mapToGlobal(pos))

    def _center_on_vehicle(self, vehicle_id: str):
        """Center map on a vehicle."""
        vehicle_data = self.vehicles.get(vehicle_id)
        if vehicle_data:
            lat, lon = vehicle_data[0], vehicle_data[1]
            self.center_on(lat, lon)

    def _show_waypoint_context_menu(self, pos, wp_id: int):
        """Show context menu for a mission waypoint."""
        menu = QMenu(self)

        # Edit waypoint
        edit_action = QAction("Edit Waypoint...", self)
        edit_action.triggered.connect(lambda: self._edit_waypoint(wp_id))
        menu.addAction(edit_action)

        # Convert to target
        target_action = QAction("Mark as Target", self)
        target_action.triggered.connect(lambda: self._convert_waypoint_to_target(wp_id))
        menu.addAction(target_action)

        menu.addSeparator()

        # Delete
        delete_action = QAction("Delete Waypoint", self)
        delete_action.triggered.connect(lambda: self._delete_waypoint(wp_id))
        menu.addAction(delete_action)

        menu.exec_(self.mapToGlobal(pos))

    def _show_target_context_menu(self, pos, target_id: str):
        """Show context menu for a target."""
        menu = QMenu(self)

        # Get target info
        target_data = self.targets.get(target_id)
        if not target_data:
            return

        # Handle both old and new formats
        lat, lon = target_data[0], target_data[1]
        assigned = target_data[2] if len(target_data) > 2 else None
        is_ew = target_data[3] if len(target_data) > 3 else False

        # Header - show target ID with EW indicator if applicable
        header_text = f"EW TARGET {target_id}" if is_ew else f"TARGET {target_id}"
        header = QAction(header_text, self)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        # Fly to target (prosecute)
        fly_to = QAction("Fly Vehicle to Target", self)
        fly_to.triggered.connect(lambda: self.target_action_requested.emit(target_id, "fly_to"))
        menu.addAction(fly_to)

        menu.addSeparator()

        # Assign orb (if not already assigned)
        if not assigned:
            assign_orb = QAction("Assign Orb to Target", self)
            assign_orb.triggered.connect(lambda: self.target_action_requested.emit(target_id, "assign_orb"))
            menu.addAction(assign_orb)
        else:
            # Show which orb is assigned
            orb_info = QAction(f"Assigned: ORB{assigned}", self)
            orb_info.setEnabled(False)
            menu.addAction(orb_info)

            unassign_orb = QAction("Unassign Orb", self)
            unassign_orb.triggered.connect(lambda: self.target_action_requested.emit(target_id, "unassign_orb"))
            menu.addAction(unassign_orb)

        menu.addSeparator()

        # Select/center
        center_on = QAction("Center on Target", self)
        center_on.triggered.connect(lambda: self.center_on(lat, lon))
        menu.addAction(center_on)

        menu.addSeparator()

        # Remove target
        remove = QAction("Remove Target", self)
        remove.triggered.connect(lambda: self.target_action_requested.emit(target_id, "remove"))
        menu.addAction(remove)

        menu.exec_(self.mapToGlobal(pos))

    def _show_emitter_context_menu(self, pos, emitter_id: str):
        """Show context menu for an EW emitter."""
        menu = QMenu(self)

        # Get emitter info
        emitter_data = self.ew_emitters.get(emitter_id)
        if not emitter_data:
            return

        lat, lon = emitter_data[0], emitter_data[1]
        cep_m = emitter_data[2] if len(emitter_data) > 2 else 0
        priority = emitter_data[3] if len(emitter_data) > 3 else False
        state = emitter_data[4] if len(emitter_data) > 4 else None

        # Header - show emitter ID (shortened)
        short_id = emitter_id[-8:] if len(emitter_id) > 8 else emitter_id
        header_text = f"EMITTER {short_id}"
        if priority:
            header_text = "! " + header_text
        header = QAction(header_text, self)
        header.setEnabled(False)
        menu.addAction(header)

        # Show CEP if available
        if cep_m > 0:
            cep_info = QAction(f"CEP: {cep_m:.0f}m", self)
            cep_info.setEnabled(False)
            menu.addAction(cep_info)

        # Show state if available
        if state:
            state_info = QAction(f"State: {state}", self)
            state_info.setEnabled(False)
            menu.addAction(state_info)

        menu.addSeparator()

        # Prosecute (main action)
        prosecute = QAction("PROSECUTE", self)
        prosecute.triggered.connect(lambda: self.emitter_action_requested.emit(emitter_id, "prosecute"))
        # Bold font for main action
        font = prosecute.font()
        font.setBold(True)
        prosecute.setFont(font)
        menu.addAction(prosecute)

        # Investigate (send vehicle without full prosecution)
        investigate = QAction("Investigate", self)
        investigate.triggered.connect(lambda: self.emitter_action_requested.emit(emitter_id, "investigate"))
        menu.addAction(investigate)

        menu.addSeparator()

        # Add as target (converts emitter position to target queue)
        add_target = QAction("Add to Target Queue", self)
        add_target.triggered.connect(lambda: self.emitter_action_requested.emit(emitter_id, "add_target"))
        menu.addAction(add_target)

        menu.addSeparator()

        # Center on emitter
        center_on = QAction("Center on Emitter", self)
        center_on.triggered.connect(lambda: self.center_on(lat, lon))
        menu.addAction(center_on)

        # Set as bullseye
        set_bullseye = QAction("Set as Bullseye", self)
        set_bullseye.triggered.connect(lambda: self._set_emitter_as_bullseye(emitter_id, lat, lon))
        menu.addAction(set_bullseye)

        menu.exec_(self.mapToGlobal(pos))

    def _set_emitter_as_bullseye(self, emitter_id: str, lat: float, lon: float):
        """Set an emitter position as the bullseye."""
        short_id = emitter_id[-8:] if len(emitter_id) > 8 else emitter_id
        self.set_bullseye(lat, lon, f"EM-{short_id}")
        self.bullseye_set.emit(lat, lon)

    def _edit_waypoint(self, wp_id: int):
        """Request to edit a waypoint."""
        if self._right_click_pos:
            lat, lon = self.screen_to_lat_lon(self._right_click_pos.x(), self._right_click_pos.y())
            self.waypoint_right_clicked.emit(wp_id, lat, lon)

    def _convert_waypoint_to_target(self, wp_id: int):
        """Emit signal to convert waypoint to target."""
        # Will be handled by mission panel
        self.waypoint_right_clicked.emit(wp_id, 0, 0)

    def _delete_waypoint(self, wp_id: int):
        """Emit signal to delete waypoint."""
        self.waypoint_right_clicked.emit(wp_id, -999, -999)  # Special marker for delete

    def _add_target_at_click(self):
        """Add target at right-click position."""
        if self._right_click_pos:
            lat, lon = self.screen_to_lat_lon(self._right_click_pos.x(), self._right_click_pos.y())
            self.target_added.emit(lat, lon)

    def _set_bullseye_at_click(self):
        """Set bullseye at right-click position."""
        if self._right_click_pos:
            lat, lon = self.screen_to_lat_lon(self._right_click_pos.x(), self._right_click_pos.y())
            self.set_bullseye(lat, lon)
            self.bullseye_set.emit(lat, lon)

    def _center_at_click(self):
        """Center map at right-click position."""
        if self._right_click_pos:
            lat, lon = self.screen_to_lat_lon(self._right_click_pos.x(), self._right_click_pos.y())
            self.center_on(lat, lon)

    def _investigate_at_click(self):
        """Send selected vehicle to investigate this point."""
        if self._right_click_pos:
            lat, lon = self.screen_to_lat_lon(self._right_click_pos.x(), self._right_click_pos.y())
            self.investigate_requested.emit(lat, lon)

    def _start_measure_at_click(self):
        """Start measuring from right-click position."""
        if self._right_click_pos:
            lat, lon = self.screen_to_lat_lon(self._right_click_pos.x(), self._right_click_pos.y())
            self._measure_start = (lat, lon)
            self._measuring = True
            self.setCursor(Qt.CrossCursor)
            self.update()

    def _finish_measure(self):
        """Finish measuring."""
        self._measuring = False
        self._measure_start = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def _cancel_measure(self):
        """Cancel measuring."""
        self._finish_measure()

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            # If measuring, finish on click
            if self._measuring:
                self._finish_measure()
                return

            # If in mission mode, emit click coordinates
            if self._mission_mode:
                lat, lon = self.screen_to_lat_lon(event.x(), event.y())
                self.mission_click.emit(lat, lon)
                return

            self.dragging = True
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for panning and cursor tracking."""
        # Track mouse position for cursor BRAA
        self._mouse_lat, self._mouse_lon = self.screen_to_lat_lon(event.x(), event.y())

        if self.dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            scale = 2 ** self.zoom * 10
            self.center_lon -= delta.x() / scale
            self.center_lat += delta.y() / scale
            self.last_mouse_pos = event.pos()
            # Clear leg hover while dragging
            self._hovered_leg = None
        else:
            # Detect leg hover (only when not dragging)
            self._hovered_leg = self.get_leg_at(event.x(), event.y())

        # Always update to refresh cursor BRAA and leg info
        self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_mouse_pos = None

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def leaveEvent(self, event):
        """Handle mouse leaving the widget."""
        self._mouse_lat = None
        self._mouse_lon = None
        self._hovered_leg = None
        self.update()

    def keyPressEvent(self, event):
        """Handle key press."""
        if event.key() == Qt.Key_Escape:
            if self._measuring:
                self._cancel_measure()
                event.accept()
                return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        """Handle focus in."""
        super().focusInEvent(event)

    def enterEvent(self, event):
        """Handle mouse entering - grab focus for key events."""
        self.setFocus()
        super().enterEvent(event)


class MapWidget(QFrame):
    """Map widget with controls overlaid."""

    target_added = pyqtSignal(float, float)
    bullseye_changed = pyqtSignal(float, float)
    investigate_requested = pyqtSignal(float, float)
    mission_waypoint_clicked = pyqtSignal(float, float)  # For adding mission waypoints
    waypoint_edit_requested = pyqtSignal(int)  # wp_id - edit request from map
    view_vehicle_mission = pyqtSignal(str)  # vehicle_id - request to view mission

    # Entity-specific context menu signals
    vehicle_action_requested = pyqtSignal(str, str)  # vehicle_id, action
    target_action_requested = pyqtSignal(str, str)   # target_id, action
    emitter_action_requested = pyqtSignal(str, str)  # emitter_id, action

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._mission_click_mode = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Map canvas
        self.canvas = MapCanvas()
        self.canvas.target_added.connect(self.target_added.emit)
        self.canvas.bullseye_set.connect(self.bullseye_changed.emit)
        self.canvas.investigate_requested.connect(self.investigate_requested.emit)
        self.canvas.mission_click.connect(self.mission_waypoint_clicked.emit)
        self.canvas.waypoint_right_clicked.connect(self._on_waypoint_clicked)
        self.canvas.view_mission_requested.connect(self.view_vehicle_mission.emit)

        # Entity action signals
        self.canvas.vehicle_action_requested.connect(self.vehicle_action_requested.emit)
        self.canvas.target_action_requested.connect(self.target_action_requested.emit)
        self.canvas.emitter_action_requested.connect(self.emitter_action_requested.emit)

        layout.addWidget(self.canvas)

        # Create overlay buttons after canvas is added
        self._create_overlay_buttons()

        # Track if we've auto-centered yet
        self._has_auto_centered = False

    def _on_waypoint_clicked(self, wp_id: int, lat: float, lon: float):
        """Handle waypoint click from canvas."""
        if lat == -999 and lon == -999:
            # Delete request - handled by mission panel
            pass
        # Emit edit request
        self.waypoint_edit_requested.emit(wp_id)

    def _create_overlay_buttons(self):
        """Create overlay buttons on the map canvas."""
        btn_style = """
            QPushButton {
                background-color: rgba(42, 42, 74, 0.9);
                border: 1px solid #4a4a6a;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover { background-color: rgba(58, 58, 106, 0.9); }
        """

        # Zoom in button
        zoom_in_btn = QPushButton("+", self.canvas)
        zoom_in_btn.setFixedSize(28, 28)
        zoom_in_btn.move(8, 8)
        zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        zoom_in_btn.setStyleSheet(btn_style)
        zoom_in_btn.show()

        # Zoom out button
        zoom_out_btn = QPushButton("-", self.canvas)
        zoom_out_btn.setFixedSize(28, 28)
        zoom_out_btn.move(40, 8)
        zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        zoom_out_btn.setStyleSheet(btn_style)
        zoom_out_btn.show()

        # Center on aircraft button
        center_btn = QPushButton("⌖", self.canvas)  # Crosshair symbol
        center_btn.setFixedSize(28, 28)
        center_btn.move(72, 8)
        center_btn.clicked.connect(self._center_on_selected)
        center_btn.setToolTip("Center on selected vehicle")
        center_btn.setStyleSheet(btn_style)
        center_btn.show()

        self._zoom_in = zoom_in_btn
        self._zoom_out = zoom_out_btn
        self._center_btn = center_btn

    def _center_on_selected(self):
        """Center map on the selected vehicle."""
        self.canvas.center_on_vehicle()

    def set_vehicles(self, vehicles: dict):
        """Update vehicle positions."""
        self.canvas.set_vehicles(vehicles)

        # Auto-center on first vehicle update (only once)
        if not self._has_auto_centered and vehicles:
            # Check if any vehicle is far from current center (> 100km)
            for vid, data in vehicles.items():
                if len(data) >= 2:
                    lat, lon = data[0], data[1]
                    # Check distance from current map center
                    dist = haversine_distance(lat, lon, self.canvas.center_lat, self.canvas.center_lon)
                    if dist > 100000:  # More than 100km away
                        print(f"[Map] Auto-centering on {vid} at ({lat:.4f}, {lon:.4f})")
                        self.canvas.center_on(lat, lon)
                        self._has_auto_centered = True
                        break

    def set_targets(self, targets: dict):
        """Update target positions."""
        self.canvas.set_targets(targets)

    def set_bullseye(self, lat: float, lon: float, name: str = "BULLSEYE"):
        """Set bullseye reference point."""
        self.canvas.set_bullseye(lat, lon, name)

    def clear_bullseye(self):
        """Clear bullseye."""
        self.canvas.clear_bullseye()

    def center_on(self, lat: float, lon: float):
        """Center map on coordinates."""
        self.canvas.center_on(lat, lon)

    def center_on_vehicle(self, vehicle_id: str = None):
        """Center map on a vehicle."""
        self.canvas.center_on_vehicle(vehicle_id)

    def set_mission_waypoints(self, waypoints: dict):
        """Update mission waypoint display."""
        self.canvas.set_mission_waypoints(waypoints)

    def set_mission_click_mode(self, enabled: bool):
        """Enable/disable mission waypoint click mode."""
        self._mission_click_mode = enabled
        self.canvas.set_mission_mode(enabled)

    def set_mission_vehicle(self, vehicle_id: str):
        """Set the vehicle ID used for mission leg estimates."""
        self.canvas.set_mission_vehicle(vehicle_id)

    def set_ew_emitters(self, emitters: list):
        """Update EW emitter display. emitters: [(lat, lon, id, cep_m), ...]"""
        self.canvas.set_ew_emitters(emitters)

    def clear_ew_emitters(self):
        """Clear all EW emitter markers."""
        self.canvas.clear_ew_emitters()
