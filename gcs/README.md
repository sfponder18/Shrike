# SwarmDrones GCS

Ground Control Station for the SwarmDrones swarm UAV system.

## Quick Start

```bash
# Install dependencies
pip install PyQt5

# Run
python -m gcs.main
# or double-click run_gcs.bat
```

## Features (v0.1 Prototype)

- **Map View**: Pan/zoom, vehicle positions, target markers, right-click to add targets
- **Video Panel**: Source selector (Bird/Chick1/Chick2), fullscreen toggle
- **Vehicle Cards**: Mode, altitude, battery for Bird, CHK1, CHK2
- **Target Queue**: View targets, manual coordinate entry, assign to orbs
- **Orb Management**: 4 orbs across 2 chicks, 3-step release workflow (Assign → Arm → Release)
- **Status Bar**: Mesh RSSI, MLRS, 4G, ELRS link status
- **Keyboard Shortcuts**: Full keyboard control support

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+1/2/3 | Select Bird/Chick1/Chick2 |
| M | Cycle flight mode |
| V | Toggle video fullscreen |
| Tab | Cycle video source |
| Space | Capture coordinate from Bird |
| T | Cycle target queue |
| A | Assign target to selected Orb |
| R (hold 2s) | Release armed Orb |
| Ctrl+R | All RTL (with confirm) |
| Esc | Cancel/close dialogs |

## Architecture

```
gcs/
├── main.py           # Entry point
├── app.py            # Main window, event handling
├── config.py         # Configuration constants
├── styles.py         # Dark mode QSS styles
├── models/           # Data models
│   ├── vehicle.py    # Vehicle state
│   ├── target.py     # Target queue
│   └── orb.py        # Orb management
└── widgets/          # UI components
    ├── map_widget.py
    ├── video_widget.py
    ├── vehicle_card.py
    ├── target_queue.py
    ├── orb_panel.py
    ├── mode_panel.py
    └── status_bar.py
```

## Current State

**Simulation mode**: All vehicle data is simulated. Real MAVLink/LoRa integration TBD.

## Next Steps

1. MAVLink integration (pymavlink)
2. T-Beam LoRa serial communication
3. Video streaming (RTSP via 4G)
4. Pre-flight check script
5. MISSION/ISR/EW tabs

## Dependencies

- Python 3.8+
- PyQt5 >= 5.15

Future:
- pymavlink (MAVLink)
- pyserial (T-Beam)
- opencv-python (video)
