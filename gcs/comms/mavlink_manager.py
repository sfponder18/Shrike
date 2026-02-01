# MAVLink Connection Manager
# Handles connections to Bird and Chicks via MLRS (primary), 4G/Tailscale (backup), or SITL
#
# =============================================================================
# CONNECTION MODES
# =============================================================================
#
# 1. SIMULATION: Internal simulation for UI development (no external dependencies)
# 2. SITL: Connect to ArduPilot SITL instances for testing
# 3. MLRS: Serial port to MLRS TX module (868MHz) for real hardware
# 4. UDP: Direct UDP to vehicle (4G/Tailscale backup)
#
# SITL Setup:
#   Bird (ArduPlane):   sim_vehicle.py -v ArduPlane --out=udp:127.0.0.1:14550
#   Chick1 (ArduCopter): sim_vehicle.py -v ArduCopter -I1 --out=udp:127.0.0.1:14560
#   Chick2 (ArduCopter): sim_vehicle.py -v ArduCopter -I2 --out=udp:127.0.0.1:14570
#
# =============================================================================

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from dataclasses import dataclass
from typing import Optional, Callable, Dict
import time
import threading

# MAVLink imports
try:
    from pymavlink import mavutil
    PYMAVLINK_AVAILABLE = True
except ImportError:
    PYMAVLINK_AVAILABLE = False
    print("[MAVLink] pymavlink not installed - SITL/hardware modes unavailable")


@dataclass
class VehicleTelemetry:
    """Telemetry data from a vehicle."""
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0
    heading: float = 0.0
    groundspeed: float = 0.0
    airspeed: float = 0.0
    battery_pct: int = 0
    battery_voltage: float = 0.0
    mode: str = ""
    armed: bool = False
    gps_fix: int = 0
    gps_sats: int = 0
    last_heartbeat: float = 0.0


class MAVLinkManager(QObject):
    """
    Manages MAVLink connections to all vehicles.

    Connection architecture:
        GCS ──MLRS TX──► Bird (MLRS RX)
        GCS ──MLRS TX──► Chick1 (MLRS RX)
        GCS ──MLRS TX──► Chick2 (MLRS RX)
        GCS ──4G/Tailscale──► Bird Pi 5 (backup)

    Usage:
        manager = MAVLinkManager()
        manager.telemetry_received.connect(on_telemetry)
        manager.connect_mlrs("COM4", 57600)  # Or UDP port
        manager.connect_backup("100.x.x.x", 14550)  # Tailscale IP
    """

    # Signals
    telemetry_received = pyqtSignal(str, object)  # vehicle_id, VehicleTelemetry
    connection_changed = pyqtSignal(str, bool)     # vehicle_id, connected
    mode_changed = pyqtSignal(str, str)            # vehicle_id, mode
    armed_changed = pyqtSignal(str, bool)          # vehicle_id, armed
    chick_launch_triggered = pyqtSignal(str, str)  # carrier_id, chick_id - for hardware: triggers release mechanism
    waypoint_reached = pyqtSignal(str, int, dict)  # vehicle_id, wp_index, waypoint_data - for hardware: mission progress

    def __init__(self, parent=None):
        super().__init__(parent)

        self._connections = {}  # vehicle_id -> mavutil connection object
        self._telemetry = {}    # vehicle_id -> VehicleTelemetry
        self._vehicle_types = {}  # vehicle_id -> "plane" or "copter" (detected from HEARTBEAT)
        self._mlrs_port = None
        self._backup_connection = None

        # Connection mode: "simulation", "sitl", "hardware"
        self._mode = "simulation"
        self._simulation_mode = True  # Legacy flag for backwards compatibility

        # SITL/Hardware receiver thread
        self._receiver_running = False
        self._receiver_thread = None

        # Simulation timer (for simulation mode only)
        self._sim_timer = QTimer()
        self._sim_timer.timeout.connect(self._simulate_telemetry)

        # Swarm tracking state
        self._swarm_config = None  # SwarmConfig object when active
        self._swarm_active = False
        self._chicks_released = {}  # chick_id -> bool (has been released from bird)
        self._chicks_attached = {}  # chick_id -> bool - initialized dynamically from config

        # ArduPilot mode mappings
        self._plane_modes = {
            "MANUAL": 0, "CIRCLE": 1, "STABILIZE": 2, "TRAINING": 3,
            "ACRO": 4, "FBWA": 5, "FBWB": 6, "CRUISE": 7, "AUTOTUNE": 8,
            "AUTO": 10, "RTL": 11, "LOITER": 12, "TAKEOFF": 13,
            "AVOID_ADSB": 14, "GUIDED": 15, "QSTABILIZE": 17, "QHOVER": 18,
            "QLOITER": 19, "QLAND": 20, "QRTL": 21, "LAND": 23
        }
        self._copter_modes = {
            "STABILIZE": 0, "ACRO": 1, "ALT_HOLD": 2, "AUTO": 3,
            "GUIDED": 4, "LOITER": 5, "RTL": 6, "CIRCLE": 7,
            "LAND": 9, "DRIFT": 11, "SPORT": 13, "FLIP": 14,
            "AUTOTUNE": 15, "POSHOLD": 16, "BRAKE": 17, "THROW": 18,
            "SMART_RTL": 21, "GUIDED_NOGPS": 20
        }

    # ==================== Connection Methods ====================

    def connect_sitl(self, vehicle_configs: dict = None) -> bool:
        """
        Connect to ArduPilot SITL instances.

        Args:
            vehicle_configs: Dict of vehicle_id -> connection string

        Returns:
            True if at least one connection successful
        """
        from ..config import get_vehicle_info, SITL_CONNECTIONS

        if not PYMAVLINK_AVAILABLE:
            print("[MAVLink] ERROR: pymavlink not installed")
            return False

        # Stop simulation if running
        self.stop_simulation()

        # Use provided config or default from config.py
        if vehicle_configs is None:
            vehicle_configs = SITL_CONNECTIONS

        self._mode = "sitl"
        self._simulation_mode = False
        connected = False

        for vehicle_id, conn_str in vehicle_configs.items():
            try:
                # Get expected vehicle type from config
                vehicle_info = get_vehicle_info(vehicle_id)
                expected_type = vehicle_info.get("type", "unknown")

                print(f"[MAVLink] Connecting to {vehicle_id} ({expected_type}) at {conn_str}...")
                conn = mavutil.mavlink_connection(conn_str, source_system=255)

                # Wait for heartbeat with timeout
                print(f"[MAVLink] Waiting for heartbeat from {vehicle_id}...")
                msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=10)

                if msg:
                    # Verify vehicle type matches expected
                    # MAV_TYPE_FIXED_WING = 1, MAV_TYPE_QUADROTOR = 2
                    mav_type = msg.type
                    actual_type = "plane" if mav_type == 1 else "copter" if mav_type in [2, 3, 4, 13, 14] else "unknown"

                    if expected_type != "unknown" and actual_type != expected_type:
                        print(f"[MAVLink] WARNING: {vehicle_id} expected {expected_type} but got {actual_type}!")
                        print(f"[MAVLink] Check your SITL configuration - vehicle may be on wrong port")

                    self._connections[vehicle_id] = conn
                    self._vehicle_types[vehicle_id] = actual_type  # Store actual type
                    self._telemetry[vehicle_id] = VehicleTelemetry(
                        last_heartbeat=time.time(),
                        mode=self._get_mode_name(vehicle_id, msg.custom_mode),
                        armed=(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                    )
                    print(f"[MAVLink] Connected to {vehicle_id} (sysid={msg.get_srcSystem()}, type={actual_type})")

                    # Request data streams for telemetry
                    self._request_data_streams(conn)

                    self.connection_changed.emit(vehicle_id, True)
                    connected = True
                else:
                    print(f"[MAVLink] No heartbeat from {vehicle_id} - timeout")

            except Exception as e:
                print(f"[MAVLink] Failed to connect to {vehicle_id}: {e}")

        # Start receiver thread if we have connections
        if connected:
            self._start_receiver_thread()

        return connected

    def connect_mlrs(self, port: str, baudrate: int = 57600) -> bool:
        """
        Connect to MLRS TX module (hardware).

        Args:
            port: Serial port (e.g., "COM4" or "/dev/ttyUSB0")
            baudrate: Serial baudrate (MLRS default is 57600)

        Returns:
            True if connection successful
        """
        if not PYMAVLINK_AVAILABLE:
            print("[MAVLink] ERROR: pymavlink not installed")
            return False

        self.stop_simulation()
        self._mode = "hardware"
        self._simulation_mode = False

        try:
            print(f"[MAVLink] Connecting to MLRS at {port} @ {baudrate}...")
            conn = mavutil.mavlink_connection(port, baud=baudrate, source_system=255)

            # Wait for heartbeat
            msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
            if msg:
                # MLRS is a shared bus - we'll identify vehicles by sysid
                self._mlrs_port = conn
                print(f"[MAVLink] MLRS connected, received heartbeat from sysid={msg.get_srcSystem()}")
                self._start_receiver_thread()
                return True
            else:
                print("[MAVLink] No heartbeat received on MLRS")
                return False

        except Exception as e:
            print(f"[MAVLink] MLRS connection failed: {e}")
            return False

    def connect_backup(self, host: str, port: int = 14550) -> bool:
        """
        Connect to Bird via 4G/Tailscale backup link.

        Args:
            host: Tailscale IP of Bird's Pi 5
            port: MAVLink UDP port

        Returns:
            True if connection successful
        """
        if not PYMAVLINK_AVAILABLE:
            print("[MAVLink] ERROR: pymavlink not installed")
            return False

        try:
            conn_str = f"udp:{host}:{port}"
            print(f"[MAVLink] Connecting to backup at {conn_str}...")
            conn = mavutil.mavlink_connection(conn_str, source_system=255)

            msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
            if msg:
                from ..config import SWARM_CONFIG
                # Backup connects to first bird in config
                first_bird = SWARM_CONFIG["birds"][0]["id"] if SWARM_CONFIG["birds"] else "bird1"
                self._backup_connection = conn
                self._connections[first_bird] = conn
                print(f"[MAVLink] Backup connected to {first_bird}")
                self.connection_changed.emit(first_bird, True)
                if not self._receiver_running:
                    self._start_receiver_thread()
                return True
            else:
                print("[MAVLink] No heartbeat on backup link")
                return False

        except Exception as e:
            print(f"[MAVLink] Backup connection failed: {e}")
            return False

    def disconnect_all(self):
        """Disconnect all MAVLink connections."""
        print("[MAVLink] Disconnecting all")

        # Stop receiver thread
        self._receiver_running = False
        if self._receiver_thread and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=2)

        # Close connections
        for vid, conn in self._connections.items():
            try:
                conn.close()
            except:
                pass
            self.connection_changed.emit(vid, False)

        self._connections.clear()
        self._mlrs_port = None
        self._backup_connection = None

    def _request_data_streams(self, conn):
        """Request telemetry data streams from the vehicle."""
        try:
            # Request all data streams at 4Hz
            conn.mav.request_data_stream_send(
                conn.target_system,
                conn.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_ALL,
                4,  # 4 Hz
                1   # Start sending
            )
            print(f"[MAVLink] Requested data streams from sysid={conn.target_system}")
        except Exception as e:
            print(f"[MAVLink] Failed to request data streams: {e}")

    def _start_receiver_thread(self):
        """Start the MAVLink message receiver thread."""
        if self._receiver_running:
            return

        self._receiver_running = True
        self._receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._receiver_thread.start()
        print("[MAVLink] Receiver thread started")

    def _receiver_loop(self):
        """Background thread that receives MAVLink messages from all connections."""
        while self._receiver_running:
            for vehicle_id, conn in list(self._connections.items()):
                try:
                    # Non-blocking receive
                    msg = conn.recv_match(blocking=False)
                    if msg:
                        self._handle_mavlink_message(vehicle_id, msg)
                except Exception as e:
                    print(f"[MAVLink] Receive error for {vehicle_id}: {e}")

            # Small sleep to prevent CPU spinning
            time.sleep(0.01)  # 100Hz polling

    def _handle_mavlink_message(self, vehicle_id: str, msg):
        """Process a received MAVLink message."""
        msg_type = msg.get_type()

        if msg_type == 'HEARTBEAT':
            self._handle_heartbeat(vehicle_id, msg)
        elif msg_type == 'GLOBAL_POSITION_INT':
            self._handle_global_position(vehicle_id, msg)
        elif msg_type == 'ATTITUDE':
            self._handle_attitude(vehicle_id, msg)
        elif msg_type == 'SYS_STATUS':
            self._handle_sys_status(vehicle_id, msg)
        elif msg_type == 'GPS_RAW_INT':
            self._handle_gps_raw(vehicle_id, msg)
        elif msg_type == 'VFR_HUD':
            self._handle_vfr_hud(vehicle_id, msg)
        elif msg_type == 'MISSION_CURRENT':
            self._handle_mission_current(vehicle_id, msg)
        elif msg_type == 'MISSION_ITEM_REACHED':
            self._handle_mission_item_reached(vehicle_id, msg)
        elif msg_type == 'STATUSTEXT':
            self._handle_statustext(vehicle_id, msg)

    def _handle_heartbeat(self, vehicle_id: str, msg):
        """Handle HEARTBEAT message."""
        telem = self._telemetry.get(vehicle_id)
        if not telem:
            telem = VehicleTelemetry()
            self._telemetry[vehicle_id] = telem

        telem.last_heartbeat = time.time()

        # Decode mode
        new_mode = self._get_mode_name(vehicle_id, msg.custom_mode)
        if new_mode != telem.mode:
            telem.mode = new_mode
            self.mode_changed.emit(vehicle_id, new_mode)

        # Decode armed state
        new_armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        if new_armed != telem.armed:
            telem.armed = new_armed
            self.armed_changed.emit(vehicle_id, new_armed)

    def _handle_global_position(self, vehicle_id: str, msg):
        """Handle GLOBAL_POSITION_INT message."""
        telem = self._telemetry.get(vehicle_id)
        if telem:
            telem.lat = msg.lat / 1e7
            telem.lon = msg.lon / 1e7
            telem.alt = msg.relative_alt / 1000.0  # mm to m
            telem.heading = msg.hdg / 100.0 if msg.hdg != 65535 else telem.heading

            # Emit telemetry update
            self.telemetry_received.emit(vehicle_id, telem)

    def _handle_attitude(self, vehicle_id: str, msg):
        """Handle ATTITUDE message."""
        telem = self._telemetry.get(vehicle_id)
        if telem:
            import math
            telem.heading = math.degrees(msg.yaw) % 360

    def _handle_sys_status(self, vehicle_id: str, msg):
        """Handle SYS_STATUS message."""
        telem = self._telemetry.get(vehicle_id)
        if telem:
            telem.battery_voltage = msg.voltage_battery / 1000.0  # mV to V
            if msg.battery_remaining >= 0:
                telem.battery_pct = msg.battery_remaining

    def _handle_gps_raw(self, vehicle_id: str, msg):
        """Handle GPS_RAW_INT message."""
        telem = self._telemetry.get(vehicle_id)
        if telem:
            telem.gps_fix = msg.fix_type
            telem.gps_sats = msg.satellites_visible

    def _handle_vfr_hud(self, vehicle_id: str, msg):
        """Handle VFR_HUD message."""
        telem = self._telemetry.get(vehicle_id)
        if telem:
            telem.groundspeed = msg.groundspeed
            telem.airspeed = msg.airspeed
            telem.heading = msg.heading
            # Emit telemetry update
            self.telemetry_received.emit(vehicle_id, telem)

    def _handle_mission_current(self, vehicle_id: str, msg):
        """Handle MISSION_CURRENT message."""
        # Track current waypoint for mission progress
        pass

    def _handle_mission_item_reached(self, vehicle_id: str, msg):
        """Handle MISSION_ITEM_REACHED message."""
        print(f"[MAVLink] {vehicle_id} reached waypoint {msg.seq}")
        self.waypoint_reached.emit(vehicle_id, msg.seq, {"seq": msg.seq})

    def _handle_statustext(self, vehicle_id: str, msg):
        """Handle STATUSTEXT message - display status/errors from vehicle."""
        try:
            text = msg.text if hasattr(msg, 'text') else str(msg)
            severity = msg.severity if hasattr(msg, 'severity') else 0
            # Severity: 0=EMERGENCY, 1=ALERT, 2=CRITICAL, 3=ERROR, 4=WARNING, 5=NOTICE, 6=INFO, 7=DEBUG
            severity_names = {0: "EMERG", 1: "ALERT", 2: "CRIT", 3: "ERROR", 4: "WARN", 5: "NOTICE", 6: "INFO", 7: "DEBUG"}
            sev_name = severity_names.get(severity, "")
            # Only print important messages (not debug/info spam)
            if severity <= 5:
                print(f"[{vehicle_id}] {sev_name}: {text}")
        except Exception:
            pass

    def _get_mode_name(self, vehicle_id: str, mode_num: int) -> str:
        """Convert mode number to name based on vehicle type."""
        # Use detected type if available, otherwise infer from config
        vehicle_type = self._vehicle_types.get(vehicle_id)
        if vehicle_type is None:
            # Fall back to config
            from ..config import get_vehicle_info
            info = get_vehicle_info(vehicle_id)
            vehicle_type = info.get("type", "copter")

        is_plane = vehicle_type == "plane"
        modes = self._plane_modes if is_plane else self._copter_modes

        for name, num in modes.items():
            if num == mode_num:
                return name
        return f"MODE_{mode_num}"

    # ==================== Command Methods ====================

    def set_mode(self, vehicle_id: str, mode: str) -> bool:
        """
        Set flight mode for a vehicle.

        Args:
            vehicle_id: Vehicle ID (e.g., "bird1", "chick1.1", "chick1.2")
            mode: Mode name (e.g., "LOITER", "RTL", "AUTO")

        Returns:
            True if command sent successfully
        """
        print(f"[MAVLink] Set mode: {vehicle_id} -> {mode}")

        # Simulation mode
        if self._simulation_mode:
            if vehicle_id in self._telemetry:
                self._telemetry[vehicle_id].mode = mode
                self.mode_changed.emit(vehicle_id, mode)
                return True
            return False

        # SITL/Hardware mode
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        try:
            # Get mode number based on vehicle type
            vehicle_type = self._vehicle_types.get(vehicle_id)
            if vehicle_type is None:
                from ..config import get_vehicle_info
                info = get_vehicle_info(vehicle_id)
                vehicle_type = info.get("type", "copter")

            is_plane = vehicle_type == "plane"
            modes = self._plane_modes if is_plane else self._copter_modes
            mode_id = modes.get(mode.upper())

            if mode_id is None:
                print(f"[MAVLink] Unknown mode: {mode}")
                return False

            # Send mode change command
            conn.set_mode(mode_id)
            print(f"[MAVLink] Mode command sent: {vehicle_id} -> {mode} ({mode_id})")
            return True

        except Exception as e:
            print(f"[MAVLink] Set mode failed: {e}")
            return False

    def arm(self, vehicle_id: str, arm: bool = True, force: bool = False) -> bool:
        """
        Arm or disarm a vehicle.

        Args:
            vehicle_id: Vehicle to arm/disarm
            arm: True to arm, False to disarm
            force: Force arm (bypass pre-arm checks) - use with caution!
        """
        action = "Arm" if arm else "Disarm"
        print(f"[MAVLink] {action}: {vehicle_id}" + (" (FORCE)" if force else ""))

        # Simulation mode
        if self._simulation_mode:
            if vehicle_id in self._telemetry:
                self._telemetry[vehicle_id].armed = arm
                self.armed_changed.emit(vehicle_id, arm)
                return True
            return False

        # SITL/Hardware mode
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        try:
            # Use MAV_CMD_COMPONENT_ARM_DISARM (works for all vehicle types)
            # param1: 1 = arm, 0 = disarm
            # param2: 21196 = force arm (magic number), 0 = normal
            conn.mav.command_long_send(
                conn.target_system,
                conn.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # confirmation
                1 if arm else 0,  # param1: arm/disarm
                21196 if force else 0,  # param2: force arm magic number
                0, 0, 0, 0, 0  # params 3-7 unused
            )
            print(f"[MAVLink] {action} command sent to {vehicle_id}")
            return True

        except Exception as e:
            print(f"[MAVLink] {action} failed: {e}")
            return False

    def change_altitude(self, vehicle_id: str, new_altitude: float) -> bool:
        """
        Change vehicle altitude while maintaining current position/mission.
        Works by adjusting the altitude target without changing flight mode.
        """
        print(f"[MAVLink] Altitude change: {vehicle_id} -> {new_altitude}m")

        # Simulation mode - set persistent target altitude
        if self._simulation_mode:
            if vehicle_id in self._telemetry:
                # Set persistent target altitude (applies in all modes)
                self._sim_target_alt[vehicle_id] = new_altitude
                print(f"[Sim] {vehicle_id} target altitude set to {new_altitude}m")
            return True

        # SITL/Hardware mode - use MAV_CMD_DO_CHANGE_ALTITUDE
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        try:
            # Use DO_CHANGE_ALTITUDE command - works in AUTO mode
            conn.mav.command_long_send(
                conn.target_system,
                conn.target_component,
                mavutil.mavlink.MAV_CMD_DO_CHANGE_ALTITUDE,
                0,  # confirmation
                new_altitude,  # param1: altitude
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # param2: frame
                0, 0, 0, 0, 0  # unused params
            )
            print(f"[MAVLink] Altitude change command sent to {vehicle_id}")
            return True

        except Exception as e:
            print(f"[MAVLink] Altitude change failed: {e}")
            return False

    def goto(self, vehicle_id: str, lat: float, lon: float, alt: float) -> bool:
        """
        Command vehicle to go to location (GUIDED mode).
        """
        print(f"[MAVLink] Goto: {vehicle_id} -> ({lat:.6f}, {lon:.6f}, {alt:.0f}m)")

        # Simulation mode
        if self._simulation_mode:
            self._sim_goto_target[vehicle_id] = (lat, lon, alt)
            # Also set target altitude for persistence
            self._sim_target_alt[vehicle_id] = alt

            # Calculate and log distance to target
            telem = self._telemetry.get(vehicle_id)
            if telem:
                dist = self._sim_distance(telem.lat, telem.lon, lat, lon)
                print(f"[MAVLink] {vehicle_id} goto set - current pos: ({telem.lat:.6f}, {telem.lon:.6f}), dist: {dist:.0f}m")
            return True

        # SITL/Hardware mode
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        try:
            # Send position target (GUIDED mode)
            conn.mav.set_position_target_global_int_send(
                0,  # time_boot_ms
                conn.target_system,
                conn.target_component,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                0b0000111111111000,  # type_mask (only positions)
                int(lat * 1e7),  # lat
                int(lon * 1e7),  # lon
                alt,  # alt
                0, 0, 0,  # velocity
                0, 0, 0,  # acceleration
                0, 0  # yaw, yaw_rate
            )
            print(f"[MAVLink] Goto command sent to {vehicle_id}")
            return True

        except Exception as e:
            print(f"[MAVLink] Goto failed: {e}")
            return False

    def takeoff(self, vehicle_id: str, altitude: float) -> bool:
        """
        Command vehicle to takeoff (must be in GUIDED mode and armed).

        Args:
            vehicle_id: Vehicle to takeoff
            altitude: Target altitude in meters
        """
        print(f"[MAVLink] Takeoff: {vehicle_id} -> {altitude}m")

        # Simulation mode
        if self._simulation_mode:
            if vehicle_id in self._telemetry:
                # Set target altitude - vehicle will climb towards it
                self._sim_target_alt[vehicle_id] = altitude
            return True

        # SITL/Hardware mode
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        try:
            # Send takeoff command
            conn.mav.command_long_send(
                conn.target_system,
                conn.target_component,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0,  # confirmation
                0,  # param1 (pitch)
                0,  # param2 (empty)
                0,  # param3 (empty)
                0,  # param4 (yaw)
                0,  # param5 (lat - 0 for current)
                0,  # param6 (lon - 0 for current)
                altitude  # param7 (altitude)
            )
            print(f"[MAVLink] Takeoff command sent to {vehicle_id}")
            return True

        except Exception as e:
            print(f"[MAVLink] Takeoff failed: {e}")
            return False

    def quick_fly(self, vehicle_id: str, altitude: float = 50) -> bool:
        """
        Quick fly sequence for SITL testing: Wait for GPS -> GUIDED -> ARM -> TAKEOFF.

        Args:
            vehicle_id: Vehicle to fly
            altitude: Target altitude in meters
        """
        print(f"[MAVLink] Quick fly: {vehicle_id} -> {altitude}m")

        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        vehicle_type = self._vehicle_types.get(vehicle_id, "copter")

        try:
            # Step 0: Wait for GPS 3D fix
            print(f"[MAVLink] Step 0: Waiting for GPS 3D fix...")
            gps_ready = self._wait_for_gps(conn, timeout=30)
            if not gps_ready:
                print(f"[MAVLink] WARNING: No GPS 3D fix, attempting arm anyway (force)")

            # Step 1: Set GUIDED mode
            print(f"[MAVLink] Step 1: Setting GUIDED mode...")
            self.set_mode(vehicle_id, "GUIDED")
            time.sleep(1.5)  # Give more time for mode to settle

            # Step 2: Arm (force for SITL)
            print(f"[MAVLink] Step 2: Arming (force)...")
            self.arm(vehicle_id, True, force=True)
            time.sleep(1.5)  # Give more time for arm to complete

            # Step 2b: Verify armed
            armed = self._verify_armed(conn, timeout=5)
            if not armed:
                print(f"[MAVLink] WARNING: Vehicle may not be armed, continuing anyway...")

            # Step 3: Takeoff (copter) or just proceed (plane)
            if vehicle_type == "copter":
                print(f"[MAVLink] Step 3: Takeoff to {altitude}m...")
                self.takeoff(vehicle_id, altitude)
            else:
                print(f"[MAVLink] Step 3: Plane armed in GUIDED - send goto command to fly")

            return True

        except Exception as e:
            print(f"[MAVLink] Quick fly failed: {e}")
            return False

    def _wait_for_gps(self, conn, timeout: float = 30) -> bool:
        """Wait for GPS 3D fix on a connection."""
        start = time.time()
        while time.time() - start < timeout:
            msg = conn.recv_match(type='GPS_RAW_INT', blocking=True, timeout=1)
            if msg:
                if msg.fix_type >= 3:  # 3D fix or better
                    print(f"[MAVLink] GPS 3D fix acquired ({msg.satellites_visible} sats)")
                    return True
                else:
                    fix_names = {0: "No GPS", 1: "No Fix", 2: "2D Fix"}
                    fix_name = fix_names.get(msg.fix_type, f"Fix {msg.fix_type}")
                    print(f"[MAVLink] GPS: {fix_name} ({msg.satellites_visible} sats) - waiting...")
        return False

    def _verify_armed(self, conn, timeout: float = 5) -> bool:
        """Verify vehicle is armed by checking heartbeat."""
        start = time.time()
        while time.time() - start < timeout:
            msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
            if msg:
                armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                if armed:
                    print(f"[MAVLink] Vehicle ARMED confirmed")
                    return True
        return False

    def upload_mission(self, vehicle_id: str, waypoints: list) -> bool:
        """
        Upload a mission to a vehicle.

        Args:
            vehicle_id: Target vehicle
            waypoints: List of waypoint dicts with keys:
                - type: "WAYPOINT", "LOITER", "RTL", "LAUNCH_CHICK", "TARGET"
                - lat, lon, alt: Coordinates
                - chick_id: (for LAUNCH_CHICK) which chick to launch
                - speed: (optional) speed for this leg in m/s
        """
        print(f"[MAVLink] Upload mission to {vehicle_id}: {len(waypoints)} waypoints")

        for i, wp in enumerate(waypoints):
            wp_type = wp.get("type", "WAYPOINT")
            if wp_type == "LAUNCH_CHICK":
                chick_id = wp.get("chick_id", "chick1")
                print(f"  WP{i}: LAUNCH_CHICK ({chick_id}) @ ({wp.get('lat')}, {wp.get('lon')}, {wp.get('alt')}m)")
            else:
                print(f"  WP{i}: {wp_type} @ ({wp.get('lat')}, {wp.get('lon')}, {wp.get('alt')}m)")

        # Simulation mode - just store locally
        if self._simulation_mode:
            self._sim_missions[vehicle_id] = waypoints
            self._sim_current_wp[vehicle_id] = 0
            print(f"[Sim] Mission stored for {vehicle_id}")
            return True

        # SITL/Hardware mode - upload via MAVLink
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return False

        try:
            # Clear existing mission
            conn.mav.mission_clear_all_send(
                conn.target_system, conn.target_component
            )
            time.sleep(0.1)

            # Build mission items
            mission_items = self._build_mission_items(waypoints, vehicle_id)

            # Send mission count
            conn.mav.mission_count_send(
                conn.target_system, conn.target_component,
                len(mission_items),
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

            # Wait for requests and send items
            for i, item in enumerate(mission_items):
                # Wait for MISSION_REQUEST_INT
                msg = conn.recv_match(type=['MISSION_REQUEST_INT', 'MISSION_REQUEST'],
                                       blocking=True, timeout=5)
                if not msg:
                    print(f"[MAVLink] Timeout waiting for mission request {i}")
                    return False

                # Send mission item
                conn.mav.mission_item_int_send(
                    conn.target_system, conn.target_component,
                    i,  # seq
                    item['frame'],
                    item['command'],
                    0 if i > 0 else 1,  # current (1 for first item)
                    1,  # autocontinue
                    item.get('param1', 0),
                    item.get('param2', 0),
                    item.get('param3', 0),
                    item.get('param4', 0),
                    item['x'],
                    item['y'],
                    item['z'],
                    mavutil.mavlink.MAV_MISSION_TYPE_MISSION
                )

            # Wait for MISSION_ACK
            msg = conn.recv_match(type='MISSION_ACK', blocking=True, timeout=5)
            if msg and msg.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
                print(f"[MAVLink] Mission uploaded successfully to {vehicle_id}")
                return True
            else:
                print(f"[MAVLink] Mission upload failed: {msg}")
                return False

        except Exception as e:
            print(f"[MAVLink] Mission upload error: {e}")
            return False

    def _build_mission_items(self, waypoints: list, vehicle_id: str) -> list:
        """Convert waypoint list to MAVLink mission items."""
        items = []

        # Add home position as first item (will be overwritten by autopilot)
        if waypoints:
            first_wp = waypoints[0]
            items.append({
                'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                'command': mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                'x': int(first_wp.get('lat', 0) * 1e7),
                'y': int(first_wp.get('lon', 0) * 1e7),
                'z': first_wp.get('alt', 100)
            })

        for wp in waypoints:
            wp_type = wp.get('type', 'WAYPOINT')
            lat = int(wp.get('lat', 0) * 1e7)
            lon = int(wp.get('lon', 0) * 1e7)
            alt = wp.get('alt', 100)

            if wp_type == 'WAYPOINT':
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    'param1': 0,  # hold time
                    'param2': wp.get('speed', 0),  # acceptance radius (or speed)
                    'x': lat, 'y': lon, 'z': alt
                })

            elif wp_type == 'LOITER':
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM,
                    'x': lat, 'y': lon, 'z': alt
                })

            elif wp_type == 'LOITER_TIME':
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME,
                    'param1': wp.get('param1', 30),  # loiter time in seconds
                    'x': lat, 'y': lon, 'z': alt
                })

            elif wp_type == 'RTL':
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                    'x': 0, 'y': 0, 'z': 0
                })

            elif wp_type == 'LAUNCH_CHICK':
                # First, waypoint to the location
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    'x': lat, 'y': lon, 'z': alt
                })
                # Then, servo command to trigger release
                # Servo channel 9 = chick1, channel 10 = chick2
                chick_id = wp.get('chick_id', 'chick1')
                servo_channel = 9 if '1' in chick_id else 10
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
                    'param1': servo_channel,  # servo number
                    'param2': 1900,  # PWM value for release
                    'x': 0, 'y': 0, 'z': 0
                })

            elif wp_type == 'TARGET':
                # Target waypoint - same as regular waypoint for autopilot
                items.append({
                    'frame': mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    'command': mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    'x': lat, 'y': lon, 'z': alt
                })

        return items

    def download_mission(self, vehicle_id: str):
        """
        Download mission from a vehicle.

        Args:
            vehicle_id: Vehicle to download from

        Returns:
            Mission object or None if failed
        """
        from ..models.mission import Mission, WaypointType

        # Simulation mode - return stored mission
        if self._simulation_mode:
            if vehicle_id in self._sim_missions:
                waypoints = self._sim_missions[vehicle_id]
                mission = Mission(name=f"{vehicle_id} Downloaded", vehicle_id=vehicle_id)
                for wp_data in waypoints:
                    wp_type_str = wp_data.get("type", "WAYPOINT")
                    try:
                        wp_type = WaypointType(wp_type_str)
                    except ValueError:
                        wp_type = WaypointType.WAYPOINT

                    mission.add_waypoint(
                        wp_type,
                        wp_data.get("lat", 0),
                        wp_data.get("lon", 0),
                        wp_data.get("alt", 100),
                        name=wp_data.get("name", "")
                    )
                print(f"[Sim] Downloaded {len(mission)} waypoints from {vehicle_id}")
                return mission
            else:
                print(f"[Sim] No mission stored for {vehicle_id}")
                return None

        # SITL/Hardware mode - download via MAVLink
        conn = self._connections.get(vehicle_id)
        if not conn:
            print(f"[MAVLink] No connection for {vehicle_id}")
            return None

        try:
            print(f"[MAVLink] Requesting mission from {vehicle_id}...")

            # Request mission count
            conn.mav.mission_request_list_send(
                conn.target_system, conn.target_component,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

            # Wait for MISSION_COUNT response
            msg = conn.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)
            if not msg:
                print("[MAVLink] Timeout waiting for MISSION_COUNT")
                return None

            count = msg.count
            print(f"[MAVLink] Mission has {count} items")

            if count == 0:
                return None

            mission = Mission(name=f"{vehicle_id} Downloaded", vehicle_id=vehicle_id)

            # Request each mission item
            for i in range(count):
                conn.mav.mission_request_int_send(
                    conn.target_system, conn.target_component, i,
                    mavutil.mavlink.MAV_MISSION_TYPE_MISSION
                )

                item = conn.recv_match(type='MISSION_ITEM_INT', blocking=True, timeout=5)
                if not item:
                    print(f"[MAVLink] Timeout waiting for item {i}")
                    continue

                # Skip home position (item 0)
                if i == 0:
                    continue

                # Map MAVLink command to waypoint type
                wp_type = WaypointType.WAYPOINT
                if item.command == mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM:
                    wp_type = WaypointType.LOITER
                elif item.command == mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME:
                    wp_type = WaypointType.LOITER_TIME
                elif item.command == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
                    wp_type = WaypointType.RTL

                lat = item.x / 1e7
                lon = item.y / 1e7
                alt = item.z

                # Only add if valid coordinates
                if lat != 0 or lon != 0:
                    mission.add_waypoint(wp_type, lat, lon, alt, name=f"WP{i}")

            # Send ACK
            conn.mav.mission_ack_send(
                conn.target_system, conn.target_component,
                mavutil.mavlink.MAV_MISSION_ACCEPTED,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

            print(f"[MAVLink] Downloaded {len(mission)} waypoints from {vehicle_id}")
            return mission

        except Exception as e:
            print(f"[MAVLink] Mission download error: {e}")
            return None

    def add_launch_point(self, lat: float, lon: float, alt: float, chick_slot: int) -> dict:
        """
        Create a launch chick waypoint for mission planning.

        Args:
            lat, lon, alt: Coordinates where chick should be launched
            chick_slot: 1 for chick1, 2 for chick2

        Returns:
            Waypoint dict suitable for upload_mission()
        """
        return {
            "type": "LAUNCH_CHICK",
            "lat": lat,
            "lon": lon,
            "alt": alt,
            "chick_slot": chick_slot
        }

    def rtl(self, vehicle_id: str) -> bool:
        """Command vehicle to Return To Launch."""
        return self.set_mode(vehicle_id, "RTL")

    def rtl_all(self) -> bool:
        """Command all vehicles to RTL."""
        from ..config import get_all_vehicles
        print("[MAVLink] RTL ALL")
        success = True
        for vid in get_all_vehicles().keys():
            if vid in self._connections or vid in self._telemetry:
                if not self.rtl(vid):
                    success = False
        return success

    # ==================== Telemetry Methods ====================

    def get_telemetry(self, vehicle_id: str) -> Optional[VehicleTelemetry]:
        """Get latest telemetry for a vehicle."""
        return self._telemetry.get(vehicle_id)

    def is_connected(self, vehicle_id: str) -> bool:
        """Check if vehicle is connected (recent heartbeat)."""
        telem = self._telemetry.get(vehicle_id)
        if telem:
            return (time.time() - telem.last_heartbeat) < 5.0
        return False

    def set_vehicle_position(self, vehicle_id: str, lat: float, lon: float, alt: float, heading: float = None):
        """
        Set a vehicle's position (for simulation - e.g., when chick is released from bird).

        In hardware, this would not be needed as the actual vehicle has its own GPS.
        """
        if self._simulation_mode:
            telem = self._telemetry.get(vehicle_id)
            if telem:
                telem.lat = lat
                telem.lon = lon
                telem.alt = alt
                if heading is not None:
                    telem.heading = heading
                # Update home and loiter center to new position
                self._sim_home[vehicle_id] = (lat, lon)
                self._sim_loiter_center[vehicle_id] = (lat, lon)
                print(f"[Sim] Set {vehicle_id} position to ({lat:.5f}, {lon:.5f}, {alt:.0f}m)")

    def activate_swarm(self, config):
        """
        Activate dynamic swarm mode - chicks will track bird position in real-time.

        Args:
            config: SwarmConfig with formation, spacing, alt_offset, coord_mode

        For TRUE SWARMING:
            - Chicks continuously calculate formation position based on bird's telemetry
            - Works via LoRa mesh in hardware, simulation uses direct telemetry
            - Chicks must be released first before they can track
        """
        self._swarm_config = config
        self._swarm_active = True
        print(f"[Swarm] ACTIVATED: {config.formation}, {config.spacing}m spacing, "
              f"{config.alt_offset}m altitude offset, mode={config.coord_mode}")

    def deactivate_swarm(self):
        """Deactivate swarm mode - chicks will return to independent flight."""
        self._swarm_active = False
        self._swarm_config = None
        print("[Swarm] DEACTIVATED")

    def mark_chick_released(self, chick_id: str):
        """Mark a chick as released from the bird (now free to track)."""
        self._chicks_released[chick_id] = True
        self._chicks_attached[chick_id] = False
        print(f"[Swarm] {chick_id} marked as released, can now track bird")

    def is_chick_attached(self, chick_id: str) -> bool:
        """Check if a chick is still attached to carrier."""
        return self._chicks_attached.get(chick_id, False)

    # ==================== Simulation ====================

    def start_simulation(self):
        """Start simulated telemetry for development."""
        from ..config import get_vehicle_performance, get_all_vehicles, SWARM_CONFIG

        self._simulation_mode = True

        # Simulation state
        self._sim_missions = {}  # vehicle_id -> list of waypoints
        self._sim_current_wp = {}  # vehicle_id -> current waypoint index
        self._sim_goto_target = {}  # vehicle_id -> (lat, lon, alt) for GUIDED mode
        self._sim_target_alt = {}  # vehicle_id -> target altitude (persists across mode changes)
        self._sim_home = {}  # vehicle_id -> (lat, lon)
        self._sim_loiter_center = {}  # vehicle_id -> (lat, lon) for orbit center
        self._sim_loiter_angle = {}  # vehicle_id -> current orbit angle (radians)
        self._sim_vehicle_type = {}  # vehicle_id -> "plane" or "copter"

        # Initialize chicks_attached from config
        for chick in SWARM_CONFIG.get("chicks", []):
            self._chicks_attached[chick["id"]] = True

        # Build vehicle list from config
        vehicles = get_all_vehicles()
        sim_vehicles = []
        for vid, info in vehicles.items():
            vtype = info.get("type", "copter")
            sim_vehicles.append((vid, (52.0, -1.5, 127, "LOITER", vtype)))

        # Initialize simulated vehicles using speeds from config
        import random
        for vid, (lat, lon, alt, mode, vtype) in sim_vehicles:
            perf = get_vehicle_performance(vid)
            cruise_speed = perf["cruise_speed_ms"]
            loiter_speed = perf.get("loiter_speed_ms", cruise_speed)

            self._telemetry[vid] = VehicleTelemetry(
                lat=lat, lon=lon, alt=alt,
                heading=random.uniform(0, 360),
                groundspeed=loiter_speed if vtype == "plane" else 0,  # Planes always moving
                airspeed=cruise_speed if vtype == "plane" else 0,
                battery_pct=random.randint(70, 95),
                battery_voltage=random.uniform(14.5, 16.8),
                mode=mode,
                armed=True,
                gps_fix=3,
                gps_sats=random.randint(12, 18),
                last_heartbeat=time.time()
            )
            self._sim_home[vid] = (lat, lon)
            self._sim_vehicle_type[vid] = vtype
            self._sim_loiter_center[vid] = (lat, lon)
            self._sim_loiter_angle[vid] = 0
            self._sim_target_alt[vid] = alt  # Initialize target altitude
            self.connection_changed.emit(vid, True)

        self._sim_timer.start(100)  # 10 Hz updates

    def stop_simulation(self):
        """Stop simulated telemetry."""
        self._sim_timer.stop()
        self._simulation_mode = False

    def _simulate_telemetry(self):
        """Generate simulated telemetry updates with realistic behavior."""
        import random
        import math
        from ..config import get_vehicle_performance, clamp_speed, is_fixed_wing, get_carrier_for_chick, get_vehicle_info

        for vid, telem in self._telemetry.items():
            telem.last_heartbeat = time.time()
            is_plane = self._sim_vehicle_type.get(vid) == "plane"

            # Get vehicle performance specs from config
            perf = get_vehicle_performance(vid)

            # Check if this is a chick (has a carrier)
            carrier_id = get_carrier_for_chick(vid)
            is_chick = carrier_id is not None
            carrier_telem = self._telemetry.get(carrier_id) if carrier_id else None

            # ATTACHED CHICKS: Skip simulation - they inherit from carrier via app.py
            # Only emit telemetry update, don't modify position/speed
            if is_chick and self._chicks_attached.get(vid, False):
                # Attached chicks match carrier's speed
                if carrier_telem:
                    telem.groundspeed = carrier_telem.groundspeed
                    telem.airspeed = carrier_telem.airspeed
                # Still drain battery
                if telem.battery_pct > 10:
                    telem.battery_pct -= random.uniform(0, 0.005)
                self.telemetry_received.emit(vid, telem)
                continue

            # Drain battery slowly
            if telem.battery_pct > 10:
                telem.battery_pct -= random.uniform(0, 0.01)

            # SWARM TRACKING: Released chicks track carrier position dynamically
            if (self._swarm_active and self._swarm_config and
                is_chick and
                self._chicks_released.get(vid) and
                carrier_telem and telem.mode == "AUTO"):

                # Import swarm calculator
                from ..widgets.mission_panel import SwarmCalculator

                # Get chick slot (0-indexed) from vehicle info
                vehicle_info = get_vehicle_info(vid)
                chick_index = vehicle_info.get("slot", 1) - 1  # slot is 1-indexed

                # Calculate formation position based on carrier's current position
                target_lat, target_lon, target_alt = SwarmCalculator.calculate_formation_position(
                    carrier_telem.lat, carrier_telem.lon, carrier_telem.heading, carrier_telem.alt,
                    chick_index, self._swarm_config
                )

                # Fly towards formation position using configured swarm tracking speed
                speed = perf.get("swarm_track_speed_ms", perf["cruise_speed_ms"])
                telem.lat, telem.lon, telem.heading, telem.groundspeed = self._sim_fly_towards(
                    telem.lat, telem.lon, target_lat, target_lon,
                    speed=speed, is_plane=False, current_heading=telem.heading,
                    vehicle_id=vid
                )
                telem.alt = target_alt + random.uniform(-1, 1)

                # Emit telemetry and continue to next vehicle
                self.telemetry_received.emit(vid, telem)
                continue

            # Mode-specific behavior
            if telem.mode == "LOITER":
                if is_plane:
                    # Fixed-wing: orbit around loiter point (can't hover)
                    self._sim_plane_orbit(vid, telem)
                else:
                    # Copter: hover with slight drift
                    telem.lat += random.uniform(-0.000002, 0.000002)
                    telem.lon += random.uniform(-0.000002, 0.000002)
                    telem.groundspeed = random.uniform(0, 2)
                    telem.heading = (telem.heading + random.uniform(-1, 1)) % 360

                # Adjust altitude towards target in LOITER mode
                target_alt = self._sim_target_alt.get(vid)
                if target_alt is not None:
                    telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)

            elif telem.mode == "RTL":
                # Fly towards home using cruise speed from config
                home = self._sim_home.get(vid, (52.0, -1.5))
                speed = perf["cruise_speed_ms"]
                telem.lat, telem.lon, telem.heading, telem.groundspeed = self._sim_fly_towards(
                    telem.lat, telem.lon, home[0], home[1], speed=speed,
                    is_plane=is_plane, current_heading=telem.heading,
                    vehicle_id=vid
                )
                # RTL altitude: maintain current or target, descend near home
                dist = self._sim_distance(telem.lat, telem.lon, home[0], home[1])
                rtl_alt = 30 if is_plane else 15  # Landing altitude
                if dist < 200:
                    # Near home - descend
                    telem.alt = self._sim_adjust_altitude(telem.alt, rtl_alt, perf)
                else:
                    # En route - maintain target altitude or current
                    target_alt = self._sim_target_alt.get(vid, telem.alt)
                    telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)

                # Check if arrived
                if dist < (50 if is_plane else 10):  # Planes need larger radius
                    telem.mode = "LOITER"
                    self._sim_loiter_center[vid] = home
                    self._sim_target_alt[vid] = rtl_alt  # Set target to landing alt
                    self.mode_changed.emit(vid, "LOITER")

            elif telem.mode == "GUIDED":
                # Fly towards goto target using cruise speed from config
                target = self._sim_goto_target.get(vid)
                if target:
                    speed = perf["cruise_speed_ms"]
                    telem.lat, telem.lon, telem.heading, telem.groundspeed = self._sim_fly_towards(
                        telem.lat, telem.lon, target[0], target[1], speed=speed,
                        is_plane=is_plane, current_heading=telem.heading,
                        vehicle_id=vid
                    )

                    # Update altitude towards target altitude
                    target_alt = target[2] if len(target) > 2 else self._sim_target_alt.get(vid, telem.alt)
                    telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)

                    # Check if arrived (both position AND altitude)
                    dist = self._sim_distance(telem.lat, telem.lon, target[0], target[1])
                    alt_diff = abs(telem.alt - target_alt)
                    # Use consistent arrival distance (copters use 30m for prosecution compatibility)
                    arrival_dist = 50 if is_plane else 30
                    if dist < arrival_dist and alt_diff < 5:
                        print(f"[Sim] {vid} ARRIVED at goto target (dist: {dist:.0f}m, alt_diff: {alt_diff:.0f}m)")
                        telem.mode = "LOITER"
                        self._sim_loiter_center[vid] = (target[0], target[1])
                        self._sim_target_alt[vid] = target_alt  # Maintain altitude at arrival
                        self.mode_changed.emit(vid, "LOITER")
                        del self._sim_goto_target[vid]
                else:
                    # No goto target - just adjust altitude if we have a target alt
                    target_alt = self._sim_target_alt.get(vid)
                    if target_alt is not None:
                        telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)

            elif telem.mode == "AUTO":
                # Follow mission waypoints
                mission = self._sim_missions.get(vid, [])
                wp_idx = self._sim_current_wp.get(vid, 0)

                if mission and wp_idx < len(mission):
                    wp = mission[wp_idx]
                    if wp.get("type") != "RTL":
                        target_lat = wp.get("lat", telem.lat)
                        target_lon = wp.get("lon", telem.lon)
                        target_alt = wp.get("alt", self._sim_target_alt.get(vid, 100))
                        # Use waypoint speed if specified, otherwise cruise speed from config
                        wp_speed = wp.get("speed", 0)
                        speed = wp_speed if wp_speed > 0 else perf["cruise_speed_ms"]

                        telem.lat, telem.lon, telem.heading, telem.groundspeed = self._sim_fly_towards(
                            telem.lat, telem.lon, target_lat, target_lon,
                            speed=speed, is_plane=is_plane, current_heading=telem.heading,
                            vehicle_id=vid
                        )

                        # Adjust altitude towards waypoint altitude
                        telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)

                        # Check if arrived at waypoint (position and altitude)
                        dist = self._sim_distance(telem.lat, telem.lon, target_lat, target_lon)
                        alt_diff = abs(telem.alt - target_alt)
                        arrival_dist = 40 if is_plane else 15
                        if dist < arrival_dist and alt_diff < 10:
                            print(f"[Sim] {vid} reached waypoint {wp_idx + 1}: {wp.get('type')} @ {target_alt:.0f}m")

                            # Update target altitude to waypoint altitude
                            self._sim_target_alt[vid] = target_alt

                            # Emit waypoint reached signal (for hardware integration)
                            self.waypoint_reached.emit(vid, wp_idx, wp)

                            # Handle launch chick waypoint - RELEASE THE CHICK
                            if wp.get("type") == "LAUNCH_CHICK":
                                chick_id = wp.get("chick_id", "chick1")
                                print(f"[Sim] {vid} RELEASING {chick_id} at waypoint!")
                                # Emit signal for app.py to handle the release
                                self.chick_launch_triggered.emit(vid, chick_id)

                            self._sim_current_wp[vid] = wp_idx + 1
                    else:
                        # RTL waypoint - switch to RTL mode
                        telem.mode = "RTL"
                        self.mode_changed.emit(vid, "RTL")
                else:
                    # Mission complete - loiter at last position
                    if is_plane:
                        self._sim_plane_orbit(vid, telem)
                    else:
                        telem.groundspeed = random.uniform(0, 2)
                    # Maintain target altitude
                    target_alt = self._sim_target_alt.get(vid)
                    if target_alt is not None:
                        telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)

            else:
                # Other modes (MANUAL, FBWA, etc.) - gentle movement
                if is_plane:
                    # Planes must keep moving at cruise speed
                    cruise = perf["cruise_speed_ms"]
                    telem.groundspeed = cruise + random.uniform(-2, 2)
                    telem.heading = (telem.heading + random.uniform(-3, 3)) % 360
                    move_lat, move_lon = self._sim_move_in_direction(
                        telem.lat, telem.lon, telem.heading, telem.groundspeed * 0.1
                    )
                    telem.lat, telem.lon = move_lat, move_lon
                else:
                    telem.lat += random.uniform(-0.000005, 0.000005)
                    telem.lon += random.uniform(-0.000005, 0.000005)
                    telem.heading = (telem.heading + random.uniform(-2, 2)) % 360

            # Altitude adjustments - use target altitude if set, otherwise use defaults
            target_alt = self._sim_target_alt.get(vid)
            if target_alt is not None:
                # Climb/descend towards target altitude (if not already handled by mode-specific code)
                if telem.mode not in ["GUIDED"]:  # GUIDED already handles altitude above
                    telem.alt = self._sim_adjust_altitude(telem.alt, target_alt, perf)
                # Add small variation for realism
                telem.alt += random.uniform(-0.5, 0.5)
            else:
                # No target altitude set - use default with variation
                if is_plane:
                    default_alt = 100
                else:
                    default_alt = 50
                # Initialize target altitude to current or default
                if vid not in self._sim_target_alt:
                    self._sim_target_alt[vid] = telem.alt if telem.alt > 10 else default_alt
                telem.alt = self._sim_adjust_altitude(telem.alt, self._sim_target_alt[vid], perf)
                telem.alt += random.uniform(-0.5, 0.5)

            if is_plane:
                telem.airspeed = telem.groundspeed + random.uniform(-2, 2)

            self.telemetry_received.emit(vid, telem)

    def _sim_plane_orbit(self, vid: str, telem):
        """Simulate fixed-wing loiter orbit pattern using configured speeds."""
        import math
        import random
        from ..config import get_vehicle_performance

        perf = get_vehicle_performance(vid)
        center = self._sim_loiter_center.get(vid, (telem.lat, telem.lon))
        orbit_radius = perf.get("loiter_radius_m", 80)  # meters from config
        orbit_speed = perf.get("loiter_speed_ms", perf["cruise_speed_ms"])  # m/s from config

        # Advance orbit angle (clockwise)
        angle_increment = (orbit_speed * 0.1) / orbit_radius  # radians per tick
        self._sim_loiter_angle[vid] = self._sim_loiter_angle.get(vid, 0) + angle_increment
        angle = self._sim_loiter_angle[vid]

        # Calculate position on orbit
        offset_lat = (orbit_radius * math.cos(angle)) / 111000
        offset_lon = (orbit_radius * math.sin(angle)) / (111000 * math.cos(math.radians(center[0])))

        telem.lat = center[0] + offset_lat
        telem.lon = center[1] + offset_lon

        # Heading is tangent to orbit (perpendicular to radius, clockwise)
        telem.heading = (math.degrees(angle) + 90) % 360
        telem.groundspeed = orbit_speed + random.uniform(-1, 1)

    def _sim_move_in_direction(self, lat: float, lon: float, heading: float, distance: float) -> tuple:
        """Move a point in a direction by a distance (meters). Returns (new_lat, new_lon)."""
        import math
        move_lat = distance * math.cos(math.radians(heading)) / 111000
        move_lon = distance * math.sin(math.radians(heading)) / (111000 * math.cos(math.radians(lat)))
        return (lat + move_lat, lon + move_lon)

    def _sim_fly_towards(self, lat: float, lon: float, target_lat: float, target_lon: float,
                         speed: float = 15, is_plane: bool = False, current_heading: float = None,
                         vehicle_id: str = None) -> tuple:
        """
        Simulate flying towards a target. Returns (new_lat, new_lon, heading, groundspeed).

        For hardware integration:
            - This method simulates what the autopilot does internally
            - Real implementation uses MAV_CMD_NAV_WAYPOINT
            - Turn rate limits for planes ensure realistic behavior
            - Minimum speed enforced for fixed-wing to prevent stall
        """
        import math
        from ..config import clamp_speed, get_vehicle_performance

        # Enforce speed limits (prevents stall for fixed-wing)
        if vehicle_id:
            speed = clamp_speed(vehicle_id, speed)
            perf = get_vehicle_performance(vehicle_id)
            max_turn_rate = perf.get("turn_rate_deg_s", 15 if is_plane else 180)
        else:
            max_turn_rate = 15 if is_plane else 180

        # Calculate desired bearing to target
        d_lat = target_lat - lat
        d_lon = target_lon - lon
        desired_heading = math.degrees(math.atan2(d_lon, d_lat)) % 360

        # Calculate distance
        dist = self._sim_distance(lat, lon, target_lat, target_lon)

        # For planes: limit turn rate (can't turn instantly)
        if is_plane and current_heading is not None:
            heading_diff = ((desired_heading - current_heading + 180) % 360) - 180
            # Turn rate per tick (10Hz updates)
            max_turn_per_tick = max_turn_rate * 0.1
            if abs(heading_diff) > max_turn_per_tick:
                heading_diff = max_turn_per_tick if heading_diff > 0 else -max_turn_per_tick
            heading = (current_heading + heading_diff) % 360
        else:
            heading = desired_heading

        # Move towards target (speed in m/s, update at 10Hz)
        move_dist = min(speed * 0.1, dist)  # Don't overshoot
        move_lat = move_dist * math.cos(math.radians(heading)) / 111000
        move_lon = move_dist * math.sin(math.radians(heading)) / (111000 * math.cos(math.radians(lat)))

        return (lat + move_lat, lon + move_lon, heading, speed)

    def _sim_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate approximate distance in meters."""
        import math
        d_lat = (lat2 - lat1) * 111000
        d_lon = (lon2 - lon1) * 111000 * math.cos(math.radians(lat1))
        return math.sqrt(d_lat**2 + d_lon**2)

    def _sim_adjust_altitude(self, current_alt: float, target_alt: float, perf: dict) -> float:
        """
        Adjust altitude towards target using climb/descent rates.

        Args:
            current_alt: Current altitude in meters
            target_alt: Target altitude in meters
            perf: Vehicle performance profile with climb_rate_ms and descent_rate_ms

        Returns:
            New altitude (moved towards target at appropriate rate)
        """
        alt_diff = target_alt - current_alt

        if abs(alt_diff) < 0.5:
            # Close enough - snap to target
            return target_alt

        # Get climb/descent rate (10Hz updates = 0.1 second intervals)
        if alt_diff > 0:
            # Climbing
            rate = perf.get("climb_rate_ms", 5) * 0.1  # meters per tick
            new_alt = current_alt + min(rate, alt_diff)
        else:
            # Descending
            rate = perf.get("descent_rate_ms", 5) * 0.1  # meters per tick
            new_alt = current_alt - min(rate, abs(alt_diff))

        return new_alt
