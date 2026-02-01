# Sandbox - Experimental GCS with EW Panel

This is an experimental version of the GCS for testing the Electronic Warfare (EW) panel and related features.

## Running the Sandbox

```batch
# From SwarmDrones root directory:
run_sandbox.bat

# Or directly:
cd sandbox
python -m gcs_sandbox.main
```

## What's Different

- **EW Tab Enabled**: The EW tab in the header is now functional
- **EW Panel**: Full Electronic Warfare panel with:
  - Spectrum display (simulated)
  - Waterfall history
  - EP Status panel (link health, threat level, hop status)
  - DF Geometry visualization
  - Emitter list with criticality scoring
  - Emitter detail panel
  - Click-to-target workflow

## Simulation Mode

The EW panel includes its own simulation that generates:
- Random emitters across tactical spectrum
- Criticality scoring based on V1 weights
- Simulated DF position estimates with CEP
- EP status updates

## Files Structure

```
sandbox/
├── gcs_sandbox/
│   ├── main.py           # Entry point
│   ├── app.py            # Modified GCSMainWindow with EW tab
│   ├── config.py         # Imports from parent + EW config
│   ├── styles.py         # Imports from parent + EW styles
│   ├── models/
│   │   ├── __init__.py
│   │   └── emitter.py    # Emitter, EmitterList, EPStatus models
│   ├── widgets/
│   │   ├── __init__.py
│   │   └── ew_panel.py   # Main EW panel widget
│   └── comms/
│       ├── __init__.py
│       └── ew_manager.py # EW simulation manager
└── run_sandbox.bat
```

## Development Notes

- Changes here don't affect the main GCS
- Once features are stable, migrate to main gcs/
- EW panel is designed to integrate with existing comms managers
