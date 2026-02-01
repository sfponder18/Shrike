# GCS Configuration
# SwarmDrones Ground Control Station

# Window
WINDOW_TITLE = "SWARM GCS"
WINDOW_SIZE = (1920, 1080)

# =============================================================================
# SWARM CONFIGURATION
# =============================================================================
# Hierarchical naming: bird1 carries chick1.1 and chick1.2
# Each bird can have multiple chicks, each chick can have orbs
#
# Vehicle IDs:
#   bird1, bird2, ...
#   chick1.1, chick1.2, chick2.1, chick2.2, ...
#   orb1.1.1, orb1.1.2, ... (future)
#

SWARM_CONFIG = {
    "birds": [
        {
            "id": "bird1",
            "name": "BIRD1",
            "icon": "✈",
            "type": "plane",
            "chicks": ["chick1.1", "chick1.2"],  # Chicks carried by this bird
        },
        # Add more birds:
        # {"id": "bird2", "name": "BIRD2", "icon": "✈", "type": "plane", "chicks": ["chick2.1", "chick2.2"]},
    ],
    "chicks": [
        {
            "id": "chick1.1",
            "name": "CHK1.1",
            "icon": "⬡",
            "type": "copter",
            "carrier": "bird1",
            "slot": 1,
            "orb_slots": 2,
        },
        {
            "id": "chick1.2",
            "name": "CHK1.2",
            "icon": "⬡",
            "type": "copter",
            "carrier": "bird1",
            "slot": 2,
            "orb_slots": 2,
        },
        # Add more chicks for bird2:
        # {"id": "chick2.1", "name": "CHK2.1", "icon": "⬡", "type": "copter", "carrier": "bird2", "slot": 1},
    ],
}

# SITL port assignments - map vehicle ID to connection
# When connecting, we verify the vehicle type matches expected type
SITL_VEHICLE_PORTS = {
    "bird1": {"port": 5760, "expected_type": "plane"},
    "chick1.1": {"port": 5770, "expected_type": "copter"},
    "chick1.2": {"port": 5780, "expected_type": "copter"},
}

def get_all_vehicles():
    """Get all vehicles from swarm config as flat dict."""
    vehicles = {}
    for bird in SWARM_CONFIG["birds"]:
        vehicles[bird["id"]] = {
            "name": bird["name"],
            "icon": bird["icon"],
            "type": bird["type"],
            "chicks": bird.get("chicks", []),
        }
    for chick in SWARM_CONFIG["chicks"]:
        vehicles[chick["id"]] = {
            "name": chick["name"],
            "icon": chick["icon"],
            "type": chick["type"],
            "carrier": chick["carrier"],
            "slot": chick["slot"],
        }
    return vehicles

def get_vehicle_info(vehicle_id: str) -> dict:
    """Get info for a specific vehicle."""
    return get_all_vehicles().get(vehicle_id, {})

def get_carrier_for_chick(chick_id: str) -> str:
    """Get the carrier bird ID for a chick."""
    for chick in SWARM_CONFIG["chicks"]:
        if chick["id"] == chick_id:
            return chick["carrier"]
    return None

def get_chicks_for_bird(bird_id: str) -> list:
    """Get list of chick IDs for a bird."""
    for bird in SWARM_CONFIG["birds"]:
        if bird["id"] == bird_id:
            return bird.get("chicks", [])
    return []

# Legacy VEHICLES dict for backwards compatibility
VEHICLES = get_all_vehicles()

# Flight modes (ArduPilot)
PLANE_MODES = ["MANUAL", "FBWA", "FBWB", "AUTO", "RTL", "LOITER", "GUIDED", "LAND"]
COPTER_MODES = ["STABILIZE", "ALT_HOLD", "LOITER", "AUTO", "RTL", "GUIDED", "LAND"]

# =============================================================================
# VEHICLE PERFORMANCE CONFIGURATION
# Used for mission planning estimates (time, distance, battery)
# Update these values to match your actual aircraft specs
# =============================================================================

# Performance profiles by vehicle TYPE (not individual vehicle)
# Individual vehicles inherit from their type
PERFORMANCE_PROFILES = {
    "plane": {
        "cruise_speed_ms": 18,        # m/s (approx 65 km/h) - V1 bird is slower
        "max_speed_ms": 25,           # m/s
        "min_speed_ms": 12,           # m/s (stall speed)
        "loiter_speed_ms": 18,        # m/s (orbit speed)
        "climb_rate_ms": 3,           # m/s
        "descent_rate_ms": 5,         # m/s
        "battery_capacity_mah": 10000,  # mAh
        "avg_current_draw_a": 15,     # Amps (cruise)
        "endurance_min": 40,          # Minutes at cruise
        "loiter_radius_m": 80,        # Loiter orbit radius
        "turn_rate_deg_s": 15,        # Max turn rate
    },
    "copter": {
        "cruise_speed_ms": 22,        # m/s - chicks are FASTER than bird v1
        "max_speed_ms": 35,           # m/s (sprint speed)
        "min_speed_ms": 0,            # Can hover
        "loiter_speed_ms": 0,         # Hovers in place
        "swarm_track_speed_ms": 25,   # m/s (speed when tracking bird in swarm)
        "climb_rate_ms": 8,           # m/s
        "descent_rate_ms": 5,         # m/s
        "battery_capacity_mah": 5000, # mAh
        "avg_current_draw_a": 20,     # Amps (cruise)
        "endurance_min": 15,          # Minutes at cruise
        "loiter_radius_m": 0,         # Can hover in place
        "turn_rate_deg_s": 180,       # Can rotate quickly
    },
}

# Optional per-vehicle overrides (if a specific vehicle differs from its type profile)
VEHICLE_PERFORMANCE_OVERRIDES = {
    # Example: "bird1": {"cruise_speed_ms": 20},  # Bird1 is faster than default plane
}

def get_vehicle_performance(vehicle_id: str) -> dict:
    """
    Get performance specs for a vehicle.

    Looks up the vehicle's type, gets the profile for that type,
    then applies any vehicle-specific overrides.
    """
    # Get vehicle info to determine type
    vehicle_info = get_vehicle_info(vehicle_id)
    vehicle_type = vehicle_info.get("type", "copter")

    # Get base profile for this type
    profile = PERFORMANCE_PROFILES.get(vehicle_type, PERFORMANCE_PROFILES["copter"]).copy()
    profile["type"] = vehicle_type

    # Apply any vehicle-specific overrides
    overrides = VEHICLE_PERFORMANCE_OVERRIDES.get(vehicle_id, {})
    profile.update(overrides)

    return profile


def clamp_speed(vehicle_id: str, speed: float) -> float:
    """
    Clamp speed to valid range for the aircraft type.

    For fixed-wing (plane): Enforces minimum speed to prevent stall.
    For rotary-wing (copter): Allows zero speed (hover).

    Args:
        vehicle_id: Vehicle identifier
        speed: Requested speed in m/s

    Returns:
        Speed clamped to valid range [min_speed_ms, max_speed_ms]
    """
    perf = get_vehicle_performance(vehicle_id)
    min_speed = perf.get("min_speed_ms", 0)
    max_speed = perf.get("max_speed_ms", 50)

    # Enforce stall speed for fixed-wing aircraft
    if perf.get("type") == "plane" and speed < min_speed:
        return min_speed

    return max(min_speed, min(speed, max_speed))


def is_fixed_wing(vehicle_id: str) -> bool:
    """Check if vehicle is a fixed-wing aircraft (cannot hover)."""
    perf = get_vehicle_performance(vehicle_id)
    return perf.get("type") == "plane"

def estimate_leg_time(vehicle_id: str, distance_m: float, alt_change_m: float = 0) -> float:
    """
    Estimate time to fly a mission leg.

    Args:
        vehicle_id: Vehicle identifier
        distance_m: Horizontal distance in meters
        alt_change_m: Altitude change in meters (positive = climb)

    Returns:
        Estimated time in seconds
    """
    perf = get_vehicle_performance(vehicle_id)

    # Horizontal time
    horiz_time = distance_m / perf["cruise_speed_ms"]

    # Vertical time
    if alt_change_m > 0:
        vert_time = alt_change_m / perf["climb_rate_ms"]
    elif alt_change_m < 0:
        vert_time = abs(alt_change_m) / perf["descent_rate_ms"]
    else:
        vert_time = 0

    # Return max of the two (assumes simultaneous climb/cruise)
    return max(horiz_time, vert_time)

def estimate_leg_battery(vehicle_id: str, time_sec: float) -> float:
    """
    Estimate battery percentage used for a mission leg.

    Args:
        vehicle_id: Vehicle identifier
        time_sec: Time in seconds

    Returns:
        Battery percentage used (0-100)
    """
    perf = get_vehicle_performance(vehicle_id)

    # mAh used = (Amps * hours) * 1000
    hours = time_sec / 3600
    mah_used = perf["avg_current_draw_a"] * hours * 1000

    # Percentage of total capacity
    pct_used = (mah_used / perf["battery_capacity_mah"]) * 100

    return pct_used

# Orbs (future - hierarchical naming: orb{bird}.{chick}.{slot})
ORBS = {
    "orb1.1.1": {"carrier": "chick1.1", "slot": 1},
    "orb1.1.2": {"carrier": "chick1.1", "slot": 2},
    "orb1.2.1": {"carrier": "chick1.2", "slot": 1},
    "orb1.2.2": {"carrier": "chick1.2", "slot": 2},
}

# Targets
TARGET_SOURCES = ["VIDEO", "MANUAL", "IMPORT"]

# =============================================================================
# SITL CONFIGURATION (Software In The Loop)
# =============================================================================
#
# Running multiple SITL instances:
#   Each instance gets its own port range (offset by 10 per instance)
#   Instance 0: TCP 5760, 5762, 5763
#   Instance 1: TCP 5770, 5772, 5773
#   Instance 2: TCP 5780, 5782, 5783
#
# To run 3 separate Mission Planner SITLs:
#   1. Open 3 Mission Planner windows
#   2. In each, go to Simulation tab and start SITL
#   3. Use Instance 0, 1, 2 respectively (or different ports)
#
# Or use sim_vehicle.py:
#   sim_vehicle.py -v ArduPlane -I 0    (bird)
#   sim_vehicle.py -v ArduCopter -I 1   (chick1)
#   sim_vehicle.py -v ArduCopter -I 2   (chick2)
#
SITL_USE_TCP = True  # Set to False if using sim_vehicle.py

SITL_CONNECTIONS = {
    # Each vehicle connects to a different SITL instance
    # Vehicle ID -> connection string
    # The MAVLink manager will verify vehicle type matches expected type
    "bird1": "tcp:127.0.0.1:5760",        # Instance 0 (plane)
    "chick1.1": "tcp:127.0.0.1:5770",     # Instance 1 (copter)
    "chick1.2": "tcp:127.0.0.1:5780",     # Instance 2 (copter)
}

# Alternative for sim_vehicle.py (UDP)
SITL_CONNECTIONS_UDP = {
    "bird1": "udp:127.0.0.1:14550",       # Instance 0
    "chick1.1": "udp:127.0.0.1:14560",    # Instance 1
    "chick1.2": "udp:127.0.0.1:14570",    # Instance 2
}

# Connection ports (for hardware MAVLink)
MAVLINK_PORTS = {
    "bird": "udp:127.0.0.1:14550",
    "chick1": "udp:127.0.0.1:14551",
    "chick2": "udp:127.0.0.1:14552",
}

# T-Beam serial (for future LoRa)
TBEAM_PORT = "COM3"  # Update for your system
TBEAM_BAUD = 115200

# Simulation refresh rate (ms)
SIM_UPDATE_INTERVAL = 100
