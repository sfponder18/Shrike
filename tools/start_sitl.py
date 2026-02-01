#!/usr/bin/env python3
"""
SwarmDrones Multi-SITL Launcher

Starts 3 SITL instances using Mission Planner's downloaded binaries:
  - Bird (ArduPlane) on Instance 0
  - Chick1 (ArduCopter) on Instance 1
  - Chick2 (ArduCopter) on Instance 2

Prerequisites:
  Run Mission Planner SITL once for Plane and Copter to download binaries.

Usage:
  python tools/start_sitl.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# SITL binary location (Mission Planner downloads here)
# Check multiple possible locations
SITL_LOCATIONS = [
    Path(os.environ.get('USERPROFILE', '')) / 'OneDrive' / 'Documents' / 'Mission Planner' / 'sitl',
    Path(os.environ.get('USERPROFILE', '')) / 'Documents' / 'Mission Planner' / 'sitl',
    Path(os.environ.get('LOCALAPPDATA', '')) / 'Mission Planner' / 'sitl',
]

SITL_DIR = None
for loc in SITL_LOCATIONS:
    if (loc / 'ArduPlane.exe').exists():
        SITL_DIR = loc
        break

if SITL_DIR is None:
    SITL_DIR = SITL_LOCATIONS[0]  # Default for error message

# Vehicle configurations - matches gcs/config.py SWARM_CONFIG
VEHICLES = [
    {
        'id': 'bird1',
        'name': 'Bird1',
        'exe': 'ArduPlane.exe',
        'model': 'plane',
        'instance': 0,
        'params': 'plane.parm',
    },
    {
        'id': 'chick1.1',
        'name': 'Chick1.1',
        'exe': 'ArduCopter.exe',
        'model': 'quad',
        'instance': 1,
        'params': 'copter.parm',
    },
    {
        'id': 'chick1.2',
        'name': 'Chick1.2',
        'exe': 'ArduCopter.exe',
        'model': 'quad',
        'instance': 2,
        'params': 'copter.parm',
    },
]


def check_binaries():
    """Check if SITL binaries are available."""
    missing = []

    plane_exe = SITL_DIR / 'ArduPlane.exe'
    copter_exe = SITL_DIR / 'ArduCopter.exe'

    if not plane_exe.exists():
        missing.append('ArduPlane.exe')
    if not copter_exe.exists():
        missing.append('ArduCopter.exe')

    if missing:
        print("ERROR: Missing SITL binaries!")
        print(f"  Looking in: {SITL_DIR}")
        print(f"  Missing: {', '.join(missing)}")
        print()
        print("To download the binaries:")
        print("  1. Open Mission Planner")
        print("  2. Go to Simulation tab")
        print("  3. Start 'Plane' SITL (wait for it to load, then close)")
        print("  4. Start 'Multirotor' SITL (wait for it to load, then close)")
        print("  5. Run this script again")
        return False

    print(f"Found SITL binaries at: {SITL_DIR}")
    return True


def start_sitl(vehicle, speedup=1, wipe=False):
    """Start a single SITL instance."""
    name = vehicle['name']
    exe = SITL_DIR / vehicle['exe']
    instance = vehicle['instance']
    model = vehicle['model']

    # Calculate ports for this instance
    # Base port 5760, each instance adds 10
    # Instance 0: 5760 (serial0), 5762 (serial1), 5763 (serial2)
    # Instance 1: 5770, 5772, 5773
    # Instance 2: 5780, 5782, 5783
    base_port = 5760 + (instance * 10)

    # Build command - run from SITL_DIR so DLLs are found
    # Let SITL use default ports based on instance number:
    #   Instance 0: 5760, 5762, 5763
    #   Instance 1: 5770, 5772, 5773
    #   Instance 2: 5780, 5782, 5783
    cmd = [
        str(exe),
        '--model', model,
        '-I', str(instance),
        '--home', '52.205278,0.174861,15,0',  # Cambridge Airport (EGSC), UK
        '--speedup', str(speedup),
    ]

    # Add --defaults if the param file exists (required for copter frame class)
    params_file = SITL_DIR / 'default_params' / vehicle['params']
    if params_file.exists():
        cmd.extend(['--defaults', str(params_file)])
    else:
        print(f"  WARNING: {vehicle['params']} not found - copter may not arm!")

    # Add --wipe to reset eeprom (helps with clean initialization)
    if wipe:
        cmd.append('--wipe')

    print(f"Starting {name} (Instance {instance})...")
    print(f"  Model: {model}")
    print(f"  Ports: TCP {base_port} (primary), {base_port+2} (secondary)")
    print(f"  Speedup: {speedup}x, Wipe: {wipe}")
    print(f"  Params: {params_file.name if params_file.exists() else 'NONE'}")
    print(f"  Command: {' '.join(str(c) for c in cmd)}")

    # Create a wrapper batch file that keeps window open on error
    wrapper_bat = SITL_DIR / f'run_{name.lower()}.bat'
    cmd_str = ' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in cmd)
    with open(wrapper_bat, 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'title {name} SITL\n')
        f.write(f'cd /d "{SITL_DIR}"\n')
        f.write(f'{cmd_str}\n')
        f.write(f'echo.\n')
        f.write(f'echo SITL exited with code %ERRORLEVEL%\n')
        f.write(f'pause\n')

    # Start the wrapper batch file in new window
    try:
        subprocess.Popen(
            ['cmd', '/c', str(wrapper_bat)],
            cwd=str(SITL_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SwarmDrones Multi-SITL Launcher')
    parser.add_argument('--speedup', type=int, default=1,
                       help='SITL speedup factor (default: 1)')
    parser.add_argument('--vehicles', type=str, default='bird',
                       help='Which vehicles to start: all, bird, copters (default: bird)')
    parser.add_argument('--wipe', action='store_true', default=False,
                       help='Wipe eeprom for clean start (default: False)')
    args = parser.parse_args()

    print("=" * 50)
    print(" SwarmDrones Multi-SITL Launcher")
    print("=" * 50)
    print()

    if not check_binaries():
        sys.exit(1)

    print()
    print("Starting SITL instances...")
    print()

    # Filter vehicles if requested
    vehicles_to_start = VEHICLES
    if args.vehicles == 'bird':
        vehicles_to_start = [v for v in VEHICLES if 'Plane' in v['exe']]
    elif args.vehicles == 'copters':
        vehicles_to_start = [v for v in VEHICLES if 'Copter' in v['exe']]

    started = 0
    for i, vehicle in enumerate(vehicles_to_start):
        if start_sitl(vehicle, speedup=args.speedup, wipe=args.wipe):
            started += 1
            if i < len(vehicles_to_start) - 1:
                print(f"  Waiting 10 seconds before starting next vehicle...")
                time.sleep(10)  # Wait longer between starts
        print()

    print("=" * 50)
    print(f" Started {started}/{len(vehicles_to_start)} SITL instances")
    print("=" * 50)
    print()
    print("SITL will take ~10-20 seconds to initialize GPS.")
    print()
    print("Connect Mission Planner to:")
    print("  bird1:    TCP 127.0.0.1:5760")
    print("  chick1.1: TCP 127.0.0.1:5770")
    print("  chick1.2: TCP 127.0.0.1:5780")
    print()
    print("Connect SwarmDrones GCS:")
    print("  Menu > Connect > SITL (ArduPilot)")
    print("  (Connects to ports 5760, 5770, 5780)")
    print()
    print("Test with: python tools/test_sitl.py")
    print()
    print("Close the SITL windows to stop simulation.")
    print()
    input("Press Enter to exit...")


if __name__ == '__main__':
    main()
