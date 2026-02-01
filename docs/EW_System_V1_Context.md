# EW System V1 - Context Document

## Purpose
This document provides the architectural context for the V1 Electronic Warfare (EW) system integrated into the SwarmDrones platform. It captures key decisions, constraints, and design rationale to enable consistent development.

---

## System Overview

### Mission
Primarily **offensive** electronic support (ES) with defensive electronic protection (EP) capabilities. The EW system detects, characterizes, and geolocates RF emitters in the tactical spectrum to support swarm operations and targeting.

### V1 Scope
- ES: Detection and characterization using existing RTL-SDR hardware on Chicks
- EP: 3-tiered response system with frequency agility under jamming
- Integration: Emitter-to-target workflow with manual operator approval
- Architecture: Foundation for V2 expansion (bladeRF, Jetson, larger platforms)

---

## Platform Configuration (V1)

| Platform | EW Hardware | Role |
|----------|-------------|------|
| Bird | None (V1) | Mesh relay, orbit adjustment for sensor geometry |
| Chick (x2) | RTL-SDR V4 (24MHz-1.7GHz) | Primary ES sensors |
| GCS | T-Beam LoRa | Command, display, fusion |

### Companion Computer
- **V1**: Raspberry Pi (existing)
- **Future**: Jetson Orin Nano (all platforms)

---

## Electronic Support (ES)

### Core Function
Autonomous spectrum scanning with GCS-commandable overrides.

### Outputs (Summarized ES Products)
The CC processes raw RF and exports only:
- Emitter list (frequency, bandwidth, modulation family, confidence)
- Occupancy metrics (band utilization)
- Anomaly flags (new emitters, characteristic changes)
- Criticality scores

**Raw RF data is NOT transmitted over mesh** - only summarized products.

### Scan Architecture

```
GUARD BANDS (guaranteed dwell)
├── Own control: 868 MHz (mLRS, T-Beam)
├── Own control: 2.4 GHz (ELRS)
└── GNSS: 1.575 GHz (L1), 1.227 GHz (L2)

SWEEP BANDS (remaining time budget)
├── VHF: 30-88 MHz, 136-174 MHz
├── UHF: 400-470 MHz
├── ISM/Cellular: 860-930 MHz
└── Other bands per mission config

PRIORITY
Guard > Event-triggered dwell > Sweep
```

### Criticality Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Known threat signature match | 35% | Matches preloaded threat library |
| Band overlap with own systems | 20% | Direct threat to comms/nav |
| Proximity to mission area | 15% | Geographically relevant |
| Signal strength | 10% | Stronger = closer/more powerful |
| New emitter in quiet band | 10% | Anomaly detection |
| Rapid characteristic change | 10% | Adaptive adversary indicator |

**Criticality Levels:**
- CRITICAL (>80): Auto multi-sensor coordination + EP response
- HIGH (60-80): Operator alert, recommend action
- MEDIUM (40-60): Track and log
- LOW (<40): Background catalog

**Overtasking Prevention**: System limits active tracking to top N emitters by criticality to prevent resource exhaustion.

### Multi-Sensor Coordination

Triggered when emitter criticality exceeds threshold:
1. Both Chicks synchronize to same frequency
2. Timestamped samples (GPS PPS, ~50ns accuracy)
3. TDOA correlation for geolocation
4. Position estimate with CEP (Circular Error Probable)

Bird participates by adjusting orbit to optimize sensor geometry.

---

## Electronic Protection (EP)

### 3-Tier Response System

| Tier | Trigger | Action | Operator Role |
|------|---------|--------|---------------|
| **1: Alert** | Any ES detection on monitored bands | Log, update GCS display | Informed only |
| **2: Recommend** | Criticality HIGH or sustained interference | Propose countermeasure | Must approve/dismiss |
| **3: Auto-Execute** | Criticality CRITICAL or >50% packet loss | Execute immediately | Notified post-facto |

### Frequency Agility Protocol

**Trigger**: Event-based (only when under attack, >50% packet loss)

**Pre-Mission Setup**:
- 16-entry hop table: [frequency, power, modulation, timing offset]
- Hop table synchronized during mission planning
- Table changes each mission (not reused)
- All vehicles and GCS share identical table + seed

**Hop Sequence**:
```
1. EP detects jamming (>50% packet loss on current channel)
2. Initiating vehicle broadcasts HOP_INTENT with next_hop_index
3. All vehicles ACK within T-2 seconds
4. Synchronized hop at T=0 (GPS time)
5. Post-hop heartbeat verification
6. If new channel jammed, repeat with next index
```

**Fallback Hierarchy**:
1. Hop through table entries
2. Fall back to 4G/Tailscale if available
3. Execute pre-planned autonomous mission if total denial

### Swarm Consensus (Hybrid Approach)

**Normal Operation**: GCS aggregates reports, computes consensus, broadcasts decision

**Degraded Operation**: If GCS link lost (timeout), vehicles compute distributed consensus

**Voting Weights**:
- Sensor quality (better hardware = higher weight)
- Position (closer to emitter = higher weight)
- Altitude (higher = better RF horizon)

**Consensus Threshold**:
- 2 of 3 agree: HIGH confidence action
- 1 of 3 with high criticality: MEDIUM, seek verification
- Conflict: Flag for operator review

---

## Emitter-to-Target Workflow

### Detection to Display
```
ES detects emitter → CC characterizes → Mesh reports to GCS
                                              ↓
                                    EW Panel displays:
                                    - Emitter ID
                                    - Frequency, bandwidth
                                    - Modulation (confidence %)
                                    - Type (from library match)
                                    - Criticality score
                                    - Position (if DF available)
                                    - CEP (position error)
                                    - Status (NEW/TRACKING/LOST)
```

### Targeting (Manual Approval Required)
```
Operator clicks [ADD TO TARGETS]
        ↓
Target Queue entry created:
- Source: EW_EMITTER
- Linked emitter ID
- Position + CEP displayed
- Auto-update: ENABLED
        ↓
If CEP > acceptable threshold:
- System recommends Chick investigation
- Chick repositions to refine DF
- CEP improves with closer observation
        ↓
When CEP acceptable:
- Operator assigns Orb
- Coords locked at release (V1)
- V2: In-flight updates via Orb LoRa
```

---

## ML Classification (V1)

### Approach
Preloaded threat library with confidence-scored matching.

### Classification Outputs
- **KNOWN_TACTICAL**: Matches threat library (high priority)
- **KNOWN_BENIGN**: Matches civilian signatures (filterable)
- **UNKNOWN_SUSPICIOUS**: Behavioral flags present (operator review)
- **UNKNOWN_BENIGN**: No concerning patterns

### Behavioral Flags (Heuristics)
- Appears when swarm enters area (reactive)
- Characteristics change with swarm movement
- Burst patterns suggest tactical data link
- Coordinated with other unknown emitters
- Uses tactical bands without civilian signature

**UNKNOWN_SUSPICIOUS always flagged for operator review** - no autonomous action on unconfirmed threats.

---

## GCS Integration

### EW Tab
Dedicated tab in GCS with:
- Real-time emitter list (sortable by criticality)
- Spectrum waterfall display
- DF geometry visualization
- EP status and response controls
- Emitter-to-target workflow buttons

### Alerts
- Priority signals trigger visual/audio alert
- Critical threats auto-promote to main display
- EP actions logged with timestamp

---

## Hardware Constraints (V1)

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| RTL-SDR dynamic range | Limited in dense RF | Prioritize guard bands |
| Pi compute | ML inference limited | Simple classifiers, library matching |
| Mesh bandwidth | 1-11 kbps | Summarized products only |
| Single antenna per Chick | No onboard DF | Multi-platform TDOA |

---

## Success Criteria (V1)

1. Detect and catalog emitters in 30-1700 MHz range
2. Characterize signals (freq, BW, modulation family)
3. Calculate criticality scores with consistent ranking
4. Geolocate critical emitters using 2-Chick TDOA
5. EP responds to jamming with coordinated frequency hop
6. Operator can convert emitter to target with one click
7. System does not overtask (graceful degradation under load)

---

## V2 Preparation

V1 architecture enables these V2 additions:
- BladeRF 2.0 (wider bandwidth, TX capability)
- Jetson Orin (ML inference, faster processing)
- Larger Chick platforms (10" with dedicated EW payload)
- Higher-frequency tiles (6GHz+ with downconversion)
- Orb LoRa modules (in-flight retargeting)
- Potential EA capabilities

---

## Key Files

| Component | Location | Purpose |
|-----------|----------|---------|
| ES Manager | `gcs/ew/es_manager.py` | Emitter detection, characterization |
| EP Manager | `gcs/ew/ep_manager.py` | Protection responses, hop control |
| Threat Library | `gcs/ew/threat_library.json` | Known signatures |
| EW Widget | `gcs/widgets/ew_panel.py` | GCS display |
| Criticality | `gcs/ew/criticality.py` | Scoring algorithm |

---

## Reference Documents

- `EWBrainstorm.txt` - Initial requirements capture
- `EW_System_V2_Context.md` - V2 expansion architecture
- `Mesh_Network_Design.md` - Communication protocols
- `SwarmDrones_Design_Document.md` - Overall system architecture
