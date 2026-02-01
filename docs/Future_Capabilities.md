# Future Capabilities

Items deferred from v1 prototype. Promote to main docs when ready.

---

## Platform

- **Jetson Orin upgrade (V2)** - Replace Pi 5 with Jetson Orin Nano for:
  - 40 TOPS AI inference (YOLO, tracking)
  - Hardware video encode (multiple streams)
  - CUDA acceleration for SDR processing
  - Required for onboard AI detection features
- **PX4 migration** - Cleaner ROS2 integration, modern codebase
- **802.11s mesh networking** - True mesh vs current AP/client topology
- **VIO/CLIP localization** - GPS-denied navigation using visual-inertial odometry
- **Collision avoidance** - Sense-and-avoid using depth sensors
- **Swarm coordination** - Formation flight, task allocation
- **Autonomous mission execution** - Behavior trees, onboard decision making
- **Edge compute offload** - Distribute inference across swarm
- **Secure boot** - Verified boot chain

## GCS

- **ISR tab** - RTL-SDR spectrum waterfall from Chicks, signal logging
- **EW tab** - HackRF tools, RF analysis
- **MISSION tab** - Waypoint planning, target list import/export, Orb loadout config
- **Plot and Avoid** - Geofencing and obstacle avoidance for mission planning:
  - Import no-fly zones (KML/GeoJSON) and display on map
  - Automatic path routing around restricted areas
  - Terrain elevation data overlay (SRTM/DTED)
  - Obstacle database (towers, powerlines, buildings)
  - Real-time collision avoidance warnings
  - Automatic waypoint adjustment to maintain safe distances
  - Integration with airspace data (ADS-B, NOTAM)
- **Release envelope calculation** - Orb glide range visualization on map
- **Multi-operator support** - Role separation (pilot, payload, commander)
- **Target metadata over mesh** - Send target name/description to Chicks for logging/display

## Orb

- **Orb LoRa radio (V2)** - Add Meshtastic module to Orbs for:
  - In-flight retargeting after release
  - Telemetry from released Orb (position, status)
  - Abort/self-destruct command capability
  - Node IDs 4-7 reserved in protocol
- **In-flight retargeting** - Update target via LoRa after release
- **Terminal guidance improvements** - Better IMU fusion, proportional navigation
- **Airburst / proximity fusing** - For future payload variants

## Comms

- **Mesh range extension** - Multi-hop LoRa beyond line-of-sight
- **Frequency hopping** - Anti-jam for MLRS/LoRa links
- **Encryption** - End-to-end encryption for all swarm traffic

## Bird

- **HackRF integration** - SDR/SIGINT capability (deferred from v1)
- **Onboard AI detection** - YOLO/similar (requires Jetson upgrade)
- **Target tracking** - Persistent track-on-target (requires Jetson upgrade)

---

*Last updated: 2026-01-23 (v2.1 mesh protocol update)*
