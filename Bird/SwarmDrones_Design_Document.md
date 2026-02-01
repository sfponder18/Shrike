# Swarm Drone System - Prototype Phase
## Minimal Viable Prototype: 1 Bird, 2 Chicks, 4 Orbs

**Document Version:** 3.0
**Date:** January 2026
**Budget Target:** Under $3,000

---

# Table of Contents

1. [Overview](#1-overview)
2. [Bill of Materials](#2-bill-of-materials)
3. [Bird Build Guide](#3-bird-build-guide)
4. [Chick Setup Guide](#4-chick-setup-guide)
5. [Orb Development](#5-orb-development)
6. [GCS Setup](#6-gcs-setup)
7. [Concept of Operations](#7-concept-of-operations)
8. [Network Architecture](#8-network-architecture)
9. [Development Timeline](#9-development-timeline)
10. [Next Steps](#10-next-steps)

---

# 1. Overview

## 1.1 Prototype Objectives

| Objective | Description |
|-----------|-------------|
| Bird ISR | Long-endurance fixed-wing with video + SIGINT capability |
| Chick Recon | COTS multirotor with spectrum monitoring |
| Orb Strike | GPS-guided glide munition proof-of-concept |
| Integration | Independent launch, shared airspace operations |

## 1.2 Design Philosophy

- **COTS First**: Buy off-the-shelf where possible, especially Chicks
- **Budget Conscious**: Under $3k total, maximize digital work
- **Iterate Fast**: Get flying quickly, improve incrementally
- **Independent Ops**: No docking - Bird and Chicks launch separately

## 1.3 Equipment You Already Have

| Item | Saves |
|------|-------|
| HackRF One | ~$340 |
| RadioMaster TX | ~$180 |
| 3D Printer | N/A |
| Laptop | ~$600 |
| FPV Goggles | ~$80 |

## 1.4 System Summary

```
PROTOTYPE SYSTEM
═══════════════════════════════════════════════════════════════

     BIRD (Ranger)                    CHICK x2 (BNF Quad)
    ┌─────────────┐                  ┌─────────────┐
    │ Pixhawk 6C  │                  │ BNF FC/ESC  │
    │ Pi 5 │                  │ Pi Zero 2W  │
    │ HackRF SDR  │                  │ RTL-SDR     │
    │ 4G + ELRS   │                  │ ELRS RX     │
    └─────────────┘                  └─────────────┘
          │                                │
          │         WiFi / 4G              │
          └────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │   GCS   │
                    │ Laptop  │
                    └─────────┘

    ORB x4 (ESP32 + 3D Printed)
    ┌─────────────┐
    │ ESP32-S3    │
    │ GPS + IMU   │
    │ 4x Servos   │
    └─────────────┘
    Carried/dropped by Chick

═══════════════════════════════════════════════════════════════
```

---

# 2. Bill of Materials

## 2.1 Bird - Complete BOM

### Airframe

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| Airframe | Volantex Ranger 2000 V2 | Banggood/AliExpress | $145 |
| Spare Props | 2-blade 11x5.5 | Amazon | $12 |

**Ranger 2000 Specs:**
- Wingspan: 2000mm
- Length: 1130mm
- Flying Weight: 1.6-2.2 kg
- Motor included: 3536 brushless
- **Endurance: 2-3 hours** (with appropriate battery)

### Flight Controller

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| Flight Controller | Holybro Pixhawk 6C | Holybro | $220 |
| GPS | Holybro M9N | Holybro | $65 |
| Airspeed Sensor | Holybro ASPD-4525 | Holybro | $45 |
| Power Module | Holybro PM02 | Holybro | $35 |

### Companion Computer + SDR

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| Pi 5 Nano 8GB | Developer Kit | NVIDIA/Arrow | $499 |
| NVMe Storage | 256GB | Amazon | $30 |
| Carrier Board | Included with Dev Kit | - | - |
| HackRF One | **Already Owned** | - | $0 |
| HackRF Antenna | ANT500 + telescopic | - | $20 |

**Pi 5 Nano Specs:**
- 40 TOPS AI performance
- 1024-core Ampere GPU
- 8GB LPDDR5
- Power: 7-15W

### Communications

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| 4G Modem | Quectel EC25 USB | AliExpress | $42 |
| 4G Antenna | External LTE | Amazon | $15 |
| ELRS RX | RadioMaster RP3 | GetFPV | $25 |
| ELRS Antenna | Immortal-T | GetFPV | $12 |
| SiK Radio | Holybro 915MHz 500mW | Holybro | $45 |

### Video

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| FPV Camera | RunCam Phoenix 2 | GetFPV | $35 |
| Servo Gimbal | 2-axis pan/tilt | Amazon | $25 |

### Power System

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| Battery | 5000mAh 4S 50C x2 | Amazon | $90 |
| BEC 5V 5A | Matek UBEC | Amazon | $12 |
| BEC 12V 3A | Pololu D24V30F12 | Pololu | $15 |
| Power Dist | XT60 harness | Amazon | $10 |
| Battery Alarm | Low voltage buzzer | Amazon | $5 |

### Servos & Misc

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| Servos | Emax ES08MA x4 (if needed) | Amazon | $24 |
| Wiring | Silicone wire kit | Amazon | $15 |
| Connectors | XT60, JST, Dupont kit | Amazon | $15 |
| Mounting | M3 hardware, standoffs | Amazon | $10 |
| Velcro/Tape | Battery straps, foam | Amazon | $10 |

### Bird BOM Summary

| Category | Cost |
|----------|------|
| Airframe | $157 |
| Flight Controller | $365 |
| Companion Computer | $529 |
| Communications | $139 |
| Video | $60 |
| Power | $132 |
| Servos/Misc | $74 |
| **BIRD TOTAL** | **$1,456** |

---

## 2.2 Chicks (x2) - Complete BOM

### Base Quad (BNF)

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| BNF Quad | iFlight Nazgul5 V2 Analog | GetFPV | $230 |
| ELRS RX | RadioMaster RP2 | GetFPV | $18 |

**Nazgul5 V2 Includes:**
- Frame: 5" X-frame
- Motors: XING-E 2207 1800KV
- ESC: SucceX-E 45A 4-in-1
- FC: SucceX-E F4
- VTX: Force VTX 600mW
- Camera: Included analog

**Alternative BNF Options:**
- GEPRC Mark5 Analog: ~$270
- Diatone Roma F5: ~$250
- iFlight Nazgul Evoque F5: ~$280

### Companion Computer + SDR

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| Raspberry Pi Zero 2W | Quad-core, WiFi | RPi Foundation | $15 |
| MicroSD 32GB | Industrial rated | Amazon | $12 |
| RTL-SDR Blog V4 | R828D tuner | RTL-SDR.com | $40 |
| SDR Antenna | Telescopic whip | Included | $0 |
| USB OTG Cable | Micro USB to USB-A | Amazon | $5 |

### Power & Batteries

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| Flight Battery | 1300mAh 6S 100C x3 | Amazon | $105 |
| Pi Power | BEC 5V from FC | - | $0 |

### Mounting & Integration

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| Pi Mount | 3D printed | Filament | $2 |
| SDR Mount | 3D printed | Filament | $2 |
| Antenna Mount | 3D printed | Filament | $1 |
| Wiring | 26AWG silicone | Amazon | $5 |
| Zip Ties/Tape | Misc | Amazon | $3 |

### Per-Chick Summary

| Category | Cost |
|----------|------|
| BNF Quad | $230 |
| ELRS RX | $18 |
| Pi Zero 2W + SD | $27 |
| RTL-SDR | $40 |
| Batteries (3x) | $105 |
| Mounts/Misc | $13 |
| **PER CHICK** | **$433** |

### Chicks Total (x2)

| Item | Cost |
|------|------|
| Chick 1 | $433 |
| Chick 2 | $433 |
| **CHICKS TOTAL** | **$866** |

---

## 2.3 Orbs (x4) - Complete BOM

### Electronics

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| MCU | ESP32-S3-DevKitC-1 | DigiKey | $10 |
| IMU | MPU6050 Module | Amazon | $3 |
| GPS | Beitian BN-180 | Amazon | $15 |
| Barometer | BMP280 Module | Amazon | $2 |

### Guidance & Control

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| Fin Servos | SG90 x4 | Amazon | $6 |
| Servo Wire | Extension cables | Amazon | $2 |

### Power

| Component | Specification | Source | Cost Each |
|-----------|---------------|--------|-----------|
| Battery | 2S 350mAh 35C | Amazon | $8 |
| Connector | JST-PH 2.0 | Amazon | $1 |

### Airframe (3D Printed)

| Component | Material | Filament Cost |
|-----------|----------|---------------|
| Body Tube | PETG | $3 |
| Nose Cone | PETG | $1 |
| Tail Section | PETG | $2 |
| Fin Set (4) | PETG | $2 |
| Hardware | M2 screws | $2 |

### Per-Orb Summary

| Category | Cost |
|----------|------|
| Electronics | $30 |
| Control | $8 |
| Power | $9 |
| Airframe | $10 |
| **PER ORB** | **$57** |

### Orbs Total (x4)

| Item | Cost |
|------|------|
| 4x Orbs | $228 |
| Dev/Proto Board | $15 |
| Extra Components | $20 |
| **ORBS TOTAL** | **$263** |

---

## 2.4 GCS Additions

| Component | Specification | Source | Cost |
|-----------|---------------|--------|------|
| SiK Radio Ground | Holybro 915MHz | Holybro | $25 |
| RTL-SDR Ground | For monitoring | RTL-SDR.com | $40 |
| USB Hub | 4-port powered | Amazon | $15 |
| Cables | USB, adapters | Amazon | $15 |
| **GCS TOTAL** | | | **$95** |

---

## 2.5 Spares & Consumables

| Item | Cost |
|------|------|
| Spare props (Bird) | $15 |
| Spare props (Chick) | $20 |
| Spare battery (Chick) | $35 |
| Spare servos | $15 |
| Filament (1kg PETG) | $25 |
| Wire/connectors | $20 |
| Misc consumables | $20 |
| **SPARES TOTAL** | **$150** |

---

## 2.6 Complete Budget Summary

| Category | Cost |
|----------|------|
| Bird | $1,456 |
| Chicks (x2) | $866 |
| Orbs (x4) | $263 |
| GCS Additions | $95 |
| Spares | $150 |
| **SUBTOTAL** | **$2,830** |
| Contingency (5%) | $142 |
| **TOTAL** | **$2,972** |

**Under $3,000 target**

---

# 3. Bird Build Guide

## 3.1 Ranger 2000 Assembly

The Volantex Ranger 2000 comes mostly assembled. Key steps:

### Airframe Prep
```
RANGER 2000 LAYOUT
═══════════════════════════════════════════════════════════════

        ┌─────────────────────────────────────┐
        │              WING                    │
        │   (removable, plug-in servos)       │
        └─────────────────┬───────────────────┘
                          │
    ┌─────────────────────┴─────────────────────┐
    │               FUSELAGE                     │
    │  ┌─────┐                         ┌─────┐  │
    │  │Motor│    [Payload Bay]        │Tail │  │
    │  │     │    FC, Pi 5, SDR      │Servos│  │
    │  └─────┘                         └─────┘  │
    │         ┌──────────────────┐              │
    │         │    Battery Bay   │              │
    │         └──────────────────┘              │
    └───────────────────────────────────────────┘

Payload Bay Volume: ~150mm x 80mm x 60mm
Sufficient for Pixhawk + Pi 5 stack

═══════════════════════════════════════════════════════════════
```

### Electronics Stack

```
BIRD ELECTRONICS LAYOUT
═══════════════════════════════════════════════════════════════

LAYER 1 (Bottom): Power Distribution
┌─────────────────────────────────────┐
│  PM02 ─── Battery XT60              │
│    │                                │
│    ├─── ESC (motor power)           │
│    ├─── 5V BEC (servos, RX)         │
│    └─── 12V BEC (Pi 5, 4G)        │
└─────────────────────────────────────┘

LAYER 2: Flight Controller
┌─────────────────────────────────────┐
│         PIXHAWK 6C                  │
│  GPS ───┤                ├─── ELRS  │
│  ASPD ──┤                ├─── SiK   │
│  PM02 ──┤                ├─── Servo │
│         │                │          │
│         └───── UART ─────┘          │
│                  │                  │
│              to Pi 5              │
└─────────────────────────────────────┘

LAYER 3: Companion Computer
┌─────────────────────────────────────┐
│       RASPBERRY PI 5 NANO              │
│  USB ───┤                ├─── 4G    │
│  UART ──┤                ├─── HackRF│
│  PWR ───┤                ├─── WiFi  │
│         │                │  (built-in)
│         └───── ETH ──────┘          │
│                  │                  │
│              (optional)             │
└─────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
```

### Wiring Diagram

```
BIRD WIRING
═══════════════════════════════════════════════════════════════

BATTERY (4S 5000mAh)
    │
    └──► PM02 Power Module
            │
            ├──► Pixhawk 6C (power + current sense)
            │
            ├──► ESC ──► Motor
            │
            ├──► 5V BEC ──┬──► Pixhawk servo rail
            │             ├──► ELRS RX
            │             └──► FPV Camera
            │
            └──► 12V BEC ─┬──► Pi 5 (barrel jack)
                          └──► 4G Modem (if 12V version)

PIXHAWK 6C CONNECTIONS:
├── TELEM1 ──► Pi 5 (MAVLink, UART)
├── TELEM2 ──► SiK Radio
├── GPS ────► M9N GPS Module
├── I2C ────► Airspeed Sensor
├── SBUS ───► ELRS RX (RC input)
├── MAIN 1-4 ► Servos (Ail L, Ail R, Elev, Rud)
└── MAIN 5 ──► ESC (throttle)

RASPBERRY PI 5 CONNECTIONS:
├── USB-A ──► HackRF One
├── USB-A ──► 4G Modem
├── UART ───► Pixhawk TELEM1
└── WiFi ───► Built-in (for Chick links)

═══════════════════════════════════════════════════════════════
```

## 3.2 ArduPlane Configuration

### Key Parameters

```
# Basic Aircraft Parameters
SERVO_AUTO_TRIM = 1
ARSPD_TYPE = 4              # I2C MS4525
ARSPD_USE = 1

# Throttle
THR_MIN = 0
THR_MAX = 100
TRIM_THROTTLE = 40
THR_PASS_STAB = 0

# Limits
LIM_PITCH_MAX = 2500        # 25 degrees
LIM_PITCH_MIN = -2500
LIM_ROLL_CD = 5500          # 55 degrees
STALL_PREVENTION = 1

# Navigation
NAVL1_PERIOD = 17
WP_RADIUS = 60
WP_LOITER_RAD = 80

# Failsafe
FS_SHORT_ACTN = 0           # Continue mission
FS_LONG_ACTN = 1            # RTL
FS_SHORT_TIMEOUT = 1.5
FS_LONG_TIMEOUT = 20

# RTL
RTL_ALTITUDE = 100
RTL_AUTOLAND = 1

# Battery Failsafe
BATT_LOW_VOLT = 13.6        # 3.4V/cell for 4S
BATT_CRT_VOLT = 13.2        # 3.3V/cell
BATT_FS_LOW_ACT = 2         # RTL
BATT_FS_CRT_ACT = 1         # Land
```

### Flight Modes (TX Switch)

| Switch Position | Mode | Use |
|-----------------|------|-----|
| 1 | MANUAL | Emergency |
| 2 | FBWA | Launch/Landing |
| 3 | AUTO | Mission |
| 4 | LOITER | Station keeping |
| 5 | RTL | Return home |
| 6 | GUIDED | GCS control |

---

# 4. Chick Setup Guide

## 4.1 BNF Quad Preparation

The iFlight Nazgul5 V2 comes ready to fly. Modifications needed:

### Step 1: Install ELRS Receiver

```
NAZGUL5 V2 FC - SucceX-E F4
═══════════════════════════════════════════════════════════════

     ┌─────────────────────────────────────┐
     │           SucceX-E F4              │
     │                                     │
     │  ┌─────┐                           │
     │  │SBUS │◄── RadioMaster RP2        │
     │  │ TX  │    (solder 3 wires)       │
     │  │ 5V  │    - 5V                   │
     │  │ GND │    - GND                  │
     │  └─────┘    - SBUS                 │
     │                                     │
     │  ┌─────┐                           │
     │  │UART2│◄── Pi Zero 2W             │
     │  │ TX  │    (MAVLink)              │
     │  │ RX  │                           │
     │  └─────┘                           │
     │                                     │
     └─────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
```

### Step 2: Flash Betaflight/ArduPilot

**Option A: Keep Betaflight (Simpler)**
- Bind ELRS receiver
- Configure rates, PIDs
- Enable MSP telemetry for Pi

**Option B: Flash ArduCopter (More Capable)**
- Unlocks GPS modes, waypoints
- MAVLink native
- More complex setup

**Recommendation:** Start with Betaflight, upgrade later if needed.

### Step 3: Mount Pi Zero 2W + RTL-SDR

```
CHICK PAYLOAD MOUNTING
═══════════════════════════════════════════════════════════════

           TOP VIEW
    ┌─────────────────────────┐
    │      Nazgul5 Frame      │
    │   ┌─────────────────┐   │
    │   │   Pi Zero 2W    │   │  ◄── 3D printed mount
    │   │   ┌─────────┐   │   │      on top plate
    │   │   │ RTL-SDR │   │   │
    │   │   └─────────┘   │   │
    │   └─────────────────┘   │
    │  M  ┌─────────┐  M     │
    │  o  │   FC    │  o     │
    │  t  │   ESC   │  t     │
    │  o  └─────────┘  o     │
    │  r              r      │
    └─────────────────────────┘

SIDE VIEW
    ═══════════════════════════
         Pi + SDR (top)
    ─────────────────────────
         FC/ESC (middle)
    ─────────────────────────
         Battery (bottom)
    ═══════════════════════════

Weight Addition: ~70g (Pi + SDR + mount)
Original AUW: ~550g
New AUW: ~620g (still within 5" quad capability)

═══════════════════════════════════════════════════════════════
```

## 4.2 Pi Zero 2W Configuration

### Base Image Setup

```bash
# Flash Raspberry Pi OS Lite (64-bit)
# Enable SSH, set hostname, WiFi

# After first boot:
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y \
    python3-pip \
    rtl-sdr \
    librtlsdr-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad

# Install Python packages
pip3 install \
    pyrtlsdr \
    numpy \
    pymavlink

# Test RTL-SDR
rtl_test -t
```

### RTL-SDR Services

```python
# /home/pi/sdr_scanner.py
# Basic spectrum scanner for Chick

import numpy as np
from rtlsdr import RtlSdr
import json
import socket

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.center_freq = 433e6  # Start frequency
sdr.gain = 'auto'

def scan_band(start_freq, end_freq, step=1e6):
    """Scan frequency band, return peak signals"""
    results = []
    freq = start_freq
    while freq < end_freq:
        sdr.center_freq = freq
        samples = sdr.read_samples(256*1024)
        power = np.abs(samples)**2
        peak_power = 10 * np.log10(np.max(power))
        results.append({
            'freq': freq,
            'power': peak_power
        })
        freq += step
    return results

# Scan common bands
bands = [
    (400e6, 450e6, "UHF"),
    (860e6, 930e6, "ISM/Cell"),
    (2.4e9, 2.5e9, "WiFi/BT"),  # May need upconverter
]

for start, end, name in bands:
    if end < 1.7e9:  # RTL-SDR limit
        results = scan_band(start, end)
        print(f"{name}: {len(results)} samples")
```

## 4.3 Chick-Bird Communication

```
CHICK NETWORK ARCHITECTURE
═══════════════════════════════════════════════════════════════

    CHICK (Pi Zero 2W)                  BIRD (Pi 5)
    ┌─────────────────┐                ┌─────────────────┐
    │  WiFi Client    │◄──── WiFi ────►│  WiFi AP        │
    │  192.168.4.x    │     5GHz       │  192.168.4.1    │
    │                 │                │                 │
    │  Services:      │                │  Services:      │
    │  - MAVLink fwd  │                │  - hostapd      │
    │  - SDR stream   │                │  - MAVProxy     │
    │  - Video stream │                │  - 4G routing   │
    └─────────────────┘                └─────────────────┘
              │                                │
              │                                │
              └──────────► GCS ◄───────────────┘
                        (Laptop)
                        via 4G

Data Flows:
- Chick telemetry: Chick → Bird WiFi → 4G → GCS
- Chick video: Analog VTX → Goggles (direct)
- Chick SDR data: Chick → Bird WiFi → 4G → GCS
- Chick commands: GCS → 4G → Bird → WiFi → Chick

═══════════════════════════════════════════════════════════════
```

---

# 5. Orb Development

## 5.1 Orb Design Overview

```
ORB PHYSICAL LAYOUT
═══════════════════════════════════════════════════════════════

    SIDE VIEW                      CROSS SECTION

    ┌──────┐                           ┌───┐
    │ Nose │ ◄── 3D printed           /     \
    │      │     (ogive shape)       │ ESP32 │
    ├──────┤                         │  IMU  │
    │      │ ◄── Electronics bay     │  GPS  │
    │ Body │     (ESP32, GPS, IMU)   │ Batt  │
    │      │                          \     /
    ├──────┤                           └───┘
    │      │ ◄── Battery bay
    │      │
    ├──────┤
    │ Tail │ ◄── Fin section
    │ ╲  ╱ │     (4x servos + fins)
    └──╲╱──┘

    DIMENSIONS:
    - Total length: 250mm
    - Body diameter: 50mm
    - Fin span: 120mm
    - Weight: ~200g (with battery)

═══════════════════════════════════════════════════════════════
```

## 5.2 Electronics Schematic

```
ORB ELECTRONICS
═══════════════════════════════════════════════════════════════

                    2S LiPo (7.4V)
                         │
                    ┌────┴────┐
                    │ AMS1117 │
                    │  3.3V   │
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ ESP32-S3│    │ BN-180  │    │ MPU6050 │
    │         │◄───│  GPS    │    │  IMU    │
    │  GPIO   │    └─────────┘    └────┬────┘
    │   │     │                        │
    │   │     │◄───────────────────────┘
    │   │     │         I2C
    └───┼─────┘
        │
        │ PWM (4 channels)
        │
    ┌───┴───────────────────────┐
    │   │     │     │     │     │
    ▼   ▼     ▼     ▼     ▼     ▼
   ┌─┐ ┌─┐   ┌─┐   ┌─┐   ┌─┐
   │1│ │2│   │3│   │4│   │BMP│
   └─┘ └─┘   └─┘   └─┘   └───┘
   Fin Servos (SG90)     Baro

ESP32-S3 Pin Assignment:
- GPIO 1:  Servo 1 (Fin A)
- GPIO 2:  Servo 2 (Fin B)
- GPIO 3:  Servo 3 (Fin C)
- GPIO 4:  Servo 4 (Fin D)
- GPIO 17: GPS TX
- GPIO 18: GPS RX
- GPIO 21: I2C SDA (IMU, Baro)
- GPIO 22: I2C SCL

═══════════════════════════════════════════════════════════════
```

## 5.3 3D Printed Airframe

### Print Settings

| Part | Material | Infill | Walls | Notes |
|------|----------|--------|-------|-------|
| Nose Cone | PETG | 15% | 3 | Smooth for aero |
| Body Tube | PETG | 20% | 3 | Slots for fins |
| Tail Section | PETG | 25% | 4 | Servo mounts |
| Fins (x4) | PETG | 100% | - | Solid for strength |

### Assembly

```
ORB ASSEMBLY SEQUENCE
═══════════════════════════════════════════════════════════════

1. ELECTRONICS BAY
   ┌─────────────────────────────────────┐
   │  Install standoffs in body tube    │
   │  Mount ESP32 board                 │
   │  Connect GPS (UART)                │
   │  Connect IMU + Baro (I2C)          │
   │  Route servo wires to tail         │
   └─────────────────────────────────────┘

2. TAIL SECTION
   ┌─────────────────────────────────────┐
   │  Mount 4x SG90 servos              │
   │  Attach fin horns                  │
   │  Connect servo wires               │
   │  Test servo movement               │
   └─────────────────────────────────────┘

3. POWER
   ┌─────────────────────────────────────┐
   │  Install battery in nose section   │
   │  Route power to regulator          │
   │  Add power switch (optional)       │
   └─────────────────────────────────────┘

4. FINAL ASSEMBLY
   ┌─────────────────────────────────────┐
   │  Join nose + body + tail           │
   │  Secure with M2 screws             │
   │  Check CG (should be 30-40% back)  │
   │  Add nose weight if needed         │
   └─────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
```

## 5.4 Guidance Software

### Basic GPS Guidance (ESP32 Arduino)

```cpp
// orb_guidance.ino
// Simple GPS pursuit guidance for Orb

#include <TinyGPS++.h>
#include <Wire.h>
#include <MPU6050.h>
#include <ESP32Servo.h>

// Hardware
TinyGPSPlus gps;
MPU6050 imu;
Servo fin[4];

// Target
double targetLat = 0;
double targetLon = 0;
bool targetSet = false;

// Guidance
const float Kp_pitch = 2.0;
const float Kp_roll = 2.0;
const float Kp_yaw = 1.5;

void setup() {
    Serial.begin(115200);
    Serial1.begin(9600);  // GPS

    Wire.begin();
    imu.initialize();

    // Servos on GPIO 1-4
    for (int i = 0; i < 4; i++) {
        fin[i].attach(i + 1);
        fin[i].write(90);  // Center
    }
}

void loop() {
    // Read GPS
    while (Serial1.available()) {
        gps.encode(Serial1.read());
    }

    // Read IMU
    int16_t ax, ay, az, gx, gy, gz;
    imu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Calculate guidance if target set
    if (targetSet && gps.location.isValid()) {
        double bearing = TinyGPSPlus::courseTo(
            gps.location.lat(), gps.location.lng(),
            targetLat, targetLon
        );

        double distance = TinyGPSPlus::distanceBetween(
            gps.location.lat(), gps.location.lng(),
            targetLat, targetLon
        );

        // Current heading from GPS course
        double heading = gps.course.deg();

        // Heading error
        double headingError = bearing - heading;
        if (headingError > 180) headingError -= 360;
        if (headingError < -180) headingError += 360;

        // Simple proportional control
        float rollCmd = constrain(Kp_roll * headingError, -30, 30);
        float pitchCmd = constrain(Kp_pitch * (distance > 50 ? -10 : 0), -20, 20);

        // Mix to fin servos (X-fin configuration)
        setFins(pitchCmd, rollCmd, 0);
    }

    delay(100);  // 10 Hz update
}

void setFins(float pitch, float roll, float yaw) {
    // X-fin mixing
    // Fin 1: +pitch +roll
    // Fin 2: +pitch -roll
    // Fin 3: -pitch -roll
    // Fin 4: -pitch +roll

    fin[0].write(90 + pitch + roll);
    fin[1].write(90 + pitch - roll);
    fin[2].write(90 - pitch - roll);
    fin[3].write(90 - pitch + roll);
}

// Called when target received (WiFi/Serial)
void setTarget(double lat, double lon) {
    targetLat = lat;
    targetLon = lon;
    targetSet = true;
}
```

## 5.5 Orb Testing Plan

### Ground Tests

| Test | Description | Success Criteria |
|------|-------------|------------------|
| Power-on | Boots, GPS lock | GPS fix <60s |
| Servo sweep | All 4 fins move | Full range, no binding |
| IMU | Attitude reading | Stable when still |
| GPS accuracy | Static position | <5m CEP |

### Drop Tests

| Test | Height | Method | Goal |
|------|--------|--------|------|
| Stability | 3m | Hand drop | Stable glide |
| Guidance | 10m | Pole drop | Tracks to point |
| Full | 30m+ | Chick release | GPS guidance works |

---

# 6. GCS Setup

## 6.1 Software Stack

```
GCS SOFTWARE LAYOUT
═══════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────┐
    │                     LAPTOP                              │
    │                                                         │
    │  ┌─────────────────┐  ┌─────────────────────────────┐  │
    │  │ QGroundControl  │  │       Terminal Windows      │  │
    │  │                 │  │  ┌───────────┐ ┌─────────┐  │  │
    │  │  - Bird map     │  │  │ SDR GUI   │ │ SSH x2  │  │  │
    │  │  - Chick map    │  │  │ (GQRX/    │ │ (Pi's)  │  │  │
    │  │  - Telemetry    │  │  │  SDR++)   │ │         │  │  │
    │  │  - Mission      │  │  └───────────┘ └─────────┘  │  │
    │  └─────────────────┘  └─────────────────────────────┘  │
    │                                                         │
    │  USB Connections:                                       │
    │  ├── SiK Radio (COM port) ──► QGC                      │
    │  ├── RTL-SDR ──► GQRX                                  │
    │  └── 4G Modem ──► Network (Pi 5 link)                │
    │                                                         │
    └─────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
```

## 6.2 Required Software

| Software | Purpose | Link |
|----------|---------|------|
| QGroundControl | Mission planning, telemetry | qgroundcontrol.com |
| GQRX | SDR waterfall display | gqrx.dk |
| SDR++ | Alternative SDR GUI | github.com/AlexandreRouworworma/SDRPlusPlus |
| PuTTY | SSH to Pi/Pi 5 | putty.org |
| VLC | Video streaming | videolan.org |

## 6.3 Connection Setup

### SiK Radio (Backup Telemetry)
```
QGroundControl:
  Comm Links → Add
  Type: Serial
  Port: COMx (SiK radio)
  Baud: 57600
```

### 4G Connection (Primary)
```
Network:
  - Pi 5 creates WiFi hotspot OR
  - Pi 5 connects to 4G, exposes MAVLink port

QGroundControl:
  Comm Links → Add
  Type: UDP
  Port: 14550
  Server: (Pi 5 IP via 4G)
```

---

# 7. Concept of Operations

## 7.1 Prototype Mission Profile

```
PROTOTYPE CONOP
═══════════════════════════════════════════════════════════════

PHASE 1: SETUP (15 min)
├── Deploy GCS (laptop, radios)
├── Power on Bird, verify GPS/links
├── Power on Chicks, verify GPS/links
├── Prep Orbs (charge, GPS lock)
└── Weather check

PHASE 2: BIRD LAUNCH (5 min)
├── Final checks
├── Arm in FBWA mode
├── Hand launch
├── Climb to 100m
└── Switch to AUTO/LOITER

PHASE 3: CHICK LAUNCH (5 min)
├── Position Chick near target area
├── Arm and launch
├── Climb to 50m
├── Verify WiFi link to Bird
└── Begin SDR scan

PHASE 4: ISR OPERATIONS (30-60 min)
├── Bird orbits target area
├── HackRF spectrum monitoring
├── Chick close recon as needed
├── Video streaming to GCS
└── Operator identifies targets

PHASE 5: ORB TEST (if applicable)
├── Chick positions over target
├── Upload coordinates to Orb
├── Manual release command
├── Track Orb descent
└── Assess accuracy

PHASE 6: RECOVERY (15 min)
├── Chicks RTL and land
├── Bird RTL
├── Bird manual landing approach
├── Power down, pack up
└── Data download

═══════════════════════════════════════════════════════════════
```

## 7.2 Emergency Procedures

| Event | Bird Response | Chick Response |
|-------|---------------|----------------|
| 4G lost | Continue on SiK | RTL to launch point |
| RC lost | Continue AUTO, SiK cmds | Land immediately |
| All links lost | RTL after 30s | Land after 10s |
| Low battery | RTL at 25% | Land at 30% |
| GPS lost | FBWA mode, manual fly | Stabilize, descend |

---

# 8. Network Architecture

## 8.1 Communication Links

```
NETWORK TOPOLOGY
═══════════════════════════════════════════════════════════════

                         INTERNET
                             │
                      ┌──────┴──────┐
                      │ Cell Tower  │
                      └──────┬──────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 │
    ┌────────────┐    ┌────────────┐          │
    │   LAPTOP   │    │   BIRD     │          │
    │            │    │ (Pi 5)   │◄─────────┘
    │ QGC ◄──────┼────│            │    4G
    │            │    │ WiFi AP    │
    │ SiK ◄──────┼────│ HackRF    │
    │ Radio      │915M│            │
    │            │    └─────┬──────┘
    │ RTL-SDR    │          │
    │            │          │ WiFi 5GHz
    │ ELRS TX ───┼──┐       │
    └────────────┘  │  ┌────┴────┐
                    │  │         │
                    │  ▼         ▼
              ELRS  │ ┌──────┐ ┌──────┐
              2.4G  └►│CHICK1│ │CHICK2│
                      │Pi+SDR│ │Pi+SDR│
                      └──────┘ └──────┘

Link Summary:
- Bird Primary: 4G (video, telemetry, data)
- Bird Backup: SiK 915MHz (telemetry only)
- Bird RC: ELRS 2.4GHz
- Chick Link: WiFi via Bird
- Chick RC: ELRS 2.4GHz (backup)
- Chick Video: Analog VTX → Goggles

═══════════════════════════════════════════════════════════════
```

## 8.2 Data Flows

| Data | Path | Rate |
|------|------|------|
| Bird telemetry | FC → Pi 5 → 4G → QGC | 10 Hz |
| Bird video | Camera → Pi 5 → 4G → GCS | 720p 30fps |
| Bird SDR | HackRF → Pi 5 → 4G → GCS | Variable |
| Chick telemetry | FC → Pi → WiFi → Bird → 4G → QGC | 5 Hz |
| Chick SDR | RTL-SDR → Pi → WiFi → Bird → 4G → GCS | Samples |
| Commands | QGC → 4G/SiK → Bird FC | On demand |

---

# 9. Development Timeline

## 9.1 Phase Schedule

```
PROTOTYPE DEVELOPMENT TIMELINE (12 weeks)
═══════════════════════════════════════════════════════════════

WEEK 1-2: PROCUREMENT
├── Order all components
├── Setup dev environment (ArduPilot SITL)
├── Design 3D print files for Orb
└── Study ArduPlane/Betaflight docs

WEEK 3-4: BIRD BUILD
├── Assemble Ranger airframe
├── Install Pixhawk, GPS, sensors
├── Wire power system
├── Bench test electronics
└── Configure ArduPlane

WEEK 5-6: BIRD FLIGHT TEST
├── Range test communications
├── First flight (manual)
├── Tune autopilot
├── Test autonomous modes
└── Verify 4G video streaming

WEEK 7-8: CHICK SETUP
├── Unbox BNF quads
├── Install ELRS receivers
├── Mount Pi Zero + RTL-SDR
├── Configure networking
├── Test hover + basic flight

WEEK 9-10: INTEGRATION
├── Test Bird-Chick WiFi link
├── Test SDR data streaming
├── Practice coordinated ops
├── Refine procedures
└── Document issues

WEEK 11-12: ORB DEVELOPMENT
├── Print airframe components
├── Assemble electronics
├── Flash guidance code
├── Ground tests
├── Drop tests
└── Integrate with Chick

═══════════════════════════════════════════════════════════════
```

## 9.2 Milestones

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 2 | Parts ordered | All components in transit |
| 4 | Bird built | Airframe complete, bench tested |
| 6 | Bird flying | Autonomous missions working |
| 8 | Chicks ready | Both quads flying, Pi integrated |
| 10 | Integration | Bird+Chick coordinated ops |
| 12 | Orbs tested | Drop test complete |

---

# 10. Next Steps

## 10.1 Immediate Actions (This Week)

### Order List - Priority 1 (Long Lead)

| Item | Source | Est. Delivery |
|------|--------|---------------|
| Volantex Ranger 2000 | Banggood | 2-3 weeks |
| Pi 5 Nano Dev Kit | Arrow/NVIDIA | 1 week |
| iFlight Nazgul5 V2 x2 | GetFPV | 3-5 days |

### Order List - Priority 2

| Item | Source |
|------|--------|
| Pixhawk 6C + GPS + Airspeed | Holybro |
| ELRS Receivers (RP3, RP2 x2) | GetFPV |
| SiK Radio set | Holybro |
| 4G Modem x2 | AliExpress/Amazon |

### Order List - Priority 3

| Item | Source |
|------|--------|
| Batteries (Bird + Chick) | Amazon |
| Pi Zero 2W x2 | RPi reseller |
| RTL-SDR V4 x2 | rtl-sdr.com |
| ESP32-S3 DevKits x5 | DigiKey |
| Orb components (GPS, IMU) | Amazon |

## 10.2 While Waiting for Parts

1. **Install software:**
   - QGroundControl
   - ArduPilot SITL
   - Betaflight Configurator
   - GQRX or SDR++

2. **Practice in simulation:**
   - Fly ArduPlane SITL
   - Understand flight modes
   - Practice mission planning

3. **Design Orb airframe:**
   - CAD model in Fusion 360/FreeCAD
   - Export STL files
   - Test print components

4. **Prepare Pi images:**
   - Flash Raspberry Pi OS
   - Configure WiFi, SSH
   - Install RTL-SDR drivers
   - Write basic SDR scripts

## 10.3 Key Resources

### Documentation
- ArduPlane: ardupilot.org/plane
- Betaflight: betaflight.com/docs
- Pi 5: developer.nvidia.com/embedded
- RTL-SDR: rtl-sdr.com/about-rtl-sdr

### Communities
- ArduPilot Discord
- RCGroups.com forums
- r/fpv, r/diydrones

---

# Appendix A: Shopping Links

## Complete Shopping List with Links

**Bird - Airframe:**
- Ranger 2000: banggood.com (search "Volantex Ranger 2000")

**Bird - Electronics:**
- Pixhawk 6C: holybro.com/products/pixhawk-6c
- M9N GPS: holybro.com/products/m9n-gps
- Raspberry Pi 5: raspberrypi.com/products/raspberry-pi-5/

**Chicks:**
- Nazgul5 V2: getfpv.com/iflight-nazgul5-v2
- RadioMaster RP2: getfpv.com/radiomaster-rp2

**Communications:**
- RTL-SDR V4: rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
- SiK Radio: holybro.com/products/sik-telemetry-radio-v3

**Orb Components:**
- ESP32-S3: digikey.com (search ESP32-S3-DevKitC)
- BN-180 GPS: amazon.com (search "Beitian BN-180")
- MPU6050: amazon.com (search "MPU6050 module")

---

# Appendix B: 3D Print Files Needed

| File | Description | Priority |
|------|-------------|----------|
| orb_body.stl | Main tube 50mm x 150mm | High |
| orb_nose.stl | Ogive nose cone | High |
| orb_tail.stl | Servo mount section | High |
| orb_fin.stl | Control fin x4 | High |
| pi_mount.stl | Pi Zero mount for Chick | Medium |
| sdr_mount.stl | RTL-SDR mount for Chick | Medium |
| antenna_mount.stl | Whip antenna holder | Low |

---

**Document Control**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial complex design |
| 2.0 | Jan 2026 | Simplified for solo dev |
| 3.0 | Jan 2026 | Minimal prototype phase |

---

*End of Document*
