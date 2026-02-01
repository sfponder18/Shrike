# GCS Design Context

## System Overview
Swarm: 1 Bird (fixed-wing), 2 Chicks (quads), 4 Orbs (glide munitions)
Operator: Single, 15" laptop, field conditions
Budget: Under $3k total (see main design doc for BOM)

## Architecture
```
GCS LAPTOP
├── RadioMaster TX ──── ELRS 2.4GHz ────► RC (model switching)
├── MLRS TX module ──── 868MHz ─────────► MAVLink telemetry
├── T-Beam (USB) ─────── LoRa 868MHz ───► Custom datawords
├── HackRF One ────────── (owned) ───────► Future EW (see Future_Capabilities.md)
└── Internet (hotspot) → Tailscale ─────► 4G backup to Bird

BIRD (Ranger 2000)
├── Pixhawk 6C (ArduPlane)
├── Raspberry Pi 5
│   ├── 4G modem → Tailscale → GCS (backup MAVLink + video)
│   ├── WiFi AP → Chicks connect as clients
│   └── Relays gimbal+GPS data to GCS for coord calculation
├── MLRS RX (868MHz) → MAVLink to GCS
├── T-Beam → LoRa commands
└── ELRS RX → RC

CHICK x2 (Darwin FPV Baby Ape II)
├── FC (ArduCopter)
├── Pi Zero 2W
│   ├── RTL-SDR (spectrum monitoring)
│   └── WiFi client → Bird AP → 4G → GCS
├── MLRS RX → MAVLink to GCS
├── T-Beam → LoRa commands
└── ELRS RX → RC

ORB x4 (glide munition)
├── ESP32-S3, GPS, IMU, 4x fin servos
├── NO T-Beam - receives target coords before release via Chick
└── Carried/dropped by Chick
```

## RF Links (per Bird/Chick)
| Link | Freq | Hardware | Purpose |
|------|------|----------|---------|
| ELRS | 2.4GHz | RP2/RP3 RX | RC control |
| MLRS | 868MHz | E77-based (TBD) | MAVLink telemetry |
| T-Beam | 868MHz LoRa | Lilygo T-Beam | Custom datawords |

T-Beams: GCS, Bird, Chick1, Chick2 (4 total). No T-Beam on Orbs.
T-Beam firmware: TBD (Meshtastic or custom)

## Data Paths
| Data | Path |
|------|------|
| Bird MAVLink | MLRS (primary), 4G/Tailscale (backup) |
| Bird video | Pi 5 → 4G → GCS dashboard |
| Chick MAVLink | MLRS (primary), Pi → WiFi → Bird → 4G (backup) |
| Chick SDR | RTL-SDR → Pi → WiFi → Bird → 4G → GCS |
| LoRa commands | T-Beam mesh (bidirectional) |
| Orb coords | GCS → LoRa/MLRS → Chick → uploaded to Orb pre-release |

## GCS Hardware
- Laptop 15" (1920x1080)
- RadioMaster TX (ELRS, 3 model profiles for Bird/Chick1/Chick2)
- MLRS TX module (868MHz, JR bay or USB)
- Lilygo T-Beam (USB-serial)
- HackRF One (already owned, future EW use)
- Phone hotspot for internet

## GCS Software
- **QGroundControl**: pre-mission planning, detailed telemetry, waypoints
- **Custom Dashboard** (Python/PyQt5/pymavlink): primary ops interface
- **Pre-flight script** (Python): validates all links
- Both apps connect to MAVLink via UDP port sharing (MAVProxy or similar)

## Dashboard UI
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ SWARM GCS          [FLIGHT] [MISSION] [ISR] [EW]          [PRE-FLIGHT] ⚙     │
├────────────────────────────────────────────┬─────────────────────────────────┤
│                                            │ VIDEO FEED [Bird▼]              │
│                                            │ ┌─────────────────────────────┐ │
│            M A P                           │ │ (click expand, V key)       │ │
│                                            │ └─────────────────────────────┘ │
│    ✈Bird ──────►        ◎1 ◎2             ├─────────────────────────────────┤
│         ⬡C1    ⬡C2      ◎3                │ VEHICLES             [Ctrl+1/2/3]│
│                                            │ ┌───────┬───────┬───────┐       │
│    [+][-] zoom                             │ │ BIRD  │ CHK1  │ CHK2  │       │
│    Right-click: add target                 │ │ AUTO  │ LOIT  │ LOIT  │       │
│                                            │ │ 127m  │ 48m   │ 52m   │       │
│                                            │ │ 67%▮▮▯│ 81%▮▮▮│ 74%▮▮▯│       │
│                                            │ └───────┴───────┴───────┘       │
├────────────────────────────────────────────┼─────────────────────────────────┤
│ SELECTED: ✈ BIRD                           │ ORB STORES                      │
│ MODE: [LOIT] [RTL] [AUTO] [LAND] [GUIDE]   │ CHK1: [●1][●2] ARM: ○ ○         │
├────────────────────────────────────────────┤ CHK2: [●3][○─] ARM: ○           │
│ TARGET QUEUE                               │                                 │
│ ┌────┬──────────────────┬────────┬───────┐ │ SELECTED: ORB1                  │
│ │ ID │ COORDINATES      │ SOURCE │ ORB   │ │ TARGET: ◎1                      │
│ ├────┼──────────────────┼────────┼───────┤ │ [ASSIGN] [ARM] [RELEASE]        │
│ │ ◎1 │ 52.1234, -1.5678 │ VIDEO  │ ORB1  │ │                                 │
│ │ ◎2 │ 52.1245, -1.5690 │ VIDEO  │  --   │ │ [MANUAL COORD ENTRY]            │
│ └────┴──────────────────┴────────┴───────┘ │                                 │
├────────────────────────────────────────────┴─────────────────────────────────┤
│ MESH: Bird -67● C1 -72● C2 -81●    MLRS: ●    4G: ●    ELRS: ●               │
└──────────────────────────────────────────────────────────────────────────────┘
```
Dark mode. Tabs: FLIGHT (v1), MISSION/ISR/EW (placeholders).

## Target Workflow
Sources: pre-planned list, video capture, manual coord entry
Capture trigger: RC TX switch (mapped channel) OR GCS spacebar
Flow: Bird gimbal+GPS → Pi 5 → MLRS/LoRa → GCS target queue (GCS calculates ground coord)
Multiple targets can be queued.

## Orb Workflow (3 steps)
1. Add target to queue (video/manual/import)
2. Select Orb → [ASSIGN TGT] → links target to Orb
3. [ARM ORB] → arms selected Orb
4. [RELEASE] → confirmation dialog → Chick releases Orb

Orb receives target coords via Chick (uploaded before release, no in-flight LoRa).

## Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Ctrl+1/2/3 | Select Bird/Chick1/Chick2 |
| M | Cycle flight mode |
| V | Toggle video fullscreen |
| Tab | Cycle video source |
| Space | Capture coordinate from Bird |
| T | Cycle target queue |
| A | Assign target to Orb |
| R (hold 2s) | Release armed Orb |
| Ctrl+R | All RTL (confirm) |
| Esc | Cancel/close dialogs |

## Pre-Flight Checklist
Script validates:
- T-Beam mesh (RSSI per node, last seen)
- MLRS link to each vehicle
- 4G/Tailscale connectivity to Bird
- ELRS binding per model profile
- GPS lock on Bird, Chicks
- Battery levels
- Orb status if loaded (GPS, battery)

## Future Tabs (see Future_Capabilities.md)
- **MISSION**: waypoint planning, target list import/export, Orb loadout config
- **ISR**: RTL-SDR spectrum waterfall from Chicks, signal logging, recording
- **EW**: HackRF tools

## Key Decisions Made
- Separate hardware for MLRS (MAVLink) and T-Beam (commands) - not combined
- Single operator, RC model switching (Bird primary, Chicks mostly autonomous)
- Dashboard is primary ops UI, QGC for planning/backup
- Dark mode UI
- 3-step Orb release: assign → arm → release with confirm
- Video over 4G to dashboard (not local analog capture to laptop)
- Tailscale for 4G NAT traversal
- Orbs have no T-Beam, get coords pre-release via Chick
- HackRF on GCS (not Bird) - Bird SDR deferred to future
- ArduPilot for all vehicles (ArduPlane Bird, ArduCopter Chicks)
- Chicks: Darwin FPV Baby Ape II (ArduCopter compatible)

## Open Items
- MLRS exact hardware selection (E77 module variant)
- T-Beam firmware (Meshtastic vs custom)
- Custom dataword format (defined elsewhere)
- Release envelope calculation (future - currently any point valid)
