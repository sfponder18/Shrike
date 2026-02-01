# EW System V2 - Context Document

## Purpose
This document defines the V2 Electronic Warfare system architecture, building on V1 foundations with expanded hardware, ML capabilities, and offensive features.

---

## V2 Scope Summary

| Capability | V1 | V2 |
|------------|----|----|
| ES Sensors | RTL-SDR (24MHz-1.7GHz) | BladeRF 2.0 (47MHz-6GHz) + high-freq tiles |
| Frequency Coverage | 24 MHz - 1.7 GHz | 47 MHz - 40+ GHz (with tiles) |
| Companion Computer | Raspberry Pi | Jetson Orin Nano (all platforms) |
| ML Classification | Library matching | Full neural inference |
| Direction Finding | 2-platform TDOA | Multi-platform + onboard arrays |
| EA Capability | None | BladeRF TX (potential) |
| Orb Targeting | Coords locked at release | In-flight LoRa updates |
| Platform Size | 3" Chicks | 10" dedicated EW Chicks |
| Timing Sync | GPS PPS (~50ns) | RTK at GCS (<20ns) |

---

## Platform Configuration (V2)

### Chick (10" EW Platform)

```
┌─────────────────────────────────────────────────────────┐
│                 CHICK V2 (10" PLATFORM)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  COMPANION COMPUTER                                     │
│  └── Jetson Orin Nano (40 TOPS AI inference)           │
│      ├── Full ML pipeline (modulation, purpose, ID)    │
│      ├── Real-time signal processing                   │
│      └── Onboard fusion and decision-making            │
│                                                         │
│  PRIMARY SDR                                            │
│  └── BladeRF 2.0 micro xA4                             │
│      ├── Frequency: 47 MHz - 6 GHz                     │
│      ├── Bandwidth: 56 MHz instantaneous               │
│      ├── Channels: 2x2 MIMO                            │
│      ├── TX capable (EA potential)                     │
│      └── Better dynamic range than RTL-SDR             │
│                                                         │
│  HIGH-FREQUENCY TILES (6 GHz+)                         │
│  └── Modular RF front-end architecture:                │
│      ┌─────────────────────────────────────┐           │
│      │  TILE STRUCTURE (per band)          │           │
│      │  ├── Dedicated antenna              │           │
│      │  ├── Preselector filter             │           │
│      │  ├── Low-noise amplifier (LNA)      │           │
│      │  ├── Mixer/downconverter            │           │
│      │  └── IF output to BladeRF           │           │
│      └─────────────────────────────────────┘           │
│                                                         │
│      Target Bands:                                      │
│      ├── 5.8 GHz tile (FPV, WiFi)                      │
│      ├── X-band tile (8-12 GHz, radar)                 │
│      ├── Ku-band tile (12-18 GHz, satellite/radar)     │
│      └── K/Ka-band tile (24-28 GHz, 5G, radar)         │
│                                                         │
│      Common Infrastructure:                             │
│      ├── Shared LO (low phase noise reference)         │
│      ├── RF switch matrix (tile selection)             │
│      ├── Common timing source (RTK-disciplined)        │
│      └── Coherent across all tiles                     │
│                                                         │
│  TIMING                                                 │
│  └── RTK GPS                                           │
│      ├── Position: cm-level accuracy                   │
│      ├── Timing: <20ns to UTC                          │
│      └── Enables precise TDOA geolocation              │
│                                                         │
│  COMMUNICATIONS                                         │
│  └── Standard swarm mesh (T-Beam, mLRS, ELRS)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Bird (V2 Enhancements)

```
┌─────────────────────────────────────────────────────────┐
│                    BIRD V2 UPGRADES                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  COMPANION COMPUTER                                     │
│  └── Jetson Orin Nano                                  │
│      ├── Video AI (YOLO object detection)              │
│      ├── EW data fusion from Chicks                    │
│      └── Autonomous mission adaptation                 │
│                                                         │
│  OPTIONAL EW PAYLOAD                                    │
│  └── BladeRF 2.0 (if payload capacity allows)         │
│      ├── Third sensor for DF geometry                  │
│      ├── Higher altitude = better RF horizon           │
│      └── Longer dwell time (2hr endurance)             │
│                                                         │
│  RTK GPS                                                │
│  └── Synchronized timing with Chicks                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### GCS (V2 Enhancements)

```
┌─────────────────────────────────────────────────────────┐
│                     GCS V2 UPGRADES                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  RTK BASE STATION                                       │
│  └── Provides corrections to all vehicles              │
│      ├── cm-level position                             │
│      ├── <20ns timing sync                             │
│      └── Broadcast via mesh or dedicated link          │
│                                                         │
│  EXPANDED PROCESSING                                    │
│  └── GPU workstation (optional)                        │
│      ├── Post-mission signal analysis                  │
│      ├── ML model training on collected data           │
│      └── High-res spectrogram generation               │
│                                                         │
│  ENHANCED EW TAB                                        │
│  └── Features detailed in UI section below             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ML Classification (V2)

### Full Neural Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                  ML CLASSIFICATION STACK                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  INPUT LAYER                                            │
│  ├── I/Q samples (time domain)                         │
│  ├── FFT (frequency domain)                            │
│  ├── Spectrogram (time-frequency)                      │
│  └── Cyclostationary features                          │
│                                                         │
│  LAYER 1: MODULATION CLASSIFICATION                    │
│  ├── Model: CNN on spectrogram + constellation         │
│  ├── Output: AM, FM, FSK, PSK, QAM, OFDM, spread...   │
│  └── Confidence score per class                        │
│                                                         │
│  LAYER 2: SIGNAL PURPOSE                               │
│  ├── Model: LSTM on temporal patterns                  │
│  ├── Features:                                         │
│  │   ├── Burst structure                               │
│  │   ├── Duty cycle patterns                           │
│  │   ├── Protocol timing                               │
│  │   └── Frequency agility behavior                    │
│  ├── Output: VOICE, DATA_LINK, RADAR, BEACON,         │
│  │           JAMMER, NAVIGATION, UNKNOWN               │
│  └── Confidence score                                  │
│                                                         │
│  LAYER 3: THREAT ASSESSMENT                            │
│  ├── Model: Ensemble (RF classifier + rules)          │
│  ├── Features:                                         │
│  │   ├── Modulation class                              │
│  │   ├── Purpose class                                 │
│  │   ├── Frequency band                                │
│  │   ├── Behavioral patterns                           │
│  │   └── Contextual factors (location, timing)         │
│  ├── Output: HOSTILE, NEUTRAL, FRIENDLY, UNKNOWN       │
│  └── Confidence + reasoning factors                    │
│                                                         │
│  LAYER 4: EMITTER IDENTIFICATION (fingerprinting)      │
│  ├── Model: Siamese network for RF fingerprinting     │
│  ├── Features:                                         │
│  │   ├── Transmitter imperfections                     │
│  │   ├── Phase noise characteristics                   │
│  │   ├── Spectral mask shape                           │
│  │   └── Power-on transients                           │
│  ├── Output: Match to known emitter DB, or new ID     │
│  └── Enables tracking same emitter across sessions     │
│                                                         │
│  LAYER 5: TACTICAL PURPOSE (hardest)                   │
│  ├── Model: Transformer on multi-signal context       │
│  ├── Features:                                         │
│  │   ├── Correlation with other emitters (nets)        │
│  │   ├── Spatial correlation with assets               │
│  │   ├── Temporal correlation with events              │
│  │   ├── Protocol-level analysis (if decodable)        │
│  │   └── Historical pattern database                   │
│  ├── Output: C2_LINK, SENSOR_NET, COMMS_RELAY,        │
│  │           TARGETING, ISR, LOGISTICS, UNKNOWN        │
│  └── LOW confidence expected - flags for review        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Training Data Strategy

| Source | Data Type | Use |
|--------|-----------|-----|
| Preloaded library | Known signatures | Baseline classification |
| Mission recordings | I/Q clips, labeled post-mission | Model improvement |
| Synthetic generation | Simulated waveforms | Augmentation |
| Federated updates | Aggregated from fleet | Shared learning |

### Inference Performance Target

| Model | Jetson Orin Nano | Latency Target |
|-------|------------------|----------------|
| Modulation classifier | 40 TOPS sufficient | <100ms |
| Purpose classifier | 40 TOPS sufficient | <200ms |
| Threat assessment | 40 TOPS sufficient | <500ms |
| Fingerprinting | May need optimization | <1s |
| Tactical purpose | Experimental | Best effort |

---

## Direction Finding (V2)

### Multi-Platform TDOA

```
┌─────────────────────────────────────────────────────────┐
│              MULTI-PLATFORM GEOLOCATION                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  GEOMETRY (3+ platforms optimal)                        │
│                                                         │
│              BIRD (high altitude)                       │
│                   ★                                     │
│                  /|\                                    │
│                 / | \                                   │
│                /  |  \                                  │
│               /   |   \                                 │
│        CHICK1    |    CHICK2                           │
│           ★      |      ★                              │
│            \     |     /                               │
│             \    |    /                                │
│              \   |   /                                 │
│               \  |  /                                  │
│                \ | /                                   │
│                 \|/                                    │
│                  ● EMITTER                             │
│                                                         │
│  METHOD: Time Difference of Arrival (TDOA)             │
│  ├── All platforms receive same signal                 │
│  ├── RTK timing gives <20ns sync                       │
│  ├── Time difference → range difference                │
│  ├── Multiple pairs → intersection = location          │
│  └── CEP improves with geometry spread                 │
│                                                         │
│  ACCURACY FACTORS                                       │
│  ├── Timing sync: <20ns → ~6m range error             │
│  ├── Platform separation: wider = better               │
│  ├── Altitude spread: Bird high helps                  │
│  ├── Signal SNR: stronger = better timing              │
│  └── Multipath: degrades accuracy                      │
│                                                         │
│  CEP TARGETS                                            │
│  ├── Long range (>2km): 100-200m CEP                   │
│  ├── Medium range (500m-2km): 30-100m CEP             │
│  └── Close range (<500m): 10-30m CEP                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Onboard Arrays (Future Option)

For platforms with antenna arrays:
- Phase interferometry for bearing
- Single-platform DF capability
- Faster initial bearing estimate
- Combine with TDOA for refinement

---

## Electronic Attack Potential (V2)

### BladeRF TX Capabilities

**V2 architecture enables but does not require EA**. BladeRF TX can support:

| Technique | Description | Considerations |
|-----------|-------------|----------------|
| Spot jamming | Narrowband noise on target freq | Legal/authorization required |
| Sweep jamming | Swept noise across band | Power limited on small platform |
| Deceptive | False signals/decoys | Complex, mission-specific |
| Reactive | Jam only when target transmits | Requires fast detection loop |

**Implementation Notes:**
- EA requires explicit mission authorization
- Separate enable flag in mission planning
- Never auto-enabled by EP
- TX power limited by platform power budget
- Antenna isolation from RX required

---

## Orb In-Flight Retargeting (V2)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              ORB LORA UPDATE CAPABILITY                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ORB HARDWARE ADDITION                                  │
│  └── Small LoRa module (SX1262 or similar)             │
│      ├── Receive-only (no TX to save power/weight)     │
│      ├── Shares antenna with GPS if possible           │
│      └── Listens on dedicated update channel           │
│                                                         │
│  UPDATE MESSAGE FORMAT                                  │
│  └── ORB_UPDATE (8 bytes)                              │
│      ├── Orb ID (1 byte)                               │
│      ├── Lat offset (2 bytes, ±3276m from original)   │
│      ├── Lon offset (2 bytes, ±3276m from original)   │
│      ├── Alt offset (1 byte, ±127m)                   │
│      ├── Sequence number (1 byte, reject old)         │
│      └── Checksum (1 byte)                             │
│                                                         │
│  UPDATE FLOW                                            │
│                                                         │
│  1. Orb released with initial target coords            │
│  2. Emitter moves or DF refines position               │
│  3. GCS/Chick sends ORB_UPDATE via mesh                │
│  4. Orb receives, validates sequence                   │
│  5. Orb adjusts guidance to new coords                 │
│  6. Repeat as needed until terminal phase              │
│                                                         │
│  CONSTRAINTS                                            │
│  ├── Update window: Release to T-10 seconds           │
│  ├── Max updates: 5 per flight (prevent oscillation)  │
│  ├── Terminal lockout: No updates in final approach   │
│  └── Sanity check: Reject >500m offset (likely error) │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Emitter Tracking Integration

```
EW tracks emitter → Position updates → GCS checks if Orb assigned
                                              ↓
                              If Orb in flight and not terminal:
                                              ↓
                              Calculate offset from current target
                                              ↓
                              If offset > threshold (e.g., 20m):
                                              ↓
                              Send ORB_UPDATE
                                              ↓
                              Log update, increment counter
```

---

## Scalability (V2)

### Multi-Vehicle Expansion

V2 architecture supports N vehicles:

```
SWARM CONFIGURATION (example)
├── Bird 1
│   ├── Chick 1.1 (EW primary)
│   ├── Chick 1.2 (EW primary)
│   └── Chick 1.3 (EW/ISR hybrid)
├── Bird 2
│   ├── Chick 2.1 (EW primary)
│   └── Chick 2.2 (EW primary)
└── Dedicated EW Bird (no Chicks, max sensors)
```

### Scaling Considerations

| Factor | Scaling Approach |
|--------|------------------|
| DF geometry | More platforms = better accuracy, diminishing returns >5 |
| Bandwidth | Summarized products scale linearly |
| Fusion | Hierarchical: local CC → Bird aggregate → GCS final |
| Consensus | Weighted voting scales to N vehicles |
| Hop coordination | All vehicles share hop table, scale via mesh |

---

## GCS EW Tab (V2)

See `EW_Panel_Mockup.md` for detailed UI specification.

Key V2 additions:
- Multi-layer spectrum view (per tile band)
- ML confidence displays
- DF geometry optimizer
- EA control panel (if enabled)
- Orb track-while-engage display

---

## Success Criteria (V2)

1. Detect and characterize signals 47 MHz - 40+ GHz
2. ML classification with >80% accuracy on known types
3. Geolocate emitters with CEP <50m at 1km range
4. Update Orb targets in-flight with <2s latency
5. Scale to 6+ EW-capable vehicles without degradation
6. RTK timing sync <20ns across swarm
7. Optional EA capability ready for authorized use

---

## Key Files (V2)

| Component | Location | Purpose |
|-----------|----------|---------|
| Tile Manager | `gcs/ew/tile_manager.py` | High-freq tile control |
| ML Pipeline | `gcs/ew/ml/` | Classification models |
| DF Engine | `gcs/ew/df_engine.py` | Multi-platform geolocation |
| Orb Tracker | `gcs/ew/orb_tracker.py` | In-flight update manager |
| EA Controller | `gcs/ew/ea_controller.py` | TX control (if enabled) |

---

## Reference Documents

- `EW_System_V1_Context.md` - V1 foundation
- `EW_Panel_Mockup.md` - GCS UI specification
- `EWBrainstorm.txt` - Original requirements
- `Mesh_Network_Design.md` - Communication protocols
