# Shrike V1 — Full System Specification

**Status:** Concept Frozen
**Target:** Post-V0 validation (April 2026+)
**Budget:** ~$77,000 (4 Scouts) / ~$98,000 (6 Scouts)
**Purpose:** Operational EW/Recon/Strike capability

---

## 1. Overview

V1 is the full-capability Shrike system. Design frozen pending V0 validation. This document captures the complete specification for reference during V0 development.

### System Summary

| Component | Quantity | Unit Cost | Description |
|-----------|----------|-----------|-------------|
| Carrier | 1 | $11,022 | 3m flying wing, VOXL 2, Starlink |
| Scout | 4-6 | $10,696 | 10" folding quad, Sidekiq X2, Pi 5 + Hailo |

---

## 2. Scout V1 Specification

### Platform

| Spec | Value |
|------|-------|
| Airframe | 10" folding quad |
| AUW | ~2.1 kg |
| Flight time | 35-45 min |
| Cruise speed | 15-20 m/s |
| Folded size | ~30 × 20 × 15 cm |
| Deployed size | ~55 cm motor-to-motor |

### Hardware BOM

| Category | Components | Cost | Weight |
|----------|------------|------|--------|
| **Airframe & Propulsion** | | | |
| Frame | iFlight XL10 V6 (folding) | $120 | 280g |
| Motors | T-Motor Velox 3110 900KV ×4 | $120 | 260g |
| ESCs | T-Motor F55A Pro II 4-in-1 | $80 | 25g |
| Props | T-Motor T1050 ×4 sets | $40 | 60g |
| **Compute & AI** | | | |
| SBC | Raspberry Pi 5 (8GB) | $80 | 50g |
| AI Accelerator | Hailo-8 M.2 + HAT | $100 | 30g |
| Cooling | Active heatsink + fan | $20 | 25g |
| Flight Controller | Holybro Pixhawk 6C Mini | $200 | 35g |
| GPS | Holybro M10 GPS | $50 | 25g |
| **Communications** | | | |
| LoRa Mesh | LILYGO T-Beam S3 Supreme | $45 | 30g |
| Video TX | DJI O3 Air Unit | $230 | 35g |
| ELRS RX | RadioMaster RP3 | $25 | 3g |
| mLRS RX | MatekSys mR900-30 | $40 | 5g |
| Antennas | LoRa, ELRS, mLRS, Video set | $40 | 30g |
| **Sensors & EW Payload** | | | |
| SDR | **Epiq Sidekiq X2** | $8,000 | 60g |
| GPSDO | Leo Bodnar Mini | $80 | 25g |
| S/C Antennas | Taoglas patches ×4 | $120 | 60g |
| Optical Flow | Mateksys 3901-L0X | $25 | 5g |
| Rangefinder | Benewake TFmini-S | $40 | 10g |
| **Power** | | | |
| Cells | Molicel P42A 21700 ×12 | $84 | 840g |
| BMS | Daly 6S 40A Smart BMS | $25 | 35g |
| Pack assembly | Nickel, shrink, XT60 | $20 | 25g |
| **Integration** | | | |
| Power distribution | Matek FCHUB-6S | $20 | 10g |
| Wiring harness | Custom | $40 | 40g |
| 3D printed parts | PETG mounts | $30 | 60g |
| Vibration damping | Gel pads, standoffs | $15 | 10g |
| Shielding | Copper tape, ferrites | $15 | 20g |
| Fasteners | Bolts, nuts, zipties | $20 | 20g |
| **Totals** | | | |
| Subtotal | | $9,724 | 2,113g |
| Contingency (10%) | | $972 | — |
| **Total** | | **$10,696** | **~2.1 kg** |

### Scout V1 Capabilities

| Capability | Specification |
|------------|---------------|
| EW bands | S-band (2-4 GHz), C-band (4-6 GHz) |
| SDR | 4 channels, 100 MHz IBW each |
| DF capable | Yes (4 coherent channels) |
| AI inference | 26 TOPS, 30-60 FPS YOLO |
| Autonomous | Yes (link-loss mission continuation) |
| Video | DJI O3 HD (10+ km range) |
| Comms | LoRa mesh + mLRS + ELRS |

### Scout V1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SCOUT V1 (10" Folding)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         SIDEKIQ X2 (4-Channel)                       │   │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │   │
│   │  │ Ch1 S   │  │ Ch2 S   │  │ Ch3 C   │  │ Ch4 C   │                 │   │
│   │  │ 2-3 GHz │  │ 3-4 GHz │  │ 4-5 GHz │  │ 5-6 GHz │                 │   │
│   │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                 │   │
│   │       └────────────┴────────────┴────────────┘                       │   │
│   │                          │                                           │   │
│   │                    Phase coherent                                    │   │
│   │                    (enables DF)                                      │   │
│   └──────────────────────────┼──────────────────────────────────────────┘   │
│                              │ USB 3.0                                       │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      RASPBERRY PI 5 + HAILO-8                        │   │
│   │                                                                      │   │
│   │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │   │
│   │   │ SDR Processing│    │ YOLO Detection│    │ Mission Logic │       │   │
│   │   │ • Pulse detect│    │ • 30-60 FPS   │    │ • Autonomous  │       │   │
│   │   │ • PDW extract │    │ • 26 TOPS     │    │ • Link-loss   │       │   │
│   │   │ • AoA (DF)    │    │               │    │ • Strike exec │       │   │
│   │   └───────────────┘    └───────────────┘    └───────────────┘       │   │
│   └─────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                            │
│   ┌──────────────┐    ┌────────┴────────┐    ┌──────────────┐              │
│   │ DJI O3 Video │    │ Pixhawk 6C Mini │    │ T-Beam S3    │              │
│   │ 5.8 GHz      │    │ ArduPilot       │    │ LoRa Mesh    │              │
│   │ ──► Carrier  │    │                 │    │ ◄─► Carrier  │              │
│   └──────────────┘    └─────────────────┘    └──────────────┘              │
│                                                                              │
│   6S2P Li-ion (8.4Ah) ──► 35-45 min flight time                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Carrier V1 Specification

### Platform

| Spec | Value |
|------|-------|
| Airframe | 3m flying wing (custom) |
| AUW | ~8.2 kg |
| Endurance | 3 hours |
| Cruise speed | 25 m/s |
| Payload bay | Fits 4-6 folded Scouts |

### Hardware BOM

| Category | Components | Cost | Weight |
|----------|------------|------|--------|
| **Airframe** | Custom 3m flying wing | $3,000 | 2,500g |
| **Propulsion** | Motor, ESC, prop, servos | $400 | 600g |
| **Autopilot** | Pixhawk 6X + redundancy | $600 | 80g |
| **Compute** | VOXL 2 | $1,270 | 16g |
| **BLOS Comms** | Starlink Mini + mount | $700 | 1,200g |
| **SDR** | Ettus B205mini | $500 | 80g |
| **Timing** | Jackson Labs CSAC | $1,500 | 50g |
| **GPS** | u-blox ZED-F9P | $200 | 20g |
| **Antennas** | VHF dipole, S/C patches | $150 | 100g |
| **Scout Comms** | LoRa gateway, Video RX, mLRS TX | $300 | 100g |
| **Power** | 6S 30Ah Li-ion | $500 | 2,800g |
| **Deploy Bay** | Scout bay, release mechanism | $400 | 400g |
| **Integration** | Wiring, shielding, enclosure | $500 | 300g |
| **Totals** | | | |
| Subtotal | | $10,020 | 8,246g |
| Contingency (10%) | | $1,002 | — |
| **Total** | | **$11,022** | **~8.2 kg** |

### Carrier V1 Capabilities

| Capability | Specification |
|------------|---------------|
| Compute | VOXL 2 (15 TOPS, integrated FC) |
| BLOS | Starlink Mini (global reach) |
| Video | Receives from all Scouts |
| EW | Own B205mini for reference/VHF |
| Timing | CSAC for TDOA master reference |
| Scout deployment | 4-6 Scouts from internal bay |

### Carrier V1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CARRIER V1 (3m Flying Wing)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         STARLINK MINI                                │   │
│   │                    ┌─────────────────────┐                          │   │
│   │                    │   29 × 25 cm dish   │                          │   │
│   │                    │   Top-mounted       │                          │   │
│   │                    │   Global backhaul   │                          │   │
│   │                    └──────────┬──────────┘                          │   │
│   │                               │ Ethernet                             │   │
│   └───────────────────────────────┼─────────────────────────────────────┘   │
│                                   │                                          │
│   ┌───────────────────────────────┼─────────────────────────────────────┐   │
│   │                          VOXL 2                                      │   │
│   │                                                                      │   │
│   │   • 15 TOPS AI processing                                           │   │
│   │   • Integrated flight controller                                    │   │
│   │   • Scout data aggregation                                          │   │
│   │   • TDOA geolocation processing                                     │   │
│   │   • Video relay to GCS via Starlink                                │   │
│   │                                                                      │   │
│   └──────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                           │
│        ┌─────────────────────────┼─────────────────────────┐                │
│        │                         │                         │                │
│        ▼                         ▼                         ▼                │
│   ┌──────────┐            ┌──────────┐            ┌──────────┐             │
│   │ B205mini │            │ LoRa GW  │            │ Video RX │             │
│   │ VHF-6GHz │            │ T-Beam   │            │ DJI/Analog│            │
│   │ Reference│            │ ◄─►Scout │            │ ◄─ Scout │             │
│   └──────────┘            └──────────┘            └──────────┘             │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         SCOUT BAY                                    │   │
│   │   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                  │   │
│   │   │  S  │ │  S  │ │  S  │ │  S  │ │  S  │ │  S  │   (4-6 Scouts)  │   │
│   │   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                  │   │
│   │                    Deploy on command                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   6S 30Ah Li-ion ──► 3 hour endurance                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Communications Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        V1 COMMUNICATIONS ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              ┌─────────────┐                                │
│                              │     GCS     │                                │
│                              │  (Anywhere) │                                │
│                              └──────┬──────┘                                │
│                                     │                                        │
│                              ════════════════                                │
│                              ║   STARLINK   ║                               │
│                              ║   (Global)   ║                               │
│                              ════════════════                                │
│                                     │                                        │
│                                     │ 50-100 Mbps, 20-40ms latency          │
│                                     │                                        │
│                              ┌──────▼──────┐                                │
│                              │   CARRIER   │                                │
│                              │             │                                │
│                              │ LoRa + mLRS │                                │
│                              │ Video RX    │                                │
│                              └──────┬──────┘                                │
│                                     │                                        │
│            ┌────────────────────────┼────────────────────────┐              │
│            │                        │                        │              │
│     ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐      │
│     │   SCOUT 1   │◄────────►│   SCOUT 2   │◄────────►│   SCOUT 3   │      │
│     │             │   Mesh   │             │   Mesh   │             │      │
│     └─────────────┘          └─────────────┘          └─────────────┘      │
│                                                                              │
│   LINK LAYERS:                                                              │
│   ═══════════                                                               │
│   • Starlink (Carrier ↔ GCS): 50+ Mbps, global, primary backhaul           │
│   • LoRa Mesh (915 MHz): Commands, telemetry, PDW data, 10-20 km           │
│   • mLRS (868 MHz): MAVLink backup, 20+ km                                 │
│   • ELRS (2.4 GHz): RC override, low latency                               │
│   • Video (5.8 GHz): HD video Scout → Carrier, 10+ km                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. EW Capability

### Detection

| Radar | Band | Frequency | Detection Range |
|-------|------|-----------|-----------------|
| 91N6E "Big Bird" | S-band | 2.5-3.5 GHz | 50+ km |
| 96L6E "Cheese Board" | C-band | 5-6 GHz | 50+ km |
| Fire control radars | S/C | 2-6 GHz | 30-50 km |

### Geolocation

| Method | Platforms | Expected CEP |
|--------|-----------|--------------|
| TDOA only | 4 Scouts | ~100-150m |
| TDOA + DF | 4 Scouts (Sidekiq X2) | ~50-80m |
| TDOA + DF + Carrier ref | 4 Scouts + Carrier | **<50m** |

### Processing Flow

```
Scout SDR (Sidekiq X2)
        │
        ▼
Pulse Detection (Pi 5)
        │
        ▼
PDW Generation (TOA, freq, amplitude, AoA)
        │
        ▼
LoRa Mesh → Carrier
        │
        ▼
TDOA Processing (VOXL 2)
        │
        ▼
Geolocation Fix
        │
        ▼
Starlink → GCS
```

---

## 6. Autonomous Operations

### Link-Loss Behavior

```python
class ScoutAutonomous:
    """Scout V1 autonomous controller"""

    def on_carrier_link_lost(self):
        # Continue current mission phase
        if self.phase == "SEARCH":
            self.continue_ew_scan()
            self.store_detections_locally()

        elif self.phase == "GEOLOCATE":
            if self.has_sufficient_data():
                self.compute_local_fix()
                self.prepare_strike_if_authorized()
            else:
                self.continue_collection()

        elif self.phase == "STRIKE_AUTHORIZED":
            # Already authorized — execute
            self.execute_terminal_attack()

        # Attempt recovery
        self.climb_for_los()
        self.try_mesh_relay()

        # Failsafe
        if self.battery_critical():
            self.rtb_or_safe_landing()
```

### Strike Authorization

Strike requires explicit authorization from GCS. Once authorized:
1. Target coordinates locked in Scout memory
2. Scout can execute even if link lost
3. Carrier cannot override after authorization

---

## 7. System Cost Summary

### 4-Scout Configuration

| Item | Cost |
|------|------|
| Carrier ×1 | $11,022 |
| Scout ×4 | $42,784 |
| Ground Station | $3,000 |
| Starlink (1 year) | $1,800 |
| Support equipment | $1,000 |
| Spares | $12,000 |
| Development | $5,000 |
| **Total** | **$76,606** |

### 6-Scout Configuration

| Item | Cost |
|------|------|
| Carrier ×1 | $11,022 |
| Scout ×6 | $64,176 |
| Ground Station | $3,000 |
| Starlink (1 year) | $1,800 |
| Support equipment | $1,000 |
| Spares | $12,000 |
| Development | $5,000 |
| **Total** | **$97,998** |

---

## 8. V0 → V1 Transition Criteria

V1 development proceeds when V0 demonstrates:

| V0 Result | V1 Implication |
|-----------|----------------|
| LoRa range adequate | Keep LoRa mesh architecture |
| LoRa range insufficient | Add more mLRS, reduce mesh reliance |
| Pi 5 ML adequate | Hailo-8 is bonus, not critical |
| Pi 5 ML insufficient | Hailo-8 confirmed necessary |
| PlutoSDR IBW limiting | Sidekiq X2 upgrade justified |
| PlutoSDR IBW adequate | Consider cheaper SDR for V1 |
| 5" endurance acceptable | 10" upgrade for range, not endurance |
| 5" endurance limiting | 10" upgrade critical |

---

## 9. Revision History

| Date | Change |
|------|--------|
| 2026-02-07 | V1 specification frozen |

---

## Appendix: Naming Convention

| Term | Description |
|------|-------------|
| **Shrike** | Project name |
| **Carrier** | Fixed-wing mothership (deploys Scouts) |
| **Scout** | Multirotor EW/Recon/Strike platform |
| **V0** | Demonstrator (5", cheap hardware) |
| **V1** | Full system (10", Sidekiq X2, Starlink) |
