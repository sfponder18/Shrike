# Airborne EW Node Concept — Brainstorm Document

**Status:** Conceptual exploration
**Relationship to SwarmDrones:** Separate R&D track
**Date:** 2026-02-05

---

## 1. Concept Overview

An SDR-based Electronic Support (ES) node carried by a 10" class drone, relaying spectrum data through an airborne relay (Bird) to a capable ground station for processing and analysis.

**Mission:** Airborne spectrum surveillance and emitter detection/geolocation — NOT real-time threat warning for the carrier platform.

### What This Is
- Persistent RF surveillance sensor
- Emitter detection and basic characterization
- Multi-platform geolocation enabler (TDOA/FDOA)
- Signal recording and relay for ground-based analysis

### What This Is NOT
- Real-time radar warning receiver for evasion
- Instantaneous wideband threat detection
- Self-protection system

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GROUND CONTROL STATION                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ High-End SDR    │  │ Processing      │  │ Operator Console    │  │
│  │ (Ettus N310 or  │  │ Server          │  │ - Spectrum display  │  │
│  │  similar)       │  │ - Threat library│  │ - Emitter tracks    │  │
│  │ - Independent   │  │ - Geolocation   │  │ - Geolocation map   │  │
│  │   ground sensor │  │ - Signal class. │  │ - Mission control   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ Backhaul (4G/LTE or dedicated link)
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                         BIRD (Airborne Relay)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Compute (Pi 5)  │  │ Mesh Radio      │  │ Optional: Own SDR   │  │
│  │ - Data aggreg.  │  │ - Receives from │  │ (Adds another       │  │
│  │ - Compression   │  │   EW nodes      │  │  geolocation point) │  │
│  │ - Relay to GCS  │  │ - Relays to GCS │  │                     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ LoRa mesh or WiFi link
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                    EW NODE (10" Drone Platform)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ ModalAI Voxl 2  │  │ Ettus B205mini  │  │ Wideband Antenna    │  │
│  │ - Snapdragon    │  │ - 70 MHz-6 GHz  │  │ - Discone or        │  │
│  │ - Real-time DSP │  │ - 56 MHz IBW    │  │   log-periodic      │  │
│  │ - Edge detect.  │  │ - USB 3.0       │  │ - Compromise for    │  │
│  │ - Compression   │  │                 │  │   weight/coverage   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware Selection Rationale

### Airborne SDR: Ettus B205mini-i

| Spec | Value | Notes |
|------|-------|-------|
| Frequency | 70 MHz - 6 GHz | Covers L, S, C bands |
| IBW | 56 MHz | Adequate for most radar pulses |
| ADC | 12-bit | Better dynamic range than RTL-SDR |
| Interface | USB 3.0 | Required for full bandwidth |
| Size | 80 x 50 x 12 mm | Fits 10" platform |
| Weight | ~30g (board only) | Plus shielding, antenna |
| Power | ~3W typical | Manageable |
| Cost | ~$500 | Reasonable for prototype |

**Alternative:** Ettus B200mini (same specs, slightly different form factor)

**Why not HackRF?**
- 8-bit ADC limits dynamic range
- Weaker filtering
- B205mini has better performance for similar size/cost

### Airborne Compute: ModalAI Voxl 2

| Spec | Value | Notes |
|------|-------|-------|
| SoC | Qualcomm QRB5165 | Same as high-end phones |
| CPU | Kryo 585, 8 cores | Serious compute |
| GPU | Adreno 650 | DSP acceleration |
| DSP | Hexagon 698 | Signal processing offload |
| RAM | 8 GB LPDDR5 | Handles IQ buffering |
| Interface | USB 3.0 | Full SDR bandwidth |
| Weight | ~40g | Flight-ready |
| Power | ~10W peak | Significant battery impact |
| PX4 Integration | Native | Autopilot included |

**Why Voxl?**
- Purpose-built for drones
- Enough compute for real-time FFT and pulse detection
- Can run GNU Radio, SigMF recording
- Native flight controller integration

### GCS SDR Options

**Option A: Ettus N310**
- 4 channels, 10 MHz - 6 GHz
- 100 MHz IBW per channel
- 10 GbE interface
- ~$8,000
- Serious geolocation capability with calibrated channels

**Option B: Ettus X310 + UBX-160 daughterboards**
- 2 channels, 10 MHz - 6 GHz
- 160 MHz IBW per channel
- ~$6,000 total
- More bandwidth, fewer channels

**Option C: Commercial spectrum analyzer with IQ capture**
- R&S, Keysight, etc.
- Better filtering, calibration
- $15,000+
- More turnkey

**Recommendation for prototyping:** Start with X310 + UBX-160, provides serious capability at reasonable cost.

### Drone Platform: 10" Class

Requirements:
- Payload: ~200-300g (Voxl + SDR + antenna + shielding)
- Flight time: 20+ minutes with payload
- Stability: Needs to hold position for direction finding
- GPS: RTK preferred for geolocation accuracy

Candidates:
- Custom build on 10" frame (iFlight XL10, etc.)
- ModalAI Sentinel (if available)
- Modified DJI Matrice (expensive, closed ecosystem)

---

## 4. Concept of Operations

### Phase 1: Spectrum Survey
1. EW node loiters at designated altitude/position
2. SDR sweeps assigned frequency bands (e.g., 1-6 GHz in segments)
3. On-board processing extracts:
   - Frequency peaks above noise floor
   - Pulsed vs. continuous signals
   - Basic pulse parameters if detected (PRF estimate, pulse width)
4. Compressed reports sent to Bird
5. Bird relays to GCS

### Phase 2: Emitter Characterization
1. GCS tasks EW node to dwell on specific frequency
2. Node records IQ data for longer duration
3. Streams or stores-and-forwards to GCS
4. GCS performs detailed analysis:
   - Pulse descriptor word extraction
   - Modulation analysis
   - Threat library matching

### Phase 3: Geolocation (Multi-Node)
1. Multiple EW nodes (or EW node + Bird + GCS) receive same emitter
2. Time-stamped detections correlated
3. TDOA/FDOA processing at GCS
4. Emitter position estimated
5. Accuracy improves with geometry and number of nodes

---

## 5. Signal Processing Pipeline

### On-Board (Voxl)

```
SDR IQ Stream (56 MSPS complex)
        │
        ▼
┌───────────────────┐
│ Polyphase Filter  │  Channelize into sub-bands
│ Bank              │  (e.g., 1 MHz channels)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Energy Detection  │  Threshold per channel
│ (FFT + threshold) │  Adaptive noise floor
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Pulse Detection   │  Rising/falling edge
│ (time domain)     │  Pulse width extraction
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ PDW Generation    │  - Time of arrival (TOA)
│                   │  - Frequency
│                   │  - Amplitude
│                   │  - Pulse width
│                   │  - Intra-pulse mod (if capable)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Compression &     │  Send PDWs, not raw IQ
│ Transmission      │  (unless tasked for IQ)
└───────────────────┘
```

### At GCS

```
PDW Stream from Node(s)
        │
        ▼
┌───────────────────┐
│ De-interleaving   │  Separate multiple emitters
│                   │  Track PRF patterns
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Threat Library    │  Match against known radars
│ Correlation       │  PRF, frequency, scan rate
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Geolocation       │  TDOA from multiple nodes
│ Processing        │  Position estimation
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Track Management  │  Fuse detections over time
│ & Display         │  Display to operator
└───────────────────┘
```

---

## 6. Key Technical Challenges

### Challenge 1: Scanning vs. Probability of Intercept

**Problem:** With 56 MHz IBW covering 1-6 GHz = ~90 scan positions. At 10ms dwell per position = 900ms full scan. Fast-scanning radars may be missed.

**Mitigations:**
- Prioritize known threat bands
- Use multiple nodes with offset scan timing
- Accept that this is surveillance, not real-time warning
- Statistical detection over multiple scans

### Challenge 2: Link Bandwidth

**Problem:** Full IQ at 56 MSPS × 16-bit I × 16-bit Q = 224 MB/s. Cannot stream raw.

**Mitigations:**
- On-board processing, send PDWs only (~1 KB/s typical)
- Selective IQ recording on command
- Compression (though IQ doesn't compress well)
- Store-and-forward for detailed analysis

### Challenge 3: Antenna Limitations

**Problem:** Wideband antenna with good gain across 1-6 GHz is physically large. Small antenna = poor sensitivity.

**Options:**
- Discone: Omnidirectional, reasonable gain, ~15cm size for low-GHz
- Log-periodic: Directional, better gain, larger
- Cavity-backed spiral: Compact, wideband, complex to build
- Blade antenna: Common on aircraft, okay gain

**Reality:** Accept reduced sensitivity compared to ground-based systems. Altitude helps (line of sight to emitters).

### Challenge 4: Platform EMI

**Problem:** Drone motors, ESCs, and power systems generate significant RF noise.

**Mitigations:**
- Shielded SDR enclosure
- Filtered power supply
- Antenna placement (above platform, on mast)
- Characterize self-interference, notch filter known frequencies

### Challenge 5: Timing Synchronization (for Geolocation)

**Problem:** TDOA requires nanosecond-level timing accuracy. GPS PPS is ~50ns typical.

**Mitigations:**
- GPS-disciplined oscillator (GPSDO) on each node — adds weight/cost
- Use FDOA (frequency difference) which is less timing-sensitive
- Accept reduced geolocation accuracy
- Calibration flights against known emitters

---

## 7. Development Roadmap

### Phase 1: Ground-Based Proof of Concept (Weeks 1-4)

**Goal:** Validate signal processing pipeline without flight complexity

- [ ] Set up Ettus B205mini + laptop with GNU Radio
- [ ] Develop pulse detection flowgraph
- [ ] Test against known signals (ADS-B at 1090 MHz, WiFi, etc.)
- [ ] Develop PDW extraction code
- [ ] Test threat library matching concept

**Deliverable:** Working pulse detector on ground, validated against known signals

### Phase 2: Voxl Integration (Weeks 5-8)

**Goal:** Port processing to airborne compute platform

- [ ] Set up Voxl 2 development environment
- [ ] Port GNU Radio flowgraph (or rewrite in C++ for performance)
- [ ] Integrate B205mini with Voxl
- [ ] Benchmark processing performance
- [ ] Develop compression/transmission protocol

**Deliverable:** Voxl running SDR processing, validated on bench

### Phase 3: Airborne Integration (Weeks 9-12)

**Goal:** Fly the sensor, validate in realistic conditions

- [ ] Integrate into 10" platform
- [ ] Address EMI issues
- [ ] Flight test with known emitters
- [ ] Validate link performance (PDW relay through Bird)
- [ ] Measure detection performance vs. ground truth

**Deliverable:** Flying EW node detecting real emitters

### Phase 4: Multi-Node Geolocation (Weeks 13-16)

**Goal:** Demonstrate cooperative geolocation

- [ ] Deploy multiple nodes (or node + ground reference)
- [ ] Implement TDOA processing at GCS
- [ ] Calibrate timing
- [ ] Demonstrate emitter geolocation

**Deliverable:** Emitter position fix from airborne network

---

## 8. Why SDR-Based and Not Traditional RWR?

### Arguments For SDR Approach

1. **Flexibility:** Reprogram for different threats, frequencies, waveforms
2. **Cost:** $500 SDR vs. $50,000+ traditional RWR
3. **COTS:** Available hardware, open-source software
4. **Recording:** Can capture IQ for post-mission analysis
5. **Upgradeable:** Software improvements don't require new hardware
6. **Multi-function:** Same hardware for SIGINT, ELINT, COMINT

### Arguments Against (Honest Assessment)

1. **Latency:** Milliseconds vs. microseconds — not suitable for self-protection
2. **Coverage:** Scanning vs. instantaneous — will miss some pulses
3. **Sensitivity:** General-purpose SDR vs. optimized receiver — weaker signals missed
4. **Size/Weight/Power:** More than purpose-built ASIC solutions
5. **Reliability:** General-purpose compute vs. hardened military hardware

### Conclusion

SDR-based EW is viable for **surveillance and intelligence** missions where:
- Real-time self-protection is not required
- Some probability of missed intercepts is acceptable
- Flexibility and cost matter more than absolute performance
- Recording and analysis are as important as detection

It is NOT suitable for:
- Threat warning for pilot/platform survival
- Dense signal environments requiring instant classification
- Missions where every pulse must be detected

---

## 9. Software Stack Considerations

### GNU Radio
- Proven, extensive block library
- Python + C++ hybrid
- Runs on Voxl (Linux/ARM64)
- Large community

### SigMF (Signal Metadata Format)
- Standard format for IQ recordings
- Include metadata (frequency, sample rate, GPS position, time)
- Enables post-mission analysis

### Custom C++ for Performance-Critical Paths
- Pulse detection needs low latency
- FFT acceleration via NEON/Hexagon DSP on Voxl
- Consider FFTW or vendor-optimized libraries

### Threat Library Format
- Define schema for radar parameters
- PRF ranges, frequency, pulse width, scan patterns
- Fuzzy matching for real-world variation

---

## 10. Open Questions

1. **What specific emitters are priority targets?**
   - Need to define frequency bands, PRF ranges, pulse widths
   - Drives scan strategy and detection thresholds

2. **What geolocation accuracy is required?**
   - CEP 100m? 1km? 10km?
   - Drives timing requirements and number of nodes

3. **What is acceptable probability of intercept?**
   - 90%? 50%? Best-effort?
   - Drives dwell time and scan strategy

4. **Is IQ recording required, or just PDW reports?**
   - IQ enables detailed post-analysis but requires storage/bandwidth
   - PDW-only is more bandwidth-efficient

5. **What is the mission duration requirement?**
   - 20 min? 1 hour? Persistent?
   - Drives platform selection and power budget

6. **What is the operating environment?**
   - Permissive (testing range) vs. contested
   - Affects link architecture and EMCON

---

## 11. Related Reading / References

- "Introduction to Electronic Warfare" — D. Curtis Schleher
- Ettus Research B200/B205 specifications
- GNU Radio documentation
- "Principles of Modern Radar" — Richards, Scheer, Holm
- TDOA/FDOA geolocation theory papers
- ModalAI Voxl 2 documentation

---

## 12. Target Emitter Set

Based on operational requirements, focusing on VHF through C-band (max 6 GHz):

| Radar | NATO Name | Band | Frequency | Role | Priority |
|-------|-----------|------|-----------|------|----------|
| Protivnik-GE | — | VHF | 150-170 MHz | Early warning | High |
| P-18 / P-19 | Spoon Rest | VHF | 150-170 MHz | Early warning | High |
| 91N6E | Big Bird | S-band | 2.5-3.5 GHz | S-400 battle management | **Critical** |
| 96L6E | Cheese Board | C-band | 5-6 GHz | S-400 acquisition | High |
| Various ATC | — | S-band | 2.7-2.9 GHz | Air traffic (not threat) | Low |

**Key insight:** The 91N6E (S-band) is the primary S-400 indicator — solidly in SDR range and high value.

### Detection Feasibility

| Radar | Frequency | Est. EIRP | Path Loss @50km | Rx Antenna | Received | Margin |
|-------|-----------|-----------|-----------------|------------|----------|--------|
| Protivnik-GE | 160 MHz | 66 dBm | 111 dB | -10 dBi* | -55 dBm | **+55 dB** |
| 91N6E | 3 GHz | 72 dBm | 136 dB | +3 dBi | -61 dBm | **+49 dB** |
| 96L6E | 5.5 GHz | 72 dBm | 141 dB | +5 dBi | -64 dBm | **+36 dB** |

*VHF antenna gain varies significantly by platform — see configurations below.

---

## 13. Configuration Comparison Summary

| Metric | Config 1 (Multirotor) | Config 2 (Fixed-Wing) | Config 3 (Hybrid) |
|--------|----------------------|----------------------|-------------------|
| EW Nodes | 4× 10" quad | 4× 2m fixed-wing | 2× fixed-wing + 2× quad |
| Mother Drone | 1× 15" quad | 1× 2.5m fixed-wing | 1× fixed-wing |
| SDR per node | Sidekiq X4 (4-ch) | Sidekiq X4 (4-ch) | Sidekiq X4 (4-ch) |
| Endurance (nodes) | 25 min | 1.5-2 hours | Mixed |
| VHF antenna gain | -10 dBi | 0 dBi | Mixed |
| POI (no scanning) | ~95% | ~95% | ~95% |
| TDOA + DF | Yes | Yes | Yes |
| FDOA | Limited | **Yes (motion)** | Yes (fixed-wing) |
| CEP estimate | 50-80m | **35-60m** | 40-70m |
| Total cost | $78,385 | **$75,260** | $77,570 |
| Best for | Precision loiter, confined areas | Wide-area persistent | Versatility |

---

## 14. CONFIG 1: Multirotor (10" Quad)

### Overview

4× 10" heavy-lift quadrotors + 1× 15" Mother Drone, all multirotor.

**Strengths:**
- Precision hover for DF
- Quick deployment (no launch equipment)
- Confined area operations
- Simpler operations

**Weaknesses:**
- Limited endurance (25 min)
- Poor VHF antenna efficiency
- Limited baseline (battery constrained)
- No FDOA (stationary)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIG 1: MULTIROTOR CONSTELLATION                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         MOTHER DRONE (15" Quad)                          │
│                    ┌─────────────────────────────┐                       │
│                    │  • Jetson Orin NX           │                       │
│                    │  • Sidekiq X4               │                       │
│                    │  • CSAC timing              │                       │
│                    │  • Processing hub           │                       │
│                    │  • 30 min endurance         │                       │
│                    └──────────────┬──────────────┘                       │
│                                   │                                      │
│              ┌────────────────────┼────────────────────┐                 │
│              │                    │                    │                 │
│              ▼                    ▼                    ▼                 │
│   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐        │
│   │   EW Node 1      │ │   EW Node 2      │ │   EW Node 3      │        │
│   │   (10" Quad)     │ │   (10" Quad)     │ │   (10" Quad)     │        │
│   │   Sidekiq X4     │ │   Sidekiq X4     │ │   Sidekiq X4     │        │
│   │   4-band simul.  │ │   4-band simul.  │ │   4-band simul.  │        │
│   │   Hover DF       │ │   Hover DF       │ │   Hover DF       │        │
│   └──────────────────┘ └──────────────────┘ └──────────────────┘        │
│              │                                         │                 │
│              └─────────────────────────────────────────┘                 │
│                                   │                                      │
│                                   ▼                                      │
│                        ┌──────────────────┐                              │
│                        │   EW Node 4      │                              │
│                        │   (10" Quad)     │                              │
│                        └──────────────────┘                              │
│                                                                          │
│   Geometry: 10-15 km baseline, nodes can hover precisely                 │
│   Endurance: 25 min per sortie                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### EW Node BOM (Config 1)

| Component | Selection | Cost | Notes |
|-----------|-----------|------|-------|
| Airframe | 10" heavy-lift (iFlight XL10 class) | $600 | T-motor or similar |
| Flight Stack | Included with Voxl or Pixhawk 6C | $0-200 | |
| Compute | ModalAI Voxl 2 | $1,200 | |
| SDR | **Epiq Sidekiq X4** | $9,000 | 4-ch, phase coherent |
| Timing GPS | u-blox ZED-F9T | $180 | |
| Position GPS | u-blox ZED-F9P (PPP) | $200 | |
| GPSDO | Leo Bodnar mini | $250 | |
| VHF Antenna | Helical stub, 25-30 cm | $40 | -8 to -10 dBi |
| L-band Antenna | Patch or helix | $40 | +2 dBi |
| S-band Antenna | Patch or horn | $50 | +4 dBi |
| C-band Antenna | Wideband patch | $50 | +5 dBi |
| Antenna mount | Custom 3D-printed radome | $30 | |
| Mesh Radio | ESP32 + LoRa | $30 | |
| Power | 6S 3000mAh × 2 | $120 | Hot-swap capable |
| Integration | Cables, shielding, filters | $250 | |
| Contingency | 15% | $1,800 | |
| **Total** | | **$13,840** | |

### Mother Drone BOM (Config 1)

| Component | Selection | Cost | Notes |
|-----------|-----------|------|-------|
| Airframe | 13-15" heavy-lift (Freefly Alta class) | $5,000 | |
| Flight Controller | Pixhawk 6X + redundancy | $600 | |
| Compute | Jetson Orin NX 16GB | $2,000 | |
| SDR | Epiq Sidekiq X4 | $9,000 | Consistency with nodes |
| Timing | Jackson Labs CSAC | $1,500 | Master reference |
| Position GPS | ZED-F9P RTK | $200 | |
| VHF Antenna | Half-wave dipole, 1m | $75 | Foldable boom |
| L/S/C Antennas | Higher-gain patches/horns | $250 | |
| Comms | Long-range LoRa + 4G modem | $400 | |
| Power | 12S 22000mAh | $500 | |
| Integration | Cables, shielding, ruggedization | $500 | |
| Contingency | 15% | $3,000 | |
| **Total** | | **$23,025** | |

### Config 1 Cost Summary

| Item | Unit Cost | Qty | Subtotal |
|------|-----------|-----|----------|
| EW Node (10" quad) | $13,840 | 4 | $55,360 |
| Mother Drone (15" quad) | $23,025 | 1 | $23,025 |
| **Total System** | | | **$78,385** |

### Config 1 Error Budget

| Source | Contribution |
|--------|--------------|
| Timing (GPSDO nodes + CSAC mother) | ~5m |
| Platform position (PPP) | ~1m |
| Geometry (GDOP with DF) | ×1.1 |
| TOA algorithm (cross-correlation) | ~5m |
| DF bearing (~10-15°) | Improves geometry |
| Multipath | ~30m |
| **Combined CEP** | **~50-80m** |

---

## 15. CONFIG 2: Fixed-Wing

### Overview

4× 2m wingspan fixed-wing + 1× 2.5m Mother fixed-wing.

**Strengths:**
- Long endurance (1.5-3 hours)
- Large baselines (50-100 km)
- Better VHF antennas (wing-integrated)
- FDOA from motion
- Natural synthetic aperture
- Lower cost per flight-hour

**Weaknesses:**
- Cannot hover (orbit patterns instead)
- Needs launch/recovery infrastructure
- Less precise positioning
- Larger turn radius

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CONFIG 2: FIXED-WING CONSTELLATION                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                       MOTHER (Believer-class FW)                         │
│                    ┌─────────────────────────────┐                       │
│                    │  • Jetson Orin NX           │                       │
│                    │  • Sidekiq X4               │                       │
│                    │  • CSAC timing              │                       │
│                    │  • Processing hub           │                       │
│                    │  • 3+ hour endurance        │                       │
│                    │  • 50-100 km standoff       │                       │
│                    └──────────────┬──────────────┘                       │
│                                   │                                      │
│         ┌─────────────────────────┼─────────────────────────┐            │
│         │                         │                         │            │
│         ▼                         ▼                         ▼            │
│   ┌───────────┐            ┌───────────┐            ┌───────────┐       │
│   │  Node 1   │            │  Node 2   │            │  Node 3   │       │
│   │ ═══════   │            │ ═══════   │            │ ═══════   │       │
│   │  ╲     ╱  │ 30 m/s     │  ╲     ╱  │ 30 m/s     │  ╲     ╱  │       │
│   │   ╲   ╱   │ ────────►  │   ╲   ╱   │ ────────►  │   ╲   ╱   │       │
│   │    ╲ ╱    │            │    ╲ ╱    │            │    ╲ ╱    │       │
│   │ Skywalker │            │ Skywalker │            │ Skywalker │       │
│   │   X8      │            │   X8      │            │   X8      │       │
│   └───────────┘            └───────────┘            └───────────┘       │
│         │                                                   │            │
│         └───────────────────────────────────────────────────┘            │
│                                   │                                      │
│                                   ▼                                      │
│                            ┌───────────┐                                 │
│                            │  Node 4   │                                 │
│                            │ ═══════   │                                 │
│                            │  ╲     ╱  │                                 │
│                            │   ╲   ╱   │                                 │
│                            │    ╲ ╱    │                                 │
│                            └───────────┘                                 │
│                                                                          │
│   Geometry: 50-100 km baseline, racetrack orbits                         │
│   Endurance: 1.5-2 hours per sortie                                      │
│   FDOA: Enabled by platform motion                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Fixed-Wing Antenna Integration

```
                    ┌─────────────────────────────────────┐
                    │      FLYING WING (top view)         │
                    │                                      │
    VHF dipole      │    ┌─────────────────────────┐      │   VHF dipole
    element         │    │      FUSELAGE BAY       │      │   element
    (wing-tip)      │    │  ┌─────────────────┐    │      │   (wing-tip)
        │           │    │  │ Voxl 2 + X4     │    │      │       │
        │           │    │  │ GPS/GPSDO       │    │      │       │
        ▼           │    │  │ Battery         │    │      │       ▼
     ───────        │    │  └─────────────────┘    │      │    ───────
    / 25cm  \       │    │                         │      │   / 25cm  \
   /  each   \      │    └─────────────────────────┘      │  /  each   \
  /           \     │              │                      │ /           \
 / S-band      \    │         L-band                      │/ C-band      \
/  patch        \───┴──────── belly ──────────────────────/  patch        \
                              patch
```

**Antenna gains (fixed-wing vs multirotor):**

| Band | Multirotor (stub) | Fixed-Wing (integrated) | Improvement |
|------|-------------------|-------------------------|-------------|
| VHF | -10 dBi | **0 dBi** | +10 dB (3× range) |
| L-band | +2 dBi | +3 dBi | +1 dB |
| S-band | +4 dBi | +5 dBi | +1 dB |
| C-band | +5 dBi | +6 dBi | +1 dB |

### EW Node BOM (Config 2)

| Component | Selection | Cost | Notes |
|-----------|-----------|------|-------|
| Airframe | Skywalker X8 or Believer | $400 | With motor, ESC, servos |
| Autopilot | Pixhawk 6C Mini or Cube Orange | $350 | ArduPlane |
| Compute | ModalAI Voxl 2 | $1,200 | |
| SDR | Epiq Sidekiq X4 | $9,000 | 4 coherent channels |
| Timing GPS | u-blox ZED-F9T | $180 | |
| Position GPS | u-blox ZED-F9P (PPP) | $200 | |
| GPSDO | Leo Bodnar mini | $250 | |
| VHF Antenna | Wing-tip dipole (custom) | $80 | ~0 dBi |
| L-band Antenna | Belly patch | $50 | |
| S-band Antenna | Underwing conformal | $60 | |
| C-band Antenna | Underwing conformal | $60 | |
| Mesh Radio | ESP32 + LoRa + amp | $60 | Longer range |
| Power | 6S 10000mAh Li-ion | $150 | |
| Launch System | Bungee allocation | $100 | |
| Integration | Cables, shielding, conformal | $300 | |
| Contingency | 15% | $1,800 | |
| **Total** | | **$14,240** | |

### Mother Drone BOM (Config 2)

| Component | Selection | Cost | Notes |
|-----------|-----------|------|-------|
| Airframe | Believer or custom 2.5m | $600 | Larger payload bay |
| Autopilot | Pixhawk 6X + redundancy | $600 | |
| Compute | Jetson Orin NX 16GB | $2,000 | |
| SDR | Epiq Sidekiq X4 | $9,000 | |
| Timing | Jackson Labs CSAC | $1,500 | |
| Position GPS | ZED-F9P RTK | $200 | |
| VHF Antenna | Fuselage dipole | $100 | Near 0 dBi |
| L/S/C Antennas | Conformal array | $300 | |
| Comms | Long-range LoRa + 4G | $400 | |
| Power | 6S 20000mAh Li-ion | $300 | 3+ hour |
| Launch System | Catapult (shared) | $500 | |
| Integration | Cables, shielding | $400 | |
| Contingency | 15% | $2,400 | |
| **Total** | | **$18,300** | |

### Config 2 Cost Summary

| Item | Unit Cost | Qty | Subtotal |
|------|-----------|-----|----------|
| EW Node (fixed-wing) | $14,240 | 4 | $56,960 |
| Mother Drone (fixed-wing) | $18,300 | 1 | $18,300 |
| **Total System** | | | **$75,260** |

### Config 2 Error Budget (TDOA + FDOA + DF)

| Source | Contribution |
|--------|--------------|
| Timing (GPSDO + CSAC) | ~5m |
| Platform position (PPP + INS) | ~1m |
| Geometry (GDOP with FDOA) | ×1.05 |
| TOA algorithm | ~5m |
| FDOA (velocity-based) | ~3m additional constraint |
| DF bearing | Improves geometry |
| Multipath | ~20m (higher altitude) |
| **Combined CEP** | **~35-60m** |

### TDOA + FDOA Fusion

Fixed-wing motion enables FDOA:

```
          Emitter
             ●
            /|\
           / | \
          /  |  \
         /   |   \
   TDOA /    |    \ TDOA
  hyper-     |     hyper-
  bola       |      bola
       \     |     /
        \    |    /
    ═════\===●===/═════►  Aircraft 1 (V1)
          \  │  /
           \ │ /
            \│/  FDOA hyperbola (from Doppler)
             │
    ═════════●═════════►  Aircraft 2 (V2)

Three constraints = tighter intersection = better CEP
```

---

## 16. CONFIG 3: Hybrid (Fixed-Wing + Multirotor)

### Overview

Best of both worlds: Fixed-wing for persistent wide-area coverage, multirotors for precision tasks.

**Composition:**
- 2× Fixed-wing EW nodes (wide-area scan, long endurance)
- 2× Multirotor EW nodes (precision loiter, DF, investigation)
- 1× Fixed-wing Mother (endurance, processing)

**Operational concept:**
1. Fixed-wing nodes provide persistent wide-area coverage
2. Upon emitter detection, multirotor dispatched for:
   - Precision hover DF
   - Close-in signal collection
   - Extended dwell on specific target
   - Confined area operations

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIG 3: HYBRID CONSTELLATION                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                      MOTHER (Fixed-Wing)                                 │
│                    ┌─────────────────────────────┐                       │
│                    │  • Processing hub           │                       │
│                    │  • 3+ hour endurance        │                       │
│                    │  • Coordinates all nodes    │                       │
│                    └──────────────┬──────────────┘                       │
│                                   │                                      │
│         ┌─────────────────────────┼─────────────────────────┐            │
│         │                         │                         │            │
│         ▼                         │                         ▼            │
│   ┌───────────┐                   │                   ┌───────────┐     │
│   │ FW Node 1 │                   │                   │ FW Node 2 │     │
│   │ ═══════   │    WIDE-AREA      │    WIDE-AREA      │ ═══════   │     │
│   │  ╲     ╱  │    PERSISTENT     │    PERSISTENT     │  ╲     ╱  │     │
│   │   ╲   ╱   │    SCAN           │    SCAN           │   ╲   ╱   │     │
│   │    ╲ ╱    │    ──────────►    │    ◄──────────    │    ╲ ╱    │     │
│   └───────────┘                   │                   └───────────┘     │
│         │                         │                         │            │
│         │    ┌────────────────────┴────────────────────┐    │            │
│         │    │                                         │    │            │
│         │    │         PRECISION TASKING               │    │            │
│         │    │                                         │    │            │
│         │    ▼                                         ▼    │            │
│         │  ┌──────────────────┐   ┌──────────────────┐ │    │            │
│         │  │   Quad Node 1    │   │   Quad Node 2    │ │    │            │
│         │  │   ┌──┬──┐        │   │   ┌──┬──┐        │ │    │            │
│         │  │   │  │  │ HOVER  │   │   │  │  │ HOVER  │ │    │            │
│         │  │   └──┴──┘ DF     │   │   └──┴──┘ DF     │ │    │            │
│         │  │   Precision      │   │   Close-in       │ │    │            │
│         │  │   loiter         │   │   investigation  │ │    │            │
│         │  └──────────────────┘   └──────────────────┘ │    │            │
│         │                                               │    │            │
│         └───────────────────────────────────────────────┘    │            │
│                                                                          │
│   Workflow:                                                              │
│   1. FW nodes scan wide area, detect emitter                            │
│   2. Mother computes coarse location (TDOA from FW nodes)               │
│   3. Quad node dispatched to precise location                           │
│   4. Quad hovers, performs precision DF                                 │
│   5. Combined TDOA (FW) + DF (Quad) = refined solution                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Config 3 Concept of Operations

```
PHASE 1: WIDE-AREA SEARCH (Fixed-Wing)
├── FW Node 1 & 2 orbit at 20-30 km from AO
├── Scan VHF/L/S/C bands continuously
├── 2-hour endurance, 80+ km baseline
├── Detect emitter, report to Mother
└── Mother computes initial TDOA fix (~500m-1km CEP)

PHASE 2: PRECISION TASKING (Multirotor)
├── Mother dispatches Quad Node to estimated location
├── Quad transits at max speed (takes 5-10 min for 10-15 km)
├── Quad arrives in vicinity, begins hover search
└── Quad performs precision DF while hovering

PHASE 3: REFINED GEOLOCATION (Combined)
├── FW nodes continue providing TDOA
├── Quad provides precise bearing (hover DF)
├── Mother fuses TDOA + bearing
├── CEP improves from 500m to ~30-50m
└── Quad can orbit for extended collection

PHASE 4: HANDOFF / PERSISTENCE
├── If Quad low on battery, RTB
├── FW nodes maintain track
├── Fresh Quad can be dispatched if needed
└── FW nodes never stop scanning
```

### Config 3 BOM

**2× Fixed-Wing EW Nodes:** (same as Config 2)
| Component | Cost |
|-----------|------|
| Per Config 2 Node BOM | $14,240 |
| **Subtotal (×2)** | **$28,480** |

**2× Multirotor EW Nodes:** (same as Config 1)
| Component | Cost |
|-----------|------|
| Per Config 1 Node BOM | $13,840 |
| **Subtotal (×2)** | **$27,680** |

**1× Fixed-Wing Mother:** (same as Config 2)
| Component | Cost |
|-----------|------|
| Per Config 2 Mother BOM | $18,300 |
| **Subtotal (×1)** | **$18,300** |

**Launch/Recovery Equipment:**
| Item | Cost |
|------|------|
| Bungee catapult (for FW) | $300 |
| Landing net (optional) | $500 |
| Quad landing pads | $100 |
| **Subtotal** | **$900** |

**Spares Allocation:**
| Item | Cost |
|------|------|
| 1× spare FW airframe | $400 |
| 1× spare Quad airframe | $600 |
| Spare props, batteries, misc | $1,200 |
| **Subtotal** | **$2,200** |

### Config 3 Cost Summary

| Item | Cost |
|------|------|
| 2× Fixed-Wing EW Nodes | $28,480 |
| 2× Multirotor EW Nodes | $27,680 |
| 1× Fixed-Wing Mother | $18,300 |
| Launch/Recovery Equipment | $900 |
| Spares | $2,200 |
| **Total System** | **$77,560** |

### Config 3 Error Budget

**Initial detection (FW only):**
| Source | Contribution |
|--------|--------------|
| 2× FW nodes + Mother TDOA | ~300-500m CEP |

**After Quad tasking (Combined):**
| Source | Contribution |
|--------|--------------|
| FW TDOA (2 platforms) | ~200m |
| Quad hover DF (±5° possible with stable hover) | ~100m at 10km |
| Mother as 3rd TDOA node | Additional constraint |
| **Combined CEP** | **~40-70m** |

### Config 3 Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Persistent coverage** | FW nodes never stop scanning, even during Quad tasking |
| **Precision when needed** | Quads provide hover DF capability |
| **Flexible response** | Can prioritize targets with limited Quad endurance |
| **Graceful degradation** | If Quads lost, FW continue mission |
| **Efficient battery use** | Quads only deployed when needed |
| **Confined area capable** | Quads can operate where FW cannot |

### Config 3 Operational Flexibility

| Scenario | Response |
|----------|----------|
| Wide area search | 2× FW scan, Quads standby |
| Emitter detected | 1× Quad dispatched, 2× FW maintain TDOA |
| Multiple emitters | Both Quads dispatched to different targets |
| Confined area (urban) | Quads operate, FW orbit outside |
| Extended surveillance | FW persistent, Quads rotate on station |
| High-value target | Both Quads converge for multi-angle DF |

---

## 17. Configuration Selection Guide

| If your priority is... | Choose | Reason |
|------------------------|--------|--------|
| **Maximum endurance** | Config 2 | 2+ hours vs 25 min |
| **Best CEP** | Config 2 | FDOA from motion, better antennas |
| **Operational flexibility** | Config 3 | Best of both worlds |
| **Simplest operations** | Config 1 | No launch equipment, hover anywhere |
| **Lowest cost** | Config 2 | $75k vs $77-78k |
| **Confined area ops** | Config 1 or 3 | Multirotors can hover in tight spaces |
| **VHF sensitivity** | Config 2 | Wing-integrated antennas |
| **Precision DF** | Config 1 or 3 | Stable hover platform |

### Recommendation

**For general-purpose EW surveillance: Config 3 (Hybrid)**

Rationale:
- Persistent wide-area coverage from fixed-wing
- Precision capability from multirotors when needed
- Operational flexibility to adapt to situation
- Cost comparable to pure fixed-wing
- Can operate in more environments

**For budget-constrained or simple ops: Config 2 (Fixed-Wing)**

Rationale:
- Lowest total cost
- Best endurance
- Best CEP (with FDOA)
- Simpler logistics (all same platform type)

---

## 18. Ground Support Requirements by Config

| Requirement | Config 1 | Config 2 | Config 3 |
|-------------|----------|----------|----------|
| Launch area | Small (5m×5m) | Medium (20m×50m) | Both |
| Launch equipment | None | Bungee catapult | Bungee catapult |
| Recovery area | Small | Large (open field) | Both |
| Transport | Backpack-able | Vehicle required | Vehicle required |
| Setup time | 5 min | 15 min | 15 min |
| Crew size (min) | 2 | 2 | 3 |
| Crew size (optimal) | 3 | 4 | 5 |

---

## 19. Development Roadmap (Updated)

### Phase 1: Ground-Based SDR Validation (Weeks 1-4)
- [ ] Procure Sidekiq X4 evaluation unit
- [ ] Develop 4-channel pulse detection on laptop
- [ ] Test against known signals (ADS-B, WiFi, etc.)
- [ ] Develop PDW + AoA extraction
- [ ] Validate TDOA algorithm with simulated data

### Phase 2: Single Platform Integration (Weeks 5-10)
- [ ] Integrate Sidekiq X4 + Voxl 2 on bench
- [ ] Port processing pipeline
- [ ] Build first fixed-wing node (simpler antenna integration)
- [ ] Flight test single node
- [ ] Validate detection performance

### Phase 3: Multi-Platform TDOA (Weeks 11-16)
- [ ] Build second fixed-wing node
- [ ] Implement timing synchronization
- [ ] Flight test 2-node TDOA
- [ ] Validate geolocation accuracy
- [ ] Build Mother drone with processing

### Phase 4: Full System (Weeks 17-22)
- [ ] Build remaining nodes (FW or Quad per config choice)
- [ ] Full system integration test
- [ ] TDOA + FDOA + DF fusion
- [ ] Operational testing against representative targets
- [ ] Documentation and training

### Phase 5: Hybrid Capability (Weeks 23-26) [If Config 3]
- [ ] Integrate multirotor nodes
- [ ] Develop Quad-tasking logic
- [ ] Test combined FW + Quad operations
- [ ] Validate precision DF handoff

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-05 | Initial brainstorm document |
| 2026-02-06 | Added initial 4+1 configuration |
| 2026-02-06 | Major update: Config 1 (multirotor), Config 2 (fixed-wing), Config 3 (hybrid) |
| 2026-02-06 | Added target emitter set, detection feasibility, antenna integration details |
| 2026-02-06 | Added FDOA processing for fixed-wing, hybrid CONOPS |

