# LoRa T-Beam Manager
# Handles communication via Lilygo T-Beam mesh for custom datawords/commands
#
# Integration points:
#   - USB Serial to T-Beam on GCS
#   - Meshtastic protocol OR custom firmware
#
# V1 Nodes: GCS, Bird, Chick1, Chick2
# Orbs receive data from Chicks via serial (no mesh radio in V1)
#
# Dependencies (install when ready):
#   pip install pyserial
#   pip install meshtastic  # If using Meshtastic firmware

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum
import struct
import time


class NodeID(Enum):
    """T-Beam node identifiers (V1 protocol)."""
    GCS = 0x00
    BIRD = 0x01
    CHICK1 = 0x02
    CHICK2 = 0x03
    # 0x04-0x07 reserved for future Orb radios
    BROADCAST = 0xFF


class MsgType(Enum):
    """V1 Codeword message types."""
    TELEM = 0x01      # 16B - Compact telemetry
    CMD = 0x02        # 4B  - Command code
    ACK = 0x03        # 3B  - Acknowledgment
    TGT = 0x04        # 12B - Target coordinates
    STATUS = 0x05     # 6B  - System status
    ALERT = 0x06      # 4B  - Priority alert
    SDR = 0x07        # 20B - SDR summary
    PING = 0x08       # 2B  - Heartbeat
    TEXT = 0xFE       # var - ASCII text (emergency)
    RAW = 0xFF        # var - Raw binary


class CmdCode(Enum):
    """V1 Command codes."""
    ARM_SYSTEM = 0x01     # Arm/disarm vehicle motors
    RTL = 0x02
    LAND = 0x03
    LOITER = 0x04
    RESUME = 0x05
    HOLD = 0x06
    MODE = 0x07
    ARM_ORB = 0x08        # Arm orb slot (param=slot, 0=disarm)
    RELEASE_ORB = 0x09    # Release orb slot
    TARGET_ORB = 0x0A     # Target orb (followed by TGT msg)
    SCAN_START = 0x0B
    SCAN_STOP = 0x0C
    REPORT = 0x0D
    LAUNCH_CHICK = 0x10   # Launch chick from Bird (param=slot 1 or 2)
    ARM_CHICK = 0x11      # Arm chick motors pre-launch
    REBOOT = 0xFE
    EMERGENCY = 0xFF


@dataclass
class NodeStatus:
    """Status of a mesh node."""
    node_id: NodeID
    rssi: int = 0          # Signal strength dBm
    snr: float = 0.0       # Signal-to-noise ratio
    last_seen: float = 0.0 # Timestamp
    battery_pct: int = 0   # T-Beam battery (if applicable)

    @property
    def is_connected(self) -> bool:
        return (time.time() - self.last_seen) < 10.0


@dataclass
class TargetCoordinate:
    """Target coordinate for Orb upload."""
    target_id: str
    lat: float
    lon: float
    alt: Optional[float] = None


class LoRaManager(QObject):
    """
    Manages T-Beam LoRa mesh communication.

    Network topology:
        GCS T-Beam ◄──► Bird T-Beam
             │              │
             ▼              ▼
        Chick1 T-Beam  Chick2 T-Beam

    Message types:
        - Node status/heartbeat
        - Target coordinates (for Orb upload)
        - Custom commands
        - Mesh RSSI reporting

    Usage:
        manager = LoRaManager()
        manager.node_status_updated.connect(on_node_status)
        manager.connect("/dev/ttyUSB0")  # or "COM3"
        manager.send_target_to_chick("chick1", target)
    """

    # Signals
    node_status_updated = pyqtSignal(str, object)  # node_name, NodeStatus
    message_received = pyqtSignal(str, bytes)       # from_node, data
    connection_changed = pyqtSignal(bool)           # connected

    def __init__(self, parent=None):
        super().__init__(parent)

        self._serial = None
        self._port = None
        self._nodes: Dict[str, NodeStatus] = {}

        # Simulation
        self._simulation_mode = True
        self._sim_timer = QTimer()
        self._sim_timer.timeout.connect(self._simulate_mesh)

    # ==================== Connection ====================

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """
        Connect to T-Beam via serial.

        Args:
            port: Serial port (e.g., "COM3" or "/dev/ttyUSB0")
            baudrate: Usually 115200 for T-Beam

        TODO: Implement with pyserial
            import serial
            self._serial = serial.Serial(port, baudrate, timeout=1)

        For Meshtastic firmware:
            import meshtastic.serial_interface
            self._interface = meshtastic.serial_interface.SerialInterface(port)
        """
        print(f"[LoRa] Connect requested: {port} @ {baudrate}")
        self._port = port
        # TODO: Real implementation
        return False

    def disconnect(self):
        """Disconnect from T-Beam."""
        print("[LoRa] Disconnect")
        if self._serial:
            self._serial.close()
            self._serial = None
        self.connection_changed.emit(False)

    # ==================== Commands ====================

    def send_target_to_chick(self, chick_id: str, target: TargetCoordinate) -> bool:
        """
        Send target coordinates to a Chick for Orb upload.

        The Chick will store this and upload to the Orb via serial before release.

        Args:
            chick_id: "chick1" or "chick2"
            target: Target coordinate data

        Protocol: TGT message (12 bytes)
            [0x04][TARGET_NODE][LAT_3B][LON_3B][ALT_2B][ORB_SLOT][FLAGS]

        Coordinate encoding (24-bit):
            LAT: (lat + 90) * 46603 as uint24  (~2.4m resolution)
            LON: (lon + 180) * 23301 as uint24 (~4.8m resolution)
        """
        target_node = NodeID.CHICK1.value if chick_id == "chick1" else NodeID.CHICK2.value

        # Encode coordinates as 24-bit integers
        lat_enc = int((target.lat + 90) * 46603) & 0xFFFFFF
        lon_enc = int((target.lon + 180) * 23301) & 0xFFFFFF
        alt_dm = int((target.alt or 0) * 10) & 0xFFFF  # decimeters

        # Determine orb slot from target_id (1-4 maps to slot 1-2 on each chick)
        orb_slot = (int(target.target_id) - 1) % 2 + 1

        packet = bytes([MsgType.TGT.value, target_node])
        packet += lat_enc.to_bytes(3, 'big')
        packet += lon_enc.to_bytes(3, 'big')
        packet += struct.pack('>H', alt_dm)
        packet += bytes([orb_slot, 0x00])  # flags=0 (store only)

        print(f"[LoRa] Target to {chick_id} slot {orb_slot}: {target.lat:.5f}, {target.lon:.5f} -> {packet.hex()}")

        # TODO: self._serial.write(packet)
        return False

    def send_arm_command(self, chick_id: str, orb_slot: int) -> bool:
        """
        Send ARM_ORB command for specific Orb slot.

        Args:
            chick_id: "chick1" or "chick2"
            orb_slot: 1 or 2

        Protocol: CMD message (4 bytes)
            [0x02][TARGET_NODE][CMD_ARM_ORB=0x08][orb_slot]
        """
        target = NodeID.CHICK1.value if chick_id == "chick1" else NodeID.CHICK2.value
        packet = bytes([MsgType.CMD.value, target, CmdCode.ARM_ORB.value, orb_slot])
        print(f"[LoRa] Arm ORB: {chick_id} slot {orb_slot} -> {packet.hex()}")

        # TODO: self._serial.write(packet)
        return False

    def send_disarm_command(self, chick_id: str, orb_slot: int) -> bool:
        """
        Send ARM_ORB command with param=0 to disarm.

        Args:
            chick_id: "chick1" or "chick2"
            orb_slot: 1 or 2 (identifies which orb, param=0 means disarm)

        Protocol: CMD message (4 bytes)
            [0x02][TARGET_NODE][CMD_ARM_ORB=0x08][0x00]
        """
        target = NodeID.CHICK1.value if chick_id == "chick1" else NodeID.CHICK2.value
        # Note: param=0 means disarm the currently armed orb
        packet = bytes([MsgType.CMD.value, target, CmdCode.ARM_ORB.value, 0x00])
        print(f"[LoRa] Disarm ORB: {chick_id} slot {orb_slot} -> {packet.hex()}")

        # TODO: self._serial.write(packet)
        return False

    def send_release_command(self, chick_id: str, orb_slot: int) -> bool:
        """
        Send RELEASE_ORB command for specific Orb slot.

        Args:
            chick_id: "chick1" or "chick2"
            orb_slot: 1 or 2

        Protocol: CMD message (4 bytes)
            [0x02][TARGET_NODE][CMD_RELEASE_ORB=0x09][orb_slot]
        """
        target = NodeID.CHICK1.value if chick_id == "chick1" else NodeID.CHICK2.value
        packet = bytes([MsgType.CMD.value, target, CmdCode.RELEASE_ORB.value, orb_slot])
        print(f"[LoRa] Release ORB: {chick_id} slot {orb_slot} -> {packet.hex()}")

        # TODO: self._serial.write(packet)
        return False

    def send_launch_chick_command(self, chick_slot: int) -> bool:
        """
        Send LAUNCH_CHICK command to Bird to release a Chick.

        The Bird will execute the mechanical release sequence and
        the Chick will begin its autonomous launch procedure.

        Args:
            chick_slot: 1 (chick1) or 2 (chick2)

        Protocol: CMD message (4 bytes)
            [0x02][BIRD][CMD_LAUNCH_CHICK=0x10][chick_slot]

        Hardware Implementation (Version 1):
            1. GCS sends this command via LoRa mesh
            2. Bird's T-Beam receives and forwards to Pi 5
            3. Pi 5 triggers servo on GPIO pin (release mechanism)
            4. Chick detaches and drops ~2m before motors engage
            5. Chick's ArduPilot enters STABILIZE then AUTO mode
            6. Chick confirms launch via return LoRa ACK

        Safety:
            - Requires Bird in level flight
            - Minimum altitude check (50m AGL)
            - Chick motors pre-armed before release
        """
        packet = bytes([MsgType.CMD.value, NodeID.BIRD.value, CmdCode.LAUNCH_CHICK.value, chick_slot])
        print(f"[LoRa] Launch Chick: slot {chick_slot} -> {packet.hex()}")

        # Hardware V1: Uncomment when T-Beam connected
        # if self._serial and self._serial.is_open:
        #     self._serial.write(packet)
        #     return True
        return True  # Return True for simulation

    def send_arm_chick_command(self, chick_slot: int) -> bool:
        """
        Send ARM_CHICK command to arm Chick motors before launch.

        Args:
            chick_slot: 1 (chick1) or 2 (chick2)

        Protocol: CMD message (4 bytes)
            [0x02][BIRD][CMD_ARM_CHICK=0x11][chick_slot]
        """
        packet = bytes([MsgType.CMD.value, NodeID.BIRD.value, CmdCode.ARM_CHICK.value, chick_slot])
        print(f"[LoRa] Arm Chick: slot {chick_slot} -> {packet.hex()}")

        # TODO: self._serial.write(packet)
        return True  # Return True for simulation

    def request_status(self):
        """Request status from all mesh nodes."""
        print("[LoRa] Request mesh status")
        # TODO: Send status request packet

    # ==================== Status ====================

    def get_node_status(self, node_name: str) -> Optional[NodeStatus]:
        """Get status of a mesh node."""
        return self._nodes.get(node_name)

    def get_all_nodes(self) -> Dict[str, NodeStatus]:
        """Get all node statuses."""
        return self._nodes.copy()

    # ==================== Simulation ====================

    def start_simulation(self):
        """Start simulated mesh for development."""
        self._simulation_mode = True

        # Initialize simulated nodes
        for name, node_id in [("bird", NodeID.BIRD), ("chick1", NodeID.CHICK1), ("chick2", NodeID.CHICK2)]:
            self._nodes[name] = NodeStatus(
                node_id=node_id,
                rssi=-67 - (ord(name[0]) % 20),  # Varying RSSI
                snr=9.5,
                last_seen=time.time(),
                battery_pct=95
            )

        self._sim_timer.start(1000)  # 1 Hz updates
        self.connection_changed.emit(True)

    def stop_simulation(self):
        """Stop mesh simulation."""
        self._sim_timer.stop()
        self._simulation_mode = False

    def _simulate_mesh(self):
        """Simulate mesh status updates."""
        import random

        for name, status in self._nodes.items():
            # Fluctuate RSSI slightly
            status.rssi += random.randint(-2, 2)
            status.rssi = max(-100, min(-40, status.rssi))
            status.last_seen = time.time()

            self.node_status_updated.emit(name, status)
