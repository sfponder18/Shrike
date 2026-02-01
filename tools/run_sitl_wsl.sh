#!/bin/bash
# SwarmDrones Multi-SITL Launcher for WSL
#
# Prerequisites:
#   1. Install WSL2 with Ubuntu
#   2. Install ArduPilot SITL: https://ardupilot.org/dev/docs/building-setup-linux.html
#
# Usage (from Windows):
#   wsl bash tools/run_sitl_wsl.sh
#

echo "============================================"
echo " SwarmDrones Multi-SITL Launcher (WSL)"
echo "============================================"
echo ""

# Check if sim_vehicle.py exists
if ! command -v sim_vehicle.py &> /dev/null; then
    echo "ERROR: sim_vehicle.py not found!"
    echo ""
    echo "Please install ArduPilot SITL:"
    echo "  https://ardupilot.org/dev/docs/building-setup-linux.html"
    echo ""
    exit 1
fi

# Get Windows host IP for networking
WIN_HOST=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo "Windows host IP: $WIN_HOST"
echo ""

echo "Starting 3 SITL instances..."
echo "  Instance 0: ArduPlane  (Bird)"
echo "  Instance 1: ArduCopter (Chick1)"
echo "  Instance 2: ArduCopter (Chick2)"
echo ""

# Start each SITL in background
cd ~/ardupilot

# Bird (Plane) - Instance 0
echo "Starting Bird..."
gnome-terminal --title="SITL Bird" -- sim_vehicle.py -v ArduPlane -I 0 --out=tcpin:0.0.0.0:5762 &
sleep 3

# Chick1 (Copter) - Instance 1
echo "Starting Chick1..."
gnome-terminal --title="SITL Chick1" -- sim_vehicle.py -v ArduCopter -I 1 --out=tcpin:0.0.0.0:5772 &
sleep 3

# Chick2 (Copter) - Instance 2
echo "Starting Chick2..."
gnome-terminal --title="SITL Chick2" -- sim_vehicle.py -v ArduCopter -I 2 --out=tcpin:0.0.0.0:5782 &

echo ""
echo "============================================"
echo " SITL instances starting..."
echo "============================================"
echo ""
echo "Wait for all instances to initialize, then connect:"
echo ""
echo "  Mission Planner:"
echo "    TCP 127.0.0.1:5760 (Bird)"
echo "    TCP 127.0.0.1:5770 (Chick1)"
echo "    TCP 127.0.0.1:5780 (Chick2)"
echo ""
echo "  SwarmDrones GCS:"
echo "    Menu > Connect > SITL (ArduPilot)"
echo ""
