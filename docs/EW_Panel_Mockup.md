# EW Panel - GCS UI Mockup

## Overview
The EW Panel is a dedicated tab in the GCS for Electronic Warfare operations, providing real-time situational awareness of the RF environment, emitter management, and EP status.

---

## Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  EW TAB                                                          [▼ Band] [⚙ Settings] │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌─────────────────────────────────────┐  ┌──────────────────────────────────────────┐ │
│  │         SPECTRUM DISPLAY            │  │            EP STATUS                     │ │
│  │                                     │  │                                          │ │
│  │  ▲ dBm                              │  │  LINK HEALTH          THREAT LEVEL       │ │
│  │  │     ╱╲                           │  │  ┌─────────────┐      ┌─────────────┐    │ │
│  │  │    ╱  ╲      ╱╲                  │  │  │ ████████░░  │      │   ● LOW     │    │ │
│  │  │   ╱    ╲    ╱  ╲     ╱╲          │  │  │    82%      │      │             │    │ │
│  │  │  ╱      ╲  ╱    ╲   ╱  ╲         │  │  └─────────────┘      └─────────────┘    │ │
│  │  │ ╱        ╲╱      ╲ ╱    ╲        │  │                                          │ │
│  │  │╱                  ╲      ╲       │  │  ACTIVE RESPONSES                        │ │
│  │  └────────────────────────────► MHz │  │  └── (none)                              │ │
│  │   400    500    600    700    800   │  │                                          │ │
│  │                                     │  │  HOP STATUS                              │ │
│  │  [◀ Prev Band] [Next Band ▶]       │  │  Channel: 3/16  │  Ready                 │ │
│  │  [Waterfall ▼] [Persistence ▼]     │  │                                          │ │
│  └─────────────────────────────────────┘  │  CONSENSUS                               │ │
│                                           │  Bird: ● OK  Chick1: ● OK  Chick2: ● OK  │ │
│  ┌─────────────────────────────────────┐  └──────────────────────────────────────────┘ │
│  │         WATERFALL HISTORY           │                                               │
│  │  ════════════════════════════════   │  ┌──────────────────────────────────────────┐ │
│  │  ═══════╪═══════════════════════   │  │            DF GEOMETRY                   │ │
│  │  ═══════╪═══════════════════════   │  │                                          │ │
│  │  ═══════╪═══════════════════════   │  │           N                              │ │
│  │  ═══════╪══════╪════════════════   │  │           │                              │ │
│  │  ═══════╪══════╪════════════════   │  │      B ───┼─── E                         │ │
│  │  ════════════════════════════════   │  │     /    │    \                         │ │
│  │  ▲ Time                             │  │    C1    │    C2                        │ │
│  │  │                                  │  │     \    │    /                         │ │
│  │  └────────────────────────► Freq    │  │      ● ──┼── ●   ← Emitter (CEP ring)   │ │
│  └─────────────────────────────────────┘  │           │                              │ │
│                                           │         [Optimize Geometry]              │ │
│                                           └──────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                    EMITTER LIST                                         │
├───────┬────────────┬────────┬───────────┬───────────┬─────────┬────────┬───────┬───────┤
│  ID   │    FREQ    │   BW   │    MOD    │   TYPE    │  CRIT   │  CEP   │  AGE  │ ACTION│
├───────┼────────────┼────────┼───────────┼───────────┼─────────┼────────┼───────┼───────┤
│EMT-042│ 423.5 MHz  │ 25 kHz │ FSK (87%) │TAC_RADIO  │ ██████░ │  85m   │  12s  │[TGT]  │
│       │            │        │           │           │   72    │        │       │       │
├───────┼────────────┼────────┼───────────┼───────────┼─────────┼────────┼───────┼───────┤
│EMT-041│ 868.2 MHz  │ 125kHz │LoRa (92%) │MESH_NODE  │ ████░░░ │   -    │  3s   │[IGN]  │
│       │            │        │           │ (FRIENDLY)│   45    │        │       │       │
├───────┼────────────┼────────┼───────────┼───────────┼─────────┼────────┼───────┼───────┤
│EMT-039│ 156.8 MHz  │ 16 kHz │ FM (95%)  │MARINE_VHF │ ███░░░░ │   -    │  45s  │[IGN]  │
│       │            │        │           │ (BENIGN)  │   28    │        │       │       │
├───────┼────────────┼────────┼───────────┼───────────┼─────────┼────────┼───────┼───────┤
│EMT-038│ 462.5 MHz  │ 12.5kHz│ FM (78%)  │ UNKNOWN   │ █████░░ │ 150m   │  8s   │[TGT]  │
│       │            │        │           │ SUSPICIOUS│   58    │        │       │[INV]  │
├───────┼────────────┼────────┼───────────┼───────────┼─────────┼────────┼───────┼───────┤
│EMT-037│ 915.0 MHz  │ 500kHz │FHSS (65%) │ UNKNOWN   │ █████░░ │ 220m   │  22s  │[TGT]  │
│       │            │        │           │ SUSPICIOUS│   61    │        │       │[INV]  │
└───────┴────────────┴────────┴───────────┴───────────┴─────────┴────────┴───────┴───────┘
│ Showing 5 of 23 emitters │ Sort: [Criticality ▼] │ Filter: [All ▼] │ [Export CSV]      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
│                                                                                         │
│  ┌─ SELECTED EMITTER DETAIL ─────────────────────────────────────────────────────────┐ │
│  │                                                                                    │ │
│  │  EMT-042 │ TACTICAL_RADIO │ Criticality: 72/100 (HIGH)                            │ │
│  │                                                                                    │ │
│  │  CHARACTERISTICS                      │  LOCATION                                 │ │
│  │  ├── Frequency: 423.500 MHz           │  ├── Lat: 37.77512°                       │ │
│  │  ├── Bandwidth: 25 kHz                │  ├── Lon: -122.41934°                     │ │
│  │  ├── Modulation: FSK (conf: 87%)      │  ├── CEP: 85m                             │ │
│  │  ├── Duty Cycle: 15% (burst)          │  └── Method: 2-platform TDOA             │ │
│  │  ├── Power Proxy: -65 dBm             │                                           │ │
│  │  └── First Seen: 14:32:18             │  TRACKING                                 │ │
│  │                                        │  ├── Status: ACTIVE                      │ │
│  │  CLASSIFICATION                        │  ├── Sensors: Chick1, Chick2             │ │
│  │  ├── Library Match: UHF_TACTICAL_NET  │  ├── Updates: 12                         │ │
│  │  ├── Purpose: DATA_LINK (conf: 72%)   │  └── Trend: STATIONARY                   │ │
│  │  ├── Threat: HOSTILE (conf: 68%)      │                                           │ │
│  │  └── Tactical: C2_LINK (conf: 41%)    │  [INVESTIGATE]  [ADD TO TARGETS]         │ │
│  │                          ↑             │                                           │ │
│  │                    Low - flags review  │                                           │ │
│  └────────────────────────────────────────┴───────────────────────────────────────────┘ │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Spectrum Display

**Purpose**: Real-time visualization of RF environment

**Features**:
- Live FFT display (updates at scan rate)
- Band selector dropdown (VHF, UHF, ISM, etc.)
- Cursor readout (frequency, power at cursor)
- Peak markers (auto or manual)
- Guard band highlighting (own frequencies shaded)
- Zoom/pan controls

**Display Modes**:
| Mode | Description |
|------|-------------|
| Instantaneous | Current FFT snapshot |
| Max Hold | Peak envelope over time |
| Average | Running average (adjustable window) |
| Persistence | Fading trails (density = frequency of occurrence) |

### 2. Waterfall History

**Purpose**: Time-frequency visualization for pattern detection

**Features**:
- Scrolling spectrogram (time on Y-axis)
- Color mapping: blue (noise floor) → red (strong signal)
- Click to select time slice for detailed view
- Adjustable history depth (30s, 1m, 5m)
- Burst pattern visualization

### 3. EP Status Panel

**Purpose**: Electronic Protection state-at-a-glance

**Components**:

| Element | Description |
|---------|-------------|
| Link Health | Aggregate packet success rate (all links) |
| Threat Level | Current assessment: LOW/MEDIUM/HIGH/CRITICAL |
| Active Responses | List of currently active EP countermeasures |
| Hop Status | Current position in hop table, ready/active state |
| Consensus | Per-vehicle health indicator (voting status) |

**Threat Level Colors**:
- LOW: Green
- MEDIUM: Yellow
- HIGH: Orange
- CRITICAL: Red (flashing)

### 4. DF Geometry Panel

**Purpose**: Visualization of multi-platform direction finding setup

**Features**:
- Top-down view of vehicle positions (B = Bird, C1/C2 = Chicks)
- Emitter position estimate with CEP circle
- Bearing lines from each platform (if available)
- Geometry quality indicator (GDOP-like metric)
- [Optimize Geometry] button: Suggests vehicle repositioning

### 5. Emitter List

**Purpose**: Tabular view of all detected emitters

**Columns**:
| Column | Description |
|--------|-------------|
| ID | Unique emitter identifier (EMT-XXXX) |
| FREQ | Center frequency |
| BW | Bandwidth |
| MOD | Modulation type + confidence % |
| TYPE | Classification (from library or ML) |
| CRIT | Criticality score (0-100) with visual bar |
| CEP | Circular Error Probable (if located) or "-" |
| AGE | Time since last update |
| ACTION | Quick action buttons |

**Action Buttons**:
- [TGT]: Add to target queue
- [IGN]: Ignore/filter (for known benign)
- [INV]: Investigate (command Chick to dwell)

**Sorting Options**:
- Criticality (default, descending)
- Frequency
- Age (newest first)
- Type

**Filtering Options**:
- All
- Tactical only
- Unknown/Suspicious only
- High criticality only
- Hide ignored

### 6. Selected Emitter Detail

**Purpose**: Full details on selected emitter from list

**Sections**:

**Characteristics**:
- All measured RF parameters
- First/last seen timestamps
- Signal stability metrics

**Classification**:
- Library match (if any)
- ML outputs with confidence scores
- "Low confidence" warning for tactical purpose

**Location**:
- Coordinates (if DF available)
- CEP estimate
- Method used (TDOA, bearing intersection, etc.)

**Tracking**:
- Active/Lost status
- Which sensors are tracking
- Update count
- Movement trend (STATIONARY, MOVING, ERRATIC)

**Actions**:
- [INVESTIGATE]: Command nearest Chick to reposition for better DF
- [ADD TO TARGETS]: Create target queue entry

---

## Interaction Flows

### Flow 1: New Critical Emitter Detected

```
1. ES detects new emitter above criticality threshold
2. Emitter appears at top of list (sorted by crit)
3. Audio/visual alert plays
4. If CRITICAL: Row highlights red, auto-selects
5. Spectrum display auto-tunes to emitter frequency
6. Multi-sensor DF auto-initiates
7. Operator reviews detail panel
8. Operator clicks [ADD TO TARGETS] or [IGN]
```

### Flow 2: Add Emitter to Target Queue

```
1. Operator selects emitter in list
2. Reviews detail panel (CEP, classification, confidence)
3. If CEP too large:
   a. Clicks [INVESTIGATE]
   b. System commands Chick to reposition
   c. CEP improves over time
   d. Operator monitors until acceptable
4. Clicks [ADD TO TARGETS]
5. Dialog confirms:
   - Target ID assigned
   - Linked emitter ID shown
   - Auto-update enabled (checkbox)
   - CEP warning if > threshold
6. Target appears in Target Queue (separate tab)
7. Emitter row shows "→ TGT-XXXX" link
```

### Flow 3: EP Hop Triggered

```
1. ES detects jamming on current channel
2. EP Status panel updates:
   - Link Health drops (red)
   - Threat Level → HIGH or CRITICAL
   - Active Responses: "HOP_PENDING"
3. If auto-execute threshold met:
   a. Hop countdown appears (T-3, T-2, T-1)
   b. All vehicles hop simultaneously
   c. Status updates: "HOP_COMPLETE → Channel 4/16"
   d. Link Health recovers (or next hop if still jammed)
4. If recommend threshold:
   a. Dialog: "Jamming detected. Recommend frequency hop?"
   b. [HOP NOW] [DISMISS] buttons
   c. Timeout auto-dismisses (continues monitoring)
```

### Flow 4: Investigate Command

```
1. Operator clicks [INV] on emitter with high CEP
2. Dialog shows:
   - Current CEP: 220m
   - Nearest Chick: Chick1 (1.2km from estimate)
   - Recommended position for optimal DF
3. Operator clicks [SEND CHICK]
4. System generates GUIDED waypoint for Chick
5. Chick repositions (shown on main map)
6. CEP updates in real-time as geometry improves
7. When CEP < threshold, [ADD TO TARGETS] highlighted
```

---

## V2 Additions

### High-Frequency Tile Selector

```
┌─ TILE BANDS ─────────────────────┐
│ [●] Primary (47MHz - 6GHz)       │
│ [ ] 5.8 GHz Tile                 │
│ [ ] X-Band Tile (8-12 GHz)       │
│ [ ] Ku-Band Tile (12-18 GHz)     │
│ [ ] K/Ka Tile (24-28 GHz)        │
│                                   │
│ Active Tile: Primary              │
│ Scan Mode: [Sweep ▼]             │
└───────────────────────────────────┘
```

### ML Confidence Display

Expanded classification section with layer-by-layer breakdown:

```
CLASSIFICATION (ML Pipeline)
├── L1 Modulation: FSK (87%) ████████░░
├── L2 Purpose: DATA_LINK (72%) ███████░░░
├── L3 Threat: HOSTILE (68%) ██████░░░░
├── L4 Fingerprint: NEW_EMITTER
└── L5 Tactical: C2_LINK (41%) ████░░░░░░ ⚠ LOW CONF
```

### EA Control Panel (V2, if enabled)

```
┌─ ELECTRONIC ATTACK ──────────────┐
│                                   │
│ ⚠ EA REQUIRES AUTHORIZATION       │
│                                   │
│ Status: [DISABLED]               │
│                                   │
│ Target: (none selected)          │
│ Mode: [Spot Jam ▼]               │
│ Power: [Low ▼]                   │
│ Duration: [5 sec ▼]              │
│                                   │
│ [ENABLE EA] (requires auth code) │
│                                   │
└───────────────────────────────────┘
```

### Orb Track-While-Engage Display (V2)

When Orb is in flight with linked emitter:

```
┌─ ORB TRACKING ───────────────────┐
│                                   │
│ Orb: ORB-1.1.1 → TGT-018         │
│ Linked Emitter: EMT-042          │
│                                   │
│ Emitter Position: UPDATING       │
│ Last Update: 2s ago              │
│ Position Δ since release: 45m    │
│                                   │
│ Orb Updates Sent: 2 of 5 max     │
│ Time to Terminal: 18s            │
│                                   │
│ Auto-Update: [ENABLED]           │
│                                   │
└───────────────────────────────────┘
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| E | Switch to EW tab |
| ↑/↓ | Navigate emitter list |
| Enter | Select emitter for detail |
| T | Add selected to targets |
| I | Investigate selected |
| G | Ignore selected |
| H | Manual hop (if EP allows) |
| Space | Pause/resume spectrum |
| +/- | Zoom spectrum |
| F | Toggle filter (all/suspicious) |

---

## Alert Sounds

| Event | Sound |
|-------|-------|
| New HIGH criticality emitter | Double beep |
| New CRITICAL emitter | Alarm tone |
| EP Tier 2 recommendation | Single chime |
| EP Tier 3 auto-action | Alert + voice "Hop initiated" |
| Emitter lost | Soft tone |
| CEP threshold met | Success chime |

---

## Color Coding Reference

| Element | Color | Meaning |
|---------|-------|---------|
| Criticality bar | Gray → Red | 0 → 100 score |
| Emitter type TACTICAL | Orange | Potential threat |
| Emitter type BENIGN | Gray | Known safe |
| Emitter type UNKNOWN_SUSPICIOUS | Yellow | Needs review |
| Emitter type FRIENDLY | Green | Own systems |
| CEP < 50m | Green | Targetable |
| CEP 50-150m | Yellow | Marginal |
| CEP > 150m | Red | Needs refinement |
| Link health > 80% | Green | Healthy |
| Link health 50-80% | Yellow | Degraded |
| Link health < 50% | Red | Critical |
