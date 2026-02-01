#!/usr/bin/env python3
"""
SITL Diagnostic Tool - Tests MAVLink connectivity and commands.
Run this while SITL instances are running to verify they work.

Key changes from previous version:
- Waits for GPS 3D fix before attempting arm
- Monitors STATUSTEXT for pre-arm failures
- Requests data streams for continuous telemetry
- More robust arm/takeoff sequence
"""

import time
import sys

try:
    from pymavlink import mavutil
except ImportError:
    print("ERROR: pymavlink not installed. Run: pip install pymavlink")
    sys.exit(1)


def request_data_streams(conn):
    """Request telemetry data streams from the vehicle."""
    # Request all data streams at 4Hz
    conn.mav.request_data_stream_send(
        conn.target_system,
        conn.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_ALL,
        4,  # 4 Hz
        1   # Start sending
    )


def wait_for_gps(conn, name, timeout=60):
    """Wait for GPS 3D fix."""
    print(f"[{name}] Waiting for GPS 3D fix...")
    start = time.time()

    while time.time() - start < timeout:
        msg = conn.recv_match(type='GPS_RAW_INT', blocking=True, timeout=1)
        if msg:
            fix_types = {0: "No GPS", 1: "No Fix", 2: "2D", 3: "3D", 4: "DGPS", 5: "RTK Float", 6: "RTK Fixed"}
            fix_name = fix_types.get(msg.fix_type, f"Fix_{msg.fix_type}")
            sats = msg.satellites_visible

            if msg.fix_type >= 3:
                print(f"[{name}] GPS: {fix_name}, {sats} sats - READY")
                return True
            else:
                print(f"[{name}] GPS: {fix_name}, {sats} sats - waiting...")

        # Check for any pre-arm failure messages
        status = conn.recv_match(type='STATUSTEXT', blocking=False)
        if status:
            print(f"[{name}] STATUS: {status.text}")

    print(f"[{name}] GPS timeout!")
    return False


def wait_for_ekf(conn, name, timeout=30):
    """Wait for EKF to be ready (healthy)."""
    print(f"[{name}] Waiting for EKF...")
    start = time.time()

    while time.time() - start < timeout:
        msg = conn.recv_match(type='EKF_STATUS_REPORT', blocking=True, timeout=1)
        if msg:
            # Check EKF flags - we want attitude and velocity estimates
            flags = msg.flags
            # EKF_ATTITUDE = 1, EKF_VELOCITY_HORIZ = 2, EKF_VELOCITY_VERT = 4, EKF_POS_HORIZ_REL = 8
            if flags & 0x0F == 0x0F:  # All basic flags set
                print(f"[{name}] EKF ready (flags=0x{flags:02X})")
                return True

        # Check for status messages
        status = conn.recv_match(type='STATUSTEXT', blocking=False)
        if status:
            print(f"[{name}] STATUS: {status.text}")

    print(f"[{name}] EKF timeout (may still work)")
    return True  # Continue anyway, some SITLs don't report EKF


def get_prearm_status(conn, name, duration=3):
    """Collect any pre-arm status messages."""
    print(f"[{name}] Checking pre-arm status...")
    start = time.time()
    messages = []

    while time.time() - start < duration:
        msg = conn.recv_match(type='STATUSTEXT', blocking=True, timeout=0.5)
        if msg:
            text = msg.text if hasattr(msg, 'text') else str(msg)
            messages.append(text)
            print(f"[{name}] STATUS: {text}")

    return messages


def set_mode_and_wait(conn, name, mode_name, mode_id, timeout=5):
    """Set mode and wait for confirmation."""
    print(f"[{name}] Setting mode to {mode_name} ({mode_id})...")

    # Determine if plane or copter based on last heartbeat
    conn.set_mode(mode_id)

    # Wait for mode change confirmation
    start = time.time()
    while time.time() - start < timeout:
        msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg:
            if msg.custom_mode == mode_id:
                print(f"[{name}] Mode changed to {mode_name}")
                return True

    print(f"[{name}] Mode change timeout")
    return False


def arm_and_wait(conn, name, force=True, timeout=10):
    """Arm the vehicle and wait for confirmation."""
    print(f"[{name}] Arming{'(force)' if force else ''}...")

    # Send arm command
    conn.mav.command_long_send(
        conn.target_system,
        conn.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,  # confirmation
        1,  # arm
        21196 if force else 0,  # force arm magic number
        0, 0, 0, 0, 0
    )

    # Wait for ACK
    ack = conn.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
    if ack:
        result_names = {0: "ACCEPTED", 1: "TEMPORARILY_REJECTED", 2: "DENIED", 3: "UNSUPPORTED", 4: "FAILED"}
        result = result_names.get(ack.result, f"RESULT_{ack.result}")
        print(f"[{name}] ARM ACK: {result}")

        if ack.result != 0:
            # Collect status messages to see why
            get_prearm_status(conn, name, 2)
            return False

    # Wait for armed state in heartbeat
    start = time.time()
    while time.time() - start < timeout:
        msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg:
            armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
            if armed:
                print(f"[{name}] ARMED!")
                return True
            else:
                print(f"[{name}] Waiting for armed state...")

        # Check status messages for any pre-arm failures
        status = conn.recv_match(type='STATUSTEXT', blocking=False)
        if status:
            text = status.text if hasattr(status, 'text') else str(status)
            print(f"[{name}] STATUS: {text}")

    print(f"[{name}] Arm timeout - vehicle did not arm")
    return False


def takeoff(conn, name, altitude=30, timeout=5):
    """Send takeoff command."""
    print(f"[{name}] Takeoff to {altitude}m...")

    conn.mav.command_long_send(
        conn.target_system,
        conn.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0,  # confirmation
        0,  # pitch
        0, 0, 0,  # empty
        0, 0,  # lat/lon (current)
        altitude
    )

    ack = conn.recv_match(type='COMMAND_ACK', blocking=True, timeout=timeout)
    if ack:
        result_names = {0: "ACCEPTED", 1: "TEMPORARILY_REJECTED", 2: "DENIED", 3: "UNSUPPORTED", 4: "FAILED"}
        result = result_names.get(ack.result, f"RESULT_{ack.result}")
        print(f"[{name}] TAKEOFF ACK: {result}")
        return ack.result == 0

    print(f"[{name}] Takeoff no ACK")
    return False


def monitor_flight(conn, name, duration=15):
    """Monitor vehicle during flight."""
    print(f"\n[{name}] Monitoring flight for {duration}s...")
    start = time.time()
    last_pos_time = 0

    while time.time() - start < duration:
        # Check for position updates
        msg = conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=0.5)
        if msg:
            lat = msg.lat / 1e7
            lon = msg.lon / 1e7
            alt = msg.relative_alt / 1000.0
            vz = msg.vz / 100.0  # cm/s to m/s (positive = down)

            if time.time() - last_pos_time > 1:  # Print every second
                print(f"[{name}] Alt={alt:.1f}m, Vz={-vz:.1f}m/s (lat={lat:.6f}, lon={lon:.6f})")
                last_pos_time = time.time()

        # Check for status messages
        status = conn.recv_match(type='STATUSTEXT', blocking=False)
        if status:
            text = status.text if hasattr(status, 'text') else str(status)
            print(f"[{name}] STATUS: {text}")


def test_connection(name, conn_str):
    """Test connection to a single SITL instance with full initialization."""
    print(f"\n{'='*60}")
    print(f" Testing: {name} at {conn_str}")
    print('='*60)

    try:
        # Connect
        print(f"[{name}] Connecting...")
        conn = mavutil.mavlink_connection(conn_str, source_system=255)

        # Wait for heartbeat
        print(f"[{name}] Waiting for heartbeat...")
        msg = conn.recv_match(type='HEARTBEAT', blocking=True, timeout=10)

        if not msg:
            print(f"[{name}] ERROR: No heartbeat received")
            return None, None

        # Parse heartbeat
        mav_type = msg.type
        type_names = {1: "PLANE", 2: "QUADCOPTER", 3: "COAX", 4: "HELICOPTER", 13: "HEXACOPTER", 14: "OCTOCOPTER"}
        type_name = type_names.get(mav_type, f"TYPE_{mav_type}")
        is_copter = mav_type in [2, 3, 4, 13, 14]

        armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0

        print(f"[{name}] Connected! SysID={msg.get_srcSystem()}, Type={type_name}")
        print(f"[{name}] Armed={armed}, Mode={msg.custom_mode}")

        # Request data streams
        request_data_streams(conn)

        return conn, is_copter

    except Exception as e:
        print(f"[{name}] ERROR: {e}")
        return None, None


def test_full_flight_sequence(conn, name, is_copter=True):
    """Run full arm/takeoff/monitor sequence."""
    print(f"\n{'='*60}")
    print(f" Flight Test: {name}")
    print('='*60)

    # 1. Wait for GPS
    if not wait_for_gps(conn, name, timeout=30):
        print(f"[{name}] Skipping arm - no GPS")
        return False

    # 2. Set mode (GUIDED for copter, FBWA for plane)
    if is_copter:
        mode_name, mode_id = "GUIDED", 4
    else:
        mode_name, mode_id = "FBWA", 5

    set_mode_and_wait(conn, name, mode_name, mode_id)

    # Small delay to let mode settle
    time.sleep(1)

    # 3. Check pre-arm status
    get_prearm_status(conn, name, 2)

    # 4. Arm
    if not arm_and_wait(conn, name, force=True, timeout=10):
        print(f"[{name}] Failed to arm")
        return False

    # 5. Takeoff (copter only)
    if is_copter:
        time.sleep(0.5)  # Brief delay after arm
        if not takeoff(conn, name, altitude=30):
            print(f"[{name}] Takeoff command failed")
            # Continue anyway - monitor what happens

    # 6. Monitor flight
    monitor_flight(conn, name, duration=15)

    return True


def main():
    print("="*60)
    print("  SITL Diagnostic Tool v2")
    print("="*60)
    print("\nMake sure SITL instances are running (tools/start_sitl.py)")
    print("This will test connectivity, GPS, arming, and flight.\n")

    # Test connections
    connections = {
        "bird1": "tcp:127.0.0.1:5760",
        "chick1.1": "tcp:127.0.0.1:5770",
        "chick1.2": "tcp:127.0.0.1:5780",
    }

    # First pass: connect to all
    active_conns = {}
    for name, conn_str in connections.items():
        conn, is_copter = test_connection(name, conn_str)
        if conn:
            active_conns[name] = (conn, is_copter)

    if not active_conns:
        print("\nERROR: No SITL instances connected!")
        print("Run: python tools/start_sitl.py")
        input("\nPress Enter to exit...")
        return

    print(f"\n{'='*60}")
    print(f"  Connected to {len(active_conns)} SITL instance(s)")
    print('='*60)

    # Test flight on first copter
    for name, (conn, is_copter) in active_conns.items():
        if is_copter:
            test_full_flight_sequence(conn, name, is_copter=True)
            break  # Just test one copter for now

    # Also test plane if connected
    for name, (conn, is_copter) in active_conns.items():
        if not is_copter:
            print(f"\n[{name}] Plane test - setting FBWA mode and arming")
            set_mode_and_wait(conn, name, "FBWA", 5)
            time.sleep(1)
            arm_and_wait(conn, name, force=True)
            # Planes need a runway/VTOL to actually take off
            # Just verify it arms
            break

    print("\n" + "="*60)
    print("  Diagnostic complete!")
    print("="*60)

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
