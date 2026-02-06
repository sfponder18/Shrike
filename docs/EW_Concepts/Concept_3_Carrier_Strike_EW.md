# Concept 3: Carrier-Deployed Strike/Recon Swarm with EW

**Status:** Conceptual Design
**Date:** 2026-02-06
**Relationship:** Intended for merge with SwarmDrones project

---

## 1. Executive Summary

A fixed-wing carrier aircraft deploys multiple low-cost attritable drones capable of:
- Electronic Support (ES) — S/C band radar detection and geolocation
- Reconnaissance — visual/IR sensor payload
- Light Strike — terminal guidance to designated targets

The carrier provides transport, C2 relay, wide-area EW scan, and standoff safety. Deployed drones are expendable/attritable, optimized for cost rather than recovery.

---

## 2. Concept Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONCEPT 3: CARRIER STRIKE/EW                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                    ┌─────────────────────────────────┐                   │
│                    │         CARRIER (MOTHER)         │                  │
│                    │  ═══════════════════════════    │                  │
│                    │   ╲                       ╱     │                  │
│                    │    ╲   2.5-3m wingspan   ╱      │                  │
│                    │     ╲                   ╱       │                  │
│                    │      ╲_________________╱        │                  │
│                    │                                  │                  │
│                    │  • Carries 4-6 Scouts internally │                  │
│                    │  • Own EW suite (wide-area scan) │                  │
│                    │  • C2 relay to ground            │                  │
│                    │  • 2-3 hour endurance            │                  │
│                    │  • Standoff: 30-50 km            │                  │
│                    └───────────────┬─────────────────┘                   │
│                                    │                                     │
│                          DEPLOY ON COMMAND                               │
│                                    │                                     │
│               ┌────────────────────┼────────────────────┐                │
│               │          │         │         │          │                │
│               ▼          ▼         ▼         ▼          ▼                │
│           ┌──────┐   ┌──────┐  ┌──────┐  ┌──────┐   ┌──────┐            │
│           │Scout │   │Scout │  │Scout │  │Scout │   │Scout │            │
│           │  1   │   │  2   │  │  3   │  │  4   │   │  5   │            │
│           └──┬───┘   └──┬───┘  └──┬───┘  └──┬───┘   └──┬───┘            │
│              │          │         │         │          │                 │
│              └──────────┴────┬────┴─────────┴──────────┘                 │
│                              │                                           │
│                              ▼                                           │
│                    ┌─────────────────────┐                               │
│                    │   MISSION MODES     │                               │
│                    ├─────────────────────┤                               │
│                    │ • EW: Detect/locate │                               │
│                    │ • RECON: ISR loiter │                               │
│                    │ • STRIKE: Terminal  │                               │
│                    └─────────────────────┘                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Design Philosophy

### Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Attritable** | Scouts are expendable; design for low cost, not longevity |
| **Multi-role** | Same platform does EW, recon, and strike |
| **Deployable** | Carrier transports Scouts to AO, deploys on command |
| **Networked** | Scouts cooperate for TDOA geolocation |
| **S/C Focus** | Prioritize 2-6 GHz; small antennas, good performance |
| **Merge-ready** | Compatible with SwarmDrones architecture |

### Target Cost Structure

| Element | Target Cost | Notes |
|---------|-------------|-------|
| Scout (each) | **$2,000-3,500** | Attritable, multi-role |
| Carrier | **$15,000-20,000** | Reusable, high-value |
| Full system (1 Carrier + 6 Scouts) | **$30,000-40,000** | Complete package |

---

## 4. Target Emitter Set (S/C Band Focus)

Simplified from earlier concepts — VHF/L-band deprioritized:

| Radar | Band | Frequency | Role | Priority |
|-------|------|-----------|------|----------|
| 91N6E "Big Bird" | S-band | 2.5-3.5 GHz | S-400 battle management | **Critical** |
| 96L6E "Cheese Board" | C-band | 5-6 GHz | S-400 acquisition | **High** |
| Fire control radars | S/C | 2-6 GHz | Various tracking | High |
| ATC Primary | S-band | 2.7-2.9 GHz | Reference signal | Low |

**Why drop VHF?**
- VHF antennas too large for small Scouts
- S/C band radars are higher-value targets (fire control, acquisition)
- Carrier can retain VHF capability if needed

---

## 5. Carrier (Mother) Specifications

### Role

- Transport 4-6 Scouts to area of operations
- Deploy Scouts on command (drop or launch)
- Provide C2 relay between Scouts and GCS
- Perform wide-area EW scan (including VHF if equipped)
- Loiter at standoff distance during Scout operations
- Optional: Recovery of Scouts (advanced, adds complexity)

### Airframe Requirements

| Spec | Requirement | Rationale |
|------|-------------|-----------|
| Wingspan | 2.5-3.0 m | Payload capacity, stability |
| Payload bay | 30 × 15 × 15 cm minimum | Fit 4-6 folded Scouts |
| Payload capacity | 3-5 kg | Scouts + own systems |
| Endurance | 2-3 hours | Persist during Scout ops |
| Speed | 25-40 m/s | Transit efficiency |
| Launch | Catapult or runway | Heavier than hand-launch |
| Recovery | Belly or parachute | Reusable |

### Carrier Candidates

| Airframe | Wingspan | Payload | Endurance | Cost | Notes |
|----------|----------|---------|-----------|------|-------|
| **Custom tube-launch** | 2.5m | 4 kg | 2 hr | $2,000 | Purpose-built |
| **Skywalker X8** | 2.1m | 1.5 kg | 1.5 hr | $400 | Marginal payload |
| **Believer** | 1.96m | 1.5 kg | 2 hr | $500 | Marginal payload |
| **XUAV Talon** | 1.7m | 1 kg | 1.5 hr | $300 | Too small |
| **Custom flying wing** | 3.0m | 5 kg | 2.5 hr | $3,000 | Ideal but custom |
| **Modified Volantex Ranger** | 2.0m | 2 kg | 2 hr | $500 | Available platform |

**Recommendation:** Custom 2.5-3m flying wing or tube-body with internal bay.

### Carrier Systems

| Component | Selection | Cost | Notes |
|-----------|-----------|------|-------|
| Airframe | Custom 3m flying wing | $3,000 | Internal payload bay |
| Autopilot | Pixhawk 6C | $300 | ArduPlane |
| Compute | Raspberry Pi 5 8GB | $100 | C2 relay, light processing |
| SDR | Ettus B205mini | $500 | 2-ch, VHF-6 GHz |
| GPS | u-blox ZED-F9P | $200 | PPP capable |
| GPSDO | Leo Bodnar mini | $250 | Timing sync |
| VHF Antenna | Wing dipole | $80 | 0 dBi |
| S/C Antenna | Conformal patch | $60 | +5 dBi |
| Comms to GCS | 4G + LoRa | $300 | Redundant |
| Comms to Scouts | LoRa mesh | $50 | Low-latency |
| Deploy mechanism | Servo-actuated bay doors | $100 | Releases Scouts |
| Power | 6S 16000mAh | $200 | 2.5+ hr |
| Integration | Cables, shielding | $300 | |
| Contingency | 15% | $800 | |
| **Carrier Total** | | **$6,240** | |

**Note:** This is significantly cheaper than previous Mother concepts because the Carrier's EW role is secondary — Scouts do the primary sensing.

---

## 6. Scout Specifications

### Role

Multi-role attritable drone:
1. **EW Mode:** Detect and help geolocate S/C band emitters
2. **Recon Mode:** Visual/IR surveillance of target area
3. **Strike Mode:** Terminal guidance to designated coordinates

### Design Concept

Small, folding quadrotor that deploys from Carrier:

```
    STOWED (in Carrier)              DEPLOYED
    ┌─────────────────┐
    │   ┌─────────┐   │                 ╱╲
    │   │  SCOUT  │   │               ╱    ╲
    │   │ folded  │   │              ●──────●
    │   │  arms   │   │              │ Scout│
    │   └─────────┘   │              │      │
    │    10×10×8 cm   │              ●──────●
    └─────────────────┘               ╲    ╱
                                        ╲╱
                                     25 cm diagonal
```

### Scout Airframe Options

| Type | Pros | Cons | Cost |
|------|------|------|------|
| **Folding quad (5")** | Compact, hover capable | Limited endurance | $200-400 |
| **Folding quad (3")** | Very compact | Less payload | $150-300 |
| **Micro fixed-wing** | Better endurance | No hover, larger stowed | $200-400 |
| **Switchblade-style** | Optimized for deploy | Less hover capable | $300-500 |

**Recommendation:** 5" folding quadrotor — balances size, capability, and cost.

### Scout Requirements

| Spec | Requirement | Rationale |
|------|-------------|-----------|
| Stowed size | ≤12 × 12 × 10 cm | Fit 4-6 in Carrier bay |
| Deployed size | ~25 cm diagonal | 5" prop class |
| Weight | 300-500g | Carrier payload budget |
| Endurance | 15-20 min | Sufficient for mission |
| Speed | 15-25 m/s | Transit and orbit |
| Payload | SDR + camera | Multi-role |

### Scout Systems

| Component | Selection | Cost | Notes |
|-----------|-----------|------|-------|
| **Airframe** | 5" folding frame (custom) | $150 | Spring-deploy arms |
| **Motors** | 2306 2400KV × 4 | $60 | |
| **ESC** | 4-in-1 35A | $40 | |
| **Flight Controller** | Speedybee F405 or similar | $50 | BetaFlight or ArduPilot |
| **Compute** | Raspberry Pi Zero 2W | $20 | Lightweight |
| **SDR** | RTL-SDR V4 | $40 | Basic, S/C capable |
| **— OR —** | AirSpy Mini | $100 | Better performance |
| **GPS** | u-blox M10 | $30 | Standard GPS |
| **S-band Antenna** | Small patch (2-4 GHz) | $20 | +3 dBi |
| **C-band Antenna** | Small patch (4-6 GHz) | $20 | +4 dBi |
| **Camera** | Caddx Peanut or similar | $40 | 1080p, low latency |
| **Mesh Radio** | ESP32 + LoRa | $15 | Scout-to-Scout, Scout-to-Carrier |
| **Power** | 4S 850mAh | $25 | 15-20 min flight |
| **Strike payload** | GPS-guided or FPV terminal | $100 | Optional, adds cost |
| **Integration** | Cables, 3D-printed parts | $50 | |
| **Contingency** | 15% | $100 | |
| **Scout Total (Basic)** | | **~$760** | EW + Recon |
| **Scout Total (Strike)** | | **~$860** | + Terminal guidance |

### Scout Cost Tiers

| Tier | SDR | Camera | Strike | Cost | Use Case |
|------|-----|--------|--------|------|----------|
| **Basic** | RTL-SDR V4 | 1080p | No | $760 | Recon + basic EW |
| **Enhanced** | AirSpy Mini | 1080p | No | $820 | Better EW performance |
| **Strike** | RTL-SDR V4 | 1080p | Yes | $860 | Full multi-role |
| **Strike+** | AirSpy Mini | 1080p | Yes | $920 | Best capability |

---

## 7. EW Capability (S/C Band)

### SDR Comparison for Scout

| SDR | Frequency | IBW | Bits | Size | Power | Cost | Score |
|-----|-----------|-----|------|------|-------|------|-------|
| RTL-SDR V4 | 24 MHz - 1.8 GHz | 2.4 MHz | 8 | Tiny | 0.3W | $40 | **Limited** |
| RTL-SDR V4 + upconverter | Extended | 2.4 MHz | 8 | Small | 0.5W | $80 | Hack, unreliable |
| **AirSpy Mini** | 24 MHz - 1.8 GHz | 6 MHz | 12 | Small | 0.5W | $100 | **Better, same limit** |
| **AirSpy R2** | 24 MHz - 1.8 GHz | 10 MHz | 12 | Medium | 1W | $200 | Good, still limited |
| **Nooelec SMArt** | 25 MHz - 1.75 GHz | 2.4 MHz | 8 | Tiny | 0.3W | $30 | Basic |

**Problem:** Consumer SDRs typically max out at 1.8 GHz. S-band (2-4 GHz) and C-band (4-6 GHz) require different hardware.

### Solution: S/C Band Capable SDRs

| SDR | Frequency | IBW | Cost | Size | Notes |
|-----|-----------|-----|------|------|-------|
| **Ettus B205mini** | 70 MHz - 6 GHz | 56 MHz | $500 | Credit card | Best option |
| **HackRF One** | 1 MHz - 6 GHz | 20 MHz | $350 | Medium | 8-bit limits dynamic range |
| **LimeSDR Mini 2.0** | 10 MHz - 3.5 GHz | 30 MHz | $300 | Small | Misses C-band |
| **PlutoSDR** | 70 MHz - 6 GHz | 20 MHz | $200 | Small | Lower performance |

**Revised Scout SDR Recommendation:**

For S/C band focus, must use an SDR that actually covers these frequencies:

| Option | SDR | Cost Impact | Performance |
|--------|-----|-------------|-------------|
| **Budget** | PlutoSDR | +$200 | Basic S/C coverage |
| **Standard** | HackRF One | +$350 | Good coverage, 8-bit |
| **Best** | Ettus B205mini | +$500 | Full performance |

### Revised Scout BOM (S/C Band Capable)

| Component | Selection | Cost |
|-----------|-----------|------|
| Airframe | 5" folding frame | $150 |
| Motors/ESC/FC | Complete stack | $150 |
| Compute | Raspberry Pi Zero 2W | $20 |
| **SDR** | **PlutoSDR** | $200 |
| GPS | u-blox M10 | $30 |
| S/C Antenna | Dual-band patch | $30 |
| Camera | Caddx Peanut | $40 |
| Mesh Radio | ESP32 + LoRa | $15 |
| Power | 4S 850mAh | $25 |
| Strike payload | Terminal guidance | $100 |
| Integration | Cables, 3D-printed | $50 |
| Contingency | 15% | $120 |
| **Scout Total** | | **$930** |

**Or with B205mini for better performance:**

| Scout Tier | SDR | Total Cost |
|------------|-----|------------|
| Basic (PlutoSDR) | $200 | **$930** |
| Standard (HackRF) | $350 | **$1,080** |
| Performance (B205mini) | $500 | **$1,230** |

---

## 8. Strike Capability

### Strike Modes

| Mode | Description | Guidance | Accuracy |
|------|-------------|----------|----------|
| **Coordinate** | Fly to GPS coordinate, terminal dive | GPS | 5-10m CEP |
| **Loitering** | Orbit target, dive on command | GPS + operator | 3-5m CEP |
| **EW-cued** | Geolocate emitter, strike location | TDOA + GPS | 50-100m CEP |
| **FPV Terminal** | Operator guides final approach | Video | <1m |

### Strike Payload Options

The Scout itself can be the munition (kamikaze), or carry a small payload:

| Approach | Payload | Pros | Cons |
|----------|---------|------|------|
| **Scout-as-munition** | Scout body + battery | Simple, reliable | Lose Scout |
| **Dropped payload** | Small grenade/bomblet | Scout survives | Complex release, less accurate |
| **Retained payload** | Fixed warhead | Simple | Heavier Scout |

**Recommendation:** Scout-as-munition for simplicity. At $930-1,200 per Scout, it's attritable.

### EW-Cued Strike CONOPS

```
PHASE 1: DEPLOYMENT
├── Carrier transits to AO (30-50 km standoff)
├── Carrier performs wide-area scan
├── Detects S-band emitter (suspected 91N6E)
├── Deploys 4× Scouts

PHASE 2: GEOLOCATION
├── Scouts spread to 5-10 km baseline
├── All Scouts tune to detected frequency
├── TDOA computed (100-200m CEP initial)
├── Scouts orbit, refine with multiple measurements
├── Final fix: 50-100m CEP

PHASE 3: STRIKE DECISION
├── Operator reviews target (recon imagery from Scouts)
├── Authorizes strike
├── Designates 1-2 Scouts for strike, others continue EW/recon

PHASE 4: TERMINAL
├── Strike Scout(s) navigate to target coordinates
├── Final approach: GPS-guided dive OR FPV terminal
├── Impact

PHASE 5: ASSESSMENT
├── Remaining Scouts provide BDA imagery
├── Report to Carrier → GCS
├── Continue mission or RTB
```

---

## 9. Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                              ┌─────────┐                                 │
│                              │   GCS   │                                 │
│                              │ Operator│                                 │
│                              └────┬────┘                                 │
│                                   │                                      │
│                            4G / Long-range                               │
│                                   │                                      │
│                              ┌────▼────┐                                 │
│                              │ CARRIER │                                 │
│                              │  ╲   ╱  │                                 │
│                              │   ═══   │                                 │
│                              └────┬────┘                                 │
│                                   │                                      │
│                             LoRa Mesh                                    │
│                                   │                                      │
│         ┌─────────────────────────┼─────────────────────────┐            │
│         │           │             │             │           │            │
│         ▼           ▼             ▼             ▼           ▼            │
│     ┌───────┐   ┌───────┐    ┌───────┐    ┌───────┐   ┌───────┐         │
│     │Scout 1│◄─►│Scout 2│◄──►│Scout 3│◄──►│Scout 4│◄─►│Scout 5│         │
│     └───────┘   └───────┘    └───────┘    └───────┘   └───────┘         │
│         │           │             │             │           │            │
│         └───────────┴─────────────┴─────────────┴───────────┘            │
│                          Scout-to-Scout mesh                             │
│                       (timing sync, PDW sharing)                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   SCOUT     │      │   CARRIER   │      │    GCS      │
├─────────────┤      ├─────────────┤      ├─────────────┤
│ • SDR RX    │      │ • Aggregate │      │ • Display   │
│ • Pulse det │ ───► │   PDWs      │ ───► │ • TDOA calc │
│ • PDW gen   │ PDW  │ • Relay     │ PDW  │ • Track mgmt│
│ • Camera    │ ───► │ • Own EW    │ ───► │ • Strike    │
│ • GPS/time  │ Vid  │ • C2 relay  │ Data │   authority │
└─────────────┘      └─────────────┘      └─────────────┘
```

### Timing Synchronization

For TDOA, Scouts need synchronized timing:

| Method | Accuracy | Cost Impact | Notes |
|--------|----------|-------------|-------|
| GPS PPS only | ~50 ns | $0 | Basic, sufficient for 15m |
| GPS PPS + correction | ~20 ns | $10 | Software correction |
| Carrier broadcasts sync | ~100 ns | $0 | Uses LoRa, less accurate |

At S/C band frequencies with 5-10 km baselines:
- 50 ns timing error ≈ 15m range error
- With 4+ Scouts: **CEP of 50-100m achievable**

This is sufficient for strike cueing.

---

## 10. Carrier Scout Deployment

### Deployment Mechanism

```
          CARRIER (side view, bay open)

    ════════════════════════════════════
     ╲                                ╱
      ╲   ┌────────────────────────┐ ╱
       ╲  │ Scout 1 │ Scout 2 │... │╱
        ╲ └────────────────────────┘
         ╲    BAY DOORS (open)    ╱
          ════════════════════════

    Deployment sequence:
    1. Carrier level flight, bay doors open
    2. Scout released (drops ~5m)
    3. Scout unfolds arms (spring-loaded)
    4. Scout motors start, stabilizes
    5. Scout enters autonomous flight
    6. Next Scout deployed (2-3 sec interval)
```

### Scout Folding Design

```
    FOLDED                    UNFOLDING                 DEPLOYED

    ┌─────┐                   ┌─────┐                   ╱╲     ╱╲
    │     │                   │╲   ╱│                  ╱  ╲   ╱  ╲
    │  ●  │ ──────────►       │ ╲ ╱ │ ──────────►     ●────●─●────●
    │     │   Release         │  ●  │   Spring         │  ●  │
    └─────┘                   │ ╱ ╲ │   deploy         │ BODY│
                              │╱   ╲│                  ●────●─●────●
                              └─────┘                   ╲  ╱   ╲  ╱
                                                         ╲╱     ╲╱

    Folded: 10×10×8 cm        Transition: 0.3s         Deployed: 25cm
```

### Deployment Safety

| Concern | Mitigation |
|---------|------------|
| Scout hits Carrier | 5m drop before motor start |
| Arm doesn't unfold | Spring-loaded with detent |
| Motor start failure | Pre-arm check before release |
| Scouts collide | 3 sec spacing, divergent paths |
| Deploy at wrong altitude | Minimum deploy altitude (100m AGL) |

---

## 11. Mission Profiles

### Profile A: EW Search & Geolocate

```
Duration: 1-2 hours
Scouts: 4-6 (no strike)

1. Carrier transits to AO
2. Deploys 4 Scouts at 10 km spacing
3. Scouts scan S/C bands
4. Detections reported to Carrier → GCS
5. TDOA geolocation computed
6. Scouts reposition for better geometry
7. Refined locations reported
8. Mission complete: Scouts RTB to Carrier vicinity or expended
```

### Profile B: EW + Strike

```
Duration: 30-60 min
Scouts: 4 (2 EW, 2 strike)

1. Carrier transits to AO
2. Deploys 4 Scouts
3. Scouts detect and geolocate emitter
4. Operator reviews, authorizes strike
5. 2 Scouts designated strike (expended)
6. 2 Scouts continue recon for BDA
7. Strike Scouts execute terminal guidance
8. Remaining Scouts image target, report BDA
9. Carrier recovers or scouts expend
```

### Profile C: Multi-Target Strike

```
Duration: 45-90 min
Scouts: 6 (all strike-capable)

1. Carrier transits with 6 Scouts
2. Deploys 4 Scouts initially
3. Scouts geolocate multiple emitters
4. Operator prioritizes targets
5. Strike authorized on Target 1 (1 Scout)
6. Remaining Scouts continue EW
7. Second target emerges (91N6E + 96L6E pair)
8. Carrier deploys reserve 2 Scouts
9. Coordinated strike on target pair
10. Remaining Scouts for BDA
```

---

## 12. Complete System BOM

### Scout (Strike-Capable, S/C Band)

| Component | Selection | Cost |
|-----------|-----------|------|
| Airframe (folding 5") | Custom | $150 |
| Motors/ESC/FC | Complete | $150 |
| Compute | Pi Zero 2W | $20 |
| SDR | PlutoSDR | $200 |
| GPS | u-blox M10 | $30 |
| Dual-band Antenna | S/C patch | $30 |
| Camera | Caddx 1080p | $40 |
| Mesh Radio | ESP32+LoRa | $15 |
| Power | 4S 850mAh | $25 |
| Terminal guidance | GPS dive | $100 |
| Integration | Cables, print | $50 |
| Contingency | 15% | $120 |
| **Scout Total** | | **$930** |

### Carrier

| Component | Selection | Cost |
|-----------|-----------|------|
| Airframe | Custom 3m flying wing | $3,000 |
| Autopilot | Pixhawk 6C | $300 |
| Compute | Raspberry Pi 5 | $100 |
| SDR | Ettus B205mini | $500 |
| GPS | u-blox ZED-F9P | $200 |
| GPSDO | Leo Bodnar | $250 |
| Antennas | VHF dipole + S/C patch | $140 |
| Comms (GCS) | 4G + LoRa | $300 |
| Comms (Scouts) | LoRa mesh | $50 |
| Deploy mechanism | Servo bay | $100 |
| Power | 6S 16000mAh | $200 |
| Integration | | $300 |
| Contingency | 15% | $800 |
| **Carrier Total** | | **$6,240** |

### System Configurations

| Configuration | Scouts | Scout Cost | Carrier | Total |
|---------------|--------|------------|---------|-------|
| **Minimal** | 4 | $3,720 | $6,240 | **$9,960** |
| **Standard** | 6 | $5,580 | $6,240 | **$11,820** |
| **Full (2 Carriers)** | 12 | $11,160 | $12,480 | **$23,640** |

### Upgrade: B205mini Scouts

For better EW performance:

| Scout SDR | Unit Cost | 6× Scouts | Carrier | Total |
|-----------|-----------|-----------|---------|-------|
| PlutoSDR ($200) | $930 | $5,580 | $6,240 | $11,820 |
| **B205mini ($500)** | $1,230 | $7,380 | $6,240 | **$13,620** |

**Recommendation:** Standard config with PlutoSDR Scouts ($11,820) for initial capability. Upgrade subset to B205mini if higher performance needed.

---

## 13. Integration with SwarmDrones

This concept maps well to SwarmDrones architecture:

| SwarmDrones | Concept 3 | Notes |
|-------------|-----------|-------|
| Bird | Carrier | Fixed-wing, carries others |
| Chick | Scout (EW/Recon mode) | Multirotor, deploys from carrier |
| Orb | Scout (Strike mode) | Same platform, terminal mode |
| GCS | GCS | Command and control |

### Naming Convention Alignment

```
SwarmDrones:    bird1 → chick1.1, chick1.2 → orb1.1.1, orb1.1.2
Concept 3:      carrier1 → scout1.1, scout1.2, scout1.3...

Merged:         carrier1 → scout1.1 (EW), scout1.2 (strike)...
```

### Shared Components

| Component | Can Share? | Notes |
|-----------|------------|-------|
| GCS software | Yes | Add EW display panel |
| Comms protocol | Yes | Extend for PDW messages |
| Mesh network | Yes | LoRa backbone compatible |
| GPS infrastructure | Yes | Same timing approach |
| Video pipeline | Yes | Same protocols |

### Key Merge Points

1. **Carrier = Bird evolution** — Add internal bay, deploy mechanism
2. **Scout = Chick evolution** — Add EW payload, strike mode
3. **Orb deprecated** — Scout-as-munition replaces dedicated Orb
4. **GCS additions** — EW display, TDOA processing, strike authorization

---

## 14. Development Roadmap

### Phase 1: Scout Prototype (Weeks 1-6)

- [ ] Design folding 5" frame (CAD)
- [ ] Prototype fold mechanism
- [ ] Integrate PlutoSDR + Pi Zero 2W
- [ ] Basic S/C band pulse detection
- [ ] Ground test complete

### Phase 2: Scout Flight Test (Weeks 7-10)

- [ ] Flight test folding Scout
- [ ] Validate deploy unfold sequence (drop test)
- [ ] Test EW detection in flight
- [ ] Test camera/video link
- [ ] Validate GPS terminal guidance (soft target)

### Phase 3: Carrier Development (Weeks 11-16)

- [ ] Design Carrier airframe with bay
- [ ] Build Carrier prototype
- [ ] Integrate bay doors and release mechanism
- [ ] Flight test Carrier (no Scouts)
- [ ] Ground test deploy mechanism

### Phase 4: Integrated System (Weeks 17-22)

- [ ] Deploy Scouts from Carrier (flight test)
- [ ] Multi-Scout coordination
- [ ] TDOA geolocation validation
- [ ] Full mission profile test
- [ ] Integrate with SwarmDrones GCS

### Phase 5: Strike Capability (Weeks 23-26)

- [ ] Terminal guidance validation
- [ ] EW-cued strike test
- [ ] Full CONOPS demonstration
- [ ] Documentation complete

---

## 15. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scout unfold failure | Medium | High | Redundant springs, pre-flight test |
| PlutoSDR insufficient | Medium | Medium | Path to B205mini upgrade |
| Carrier payload marginal | Low | High | Design for margin, reduce Scout weight |
| TDOA accuracy insufficient | Medium | Medium | More Scouts, better timing |
| Scout endurance too short | Medium | Medium | Battery optimization, efficient ops |
| Mesh network overload | Low | Medium | Prioritize PDW over video |
| Scout-to-Scout collision | Low | High | Deconfliction algorithm |

---

## 16. Comparison: Concept 3 vs Earlier Configs

| Metric | Config 1 (Quad) | Config 2 (FW) | **Concept 3 (Carrier)** |
|--------|-----------------|---------------|-------------------------|
| EW Nodes | 4 dedicated | 4 dedicated | 4-6 Scouts (multi-role) |
| Mother | 1 (hover) | 1 (FW) | 1 Carrier (deploys) |
| Strike | No | No | **Yes** |
| Recon | Limited | Limited | **Yes** |
| Node cost | $13,840 | $14,240 | **$930-1,230** |
| System cost | $78,385 | $75,260 | **$11,820-13,620** |
| CEP (EW) | 50-80m | 35-60m | 50-100m |
| Attritable | No (expensive) | No | **Yes** |
| VHF capable | Yes (poor) | Yes (good) | Carrier only |
| Endurance | 25 min | 2 hours | 15 min (Scouts), 2.5 hr (Carrier) |

**Concept 3 is 6× cheaper** than earlier configs while adding strike and recon capability. Trade-off is reduced per-node EW performance (simpler SDR) and shorter Scout endurance.

---

## 17. Future Enhancements

| Enhancement | Benefit | Complexity |
|-------------|---------|------------|
| Scout recovery (net) | Reuse Scouts | High |
| Scout refuel/rearm | Extended ops | Very High |
| AI target recognition | Autonomous strike | Medium |
| Swarm coordination | Mass strike | Medium |
| EW-guided terminal | Better strike accuracy | Medium |
| Carrier VHF payload | Early warning detection | Low |
| Larger Scout (7") | More payload/endurance | Low |

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-06 | Initial Concept 3 document |
