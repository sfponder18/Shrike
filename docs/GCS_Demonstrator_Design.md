# Shrike GCS Demonstrator - Design Document

**Status:** Ready to Build
**Date:** 2026-02-07
**Purpose:** Pure Python simulation demonstrating EW/Strike CONOP flow

---

## 1. Scope

Software-only GCS demonstrator that simulates the full Shrike mission flow:
- Carrier transit to target area
- Scout deployment
- EW detection and geolocation
- Strike authorization and execution
- BDA and RTB

Hardware integration deferred; architecture designed to support future hardware.

---

## 2. CONOP Summary

1. Operator provides target cue ("System X" approximate location)
2. Carrier launches and transits to AO
3. Carrier loiters at safe distance, deploys 4 Scouts
4. Scouts search for emitters (proximity-based detection)
5. Progressive geolocation refines target position (CEP shrinks)
6. Operator manually authorizes strike
7. Scout(s) execute strike (travel time → impact → expended)
8. Remaining Scouts pursue secondary targets if on interest list
9. Data relayed through Carrier to GCS
10. Carrier RTBs

---

## 3. Architecture

```
Shrike/
└── gcs/
    ├── main.py                 # Entry point
    ├── simulation/
    │   ├── sim_engine.py       # Time, vehicle movement, detection logic
    │   ├── vehicles.py         # Carrier, Scout models
    │   ├── emitters.py         # Radar emitter models
    │   └── geolocation.py      # Progressive CEP calculation
    ├── ui/
    │   ├── main_window.py      # Main layout
    │   ├── map_widget.py       # Folium/PyQt map
    │   ├── ew_panel.py         # Emitter table, detection display
    │   ├── event_log.py        # Scrolling event log
    │   ├── state_bar.py        # Mission phase indicator
    │   └── comms_panel.py      # Link status display
    ├── mission/
    │   ├── mission_manager.py  # State machine, phase transitions
    │   └── strike_auth.py      # Manual approval workflow
    └── data/
        └── emitter_library.py  # Sample radar types
```

---

## 4. Mission State Machine

```
┌──────────┐    ┌─────────┐    ┌────────┐    ┌────────┐
│ PLANNING │───►│ TRANSIT │───►│ DEPLOY │───►│ SEARCH │
└──────────┘    └─────────┘    └────────┘    └───┬────┘
                                                  │
                                                  ▼
┌──────────┐    ┌────────┐    ┌─────────────┐  ┌────────┐
│   RTB    │◄───│  BDA   │◄───│ STRIKE_EXEC │◄─│ LOCATE │
└──────────┘    └────────┘    └─────────────┘  └───┬────┘
                                   ▲               │
                                   │          ┌────▼─────┐
                                   └──────────│STRIKE_AUTH│
                                              └──────────┘
```

### State Descriptions

| State | Description | Exit Condition |
|-------|-------------|----------------|
| PLANNING | Operator sets target cue, mission params | Operator clicks "Launch" |
| TRANSIT | Carrier flies to AO | Carrier reaches loiter point |
| DEPLOY | Carrier releases Scouts | All 4 Scouts deployed |
| SEARCH | Scouts spread out, search for emitters | Emitter detected |
| LOCATE | Progressive geolocation, CEP refining | CEP < threshold OR operator decides |
| STRIKE_AUTH | Awaiting operator approval | Operator approves/denies |
| STRIKE_EXEC | Scout(s) fly to target, impact | Impact confirmed |
| BDA | Remaining Scouts assess, find secondaries | Assessment complete |
| RTB | Carrier + surviving Scouts return | Carrier lands |

---

## 5. Simulation Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Scout count | 4 | Configurable |
| Detection method | Proximity | < X km from emitter |
| Detection range | 5 km | Configurable |
| Initial CEP | 500m | Before geolocation |
| Final CEP | 50m | With 4 Scouts contributing |
| CEP improvement | Progressive | Shrinks as Scouts contribute |
| Strike success | 100% | Simplified for demo |
| Scout post-strike | Expended | Removed from sim |
| Sim speed | Real-time | 1:1 |
| Carrier behavior | Loiter | Safe distance from target |

---

## 6. Sample Emitter Library

| ID | Type | NATO Name | Band | Frequency | Priority | Notes |
|----|------|-----------|------|-----------|----------|-------|
| E001 | 91N6E | "Big Bird" | S | 2.5-3.5 GHz | Critical | S-400 acquisition |
| E002 | 96L6E | "Cheese Board" | C | 5-6 GHz | High | All-altitude detection |
| E003 | 92N6E | "Grave Stone" | X | 8-10 GHz | High | S-400 fire control |
| E004 | Unknown | - | S | 2-4 GHz | Medium | Unclassified S-band |
| E005 | Unknown | - | C | 4-6 GHz | Medium | Unclassified C-band |
| E006 | TEL Radar | - | S | 3.0 GHz | Critical | Mobile launcher |

### Interest List (Auto-Engage Candidates)

Emitters with priority **High** or **Critical** are automatically flagged for strike consideration. Operator must still manually authorize.

---

## 7. UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STATE: [SEARCH]  ██████████░░░░░░░░░░  Scout1:● Scout2:● Scout3:● S4:● │
├─────────────────────────────────────────┬───────────────────────────────┤
│                                         │  EW PANEL                     │
│                                         │  ┌───────────────────────────┐│
│                                         │  │ ID    Type      CEP  Pri  ││
│              MAP                        │  │ E001  91N6E     127m CRIT ││
│                                         │  │ E004  Unk S-bd  340m MED  ││
│    ◇ Carrier (loiter)                   │  └───────────────────────────┘│
│    ● Scout 1                            │                               │
│    ● Scout 2           ╳ Target         │  ┌───────────────────────────┐│
│    ● Scout 3           ◌ CEP circle     │  │ COMMS STATUS              ││
│    ● Scout 4                            │  │ Scout1 ↔ Carrier: ●       ││
│                                         │  │ Scout2 ↔ Carrier: ●       ││
│                                         │  │ Scout3 ↔ Carrier: ●       ││
│                                         │  │ Scout4 ↔ Carrier: ●       ││
│                                         │  │ Carrier ↔ GCS: ●          ││
│                                         │  └───────────────────────────┘│
├─────────────────────────────────────────┴───────────────────────────────┤
│  EVENT LOG                                                              │
│  ──────────────────────────────────────────────────────────────────────│
│  14:32:01 [DETECT]  Scout 2 detected emitter (S-band, 3.1 GHz)         │
│  14:32:05 [LOCATE]  Geolocation initiated, 1/4 Scouts contributing     │
│  14:32:15 [LOCATE]  CEP refined: 340m → 127m (3/4 Scouts)              │
│  14:32:30 [AUTH]    Strike authorization requested: 91N6E (CEP 127m)   │
│  14:32:45 [STRIKE]  Operator APPROVED strike on E001                   │
│  14:32:46 [STRIKE]  Scout 2 tasked to E001, ETA 45 sec                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Key UI Components

### 8.1 State Bar (Top)
- Current mission state (color-coded)
- Progress indicator
- Scout status indicators (alive/expended)

### 8.2 Map Widget (Left)
- Interactive pan/zoom (user controlled)
- Carrier icon (◇) with heading
- Scout icons (●) with trails
- Emitter markers (╳) when detected
- CEP circles (◌) showing geolocation uncertainty
- Target cue marker (initial estimate)

### 8.3 EW Panel (Right Top)
- Table of detected emitters
- Columns: ID, Type, Frequency, CEP, Priority, Status
- Click to select for strike authorization
- Color coding by priority

### 8.4 Comms Panel (Right Middle)
- Link status indicators
- Scout ↔ Carrier links
- Carrier ↔ GCS link
- Green = connected, Yellow = degraded, Red = lost

### 8.5 Event Log (Bottom)
- Scrolling timestamped log
- Color-coded by event type:
  - [DETECT] - Blue
  - [LOCATE] - Cyan
  - [AUTH] - Yellow
  - [STRIKE] - Red
  - [BDA] - Green
  - [SYSTEM] - Gray

---

## 9. Strike Authorization Workflow

```
┌─────────────────────────────────────────┐
│         STRIKE AUTHORIZATION            │
├─────────────────────────────────────────┤
│                                         │
│  Target: 91N6E "Big Bird"               │
│  Location: 34.5678°N, 45.1234°E         │
│  CEP: 127m                              │
│  Priority: CRITICAL                     │
│                                         │
│  Scouts Available: 3                    │
│  Recommended: 1 Scout                   │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  AUTHORIZE  │    │    DENY     │    │
│  └─────────────┘    └─────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

---

## 10. Progressive Geolocation

CEP calculation based on number of contributing Scouts:

| Scouts Contributing | CEP (meters) |
|---------------------|--------------|
| 1 | 500m |
| 2 | 250m |
| 3 | 125m |
| 4 | 50m |

CEP displayed as circle on map, shrinks in real-time as Scouts contribute.

---

## 11. Tech Stack

| Component | Technology |
|-----------|------------|
| UI Framework | PyQt5 |
| Map | Folium + QtWebEngineWidgets |
| Simulation | Python threading |
| Data | Python dataclasses |
| Config | YAML or JSON |

---

## 12. Development Phases

### Phase 1: Core Framework
- [ ] Project structure setup
- [ ] Simulation engine (time, movement)
- [ ] Vehicle models (Carrier, Scout)
- [ ] Emitter models

### Phase 2: UI Shell
- [ ] Main window layout
- [ ] Map widget (basic)
- [ ] State bar
- [ ] Event log

### Phase 3: EW Integration
- [ ] Detection logic
- [ ] EW panel
- [ ] Progressive geolocation
- [ ] CEP visualization on map

### Phase 4: Strike Flow
- [ ] Strike authorization dialog
- [ ] Strike execution
- [ ] Scout expend logic
- [ ] BDA state

### Phase 5: Polish
- [ ] Comms panel
- [ ] Secondary target handling
- [ ] RTB logic
- [ ] Testing and refinement

---

## 13. Files to Pull from SwarmDrones

| File | Purpose | Modifications Needed |
|------|---------|---------------------|
| `gcs/widgets/map_widget.py` | Map display | Update for Shrike icons |
| `gcs/models/vehicle.py` | Vehicle base class | Extend for Scout/Carrier |
| `gcs/comms/` | Communication patterns | Reference only |

---

## 14. Future Hardware Integration Points

Designed for future hardware connection:

| Interface | Current (Sim) | Future (Hardware) |
|-----------|---------------|-------------------|
| Vehicle position | Simulated movement | MAVLink telemetry |
| Emitter detection | Proximity trigger | SDR PDW input |
| Strike command | State change | MAVLink waypoint |
| Video | Not implemented | GStreamer RTP |

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-07 | Initial design document |
