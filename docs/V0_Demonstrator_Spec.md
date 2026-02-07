# Shrike V0 — Demonstrator Specification

**Status:** Active Development
**Target Completion:** March 2026
**Budget:** $5,000
**Purpose:** Prove concepts, finalize V1 requirements

---

## 1. Overview

V0 is a small-scale demonstrator to validate core Shrike concepts before committing to the full V1 system. Uses COTS hardware on smaller platforms to reduce cost and risk.

### V0 vs V1 Comparison

| Aspect | V0 (Demonstrator) | V1 (Full System) |
|--------|-------------------|------------------|
| Scout platform | 5" quad | 10" folding quad |
| Scout compute | Pi 5 (no Hailo) | Pi 5 + Hailo-8 |
| Scout SDR | PlutoSDR | Sidekiq X2 |
| Carrier platform | Foamy (friend-built) | 3m flying wing |
| Carrier compute | Jetson Orin Nano | VOXL 2 |
| Carrier BLOS | No | Starlink Mini |
| Fleet size | 1 + 2 | 1 + 4-6 |
| Budget | $5,000 | ~$77,000 |
| Purpose | Prove concepts | Operational capability |

---

## 2. V0 Test Objectives

### Primary (Must Demonstrate)

| # | Objective | Success Criteria |
|---|-----------|------------------|
| 1 | **LoRa mesh comms** | Scouts and Carrier exchange data reliably at 2+ km |
| 2 | **Video streaming** | Scout streams 720p+ video to Carrier |
| 3 | **Autonomous flight** | Scouts execute waypoint missions independently |
| 4 | **SDR spectrum sensing** | Scout detects known S/C band signals |

### Secondary (Stretch Goals)

| # | Objective | Success Criteria |
|---|-----------|------------------|
| 5 | Basic ML detection | Pi 5 runs YOLO at 5+ FPS, detects objects |
| 6 | Link-loss behavior | Scout continues mission when Carrier link lost |
| 7 | Multi-Scout coordination | 2 Scouts share data via mesh |

### Deferred to V1

- TDOA geolocation (needs GPSDO, precise timing)
- Direction finding (needs 4-channel SDR)
- Carrier deploys Scouts (complex mechanism)
- Strike/terminal guidance
- Starlink BLOS

---

## 3. Fleet Composition

```
V0 FLEET
════════

    CARRIER (×1)                      SCOUT (×2)
    ════════════                      ══════════

    ┌─────────────────┐               ┌─────────────┐
    │  Foamy airframe │               │  5" Quad    │
    │  (friend-built) │               │             │
    │                 │               │  ┌───┬───┐  │
    │  ┌───────────┐  │               │  │ ● │ ● │  │
    │  │  Jetson   │  │               │  ├───┼───┤  │
    │  │ Orin Nano │  │               │  │ ● │ ● │  │
    │  └───────────┘  │               │  └───┴───┘  │
    │                 │               │             │
    │  • Processes    │◄─────────────►│  • Sensors  │
    │    Scout data   │   LoRa Mesh   │  • PlutoSDR │
    │  • Video RX     │               │  • Camera   │
    │  • Relay to GCS │               │  • Pi 5     │
    │                 │               │             │
    └─────────────────┘               └─────────────┘
```

---

## 4. Scout V0 Specification

### Hardware Summary

| Component | Selection | Cost |
|-----------|-----------|------|
| Frame | 5" freestyle (iFlight Nazgul5 / similar) | $80 |
| Motors | 2306 2450KV ×4 | $50 |
| ESC | 4-in-1 45A | $40 |
| FC | SpeedyBee F405 V4 | $45 |
| Props | 5" ×4 sets | $15 |
| Compute | Raspberry Pi 5 (4GB) | $60 |
| SDR | PlutoSDR | $200 |
| GPS | BN-220 (u-blox M8) | $20 |
| LoRa | LILYGO T-Beam S3 | $35 |
| Video TX | Rush Tank Mini 5.8G | $40 |
| Camera | Caddx Ratel 2 | $30 |
| ELRS RX | BetaFPV Lite | $18 |
| Battery | 4S 1300mAh LiPo | $25 |
| S/C Antenna | Wideband patch 2-6 GHz | $25 |
| Wiring/misc | Connectors, mounts | $40 |
| **Subtotal** | | **$723** |
| Contingency (10%) | | $72 |
| **Total per Scout** | | **$795** |
| **2× Scouts** | | **$1,590** |

### Scout V0 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SCOUT V0 (5" Quad)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│   │ Raspberry   │     │  PlutoSDR   │     │  T-Beam S3  │       │
│   │ Pi 5 (4GB)  │◄───►│  (S/C band) │     │  LoRa Mesh  │       │
│   │             │ USB │             │     │             │       │
│   │ • Mission   │     │ • 70M-6GHz  │     │ • Commands  │       │
│   │ • SDR ctrl  │     │ • 20MHz IBW │     │ • Telemetry │       │
│   │ • Optional  │     │             │     │ • PDW relay │       │
│   │   YOLO      │     └─────────────┘     └─────────────┘       │
│   └──────┬──────┘                                │              │
│          │ UART                                  │              │
│          ▼                                       │              │
│   ┌─────────────┐     ┌─────────────┐           │              │
│   │  FC (F405)  │     │  Video TX   │───────────┼──► Carrier   │
│   │  ArduPilot  │     │  5.8 GHz    │           │              │
│   └─────────────┘     └─────────────┘           │              │
│          │                   ▲                   │              │
│          │            ┌──────┴──────┐           │              │
│          ▼            │   Camera    │           │              │
│   ┌─────────────┐     │  Caddx      │           │              │
│   │   Motors    │     └─────────────┘           │              │
│   │   × 4       │                               │              │
│   └─────────────┘                               ▼              │
│                                          To Carrier            │
│   ┌─────────────┐                        via LoRa              │
│   │  ELRS RX    │◄── RC override from GCS                      │
│   └─────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Scout V0 Specs

| Spec | Value |
|------|-------|
| AUW | ~600-700g |
| Flight time | 12-15 min |
| SDR coverage | 70 MHz - 6 GHz |
| SDR IBW | 20 MHz |
| Compute | Pi 5, no AI accelerator |
| ML capability | ~5-10 FPS (CPU only) |
| Video | 720p analog or digital |
| Range (LoRa) | 2-5 km |

---

## 5. Carrier V0 Specification

**Note:** Airframe built by friend. This spec covers electronics only.

### Hardware Summary

| Component | Selection | Cost |
|-----------|-----------|------|
| Autopilot | Pixhawk 6C Mini | $220 |
| Compute | Jetson Orin Nano (Dev Kit) | $249 |
| GPS | Holybro M9N | $45 |
| Airspeed | MS4525DO | $40 |
| LoRa Gateway | LILYGO T-Beam S3 | $35 |
| Video RX | Eachine ROTG02 or similar | $50 |
| mLRS TX | MatekSys mR900-30 | $45 |
| Telemetry radio | SiK 915MHz | $40 |
| Power module | Holybro PM02 | $30 |
| Battery | 4S 5000mAh (provided by friend?) | $50 |
| Wiring/misc | Connectors, mounts, cables | $60 |
| **Subtotal** | | **$864** |
| Contingency (10%) | | $86 |
| **Total Carrier Electronics** | | **$950** |

### Carrier V0 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CARRIER V0 (Electronics Only)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    JETSON ORIN NANO                      │   │
│   │                                                          │   │
│   │   • 40 TOPS AI performance                              │   │
│   │   • Receives video from Scouts                          │   │
│   │   • Runs detection models                               │   │
│   │   • Aggregates Scout data                               │   │
│   │   • Relays to GCS                                       │   │
│   │                                                          │   │
│   └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│   ┌───────────┐       ┌───────────┐       ┌───────────┐        │
│   │ Video RX  │       │ T-Beam S3 │       │ mLRS TX   │        │
│   │ 5.8 GHz   │       │ LoRa Mesh │       │ 868 MHz   │        │
│   │           │       │           │       │           │        │
│   │ ◄─ Scout  │       │ ◄─► Scout │       │ ──► GCS   │        │
│   │    video  │       │     data  │       │    telem  │        │
│   └───────────┘       └───────────┘       └───────────┘        │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    PIXHAWK 6C MINI                       │   │
│   │                                                          │   │
│   │   • ArduPlane autopilot                                 │   │
│   │   • GPS + airspeed + baro                               │   │
│   │   • Waypoint navigation                                 │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Power: From airframe battery (4S-6S)                          │
│   Carrier airframe: Built by friend (not in this budget)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Carrier V0 Specs

| Spec | Value |
|------|-------|
| Compute | Jetson Orin Nano (40 TOPS) |
| Autopilot | Pixhawk 6C Mini + ArduPlane |
| ML capability | 30-60 FPS YOLO |
| Video RX | 1 channel from Scouts |
| LoRa | Mesh gateway |
| Telemetry | mLRS to GCS |

---

## 6. Ground Station V0

| Component | Selection | Cost |
|-----------|-----------|------|
| Laptop | Existing | $0 |
| ELRS TX | RadioMaster TX16S (if owned) or Zorro | $0-200 |
| mLRS RX | MatekSys mR900-30 | $45 |
| LoRa Gateway | T-Beam S3 | $35 |
| Video RX | HDZero VRX or analog goggles | $100 |
| Antennas | Directional + omni | $50 |
| **Total GCS** | | **$230-430** |

---

## 7. V0 Budget Summary

| Category | Cost |
|----------|------|
| Scout ×2 | $1,590 |
| Carrier electronics | $950 |
| Ground Station | $400 |
| Development (SDcard, cables, adapters) | $200 |
| Shipping/misc | $150 |
| **Subtotal** | **$3,290** |
| **Remaining margin** | **$1,710** |
| **Total Budget** | **$5,000** |

**Margin usage:**
- Spares (props, batteries, replacement parts)
- Unexpected issues
- Additional dev hardware
- Upgrade path testing

---

## 8. Development Timeline

### March 2026 — V0 Complete

| Week | Milestone |
|------|-----------|
| Week 1-2 | Order components, begin Scout assembly |
| Week 2-3 | Scout #1 flying (basic ArduPilot) |
| Week 3-4 | Scout #2 flying, LoRa mesh tested |
| Week 4-5 | PlutoSDR integration, spectrum sensing |
| Week 5-6 | Carrier electronics integration |
| Week 6-7 | Carrier flying, Scout-Carrier comms |
| Week 7-8 | Full system test, video relay |
| End March | **V0 Demonstrator Complete** |

### April 2026 — V1 Concept Finalized

| Week | Milestone |
|------|-----------|
| Week 1 | V0 lessons learned documented |
| Week 2 | V1 requirements refined based on V0 |
| Week 3 | V1 detailed design review |
| Week 4 | **V1 Concept Frozen** |

---

## 9. Test Plan

### Test 1: Basic Flight (Week 2-3)
- [ ] Scout #1 hovers, responds to RC
- [ ] Scout #1 executes waypoint mission
- [ ] Scout #2 same tests
- [ ] Carrier flies (basic loiter)

### Test 2: Communications (Week 3-4)
- [ ] LoRa link: Scout → Carrier (1 km)
- [ ] LoRa link: Scout → Carrier (2 km)
- [ ] LoRa mesh: Scout ↔ Scout ↔ Carrier
- [ ] Video: Scout → Carrier (analog/digital)

### Test 3: SDR (Week 4-5)
- [ ] PlutoSDR receives known signal (WiFi at 2.4 GHz)
- [ ] PlutoSDR detects S-band signal (if available)
- [ ] Basic spectrum display on Pi 5

### Test 4: Integration (Week 6-8)
- [ ] Scout streams video while flying mission
- [ ] Carrier receives and displays Scout video
- [ ] Scout sends telemetry via LoRa mesh
- [ ] Carrier relays to GCS
- [ ] Multi-Scout coordination

### Test 5: Autonomous (Stretch)
- [ ] Scout continues mission on link loss
- [ ] Scout RTBs on critical battery
- [ ] Basic object detection on Pi 5

---

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PlutoSDR too heavy for 5" | Low | Medium | Verified: 60g is acceptable |
| Pi 5 power draw issues | Medium | Medium | Adequate battery, BEC sizing |
| LoRa range insufficient | Low | High | Higher power module, better antennas |
| Carrier airframe delayed | Medium | High | Can test Scouts independently |
| SDR software complexity | Medium | Medium | Start with GNU Radio examples |
| Integration issues | Medium | Medium | $1,700 margin for fixes |

---

## 11. Success Criteria

**V0 is successful if:**

1. ✅ Two Scouts fly autonomous waypoint missions
2. ✅ Scouts and Carrier communicate via LoRa mesh at 2+ km
3. ✅ Scout video received at Carrier
4. ✅ PlutoSDR detects RF signals in S/C band
5. ✅ System operates for 10+ minute missions

**V0 informs V1 by answering:**

- Is LoRa mesh sufficient, or need mLRS for everything?
- Is Pi 5 adequate, or Hailo-8 required for V1?
- Is PlutoSDR IBW (20 MHz) limiting?
- What's the realistic Scout endurance with full payload?
- How much Carrier processing is needed?

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-07 | Initial V0 specification |
