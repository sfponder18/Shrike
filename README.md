# Shrike

**Carrier-Deployed Autonomous Swarm for EW, Reconnaissance, and Strike**

---

## Overview

Shrike is a multi-platform autonomous drone system featuring:
- **Carrier** — Fixed-wing aircraft that transports and deploys Scouts
- **Scout** — Attritable multirotor drone with three operational modes:
  - **EW Mode** — S/C band radar detection and geolocation (TDOA)
  - **Recon Mode** — Visual/IR surveillance
  - **Strike Mode** — GPS-guided terminal attack

The system enables standoff deployment of a coordinated swarm for electronic warfare, reconnaissance, and precision strike missions.

---

## System Architecture

```
                         ┌─────────────────────────┐
                         │          GCS            │
                         │  Command & Control      │
                         └───────────┬─────────────┘
                                     │
                              4G / LoRa
                                     │
                         ┌───────────▼─────────────┐
                         │        CARRIER          │
                         │   ═══════════════════   │
                         │    ╲               ╱    │
                         │     ╲   [SCOUTS]  ╱     │
                         │      ╲___________╱      │
                         │                         │
                         │  • 3m wingspan          │
                         │  • 2.5 hr endurance     │
                         │  • Carries 4-6 Scouts   │
                         │  • Own EW capability    │
                         └───────────┬─────────────┘
                                     │
                              Deploy on command
                                     │
            ┌────────────────────────┼────────────────────────┐
            │              │         │         │              │
            ▼              ▼         ▼         ▼              ▼
       ┌─────────┐   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
       │ Scout 1 │   │ Scout 2 │ │ Scout 3 │ │ Scout 4 │ │ Scout 5 │
       │   EW    │   │  Recon  │ │   EW    │ │ Strike  │ │ Strike  │
       └─────────┘   └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## Project Structure

```
Shrike/
├── README.md                 # This file
├── Carrier/                  # Fixed-wing carrier aircraft
│   ├── airframe/            # CAD, build docs
│   ├── avionics/            # Autopilot config
│   ├── deploy_mechanism/    # Scout deployment system
│   └── ew_payload/          # Carrier EW suite
│
├── Scout/                    # Deployable multirotor
│   ├── airframe/            # Folding frame design
│   ├── avionics/            # Flight controller, compute
│   ├── ew_payload/          # SDR, antennas
│   ├── camera/              # Recon payload
│   └── strike/              # Terminal guidance
│
├── gcs/                      # Ground Control Station
│   ├── app.py               # Main application
│   ├── models/              # Vehicle, target, mission models
│   ├── widgets/             # UI components
│   ├── comms/               # Communication managers
│   └── ew/                  # EW display, TDOA processing
│
├── docs/                     # Documentation
│   ├── EW_Concepts/         # EW system design docs
│   ├── Design_Documents/    # System architecture
│   └── Build_Guides/        # Assembly instructions
│
├── tools/                    # Utility scripts
└── Sandbox/                  # Experimental features
```

---

## Key Specifications

### Carrier

| Spec | Value |
|------|-------|
| Wingspan | 2.5-3.0 m |
| Endurance | 2.5 hours |
| Payload | 4-6 Scouts (3-5 kg) |
| EW Coverage | VHF - C band (70 MHz - 6 GHz) |
| Compute | Raspberry Pi 5 |
| SDR | Ettus B205mini |
| Cost | ~$6,240 |

### Scout

| Spec | Value |
|------|-------|
| Size (stowed) | 12 × 12 × 10 cm |
| Size (deployed) | 25 cm diagonal (5" props) |
| Weight | 300-500g |
| Endurance | 15-20 min |
| EW Coverage | S/C band (2-6 GHz) |
| SDR | PlutoSDR or B205mini |
| Camera | 1080p, low-latency |
| Strike | GPS-guided terminal |
| Cost | ~$930-1,230 each |

### System Cost

| Configuration | Cost |
|---------------|------|
| Minimal (1 Carrier + 4 Scouts) | ~$10,000 |
| Standard (1 Carrier + 6 Scouts) | ~$12,000 |
| Full (2 Carriers + 12 Scouts) | ~$24,000 |

---

## EW Capability

### Target Emitters (S/C Band Focus)

| Radar | Band | Frequency | Priority |
|-------|------|-----------|----------|
| 91N6E "Big Bird" | S-band | 2.5-3.5 GHz | Critical |
| 96L6E "Cheese Board" | C-band | 5-6 GHz | High |
| Fire control radars | S/C | 2-6 GHz | High |

### Geolocation

- **Method:** TDOA (Time Difference of Arrival)
- **Platforms:** 4+ Scouts + Carrier
- **Timing:** GPS PPS synchronized (~50 ns)
- **CEP:** 50-100m (sufficient for strike cueing)

---

## Mission Profiles

### Profile A: EW Search & Geolocate
1. Carrier transits to AO
2. Deploys 4 Scouts at 10 km spacing
3. Scouts detect and geolocate emitters
4. Report locations to GCS
5. Scouts RTB or expend

### Profile B: EW-Cued Strike
1. Carrier deploys Scouts
2. Scouts geolocate target radar
3. Operator authorizes strike
4. 1-2 Scouts execute terminal attack
5. Remaining Scouts provide BDA

### Profile C: Multi-Target Strike
1. Carrier deploys 6 Scouts
2. Scouts identify multiple emitters
3. Prioritized strikes authorized
4. Coordinated attack on targets
5. BDA and reattack as needed

---

## Development Status

| Component | Status |
|-----------|--------|
| GCS Core | Functional (from SwarmDrones) |
| Vehicle Models | Functional |
| EW Panel | Prototype (Sandbox) |
| Carrier Airframe | Design phase |
| Scout Airframe | Design phase |
| Deploy Mechanism | Concept |
| TDOA Processing | Concept |
| Strike Guidance | From Orb codebase |

---

## Heritage

Shrike merges two projects:

### SwarmDrones (Original)
- Bird (fixed-wing ISR) → **Carrier**
- Chick (multirotor recon) → **Scout (Recon mode)**
- Orb (glide munition) → **Scout (Strike mode)**
- GCS → **GCS (with EW additions)**

### EW Node Concept
- Config 1/2 (dedicated EW platforms) → Informed Scout EW design
- Concept 3 (carrier-deployed) → **Core Shrike architecture**
- TDOA/geolocation → **Scout cooperative EW**

---

## Getting Started

### Run GCS (Simulation Mode)
```bash
cd gcs
pip install -r requirements.txt
python main.py
```

### Documentation
- [Concept 3: Carrier-Deployed Strike/EW](docs/EW_Concepts/Concept_3_Carrier_Strike_EW.md)
- [EW System Brainstorm](docs/EW_Concepts/EW_Node_Brainstorm.md)
- [Original Design Document](SwarmDrones_Design_Document.md)

---

## Naming

**Shrike** — A predatory songbird known for impaling its prey on thorns. Also the designation of the AGM-45 Shrike anti-radiation missile, the first American purpose-built ARM.

Fitting for a system that hunts radars and strikes.

---

## License

Internal development project.

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-06 | Project created from SwarmDrones + EW Node Concept merge |
