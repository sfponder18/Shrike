# Orb Controller PCB Specification

## Overview

A simple carrier board that connects:
- ESP32-S3-DevKit C N16R8 (plugs into female headers)
- GY-NEO6MV2 GPS (plugs into female headers)
- GY-521 IMU (plugs into female headers)
- GY-BMP280 Barometer (plugs into female headers)
- 4x Servo connectors (3-pin male headers)
- Battery input (JST-PH 2.0 or screw terminal)

## Board Dimensions

- **Size:** 70mm x 50mm (fits in orb body tube)
- **Layers:** 2 (top and bottom)
- **Thickness:** 1.6mm standard

## Component Placement

```
TOP VIEW (70mm x 50mm)
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ┌─────────────────────────────────────────────────────────────┐   ║
║   │                                                             │   ║
║   │              ESP32-S3-DevKit C N16R8                        │   ║
║   │              (Female headers - board plugs in)              │   ║
║   │                                                             │   ║
║   └─────────────────────────────────────────────────────────────┘   ║
║                                                                      ║
║   ┌─────────┐  ┌─────────┐  ┌─────────┐     [S1] [S2] [S3] [S4]     ║
║   │  GPS    │  │  IMU    │  │  BARO   │      ███  ███  ███  ███     ║
║   │NEO6MV2  │  │ GY-521  │  │ BMP280  │     Servo Connectors        ║
║   └─────────┘  └─────────┘  └─────────┘                              ║
║                                                                      ║
║   [BATT+]  [BATT-]                              [3.3V AMS1117]       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

## Pin Connections

### ESP32-S3-DevKit C Header Pinout

The DevKit C has two rows of pins. We only need to connect specific pins:

**Left Side (directly used):**
| DevKit Pin | GPIO | Function | Connects To |
|------------|------|----------|-------------|
| 3V3 | - | Power out | 3.3V rail |
| GPIO4 | 4 | Servo 1 | S1 signal |
| GPIO5 | 5 | Servo 2 | S2 signal |
| GPIO6 | 6 | Servo 3 | S3 signal |
| GPIO7 | 7 | Servo 4 | S4 signal |
| GPIO8 | 8 | I2C SCL | SCL rail |
| GPIO18 | 18 | I2C SDA | SDA rail |
| GPIO16 | 16 | UART TX | GPS RX |
| GPIO17 | 17 | UART RX | GPS TX |
| GND | - | Ground | GND rail |
| 5V | - | USB power | (optional) |

### Sensor Connections

**GPS (GY-NEO6MV2) - 4 pins:**
| GPS Pin | Connects To |
|---------|-------------|
| VCC | 3.3V rail |
| GND | GND rail |
| TX | ESP32 GPIO17 |
| RX | ESP32 GPIO16 |

**IMU (GY-521) - 5 pins used:**
| IMU Pin | Connects To |
|---------|-------------|
| VCC | 3.3V rail |
| GND | GND rail |
| SCL | SCL rail (GPIO8) |
| SDA | SDA rail (GPIO18) |
| AD0 | GND rail |

*XDA, XCL, INT not connected*

**Barometer (GY-BMP280) - 5 pins used:**
| Baro Pin | Connects To |
|----------|-------------|
| VCC | 3.3V rail |
| GND | GND rail |
| SCL | SCL rail (GPIO8) |
| SDA | SDA rail (GPIO18) |
| CSB | 3.3V rail |

*SDO not connected*

### Servo Connectors (4x 3-pin)

Standard servo pinout (looking at connector):
```
[GND] [VCC] [SIG]
 Brn   Red   Org
```

| Servo | Signal | VCC | GND |
|-------|--------|-----|-----|
| S1 (Top) | GPIO4 | VBATT | GND |
| S2 (Right) | GPIO5 | VBATT | GND |
| S3 (Bottom) | GPIO6 | VBATT | GND |
| S4 (Left) | GPIO7 | VBATT | GND |

### Power

**Battery Input:** 2S LiPo (7.4V nominal)
- VBATT+ → Servo VCC rail, AMS1117 VIN
- VBATT- → GND rail

**3.3V Regulator (AMS1117-3.3V module or SOT-223):**
- VIN ← VBATT+
- VOUT → 3.3V rail
- GND → GND rail

## Net List

```
Net Name    | Connections
------------|--------------------------------------------------
GND         | ESP32 GND, GPS GND, IMU GND, IMU AD0, BARO GND,
            | Servo GND x4, Battery-, AMS1117 GND
3V3         | ESP32 3V3, GPS VCC, IMU VCC, BARO VCC, BARO CSB,
            | AMS1117 VOUT
VBATT       | Battery+, AMS1117 VIN, Servo VCC x4
SDA         | ESP32 GPIO18, IMU SDA, BARO SDA
SCL         | ESP32 GPIO8, IMU SCL, BARO SCL
GPS_TX      | ESP32 GPIO17, GPS TX
GPS_RX      | ESP32 GPIO16, GPS RX
SERVO1      | ESP32 GPIO4, S1 Signal
SERVO2      | ESP32 GPIO5, S2 Signal
SERVO3      | ESP32 GPIO6, S3 Signal
SERVO4      | ESP32 GPIO7, S4 Signal
```

## Header Specifications

| Component | Header Type | Pin Count | Pitch |
|-----------|-------------|-----------|-------|
| ESP32 Left | Female, single row | 20 | 2.54mm |
| ESP32 Right | Female, single row | 20 | 2.54mm |
| GPS | Female, single row | 4 | 2.54mm |
| IMU | Female, single row | 8 | 2.54mm |
| Baro | Female, single row | 6 | 2.54mm |
| Servos x4 | Male, single row | 3 | 2.54mm |
| Battery | JST-PH 2.0 or 2-pos screw terminal | 2 | 2.0mm |

## Design Rules (JLCPCB Compatible)

- Minimum trace width: 0.2mm (use 0.3mm for signals, 0.5mm+ for power)
- Minimum clearance: 0.2mm
- Minimum via drill: 0.3mm
- Via diameter: 0.6mm
- Copper weight: 1oz

## Ordering Notes (JLCPCB)

When ordering:
- Quantity: 5 (minimum)
- Layers: 2
- Dimensions: 70 x 50 mm
- PCB Thickness: 1.6mm
- Surface Finish: HASL (cheapest)
- Copper Weight: 1oz
- Color: Any (green cheapest)

Approximate cost: $2-5 + ~$5-15 shipping
