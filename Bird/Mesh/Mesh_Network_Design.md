# Swarm Drone Mesh Network Design
## Secure, Encrypted Communication Layer

**Version:** 2.0
**Date:** January 2026
**Status:** Implementation Ready

---

# Table of Contents

1. [Overview](#1-overview)
2. [Communication Architecture](#2-communication-architecture)
3. [Layer 1: ELRS - RC Control](#3-layer-1-elrs---rc-control)
4. [Layer 2: mLRS - Primary Telemetry](#4-layer-2-mlrs---primary-telemetry)
5. [Layer 3: Meshtastic - Mesh Backbone](#5-layer-3-meshtastic---mesh-backbone)
6. [V1 Codeword Protocol](#6-v1-codeword-protocol)
7. [V2 High-Fidelity Upgrade](#7-v2-high-fidelity-upgrade)
8. [Hardware Components](#8-hardware-components)
9. [Security & Encryption](#9-security--encryption)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

# 1. Overview

## 1.1 Design Philosophy

**Three-layer communication stack** - each layer serves a specific purpose:

| Layer | Protocol | Purpose | Data Rate | Latency |
|-------|----------|---------|-----------|---------|
| 1 | ELRS 2.4GHz | RC Control | N/A | 2-5ms |
| 2 | mLRS 915MHz | Bird Telemetry | 50-91 kbps | 20-50ms |
| 3 | Meshtastic 915MHz | Mesh Backbone | 1-11 kbps | 100-500ms |

## 1.2 Why Three Layers?

```
LAYERED COMMUNICATION RATIONALE
═══════════════════════════════════════════════════════════════

LAYER 1 - ELRS (RC Control)
├── Purpose: Direct stick control, failsafe trigger
├── Why separate: RC must NEVER share bandwidth with data
├── Failsafe: Drone knows immediately if RC lost
└── You already have: RadioMaster TX with ELRS

LAYER 2 - mLRS (Primary Telemetry)
├── Purpose: High-bandwidth MAVLink to Bird
├── Why mLRS: 8-10x faster than Meshtastic
├── Data: Full telemetry, waypoints, parameters
└── Point-to-point: GCS ↔ Bird only

LAYER 3 - Meshtastic (Mesh Backbone)
├── Purpose: Inter-swarm communication, backup, Orbs
├── Why mesh: Self-healing, multi-node, resilient
├── V1: Compact codewords for efficiency
└── V2: Upgrade path for higher fidelity

═══════════════════════════════════════════════════════════════
```

---

# 2. Communication Architecture

## 2.1 Complete Network Topology

```
SWARM COMMUNICATION ARCHITECTURE
═══════════════════════════════════════════════════════════════

                         ┌─────────────────┐
                         │       GCS       │
                         │    (Laptop)     │
                         │                 │
                         │ ┌─────────────┐ │
                         │ │RadioMaster  │ │◄── ELRS TX (2.4GHz)
                         │ │    TX16S    │ │    RC Control
                         │ └─────────────┘ │
                         │                 │
                         │ ┌─────────────┐ │
                         │ │ mLRS Ground │ │◄── mLRS TX (915MHz)
                         │ │   Module    │ │    91kbps MAVLink
                         │ └─────────────┘ │
                         │                 │
                         │ ┌─────────────┐ │
                         │ │ Meshtastic  │ │◄── Mesh Node (915MHz)
                         │ │   T-Beam    │ │    Backbone
                         │ └─────────────┘ │
                         └────────┬────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        │ ELRS 2.4GHz            │ mLRS 915MHz             │ Mesh 915MHz
        │ (RC only)              │ (telemetry)             │ (swarm data)
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│     BIRD      │         │     BIRD      │         │     BIRD      │
│   ┌───────┐   │         │   ┌───────┐   │         │   ┌───────┐   │
│   │ELRS RX│   │         │   │ mLRS  │   │         │   │Meshtas│   │
│   │ RP3   │   │         │   │  RX   │   │         │   │tic    │   │
│   └───┬───┘   │         │   └───┬───┘   │         │   └───┬───┘   │
│       │       │         │       │       │         │       │       │
│       ▼       │         │       ▼       │         │       ▼       │
│   Pixhawk     │         │   Pi 5      │         │   Pi 5      │
│   (SBUS)      │         │   (MAVLink)   │         │   (Mesh API)  │
└───────────────┘         └───────────────┘         └───────┬───────┘
                                                            │
                                          ┌─────────────────┼─────────────────┐
                                          │                 │                 │
                                          ▼                 ▼                 ▼
                                   ┌───────────┐     ┌───────────┐     ┌───────────┐
                                   │  CHICK 1  │     │  CHICK 2  │     │   ORBS    │
                                   │ Meshtastic│     │ Meshtastic│     │ Meshtastic│
                                   └───────────┘     └───────────┘     └───────────┘

═══════════════════════════════════════════════════════════════
```

## 2.2 Data Flow Summary

| Data | Path | Protocol | Rate |
|------|------|----------|------|
| RC Sticks | GCS → Bird | ELRS | 500Hz |
| Bird Telemetry | Bird → GCS | mLRS | 50Hz |
| Bird Commands | GCS → Bird | mLRS | On demand |
| Bird → Chick | Bird → Chick | Meshtastic | 2-5Hz |
| Chick Telemetry | Chick → GCS | Meshtastic (via Bird) | 1-2Hz |
| Orb Targeting | Bird/Chick → Orb | Meshtastic | On demand |
| Emergency/Backup | Any → Any | Meshtastic | As needed |

---

# 3. Layer 1: ELRS - RC Control

## 3.1 Purpose

ELRS handles **only** RC control - stick inputs and flight mode switches. This separation ensures:
- RC link is never congested by telemetry
- Immediate failsafe detection
- Lowest possible latency for control

## 3.2 Configuration

```
ELRS SETUP (Already in your design)
═══════════════════════════════════════════════════════════════

Hardware:
- TX: RadioMaster TX16S (already owned)
- RX Bird: RadioMaster RP3 (ELRS 2.4GHz)
- RX Chicks: RadioMaster RP2 (ELRS 2.4GHz)

Settings:
- Packet Rate: 500Hz (lowest latency)
- TX Power: 250mW (plenty for LOS)
- Telemetry Ratio: OFF (using mLRS instead)

Wiring:
- RX → Pixhawk SBUS input
- RX → FC SBUS input (Chicks)

═══════════════════════════════════════════════════════════════
```

## 3.3 Failsafe Behavior

| Condition | Bird Response | Chick Response |
|-----------|---------------|----------------|
| ELRS signal lost | Continue AUTO mode, wait for mLRS cmd | RTL after 5s |
| ELRS + mLRS lost | RTL after 30s | Land after 10s |
| ELRS + all links lost | RTL, then loiter at home | Land immediately |

---

# 4. Layer 2: mLRS - Primary Telemetry

## 4.1 Purpose

mLRS provides **high-bandwidth MAVLink** between GCS and Bird:
- Full telemetry stream (attitude, position, sensors)
- Parameter upload/download
- Mission upload
- Low-latency commands

## 4.2 mLRS Specifications

```
mLRS CONFIGURATION
═══════════════════════════════════════════════════════════════

Mode:           19 Hz (recommended balance)
Data Rate:      53 kbps (bidirectional)
Latency:        ~53ms
Range:          5-10km LOS
Encryption:     AES-128-CTR
Frequency:      915MHz ISM band

Available Modes:
┌──────────┬──────────┬─────────┬──────────┐
│ Mode     │ Rate     │ Latency │ Range    │
├──────────┼──────────┼─────────┼──────────┤
│ 31 Hz    │ 91 kbps  │ 32ms    │ 2-5km    │
│ 19 Hz    │ 53 kbps  │ 53ms    │ 5-10km   │◄── START HERE
│ FSK 50Hz │ 50 kbps  │ 20ms    │ 1-3km    │
└──────────┴──────────┴─────────┴──────────┘

Why 19 Hz: Best balance of range and bandwidth for initial testing.
Can switch to 31 Hz if you need more bandwidth at shorter range.

═══════════════════════════════════════════════════════════════
```

## 4.3 mLRS Hardware

```
mLRS HARDWARE OPTIONS
═══════════════════════════════════════════════════════════════

OPTION A: MatekSys mLRS (Recommended - Purpose Built)
──────────────────────────────────────────────────────────────
- mLRS TX Module: MatekSys mR900-30-TX         $40
  - 30dBm (1W) output
  - JR bay compatible (fits RadioMaster)
  - Or standalone with USB

- mLRS RX Module: MatekSys mR900-22-RX         $25
  - 22dBm output
  - UART to Pi 5
  - Tiny form factor

  MatekSys Total: $65

OPTION B: DIY with EBYTE E77 Modules (Budget)
──────────────────────────────────────────────────────────────
- E77-900M22S modules x2                       $24
  - Requires soldering
  - Needs custom housing
  - Same performance

OPTION C: SeeedStudio Wio-E5 (Dev Friendly)
──────────────────────────────────────────────────────────────
- Wio-E5 Dev Boards x2                         $30
  - Easy USB flashing
  - Good for bench testing

RECOMMENDATION: MatekSys for flight, Wio-E5 for bench dev

═══════════════════════════════════════════════════════════════
```

## 4.4 mLRS Wiring

```
mLRS INTEGRATION - BIRD
═══════════════════════════════════════════════════════════════

    mLRS RX Module              RASPBERRY PI 5
    ┌─────────────┐            ┌─────────────────┐
    │             │            │                 │
    │  TX ────────┼────────────┼─► UART RX      │
    │  RX ────────┼────────────┼─► UART TX      │
    │  GND ───────┼────────────┼─► GND          │
    │  5V ────────┼────────────┼─► 5V           │
    │             │            │                 │
    │  [Antenna]  │            │   MAVProxy     │
    └─────────────┘            │   listens on   │
                               │   /dev/ttyTHS1 │
                               └─────────────────┘

    Pi 5 runs MAVProxy:
    mavproxy.py --master=/dev/ttyTHS1,57600 \
                --out=udp:127.0.0.1:14550

    QGroundControl on GCS connects via UDP through mLRS link

═══════════════════════════════════════════════════════════════
```

---

# 5. Layer 3: Meshtastic - Mesh Backbone

## 5.1 Purpose

Meshtastic provides the **mesh backbone** for:
- Bird ↔ Chick communication
- Chick ↔ Chick communication
- Orb targeting data
- Backup command path if mLRS fails
- Inter-swarm coordination

## 5.2 V1 Design Philosophy

**Constraint**: Meshtastic is slow (1-11 kbps)
**Solution**: Compact codeword system to maximize information per byte

```
V1 MESH DATA STRATEGY
═══════════════════════════════════════════════════════════════

PROBLEM:
- Meshtastic max: ~237 bytes/packet
- Update rate: ~4 packets/second total
- With 4 nodes: ~1 packet/node/second

SOLUTION:
- Design compact binary codewords
- Encode maximum information in minimum bytes
- Reserve full text for emergencies only

RESULT:
- 20-30 byte telemetry vs 100+ byte JSON
- 3-5x more updates per second
- Room for more nodes

═══════════════════════════════════════════════════════════════
```

---

# 6. V1 Codeword Protocol

## 6.1 Message Structure

```
V1 CODEWORD FORMAT
═══════════════════════════════════════════════════════════════

All V1 messages use this compact binary format:

HEADER (2 bytes):
┌────────┬────────┐
│ TYPE   │ NODE   │
│ 1 byte │ 1 byte │
└────────┴────────┘

TYPE: Message type (see table below)
NODE: Sender ID (0=GCS, 1=Bird, 2=Chick1, 3=Chick2, 4-7=Orbs)

═══════════════════════════════════════════════════════════════
```

## 6.2 Message Types

```
V1 MESSAGE TYPES
═══════════════════════════════════════════════════════════════

TYPE   NAME        SIZE    DESCRIPTION
────────────────────────────────────────────────────────────────
0x01   TELEM       16B     Compact telemetry
0x02   CMD         4B      Command code
0x03   ACK         3B      Acknowledgment
0x04   TGT         12B     Target coordinates
0x05   STATUS      6B      System status
0x06   ALERT       4B      Priority alert
0x07   SDR         20B     SDR summary data
0x08   PING        2B      Heartbeat/keepalive

0xFE   TEXT        var     ASCII text (emergency only)
0xFF   RAW         var     Raw binary data

═══════════════════════════════════════════════════════════════
```

## 6.3 Telemetry Message (0x01)

```
COMPACT TELEMETRY - 16 BYTES TOTAL
═══════════════════════════════════════════════════════════════

BYTE    FIELD           ENCODING                    RANGE
────────────────────────────────────────────────────────────────
0       TYPE            0x01                        -
1       NODE            0-7                         -
2-4     LAT             (lat+90)*46603 as uint24    ±90°, ~2.4m res
5-7     LON             (lon+180)*23301 as uint24   ±180°, ~4.8m res
8-9     ALT             altitude in decimeters      0-6553m
10      HDG             heading/2 as uint8          0-360° (2° res)
11      SPD             speed*4 as uint8            0-63 m/s
12      BATT            percentage                  0-100%
13      MODE            flight mode code            see table
14      FLAGS           status flags (bitfield)     see table
15      SEQ             sequence number             0-255

EXAMPLE:
Position: 37.7749°N, 122.4194°W, 100m
Encoded:  01 01 8A3B2F 4D6E1A 03E8 57 3C 55 03 00 2A

Total: 16 bytes vs ~120 bytes JSON = 7.5x compression

═══════════════════════════════════════════════════════════════
```

## 6.4 Flight Mode Codes

```
MODE CODES (1 byte)
═══════════════════════════════════════════════════════════════

CODE    MODE            DESCRIPTION
────────────────────────────────────────────────────────────────
0x00    DISARMED        Motors disarmed
0x01    MANUAL          Full manual control
0x02    STABILIZE       Attitude stabilization
0x03    FBWA            Fly-by-wire A (ArduPlane)
0x04    FBWB            Fly-by-wire B
0x05    AUTO            Autonomous mission
0x06    LOITER          Hold position
0x07    RTL             Return to launch
0x08    GUIDED          GCS-guided flight
0x09    LAND            Landing
0x0A    TAKEOFF         Taking off

0x10    ACRO            Acro mode (quads)
0x11    ALTHOLD         Altitude hold
0x12    POSHOLD         Position hold

0xFF    UNKNOWN         Unknown/error

═══════════════════════════════════════════════════════════════
```

## 6.5 Status Flags

```
FLAGS BITFIELD (1 byte)
═══════════════════════════════════════════════════════════════

BIT     FLAG            MEANING WHEN SET
────────────────────────────────────────────────────────────────
0       GPS_OK          GPS has fix
1       ARMED           Motors armed
2       IN_AIR          Currently flying
3       LOW_BATT        Battery warning
4       CRIT_BATT       Battery critical
5       LINK_LOST       Lost link to higher node
6       ERROR           System error active
7       PAYLOAD         Payload attached/active (Orbs)

EXAMPLE: 0x27 = 0010 0111
- GPS_OK (bit 0)
- ARMED (bit 1)
- IN_AIR (bit 2)
- CRIT_BATT (bit 5)

═══════════════════════════════════════════════════════════════
```

## 6.6 Command Message (0x02)

```
COMMAND MESSAGE - 4 BYTES
═══════════════════════════════════════════════════════════════

BYTE    FIELD           DESCRIPTION
────────────────────────────────────────────────────────────────
0       TYPE            0x02
1       TARGET          Destination node (0xFF = broadcast)
2       CMD_CODE        Command (see table)
3       PARAM           Command parameter (optional)

COMMAND CODES:
────────────────────────────────────────────────────────────────
CODE    COMMAND         PARAM MEANING
────────────────────────────────────────────────────────────────
0x01    ARM             0=disarm, 1=arm
0x02    RTL             -
0x03    LAND            -
0x04    LOITER          -
0x05    RESUME          Resume mission
0x06    HOLD            Pause mission
0x07    MODE            Mode code (see 6.4)
0x08    DROP            Orb index (1-4)
0x09    SCAN_START      Band index
0x0A    SCAN_STOP       -
0x0B    REPORT          Request telemetry burst

0xFE    REBOOT          Confirmation code (0xAA)
0xFF    EMERGENCY       0=cancel, 1=RTL all, 2=land all

EXAMPLE: Command Bird to RTL
Encoded: 02 01 02 00

═══════════════════════════════════════════════════════════════
```

## 6.7 Target Message (0x04)

```
TARGET COORDINATES - 12 BYTES
═══════════════════════════════════════════════════════════════

Used to send target coordinates to Orbs or waypoints to drones.

BYTE    FIELD           ENCODING
────────────────────────────────────────────────────────────────
0       TYPE            0x04
1       TARGET_NODE     Recipient (4-7 for Orbs)
2-4     LAT             uint24 encoded (same as TELEM)
5-7     LON             uint24 encoded
8-9     ALT             Altitude in decimeters
10      ACTION          0=navigate, 1=orbit, 2=attack
11      PARAM           Radius/timeout/etc

EXAMPLE: Target Orb 1 to coordinates
Encoded: 04 04 8A3B2F 4D6E1A 0000 02 00

═══════════════════════════════════════════════════════════════
```

## 6.8 SDR Summary Message (0x07)

```
SDR SUMMARY - 20 BYTES
═══════════════════════════════════════════════════════════════

Compact representation of SDR scan results.

BYTE    FIELD           ENCODING
────────────────────────────────────────────────────────────────
0       TYPE            0x07
1       NODE            Sending node
2-3     BAND_START      Start freq in 100kHz units (uint16)
4-5     BAND_END        End freq in 100kHz units (uint16)
6       NUM_PEAKS       Number of signals found (0-5)
7-9     PEAK1_FREQ      Frequency in 10kHz units (uint24)
10      PEAK1_POWER     dBm + 128 (uint8, range -128 to +127)
11-14   PEAK2           Same format
15-18   PEAK3           Same format
19      FLAGS           Scan flags

EXAMPLE: Found signal at 433.92 MHz, -45 dBm
BAND: 400-450 MHz
Encoded: 07 02 0FA0 1194 01 A8F8 53 ...

═══════════════════════════════════════════════════════════════
```

## 6.9 Python Encoder/Decoder

```python
# codeword.py
# V1 Codeword Protocol Implementation

import struct
from dataclasses import dataclass
from typing import Optional

# Message types
MSG_TELEM = 0x01
MSG_CMD = 0x02
MSG_ACK = 0x03
MSG_TGT = 0x04
MSG_STATUS = 0x05
MSG_ALERT = 0x06
MSG_SDR = 0x07
MSG_PING = 0x08
MSG_TEXT = 0xFE
MSG_RAW = 0xFF

@dataclass
class Telemetry:
    node: int
    lat: float
    lon: float
    alt: float      # meters
    heading: int    # degrees
    speed: float    # m/s
    battery: int    # percent
    mode: int
    flags: int
    seq: int

def encode_coord24(value: float, offset: float, scale: float) -> bytes:
    """Encode coordinate as 24-bit unsigned integer"""
    encoded = int((value + offset) * scale)
    return struct.pack('>I', encoded)[1:4]  # Take lower 3 bytes

def decode_coord24(data: bytes, offset: float, scale: float) -> float:
    """Decode 24-bit coordinate back to float"""
    encoded = struct.unpack('>I', b'\x00' + data)[0]
    return (encoded / scale) - offset

def encode_telemetry(telem: Telemetry) -> bytes:
    """Encode telemetry to 16-byte codeword"""
    msg = bytes([MSG_TELEM, telem.node])
    msg += encode_coord24(telem.lat, 90, 46603)
    msg += encode_coord24(telem.lon, 180, 23301)
    msg += struct.pack('>H', int(telem.alt * 10))  # decimeters
    msg += bytes([
        int(telem.heading / 2) & 0xFF,
        int(telem.speed * 4) & 0xFF,
        telem.battery & 0xFF,
        telem.mode & 0xFF,
        telem.flags & 0xFF,
        telem.seq & 0xFF
    ])
    return msg

def decode_telemetry(data: bytes) -> Optional[Telemetry]:
    """Decode 16-byte codeword to telemetry"""
    if len(data) < 16 or data[0] != MSG_TELEM:
        return None

    return Telemetry(
        node=data[1],
        lat=decode_coord24(data[2:5], 90, 46603),
        lon=decode_coord24(data[5:8], 180, 23301),
        alt=struct.unpack('>H', data[8:10])[0] / 10.0,
        heading=data[10] * 2,
        speed=data[11] / 4.0,
        battery=data[12],
        mode=data[13],
        flags=data[14],
        seq=data[15]
    )

def encode_command(target: int, cmd_code: int, param: int = 0) -> bytes:
    """Encode command message (4 bytes)"""
    return bytes([MSG_CMD, target, cmd_code, param])

def encode_target(target_node: int, lat: float, lon: float,
                  alt: float, action: int = 0, param: int = 0) -> bytes:
    """Encode target coordinates (12 bytes)"""
    msg = bytes([MSG_TGT, target_node])
    msg += encode_coord24(lat, 90, 46603)
    msg += encode_coord24(lon, 180, 23301)
    msg += struct.pack('>H', int(alt * 10))
    msg += bytes([action, param])
    return msg

# Command codes
CMD_ARM = 0x01
CMD_RTL = 0x02
CMD_LAND = 0x03
CMD_LOITER = 0x04
CMD_RESUME = 0x05
CMD_HOLD = 0x06
CMD_MODE = 0x07
CMD_DROP = 0x08
CMD_SCAN_START = 0x09
CMD_SCAN_STOP = 0x0A
CMD_REPORT = 0x0B
CMD_REBOOT = 0xFE
CMD_EMERGENCY = 0xFF

# Node IDs
NODE_GCS = 0
NODE_BIRD = 1
NODE_CHICK1 = 2
NODE_CHICK2 = 3
NODE_ORB1 = 4
NODE_ORB2 = 5
NODE_ORB3 = 6
NODE_ORB4 = 7
NODE_BROADCAST = 0xFF

# Example usage
if __name__ == "__main__":
    # Encode telemetry
    telem = Telemetry(
        node=NODE_BIRD,
        lat=37.7749,
        lon=-122.4194,
        alt=100.0,
        heading=270,
        speed=15.5,
        battery=85,
        mode=0x05,  # AUTO
        flags=0x07, # GPS_OK + ARMED + IN_AIR
        seq=42
    )

    encoded = encode_telemetry(telem)
    print(f"Telemetry ({len(encoded)} bytes): {encoded.hex()}")

    # Decode it back
    decoded = decode_telemetry(encoded)
    print(f"Decoded: lat={decoded.lat:.4f}, lon={decoded.lon:.4f}, alt={decoded.alt}m")

    # Encode command
    cmd = encode_command(NODE_BIRD, CMD_RTL)
    print(f"RTL Command ({len(cmd)} bytes): {cmd.hex()}")

    # Encode target for Orb
    target = encode_target(NODE_ORB1, 37.7750, -122.4200, 0, action=2)
    print(f"Target ({len(target)} bytes): {target.hex()}")
```

---

# 7. V2 High-Fidelity Upgrade

## 7.1 V2 Goals

When V1 is working and you need more bandwidth:

| Requirement | V1 Solution | V2 Upgrade |
|-------------|-------------|------------|
| More telemetry data | Codewords | Full JSON via mLRS relay |
| Higher update rate | 1-2 Hz | 5-10 Hz |
| Raw SDR data | Summaries only | Stream via mLRS |
| Video to Chicks | Not possible | WiFi direct link |

## 7.2 V2 Architecture Options

```
V2 UPGRADE PATHS
═══════════════════════════════════════════════════════════════

OPTION A: mLRS on Every Node
──────────────────────────────────────────────────────────────
Add dedicated mLRS modules to Chicks for direct GCS link.

    GCS ◄───mLRS───► Bird    (existing)
    GCS ◄───mLRS───► Chick1  (new link)
    GCS ◄───mLRS───► Chick2  (new link)

Pros: 50+ kbps to each node
Cons: More hardware, frequency coordination needed

OPTION B: mLRS Relay Through Bird
──────────────────────────────────────────────────────────────
Bird receives Chick data via mesh, forwards via mLRS.

    Chick1 ──mesh──► Bird ──mLRS──► GCS
    Chick2 ──mesh──► Bird ──mLRS──► GCS

Pros: Uses existing hardware, simpler
Cons: Limited by mesh bandwidth to Bird

OPTION C: Hybrid Frequency Plan
──────────────────────────────────────────────────────────────
Use different LoRa frequencies for mLRS vs Meshtastic.

    mLRS:       902-915 MHz
    Meshtastic: 915-928 MHz

Pros: No interference, full bandwidth both systems
Cons: Antenna considerations

RECOMMENDATION: Start with Option B, upgrade to A if needed

═══════════════════════════════════════════════════════════════
```

## 7.3 V2 Message Framing

For V2, add an extended message type that allows larger payloads:

```
V2 EXTENDED MESSAGE FORMAT
═══════════════════════════════════════════════════════════════

For messages >32 bytes, use fragmentation:

HEADER (4 bytes):
┌────────┬────────┬────────┬────────┐
│ TYPE   │ NODE   │ SEQ    │ FRAG   │
│ 0xF0   │ 1 byte │ 1 byte │ 1 byte │
└────────┴────────┴────────┴────────┘

FRAG byte:
- High nibble: fragment index (0-15)
- Low nibble: total fragments (1-16)

Example: Fragment 2 of 4 = 0x24

This allows payloads up to 237 * 16 = 3,792 bytes
(reassembled from multiple Meshtastic packets)

═══════════════════════════════════════════════════════════════
```

---

# 8. Hardware Components

## 8.1 Complete BOM - All Layers

```
COMMUNICATION HARDWARE BOM
═══════════════════════════════════════════════════════════════

LAYER 1: ELRS (Already in main design)
──────────────────────────────────────────────────────────────
Qty  Item                              You Have?   Cost
────────────────────────────────────────────────────────────────
1    RadioMaster TX16S                 YES         $0
1    RadioMaster RP3 (Bird)            NO          $25
2    RadioMaster RP2 (Chicks)          NO          $36
                                       ELRS Total: $61

LAYER 2: mLRS (New - Bird Telemetry)
──────────────────────────────────────────────────────────────
Qty  Item                              Source      Cost
────────────────────────────────────────────────────────────────
1    MatekSys mR900-30-TX              Matek       $40
     (GCS transmitter, 1W)
1    MatekSys mR900-22-RX              Matek       $25
     (Bird receiver)
2    915MHz SMA Antenna                Amazon      $10
                                       mLRS Total: $75

LAYER 3: Meshtastic (Mesh Backbone)
──────────────────────────────────────────────────────────────
Qty  Item                              Source      Cost
────────────────────────────────────────────────────────────────
1    LILYGO T-Beam v1.2 915MHz (GCS)   AliExpress  $35
3    Heltec WiFi LoRa 32 V3 915MHz     Amazon      $66
     (Bird + Chick1 + Chick2)
4    18650 Battery (T-Beam)            Amazon      $5
4    915MHz SMA Antenna                Amazon      $12
                                       Mesh Total: $118

BENCH TESTING (Extra for Dev)
──────────────────────────────────────────────────────────────
2    Extra Heltec LoRa 32              Amazon      $44
1    USB Hub 4-port                    Amazon      $15
     USB cables, adapters              Amazon      $15
                                       Bench Total: $74

═══════════════════════════════════════════════════════════════
GRAND TOTAL COMMUNICATION HARDWARE:                $328
═══════════════════════════════════════════════════════════════
```

## 8.2 Shopping List by Priority

```
PHASE 1 ORDER (Week 1) - Bench Testing
═══════════════════════════════════════════════════════════════

PRIORITY 1 - mLRS (Long lead time from Matek)
────────────────────────────────────────────────────────────────
□ MatekSys mR900-30-TX                matek.com           $40
□ MatekSys mR900-22-RX                matek.com           $25
□ 915MHz Antenna x2                   Amazon              $10

PRIORITY 2 - Meshtastic Dev Kit
────────────────────────────────────────────────────────────────
□ LILYGO T-Beam v1.2 915MHz x4        AliExpress          $140
  (Get 4 for full swarm testing)
□ 18650 Battery 3000mAh x4            Amazon              $20
□ 915MHz SMA Antenna x4               Amazon              $12
□ USB-C cables x4                     Amazon              $8

PRIORITY 3 - Bench Accessories
────────────────────────────────────────────────────────────────
□ Powered USB Hub 4-port              Amazon              $15
□ USB serial adapters                 Amazon              $10

                                      PHASE 1 TOTAL:      $280

PHASE 2 ORDER (Week 3) - Flight Hardware
═══════════════════════════════════════════════════════════════
□ Heltec WiFi LoRa 32 V3 x3           Amazon              $66
  (Smaller form factor for drones)
□ USB OTG cables for Pi               Amazon              $6
□ SMA extension cables                Amazon              $9
□ High-gain antenna for GCS           Amazon              $15

                                      PHASE 2 TOTAL:      $96

═══════════════════════════════════════════════════════════════
```

## 8.3 Where to Buy

| Item | Best Source | Notes |
|------|-------------|-------|
| MatekSys mLRS | matek.com | Direct from manufacturer |
| LILYGO T-Beam | AliExpress/lilygo.cc | Official store best price |
| Heltec LoRa32 | Amazon | Fast shipping, slightly higher price |
| Antennas | Amazon | "915MHz LoRa antenna SMA" |
| Batteries | Amazon | Get protected 18650 cells |

---

# 9. Security & Encryption

## 9.1 Encryption by Layer

| Layer | Protocol | Encryption | Key Management |
|-------|----------|------------|----------------|
| ELRS | Proprietary | Binding phrase | Set once in TX/RX |
| mLRS | AES-128-CTR | Bind phrase | Set during bind |
| Meshtastic | AES-256-CTR | PSK | Configure all nodes |

## 9.2 Key Setup Procedure

```
SECURITY CONFIGURATION
═══════════════════════════════════════════════════════════════

STEP 1: ELRS Binding Phrase (Already configured)
────────────────────────────────────────────────────────────────
In RadioMaster TX and all ELRS RX firmware:
  Binding Phrase: "YourSecretPhrase123"

This prevents other ELRS systems from controlling your drones.

STEP 2: mLRS Bind Phrase
────────────────────────────────────────────────────────────────
During mLRS binding, set a phrase (both TX and RX must match):
  Bind Phrase: "SwarmBird2026"

The phrase is hashed to create the AES-128 key.

STEP 3: Meshtastic PSK
────────────────────────────────────────────────────────────────
Generate a strong key:
  $ meshtastic --genkey

Output: YjE2ZjNiNGM1ZjZhN2I4Yzlk...

Apply to ALL mesh nodes:
  $ meshtastic --ch-set psk base64:YjE2ZjNi... --ch-index 0

IMPORTANT:
- Store PSK securely (password manager)
- If any node is compromised, re-key all nodes
- Don't use default Meshtastic key (it's public)

═══════════════════════════════════════════════════════════════
```

## 9.3 Security Considerations

| Threat | Mitigation |
|--------|------------|
| Eavesdropping | All links encrypted (AES) |
| Replay attacks | Per-packet nonce/counter |
| Jamming | Frequency hopping (ELRS), spread spectrum (LoRa) |
| Physical capture | Node compromise reveals PSK - re-key others |
| Signal tracking | LoRa spread spectrum harder to DF than narrow FM |

---

# 10. Implementation Roadmap

## 10.1 Phase 1 Schedule

```
PHASE 1: BENCH INTEGRATION
═══════════════════════════════════════════════════════════════

WEEK 1: Hardware Arrival + mLRS Setup
────────────────────────────────────────────────────────────────
Day 1-2:
  □ Order all Phase 1 hardware
  □ Flash Meshtastic to T-Beams (while waiting)
  □ Test Meshtastic mesh on bench

Day 3-5:
  □ mLRS arrives - flash firmware
  □ Bind mLRS TX/RX pair
  □ Test mLRS with MAVLink passthrough
  □ Verify 50+ kbps throughput

Day 6-7:
  □ Integrate mLRS with QGroundControl
  □ Test full telemetry stream
  □ Test command/control path

WEEK 2: Meshtastic + Codeword Development
────────────────────────────────────────────────────────────────
Day 8-10:
  □ Configure Meshtastic channel + encryption
  □ Write codeword encoder/decoder (Python)
  □ Test codeword transmission between nodes

Day 11-14:
  □ Build mesh bridge service for Pi 5 (simulated)
  □ Build mesh bridge service for Pi (simulated)
  □ Test full swarm message flow on bench
  □ Document latency and throughput

WEEK 3-4: Integration Testing
────────────────────────────────────────────────────────────────
  □ Connect mLRS to actual Pixhawk
  □ Connect Meshtastic to Pi 5
  □ Test both links simultaneously
  □ Verify no interference between 915MHz systems
  □ Range test mLRS (ground test)
  □ Range test Meshtastic (ground test)

═══════════════════════════════════════════════════════════════
```

## 10.2 Milestone Checklist

| Milestone | Criteria | Target |
|-----------|----------|--------|
| mLRS working | QGC sees telemetry via mLRS | Week 1 |
| Mesh working | 4 nodes see each other | Week 1 |
| Codewords working | Encode/decode telemetry | Week 2 |
| Integration | Both systems on Bird hardware | Week 3 |
| Range verified | >1km both systems | Week 4 |

## 10.3 Success Criteria

```
V1 COMPLETE WHEN:
═══════════════════════════════════════════════════════════════

□ mLRS provides 50+ kbps MAVLink to Bird
□ QGroundControl full function via mLRS
□ Meshtastic mesh connects all nodes
□ Codeword telemetry updating at 1+ Hz per node
□ Commands delivered in <500ms via mesh
□ All links encrypted
□ Range >2km for both systems
□ No interference between mLRS and Meshtastic

═══════════════════════════════════════════════════════════════
```

---

# Appendix A: Quick Reference Card

```
SWARM COMMUNICATION QUICK REFERENCE
═══════════════════════════════════════════════════════════════

LAYER 1: ELRS 2.4GHz
  Purpose:    RC Control only
  Hardware:   RadioMaster TX → RP3/RP2 RX
  Binding:    Use phrase, not button
  Failsafe:   Immediate detection

LAYER 2: mLRS 915MHz
  Purpose:    Bird telemetry + commands
  Hardware:   MatekSys TX → RX
  Data rate:  53-91 kbps
  Encryption: AES-128

LAYER 3: Meshtastic 915MHz
  Purpose:    Mesh backbone
  Hardware:   T-Beam (GCS), Heltec (drones)
  Data rate:  1-11 kbps
  Encryption: AES-256

CODEWORD TYPES:
  0x01 TELEM   16B  Position + status
  0x02 CMD      4B  Command code
  0x03 ACK      3B  Acknowledgment
  0x04 TGT     12B  Target coordinates
  0x07 SDR     20B  SDR summary

NODE IDS:
  0 = GCS
  1 = Bird
  2 = Chick1
  3 = Chick2
  4-7 = Orbs

═══════════════════════════════════════════════════════════════
```

---

**Document Control**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial Meshtastic-only design |
| 2.0 | Jan 2026 | Added mLRS layer, codeword protocol, V2 path |

---

*End of Document*
