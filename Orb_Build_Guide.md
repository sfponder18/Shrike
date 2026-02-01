# Orb Build Guide
## GPS-Guided Glide Munition - Step-by-Step Assembly

**Version:** 1.0
**Date:** January 2026
**Build Time:** ~4 hours per Orb (first one longer)

---

# Table of Contents

1. [Parts List & Shopping](#1-parts-list--shopping)
2. [Tools Required](#2-tools-required)
3. [Wiring Diagram](#3-wiring-diagram)
4. [Step-by-Step Assembly](#4-step-by-step-assembly)
5. [Firmware Setup](#5-firmware-setup)
6. [Testing Procedures](#6-testing-procedures)
7. [3D Printed Parts](#7-3d-printed-parts)
8. [Final Assembly](#8-final-assembly)
9. [Troubleshooting](#9-troubleshooting)

---

# 1. Parts List & Shopping

## 1.1 Breakout Boards (Per Orb)

| Component | Product Name | Specs | Link/Search Term |
|-----------|--------------|-------|------------------|
| **MCU** | Seeed XIAO ESP32S3 | Dual-core 240MHz, 8MB Flash, WiFi/BLE, **21x17.5mm** | Amazon/Seeed: "XIAO ESP32S3" |
| **IMU** | GY-521 Module | MPU6050, 6-axis, I2C | Amazon: "GY-521 MPU6050" |
| **GPS** | Beitian BN-180 | UBlox M8N, 10Hz, 25x25mm | Amazon: "BN-180 GPS" |
| **Barometer** | GY-BMP280 | BMP280, I2C/SPI | Amazon: "GY-BMP280" |
| **Voltage Reg** | AMS1117-3.3V Module | 3.3V 1A LDO (for servos) | Amazon: "AMS1117 3.3V module" |

**Why Seeed XIAO ESP32S3:**
- Tiny footprint: 21 x 17.5mm (vs 70x25mm DevKitC)
- Lightweight: ~3g (vs ~10g)
- Built-in USB-C
- Built-in 3.3V regulator for logic
- 11 GPIO pins (we need 8)
- ~$7 each vs ~$10 for DevKitC

## 1.2 Servos & Mechanical

| Component | Product Name | Specs | Qty/Orb |
|-----------|--------------|-------|---------|
| **Fin Servos** | SG90 Micro Servo | 9g, 180°, 4.8V | 4 |
| **Servo Extensions** | 10cm servo wire | JR/Futaba connector | 4 |
| **Control Horns** | Micro horns | Included with SG90 | 4 |

## 1.3 Power Components

| Component | Product Name | Specs | Qty/Orb |
|-----------|--------------|-------|---------|
| **Battery** | 2S 350mAh 35C LiPo | 7.4V, JST-PH | 1 |
| **JST Connector** | JST-PH 2.0 Male | 2-pin | 1 |
| **Power Switch** | SS12D00 Slide Switch | SPDT (optional) | 1 |

## 1.4 Wiring & Connectors

| Component | Qty/Orb | Notes |
|-----------|---------|-------|
| 26AWG silicone wire (multi-color) | 1m | Red, black, yellow, white, green |
| Dupont connectors female | 20 | For breadboard testing |
| JST-PH 2.0 kit | 1 kit | Shared across builds |
| Heat shrink assortment | 1 pack | Shared |
| M2x6mm screws | 10 | Electronics mounting |
| M2x10mm screws | 8 | Servo mounting |
| M2 nuts | 10 | - |
| M2 standoffs 6mm | 4 | PCB mounting |

## 1.5 Complete Shopping List (4 Orbs + Spares)

### Amazon Order

```
AMAZON/SEEED SHOPPING LIST
═══════════════════════════════════════════════════════════════

□ Seeed XIAO ESP32S3                       x6    ~$42
  Search: "Seeed XIAO ESP32S3" or seeedstudio.com
  Direct: https://www.seeedstudio.com/XIAO-ESP32S3-p-5627.html

□ GY-521 MPU6050 Module (pack of 5)        x1    ~$10
  Search: "GY-521 MPU6050 accelerometer"

□ Beitian BN-180 GPS Module                x5    ~$75
  Search: "BN-180 GPS module"

□ GY-BMP280 Barometer (pack of 5)          x1    ~$10
  Search: "BMP280 module GY-BMP280"

□ SG90 Micro Servo (pack of 10)            x2    ~$16
  Search: "SG90 micro servo 9g"

□ AMS1117-5V Module (pack of 10)           x1    ~$6
  Search: "AMS1117 5V regulator module"
  Note: 5V version for servo power from 2S LiPo

□ 2S 350mAh LiPo Battery                   x6    ~$48
  Search: "2S 350mAh 35C lipo JST"

□ JST-PH 2.0 Connector Kit                 x1    ~$12
  Search: "JST PH 2.0 connector kit"

□ 26AWG Silicone Wire Kit                  x1    ~$12
  Search: "26AWG silicone wire kit"

□ Dupont Connector Kit                     x1    ~$10
  Search: "dupont connector kit"

□ M2 Screw/Nut/Standoff Assortment        x1    ~$10
  Search: "M2 screw standoff assortment"

□ Heat Shrink Tubing Kit                   x1    ~$8
  Search: "heat shrink tubing assortment"

□ 5x7cm Prototype PCB (pack of 10)         x1    ~$8
                                          ─────────────
                                   TOTAL:  ~$267

═══════════════════════════════════════════════════════════════
```

### Seeed Direct (Recommended for XIAO)

Best price and availability for XIAO ESP32S3:
- Seeed Studio: seeedstudio.com
- Product: XIAO ESP32S3 (~$6.99 each)
- Also available on Amazon, but often marked up

---

# 2. Tools Required

## 2.1 Essential Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Soldering iron | 60W, temp controlled | Recommended: Pinecil, TS100 |
| Solder | 60/40 or lead-free, 0.8mm | Rosin core |
| Flush cutters | Trimming leads | - |
| Wire strippers | 22-30 AWG | - |
| Multimeter | Continuity, voltage | - |
| Tweezers | SMD work | - |
| Helping hands | Hold PCBs | - |
| USB-C cable | Programming ESP32 | - |

## 2.2 Nice to Have

| Tool | Purpose |
|------|---------|
| Hot air station | Rework |
| Solder wick | Desoldering |
| Flux pen | Better joints |
| PCB holder | Stability |
| Label maker | Wire identification |

## 2.3 3D Printing

| Item | Notes |
|------|-------|
| 3D Printer | PETG capable |
| PETG filament | 1kg, any color |
| Calipers | Measuring parts |
| Sandpaper | 220, 400 grit |
| CA glue | Assembly |

---

# 3. Wiring Diagram

## 3.1 System Block Diagram

```
ORB ELECTRONICS BLOCK DIAGRAM (Seeed XIAO ESP32S3)
═══════════════════════════════════════════════════════════════

                    2S LiPo Battery
                    (7.4V 350mAh)
                         │
                         │ JST-PH
                         ▼
                   ┌───────────┐
         ┌────────┤  SWITCH   ├────────┐
         │        │ (optional)│        │
         │        └───────────┘        │
         │                             │
         │ VIN (7.4V)                  │ GND
         ▼                             ▼
    ┌─────────────────────────────────────┐
    │           AMS1117-3.3V              │
    │  VIN ──────────────────────── VOUT  │
    │                               3.3V  │
    │  GND ──────────────────────── GND   │
    └─────────────────────────────────────┘
         │                             │
         │ 3.3V                        │ GND
         │                             │
    ┌────┴────┬────────┬────────┬──────┴────┐
    │         │        │        │           │
    ▼         ▼        ▼        ▼           │
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐    │
│ XIAO  │ │BN-180 │ │GY-521 │ │BMP280 │    │
│ESP32S3│ │ GPS   │ │ IMU   │ │ Baro  │    │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘    │
    │         │        │        │           │
    │         │        └────┬───┘           │
    │         │             │               │
    │    UART │        I2C  │               │
    │   (D6/D7)       (D4/D5)               │
    │         │             │               │
    │         │             │               │
    │    ┌────┴─────────────┴────┐          │
    │    │                       │          │
    └────┤   XIAO ESP32S3        ├──────────┘
         │   (21 x 17.5mm)       │
         │                       │
         │  D0 (GPIO1) ──► Servo 1  │
         │  D1 (GPIO2) ──► Servo 2  │
         │  D2 (GPIO3) ──► Servo 3  │
         │  D3 (GPIO4) ──► Servo 4  │
         │                       │
         └───────────────────────┘
                    │
              PWM to 4x SG90
              (powered by VIN)

═══════════════════════════════════════════════════════════════
```

## 3.2 Detailed Pinout

### Seeed XIAO ESP32S3 Pinout

```
SEEED XIAO ESP32S3 PINOUT (Top View)
═══════════════════════════════════════════════════════════════

                    USB-C
              ┌───────┴───────┐
              │    ┌─────┐    │
              │    │XIAO │    │
              │    │ESP32│    │
              │    │ S3  │    │
              │    └─────┘    │
              │               │
     D0/GPIO1 ├─●           ●─┤ 5V
     D1/GPIO2 ├─●           ●─┤ GND
     D2/GPIO3 ├─●           ●─┤ 3V3
     D3/GPIO4 ├─●           ●─┤ D10/GPIO9
     D4/GPIO5 ├─●           ●─┤ D9/GPIO8
     D5/GPIO6 ├─●           ●─┤ D8/GPIO7
    D6/GPIO43 ├─●           ●─┤ D7/GPIO44
              │               │
              └───────────────┘
                 21 x 17.5mm

ACTIVE PINS FOR ORB:
═══════════════════════════════════════════════════════════════
Pin   │ Label │ GPIO │ Function      │ Connection
──────┼───────┼──────┼───────────────┼──────────────────────────
Left  │ D0    │ GPIO1│ Servo PWM 1   │ Fin Servo 1 (signal)
Left  │ D1    │ GPIO2│ Servo PWM 2   │ Fin Servo 2 (signal)
Left  │ D2    │ GPIO3│ Servo PWM 3   │ Fin Servo 3 (signal)
Left  │ D3    │ GPIO4│ Servo PWM 4   │ Fin Servo 4 (signal)
Left  │ D4    │ GPIO5│ I2C SDA       │ MPU6050 SDA, BMP280 SDA
Left  │ D5    │ GPIO6│ I2C SCL       │ MPU6050 SCL, BMP280 SCL
Left  │ D6    │GPIO43│ UART TX       │ BN-180 RX (ESP TX out)
Right │ D7    │GPIO44│ UART RX       │ BN-180 TX (ESP RX in)
Right │ 3V3   │ -    │ Power Out     │ (use AMS1117 instead)
Right │ GND   │ -    │ Ground        │ Common ground
Right │ 5V    │ -    │ Power In      │ (not used, battery powered)
═══════════════════════════════════════════════════════════════

NOTE: XIAO has built-in 3.3V regulator but we use external
AMS1117 to handle servo current spikes and sensor load.
```

### BN-180 GPS Pinout

```
BN-180 GPS MODULE
═══════════════════════════════════════════════════════════════

    ┌─────────────────────┐
    │    BN-180 GPS       │
    │   ┌───────────┐     │
    │   │  Antenna  │     │
    │   │   Patch   │     │
    │   └───────────┘     │
    │                     │
    │  VCC  GND  TX  RX   │
    └──┬────┬────┬────┬───┘
       │    │    │    │
       │    │    │    └──► ESP32 GPIO38 (ESP TX)
       │    │    └───────► ESP32 GPIO39 (ESP RX)
       │    └────────────► GND
       └─────────────────► 3.3V

Default Baud: 9600
Protocol: NMEA
Update Rate: 1Hz (configurable to 10Hz)

═══════════════════════════════════════════════════════════════
```

### GY-521 (MPU6050) Pinout

```
GY-521 IMU MODULE
═══════════════════════════════════════════════════════════════

    ┌─────────────────────┐
    │      GY-521         │
    │    ┌────────┐       │
    │    │MPU6050 │       │
    │    └────────┘       │
    │                     │
    │ VCC GND SCL SDA XDA XCL AD0 INT
    └──┬───┬───┬───┬───┬───┬───┬───┬─
       │   │   │   │   │   │   │   │
       │   │   │   │   │   │   │   └─► (not used)
       │   │   │   │   │   │   └─────► GND (addr 0x68)
       │   │   │   │   │   └─────────► (not used)
       │   │   │   │   └─────────────► (not used)
       │   │   │   └─────────────────► ESP32 GPIO21
       │   │   └─────────────────────► ESP32 GPIO14
       │   └─────────────────────────► GND
       └─────────────────────────────► 3.3V

I2C Address: 0x68 (AD0 to GND)
             0x69 (AD0 to VCC)

═══════════════════════════════════════════════════════════════
```

### GY-BMP280 Pinout

```
GY-BMP280 BAROMETER MODULE
═══════════════════════════════════════════════════════════════

    ┌─────────────────────┐
    │     GY-BMP280       │
    │    ┌────────┐       │
    │    │BMP280  │       │
    │    └────────┘       │
    │                     │
    │ VCC  GND  SCL  SDA  CSB  SDO
    └──┬───┬────┬────┬────┬────┬──
       │   │    │    │    │    │
       │   │    │    │    │    └──► (not used, I2C mode)
       │   │    │    │    └───────► 3.3V (I2C mode select)
       │   │    │    └────────────► ESP32 GPIO21 (shared)
       │   │    └─────────────────► ESP32 GPIO14 (shared)
       │   └──────────────────────► GND
       └──────────────────────────► 3.3V

I2C Address: 0x76 (CSB to VCC)
             0x77 (CSB to GND)

═══════════════════════════════════════════════════════════════
```

### SG90 Servo Pinout

```
SG90 SERVO CONNECTIONS
═══════════════════════════════════════════════════════════════

    ┌─────────────┐
    │   SG90      │
    │  ┌─────┐    │
    │  │Motor│    │
    │  └─────┘    │
    │             │
    │  ┌───────┐  │
    │  │Gearbox│  │
    │  └───────┘  │
    │      │      │
    └──────┼──────┘
           │
    ╔══════╧══════╗
    ║  ┌─┬─┬─┐   ║
    ║  │●│●│●│   ║  Wire Colors:
    ║  └─┴─┴─┘   ║  Brown = GND
    ╚════════════╝  Red   = VCC (5V from battery VIN)
         │││        Orange= Signal (PWM)
         │││
         ││└──► Signal (Orange) ──► ESP32 GPIO
         │└───► VCC (Red) ────────► Battery VIN (7.4V OK for SG90)
         └────► GND (Brown) ──────► Common GND

Note: SG90 servos tolerate 4.8-6V but work fine at 7.4V
      for short durations. For reliability, add a 5V BEC.

═══════════════════════════════════════════════════════════════
```

## 3.3 Complete Wiring Table

```
COMPLETE WIRING CONNECTIONS (XIAO ESP32S3)
═══════════════════════════════════════════════════════════════

FROM                    TO                      WIRE COLOR
────────────────────────────────────────────────────────────────
POWER
────────────────────────────────────────────────────────────────
Battery + (7.4V)        AMS1117 VIN             Red
Battery + (7.4V)        Servo VCC (all 4)       Red
Battery -               Common GND               Black
AMS1117 VOUT (3.3V)     XIAO 3V3                Red
AMS1117 VOUT (3.3V)     BN-180 VCC              Red
AMS1117 VOUT (3.3V)     GY-521 VCC              Red
AMS1117 VOUT (3.3V)     BMP280 VCC              Red
AMS1117 VOUT (3.3V)     BMP280 CSB              Red
AMS1117 GND             XIAO GND                Black
AMS1117 GND             All sensor GND          Black

GPS (BN-180)
────────────────────────────────────────────────────────────────
BN-180 TX               XIAO D7 (GPIO44)        Yellow
BN-180 RX               XIAO D6 (GPIO43)        Green
BN-180 VCC              3.3V rail               Red
BN-180 GND              GND rail                Black

IMU (GY-521)
────────────────────────────────────────────────────────────────
GY-521 SDA              XIAO D4 (GPIO5)         Blue
GY-521 SCL              XIAO D5 (GPIO6)         Purple
GY-521 VCC              3.3V rail               Red
GY-521 GND              GND rail                Black
GY-521 AD0              GND rail                Black

BAROMETER (BMP280)
────────────────────────────────────────────────────────────────
BMP280 SDA              XIAO D4 (GPIO5) shared  Blue
BMP280 SCL              XIAO D5 (GPIO6) shared  Purple
BMP280 VCC              3.3V rail               Red
BMP280 GND              GND rail                Black
BMP280 CSB              3.3V rail               Red

SERVOS
────────────────────────────────────────────────────────────────
Servo 1 Signal          XIAO D0 (GPIO1)         Orange
Servo 2 Signal          XIAO D1 (GPIO2)         Orange
Servo 3 Signal          XIAO D2 (GPIO3)         Orange
Servo 4 Signal          XIAO D3 (GPIO4)         Orange
Servo 1-4 VCC           Battery + (7.4V)        Red
Servo 1-4 GND           GND rail                Brown/Black

═══════════════════════════════════════════════════════════════
```

---

# 4. Step-by-Step Assembly

## 4.1 Phase 1: Breadboard Prototype

Before soldering, test everything on a breadboard.

### Step 1.1: Prepare Components

```
BREADBOARD LAYOUT (XIAO ESP32S3)
═══════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────┐
    │ + + + + + + + + + + + + + + + + + + + + + + + + + + + + │ ◄─ Power rail (+)
    │ - - - - - - - - - - - - - - - - - - - - - - - - - - - - │ ◄─ GND rail (-)
    ├─────────────────────────────────────────────────────────┤
    │ a ┌─────────────────────────────────────────────────┐ a │
    │ b │                                                 │ b │
    │ c │    ┌────────┐           ┌────────┐            │ c │
    │ d │    │  XIAO  │           │ BN-180 │            │ d │
    │ e │    │ESP32S3 │           │  GPS   │            │ e │
    │   │    └────────┘           └────────┘            │   │
    │ f │     (tiny!)                                     │ f │
    │ g │    ┌────────┐    ┌────────┐   ┌────────┐      │ g │
    │ h │    │ GY-521 │    │BMP280  │   │AMS1117 │      │ h │
    │ i │    │  IMU   │    │ Baro   │   │  3.3V  │      │ i │
    │ j │    └────────┘    └────────┘   └────────┘      │ j │
    │   └─────────────────────────────────────────────────┘   │
    ├─────────────────────────────────────────────────────────┤
    │ - - - - - - - - - - - - - - - - - - - - - - - - - - - - │
    │ + + + + + + + + + + + + + + + + + + + + + + + + + + + + │
    └─────────────────────────────────────────────────────────┘

Note: XIAO is very small (21x17.5mm) - easily fits on breadboard

═══════════════════════════════════════════════════════════════
```

### Step 1.2: Wire Power

```
ACTION: Connect power circuit

1. Connect AMS1117 module to breadboard
2. Wire battery + to AMS1117 VIN
3. Wire battery - to GND rail
4. Wire AMS1117 VOUT to + power rail (3.3V)
5. Wire AMS1117 GND to - power rail

TEST:
- Connect battery
- Measure voltage on + rail (should be 3.3V ± 0.1V)
- If not 3.3V, check connections
```

### Step 1.3: Connect XIAO ESP32S3

```
ACTION: Insert and power XIAO

1. Insert XIAO ESP32S3 into breadboard
   - It's tiny! Only spans a few rows
   - USB-C port facing outward for programming

2. Connect power:
   - 3V3 pin to + rail (3.3V from AMS1117)
   - GND pin to - rail

3. Connect to computer via USB-C

TEST:
- XIAO power LED should illuminate (orange)
- Device should appear in Device Manager (Windows)
  or `lsusb` (Linux) as "USB JTAG/serial debug unit"
```

### Step 1.4: Connect GPS (BN-180)

```
ACTION: Wire GPS module

1. Place BN-180 on breadboard (antenna facing up)

2. Connect:
   - VCC → 3.3V rail
   - GND → GND rail
   - TX  → XIAO D7 / GPIO44 (yellow wire) - GPS sends TO ESP
   - RX  → XIAO D6 / GPIO43 (green wire)  - GPS receives FROM ESP

TEST (after firmware upload):
- GPS LED should blink (searching)
- GPS LED solid = fix acquired
- Takes 30-60 seconds for first fix outdoors
```

### Step 1.5: Connect IMU (GY-521)

```
ACTION: Wire IMU module

1. Place GY-521 on breadboard

2. Connect:
   - VCC → 3.3V rail
   - GND → GND rail
   - SCL → XIAO D5 / GPIO6 (purple wire)
   - SDA → XIAO D4 / GPIO5 (blue wire)
   - AD0 → GND rail (sets I2C address to 0x68)

TEST (after firmware upload):
- I2C scan should find device at 0x68
```

### Step 1.6: Connect Barometer (BMP280)

```
ACTION: Wire barometer module

1. Place BMP280 on breadboard

2. Connect:
   - VCC → 3.3V rail
   - GND → GND rail
   - SCL → XIAO D5 / GPIO6 (shared with IMU)
   - SDA → XIAO D4 / GPIO5 (shared with IMU)
   - CSB → 3.3V rail (enables I2C mode, address 0x76)

TEST (after firmware upload):
- I2C scan should find device at 0x76
- IMU still at 0x68
```

### Step 1.7: Connect Servos

```
ACTION: Wire servo motors

1. Connect each servo:

   Servo 1 (Fin A - Top):
   - Signal (orange) → XIAO D0 / GPIO1
   - VCC (red) → Battery + (7.4V direct, not 3.3V rail!)
   - GND (brown) → GND rail

   Servo 2 (Fin B - Right):
   - Signal → XIAO D1 / GPIO2
   - VCC → Battery +
   - GND → GND rail

   Servo 3 (Fin C - Bottom):
   - Signal → XIAO D2 / GPIO3
   - VCC → Battery +
   - GND → GND rail

   Servo 4 (Fin D - Left):
   - Signal → XIAO D3 / GPIO4
   - VCC → Battery +
   - GND → GND rail

WARNING:
- Servos draw significant current
- Power directly from battery, NOT the 3.3V rail
- The AMS1117 cannot supply enough current for servos

TEST (after firmware upload):
- Servos should center to 90°
- Sweep test: servos move smoothly 0-180°
```

---

## 4.2 Phase 2: Firmware Upload

### Step 2.1: Install Arduino IDE & ESP32 Support

```
ARDUINO IDE SETUP (for Seeed XIAO ESP32S3)
═══════════════════════════════════════════════════════════════

1. Download Arduino IDE 2.x from arduino.cc

2. Add ESP32 board support:
   - File → Preferences
   - Additional Board Manager URLs:
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

3. Install ESP32 boards:
   - Tools → Board → Boards Manager
   - Search "esp32"
   - Install "esp32 by Espressif Systems" (v2.0.x or later)

4. Select board:
   - Tools → Board → esp32 → XIAO_ESP32S3

5. Configure settings:
   - USB CDC On Boot: Enabled
   - Flash Size: 8MB (8MB Flash)
   - Partition Scheme: Default 4MB with spiffs
   - PSRAM: Disabled (XIAO ESP32S3 base has no PSRAM)

═══════════════════════════════════════════════════════════════
```

### Step 2.2: Install Required Libraries

```
LIBRARY INSTALLATION
═══════════════════════════════════════════════════════════════

Tools → Manage Libraries → Search and Install:

1. TinyGPSPlus (by Mikal Hart)
   - GPS NMEA parsing

2. MPU6050 (by Electronic Cats)
   - IMU driver

3. Adafruit BMP280 Library
   - Barometer driver
   - Also installs Adafruit Unified Sensor

4. ESP32Servo
   - PWM servo control for ESP32

═══════════════════════════════════════════════════════════════
```

### Step 2.3: Upload Test Firmware

```cpp
// orb_test.ino
// Test firmware for Orb components (XIAO ESP32S3)

#include <Wire.h>
#include <TinyGPSPlus.h>
#include <MPU6050.h>
#include <Adafruit_BMP280.h>
#include <ESP32Servo.h>

// Pin definitions for Seeed XIAO ESP32S3
// Using GPIO numbers (D0=GPIO1, D1=GPIO2, etc.)
#define GPS_RX_PIN 44    // D7 - receives FROM GPS TX
#define GPS_TX_PIN 43    // D6 - sends TO GPS RX
#define I2C_SDA 5        // D4
#define I2C_SCL 6        // D5
#define SERVO1_PIN 1     // D0
#define SERVO2_PIN 2     // D1
#define SERVO3_PIN 3     // D2
#define SERVO4_PIN 4     // D3

// Objects
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
MPU6050 mpu;
Adafruit_BMP280 bmp;
Servo servo[4];

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n=== ORB TEST FIRMWARE ===\n");

    // Initialize I2C
    Wire.begin(I2C_SDA, I2C_SCL);
    Serial.println("I2C initialized");

    // Scan I2C bus
    Serial.println("\nI2C Scan:");
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  Found device at 0x%02X\n", addr);
        }
    }

    // Initialize GPS
    gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
    Serial.println("\nGPS Serial initialized");

    // Initialize MPU6050
    mpu.initialize();
    if (mpu.testConnection()) {
        Serial.println("MPU6050 connected!");
    } else {
        Serial.println("MPU6050 FAILED!");
    }

    // Initialize BMP280
    if (bmp.begin(0x76)) {
        Serial.println("BMP280 connected!");
    } else {
        Serial.println("BMP280 FAILED!");
    }

    // Initialize Servos
    servo[0].attach(SERVO1_PIN);
    servo[1].attach(SERVO2_PIN);
    servo[2].attach(SERVO3_PIN);
    servo[3].attach(SERVO4_PIN);
    Serial.println("Servos attached");

    // Center all servos
    for (int i = 0; i < 4; i++) {
        servo[i].write(90);
    }
    Serial.println("Servos centered to 90°\n");

    Serial.println("=== SETUP COMPLETE ===\n");
}

void loop() {
    static unsigned long lastPrint = 0;

    // Read GPS
    while (gpsSerial.available()) {
        gps.encode(gpsSerial.read());
    }

    // Print sensor data every second
    if (millis() - lastPrint > 1000) {
        lastPrint = millis();

        Serial.println("--- Sensor Readings ---");

        // GPS
        Serial.print("GPS: ");
        if (gps.location.isValid()) {
            Serial.printf("%.6f, %.6f", gps.location.lat(), gps.location.lng());
        } else {
            Serial.print("No fix");
        }
        Serial.printf(" (Sats: %d)\n", gps.satellites.value());

        // IMU
        int16_t ax, ay, az, gx, gy, gz;
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        Serial.printf("IMU: Accel(%d, %d, %d) Gyro(%d, %d, %d)\n",
                      ax, ay, az, gx, gy, gz);

        // Barometer
        Serial.printf("Baro: %.1f hPa, %.1f °C\n",
                      bmp.readPressure() / 100.0,
                      bmp.readTemperature());

        Serial.println();
    }

    // Servo sweep test (press 's' in Serial Monitor)
    if (Serial.available()) {
        char c = Serial.read();
        if (c == 's' || c == 'S') {
            Serial.println("Servo sweep test...");
            for (int angle = 90; angle >= 60; angle -= 5) {
                for (int i = 0; i < 4; i++) servo[i].write(angle);
                delay(100);
            }
            for (int angle = 60; angle <= 120; angle += 5) {
                for (int i = 0; i < 4; i++) servo[i].write(angle);
                delay(100);
            }
            for (int angle = 120; angle >= 90; angle -= 5) {
                for (int i = 0; i < 4; i++) servo[i].write(angle);
                delay(100);
            }
            Serial.println("Servo sweep complete");
        }
    }
}
```

### Step 2.4: Verify Test Results

```
EXPECTED TEST OUTPUT
═══════════════════════════════════════════════════════════════

=== ORB TEST FIRMWARE ===

I2C initialized

I2C Scan:
  Found device at 0x68    ◄── MPU6050
  Found device at 0x76    ◄── BMP280

GPS Serial initialized
MPU6050 connected!
BMP280 connected!
Servos attached
Servos centered to 90°

=== SETUP COMPLETE ===

--- Sensor Readings ---
GPS: No fix (Sats: 0)           ◄── Normal indoors
IMU: Accel(1024, -256, 16384) Gyro(12, -8, 4)   ◄── Values change when moved
Baro: 1013.2 hPa, 24.5 °C       ◄── Should match local conditions

TROUBLESHOOTING:
════════════════════════════════════════════════════════════════
Problem: "MPU6050 FAILED!"
- Check I2C wiring (SDA/SCL swapped?)
- Check AD0 pin is connected to GND
- Try I2C scan to verify address

Problem: "BMP280 FAILED!"
- Check CSB is connected to 3.3V
- Try address 0x77 instead of 0x76
- Verify I2C connections

Problem: GPS never gets fix
- Take outside with clear sky view
- Wait 1-2 minutes for cold start
- Check TX/RX not swapped

Problem: Servos don't move
- Check battery is connected
- Verify GPIO pins correct
- Servos need 5V+, not 3.3V

═══════════════════════════════════════════════════════════════
```

---

## 4.3 Phase 3: Permanent Assembly

Once breadboard testing passes, solder permanent connections.

### Step 3.1: Prepare Protoboard

```
PROTOBOARD LAYOUT (5x7cm) - XIAO ESP32S3
═══════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────┐
    │  ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○  │  ◄─ 3.3V
    │  ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○  │  ◄─ GND
    │  ○ ○ ┌────────┐  ┌─────────┐ ┌─────────┐ ○ ○  │
    │  ○ ○ │  XIAO  │  │ GY-521  │ │ BMP280  │ ○ ○  │
    │  ○ ○ │ESP32S3 │  │  IMU    │ │  Baro   │ ○ ○  │
    │  ○ ○ │(tiny!) │  └─────────┘ └─────────┘ ○ ○  │
    │  ○ ○ └────────┘                          ○ ○  │
    │  ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○  │
    │  ○ ○ ┌─────────┐  ┌──────────────────┐   ○ ○  │
    │  ○ ○ │AMS1117  │  │   GPS Connector  │   ○ ○  │
    │  ○ ○ │  3.3V   │  │    (to BN-180)   │   ○ ○  │
    │  ○ ○ └─────────┘  └──────────────────┘   ○ ○  │
    │  ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○  │
    │                                              │
    │  [Servo1] [Servo2] [Servo3] [Servo4] [Batt]  │
    └──────────────────────────────────────────────┘

Note: XIAO is only 21x17.5mm - leaves lots of room!
Use female headers for XIAO - allows removal for reprogramming.
Or solder directly for minimum weight.

═══════════════════════════════════════════════════════════════
```

### Step 3.2: Soldering Order

```
SOLDERING SEQUENCE
═══════════════════════════════════════════════════════════════

1. POWER SECTION (solder first)
   □ Solder AMS1117 module to board
   □ Solder power rails (3.3V and GND traces)
   □ Solder battery connector (JST-PH)
   □ Test: Verify 3.3V output before proceeding

2. ESP32 HEADERS
   □ Solder female pin headers for ESP32
   □ 2 rows of 20 pins each
   □ Check alignment before soldering all pins

3. I2C BUS
   □ Solder GY-521 module
   □ Solder BMP280 module
   □ Wire SDA bus (both to GPIO21)
   □ Wire SCL bus (both to GPIO14)
   □ Wire power to both

4. GPS CONNECTION
   □ Solder JST connector for GPS cable
   □ Or solder GPS directly (less flexible)
   □ Wire TX/RX to GPIO39/38

5. SERVO CONNECTIONS
   □ Solder 4x 3-pin headers for servos
   □ Wire signals to GPIO1, 2, 4, 5
   □ Wire VCC to battery + rail
   □ Wire GND to common ground

6. FINAL CHECKS
   □ Visual inspection for solder bridges
   □ Continuity test all connections
   □ Check for shorts between power rails

═══════════════════════════════════════════════════════════════
```

### Step 3.3: Weight Budget

```
ELECTRONICS WEIGHT (XIAO ESP32S3)
═══════════════════════════════════════════════════════════════

Component                    Weight
───────────────────────────────────
XIAO ESP32S3                 3g    ◄── 7g lighter than DevKit!
GY-521 (MPU6050)             3g
BN-180 GPS                   8g
BMP280 module                1g
AMS1117 module               2g
Protoboard (trimmed)         6g    ◄── Can be smaller with XIAO
Wiring                       4g
Servo x4                     36g (9g each)
Battery (2S 350mAh)          25g
───────────────────────────────────
ELECTRONICS TOTAL            88g

3D Printed Airframe          ~60g
───────────────────────────────────
TOTAL ORB WEIGHT             ~150g

Target: <200g
Status: ✓ Well within budget (50g margin!)

═══════════════════════════════════════════════════════════════
```

---

# 5. Firmware Setup

## 5.1 Guidance Firmware

Once hardware is tested, upload the full guidance firmware:

```cpp
// orb_guidance.ino
// Full GPS guidance firmware for Orb (XIAO ESP32S3)

#include <Wire.h>
#include <TinyGPSPlus.h>
#include <MPU6050.h>
#include <Adafruit_BMP280.h>
#include <ESP32Servo.h>
#include <WiFi.h>

// ============== PIN DEFINITIONS (XIAO ESP32S3) ==============
// Seeed XIAO ESP32S3 pinout:
// D0=GPIO1, D1=GPIO2, D2=GPIO3, D3=GPIO4
// D4=GPIO5(SDA), D5=GPIO6(SCL), D6=GPIO43(TX), D7=GPIO44(RX)
#define GPS_RX_PIN 44    // D7 - receives FROM GPS TX
#define GPS_TX_PIN 43    // D6 - sends TO GPS RX
#define I2C_SDA 5        // D4
#define I2C_SCL 6        // D5
#define SERVO1_PIN 1     // D0 - Top fin
#define SERVO2_PIN 2     // D1 - Right fin
#define SERVO3_PIN 3     // D2 - Bottom fin
#define SERVO4_PIN 4     // D3 - Left fin

// ============== GUIDANCE PARAMETERS ==============
#define Kp_ROLL 2.0      // Roll proportional gain
#define Kp_PITCH 1.5     // Pitch proportional gain
#define MAX_FIN_DEFLECT 30  // Max fin deflection (degrees)
#define GUIDANCE_RATE 10    // Hz

// ============== OBJECTS ==============
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
MPU6050 mpu;
Adafruit_BMP280 bmp;
Servo servo[4];

// ============== STATE ==============
struct {
    double lat;
    double lon;
    double alt;
    float heading;
    float speed;
    bool valid;
} currentPos;

struct {
    double lat;
    double lon;
    bool set;
} target;

enum State {
    STATE_IDLE,
    STATE_ARMED,
    STATE_RELEASED,
    STATE_TERMINAL
} state = STATE_IDLE;

float initialAlt = 0;

// ============== SETUP ==============
void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n=== ORB GUIDANCE v1.0 ===\n");

    // Initialize I2C
    Wire.begin(I2C_SDA, I2C_SCL);

    // Initialize GPS
    gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

    // Initialize IMU
    mpu.initialize();
    if (!mpu.testConnection()) {
        Serial.println("ERROR: MPU6050 not found!");
    }

    // Initialize Barometer
    if (!bmp.begin(0x76)) {
        Serial.println("ERROR: BMP280 not found!");
    }

    // Initialize Servos (center position)
    servo[0].attach(SERVO1_PIN);
    servo[1].attach(SERVO2_PIN);
    servo[2].attach(SERVO3_PIN);
    servo[3].attach(SERVO4_PIN);
    centerServos();

    // Setup WiFi AP for target upload
    WiFi.softAP("ORB_01", "12345678");
    Serial.print("WiFi AP IP: ");
    Serial.println(WiFi.softAPIP());

    Serial.println("\nReady. Waiting for target...");
    Serial.println("Commands: T<lat>,<lon> to set target, A to arm, R to release");
}

// ============== MAIN LOOP ==============
void loop() {
    static unsigned long lastGuidance = 0;

    // Read GPS continuously
    while (gpsSerial.available()) {
        gps.encode(gpsSerial.read());
    }
    updatePosition();

    // Read IMU
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Process serial commands
    processCommands();

    // Run guidance at fixed rate
    if (millis() - lastGuidance >= (1000 / GUIDANCE_RATE)) {
        lastGuidance = millis();

        switch (state) {
            case STATE_IDLE:
                // Wait for target and arm command
                centerServos();
                break;

            case STATE_ARMED:
                // Waiting for release
                centerServos();
                if (currentPos.valid) {
                    initialAlt = bmp.readAltitude(1013.25);
                }
                break;

            case STATE_RELEASED:
                // Active guidance
                if (target.set && currentPos.valid) {
                    runGuidance();
                }
                break;

            case STATE_TERMINAL:
                // Hold last command or go ballistic
                break;
        }
    }

    // Print status every second
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint >= 1000) {
        lastPrint = millis();
        printStatus();
    }
}

// ============== GUIDANCE ==============
void runGuidance() {
    // Calculate bearing to target
    double bearing = TinyGPSPlus::courseTo(
        currentPos.lat, currentPos.lon,
        target.lat, target.lon
    );

    // Calculate distance to target
    double distance = TinyGPSPlus::distanceBetween(
        currentPos.lat, currentPos.lon,
        target.lat, target.lon
    );

    // Get current heading from GPS (or IMU if available)
    float heading = currentPos.heading;

    // Calculate heading error
    float headingError = bearing - heading;
    if (headingError > 180) headingError -= 360;
    if (headingError < -180) headingError += 360;

    // Simple proportional guidance
    float rollCmd = constrain(Kp_ROLL * headingError, -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);

    // Pitch command - nose down to target (simple)
    float pitchCmd = -10;  // Constant dive angle

    // Apply to fins
    setFins(pitchCmd, rollCmd, 0);

    // Terminal phase check
    if (distance < 10) {
        state = STATE_TERMINAL;
        Serial.println("TERMINAL PHASE");
    }
}

void setFins(float pitch, float roll, float yaw) {
    // X-fin configuration mixing
    // Fin layout (looking from rear):
    //      1
    //   4     2
    //      3

    float fin1 = 90 + pitch + roll;   // Top
    float fin2 = 90 - roll + yaw;     // Right
    float fin3 = 90 - pitch - roll;   // Bottom
    float fin4 = 90 + roll - yaw;     // Left

    servo[0].write(constrain(fin1, 45, 135));
    servo[1].write(constrain(fin2, 45, 135));
    servo[2].write(constrain(fin3, 45, 135));
    servo[3].write(constrain(fin4, 45, 135));
}

void centerServos() {
    for (int i = 0; i < 4; i++) {
        servo[i].write(90);
    }
}

// ============== POSITION UPDATE ==============
void updatePosition() {
    if (gps.location.isValid()) {
        currentPos.lat = gps.location.lat();
        currentPos.lon = gps.location.lng();
        currentPos.alt = gps.altitude.meters();
        currentPos.heading = gps.course.deg();
        currentPos.speed = gps.speed.mps();
        currentPos.valid = true;
    }
}

// ============== COMMAND PROCESSING ==============
void processCommands() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd.startsWith("T")) {
            // Target command: T<lat>,<lon>
            int comma = cmd.indexOf(',');
            if (comma > 1) {
                target.lat = cmd.substring(1, comma).toDouble();
                target.lon = cmd.substring(comma + 1).toDouble();
                target.set = true;
                Serial.printf("Target set: %.6f, %.6f\n", target.lat, target.lon);
            }
        }
        else if (cmd == "A") {
            // Arm command
            if (target.set) {
                state = STATE_ARMED;
                Serial.println("ARMED - Waiting for release");
            } else {
                Serial.println("Cannot arm - no target set");
            }
        }
        else if (cmd == "R") {
            // Release command
            if (state == STATE_ARMED) {
                state = STATE_RELEASED;
                Serial.println("RELEASED - Guidance active");
            }
        }
        else if (cmd == "S") {
            // Safe/disarm
            state = STATE_IDLE;
            target.set = false;
            centerServos();
            Serial.println("SAFE - Disarmed");
        }
        else if (cmd == "C") {
            // Center servos
            centerServos();
            Serial.println("Servos centered");
        }
    }
}

// ============== STATUS ==============
void printStatus() {
    Serial.print("State: ");
    switch (state) {
        case STATE_IDLE: Serial.print("IDLE"); break;
        case STATE_ARMED: Serial.print("ARMED"); break;
        case STATE_RELEASED: Serial.print("RELEASED"); break;
        case STATE_TERMINAL: Serial.print("TERMINAL"); break;
    }

    Serial.printf(" | GPS: ");
    if (currentPos.valid) {
        Serial.printf("%.6f,%.6f", currentPos.lat, currentPos.lon);
    } else {
        Serial.print("No fix");
    }
    Serial.printf(" (%d sats)", gps.satellites.value());

    if (target.set) {
        double dist = TinyGPSPlus::distanceBetween(
            currentPos.lat, currentPos.lon,
            target.lat, target.lon
        );
        Serial.printf(" | Dist: %.1fm", dist);
    }

    Serial.printf(" | Alt: %.1fm", bmp.readAltitude(1013.25));
    Serial.println();
}
```

## 5.2 Uploading Firmware

```
UPLOAD PROCEDURE
═══════════════════════════════════════════════════════════════

1. Connect ESP32-S3 via USB-C

2. Put in bootloader mode (if needed):
   - Hold BOOT button
   - Press and release RESET
   - Release BOOT button

3. In Arduino IDE:
   - Select correct port (COMx or /dev/ttyUSBx)
   - Click Upload

4. Open Serial Monitor (115200 baud)

5. Verify startup messages

═══════════════════════════════════════════════════════════════
```

---

# 6. Testing Procedures

## 6.1 Bench Test Checklist

```
BENCH TEST CHECKLIST
═══════════════════════════════════════════════════════════════

□ POWER
  □ Battery voltage: 7.4V nominal
  □ 3.3V rail: 3.3V ± 0.1V
  □ No excessive heat from regulator

□ GPS
  □ LED blinks on power-up
  □ Gets fix outdoors in <60s
  □ Position displayed in serial

□ IMU
  □ I2C detected at 0x68
  □ Accelerometer reads ~16384 on Z-axis (gravity)
  □ Values change when tilted

□ BAROMETER
  □ I2C detected at 0x76
  □ Reads reasonable pressure (~1013 hPa at sea level)
  □ Temperature reasonable

□ SERVOS
  □ All 4 center on power-up
  □ Sweep test moves all servos
  □ No jitter or oscillation
  □ Fins move correct direction

□ FIRMWARE
  □ Responds to serial commands
  □ Target can be set (T command)
  □ Arm command accepted (A)
  □ Safe command works (S)

═══════════════════════════════════════════════════════════════
```

## 6.2 Outdoor GPS Test

```
GPS ACCURACY TEST
═══════════════════════════════════════════════════════════════

1. Take unit outside with clear sky view

2. Wait for GPS fix (solid LED)

3. Record position in serial monitor

4. Walk 10m North, record position

5. Walk 10m East, record position

6. Compare to known positions (Google Maps)

EXPECTED RESULTS:
- Fix time: <60 seconds (cold start)
- Position accuracy: <5m CEP
- Heading accuracy: ±5° (when moving)

═══════════════════════════════════════════════════════════════
```

## 6.3 Servo Direction Test

```
SERVO DIRECTION VERIFICATION
═══════════════════════════════════════════════════════════════

With Orb pointing nose-up, verify fin directions:

1. Send roll-right command
   - Fin 1 (top): should deflect LEFT
   - Fin 3 (bottom): should deflect RIGHT

2. Send pitch-down command
   - Fin 1 (top): should deflect toward nose
   - Fin 3 (bottom): should deflect away from nose

If directions are wrong:
- Swap servo connections, OR
- Invert in firmware (multiply by -1)

═══════════════════════════════════════════════════════════════
```

---

# 7. 3D Printed Parts

## 7.1 Design Requirements

```
ORB AIRFRAME REQUIREMENTS
═══════════════════════════════════════════════════════════════

DIMENSIONS:
- Total length: 250mm
- Body diameter: 50mm (OD)
- Fin span: 120mm (tip to tip)
- Fin chord: 40mm

MATERIALS:
- Body: PETG (strong, some flex)
- Fins: PETG 100% infill (rigid)
- Nose: PETG (impact resistant)

FEATURES NEEDED:
- Electronics bay access (screws or snap fit)
- Servo mounting points (4x)
- Fin attachment slots
- Battery bay in nose (for CG)
- GPS antenna window (or external mount)

═══════════════════════════════════════════════════════════════
```

## 7.2 DIMENSIONED CAD DRAWINGS

### OVERALL ASSEMBLY - SIDE VIEW

```
COMPLETE ORB ASSEMBLY - SIDE VIEW (All dimensions in mm)
═══════════════════════════════════════════════════════════════════════════════════════

                         ◄─────────────────── 250 TOTAL LENGTH ──────────────────────►

        ◄── 50 ──►◄────────────────── 150 ──────────────────►◄─────── 50 ────────►
        ┌─────────┐                                           ┌───────────────────┐
        │  NOSE   │              BODY TUBE                    │   TAIL SECTION    │
        │  CONE   │                                           │                   │
        │         │                                           │                   │
     ╱──┴─────────┴───────────────────────────────────────────┴───────────────────┴──╲
    ╱                                                                                  ╲
   ╱      ┌───────────────────────────────────────────────────────────────────┐        ╲
  │  Batt │                     ELECTRONICS BAY                               │Servos   │
  │  Bay  │   [XIAO] [IMU] [BARO]          [GPS Module]                       │  (x4)   │
   ╲      └───────────────────────────────────────────────────────────────────┘        ╱
    ╲                                                                                  ╱
     ╲──┬─────────┬───────────────────────────────────────────┬───────────────────┬──╱
        │         │                                           │                   │
        │         │                                           │     ┌───┐         │
        └─────────┘                                           │     │FIN│         │
                                                              │     │   │         │
             │                      │                         │     │60 │         │
             ▼                      ▼                         └─────┴───┴─────────┘
         CG TARGET              MOUNTING                              │
        75-100mm               STANDOFFS                              ▼
       from nose                                                  FIN SPAN
                                                                   120mm
                                                                (tip to tip)

═══════════════════════════════════════════════════════════════════════════════════════
```

### NOSE CONE - DETAILED DIMENSIONS

```
NOSE CONE - CROSS SECTION (All dimensions in mm)
═══════════════════════════════════════════════════════════════════════════════════════

    FRONT VIEW                              SIDE CROSS-SECTION
    ───────────                             ──────────────────

         ┌───┐                                      ╱╲
         │   │◄─ ø10 tip                           ╱  ╲
        ╱     ╲                                   ╱    ╲ ◄─ Ogive curve
       ╱       ╲                                 ╱      ╲    (tangent ogive)
      ╱         ╲                               ╱        ╲
     ╱           ╲                             ╱          ╲
    │             │                           │    ┌──────┐│
    │             │◄─ ø50 base               │    │ BATT ││◄─ Battery pocket
    │             │                           │    │ BAY  ││    35mm deep
    │             │                           │    │      ││    ø40 ID
    └─────────────┘                           │    │      ││
                                              │    └──────┘│
     ◄─── 50 ───►                             └────────────┘
                                                    │
                                               ◄─── 50 ───►

    DIMENSIONS:
    ─────────────────────────────────────
    Total Length:        50mm
    Base OD:             50mm
    Base ID (socket):    46mm (2mm wall)
    Socket depth:        10mm
    Battery bay depth:   35mm
    Battery bay ID:      40mm
    Tip diameter:        10mm (rounded)
    Wall thickness:      2mm (body)
                         3mm (tip, reinforced)
    Ogive ratio:         1:1 (length:diameter)

    THREAD/FIT DETAIL:
    ─────────────────────────────────────
              ┌─────────┐
              │         │◄─ 46mm OD socket
              │  ┌───┐  │
              │  │   │  │◄─ 2mm wall
              │  │   │  │
              └──┴───┴──┘
                 10mm
              socket depth

═══════════════════════════════════════════════════════════════════════════════════════
```

### BODY TUBE - DETAILED DIMENSIONS

```
BODY TUBE - CROSS SECTION (All dimensions in mm)
═══════════════════════════════════════════════════════════════════════════════════════

    END VIEW                               SIDE CROSS-SECTION
    ────────                               ──────────────────

         ┌───┐                     ┌──────────────────────────────────────────────┐
        ╱     ╲                    │                                              │
       │   ○   │◄─ M2 standoff    │  ┌────────────────────────────────────────┐  │
       │       │   holes (x4)      │  │          ELECTRONICS BAY               │  │
       │ ○   ○ │                   │  │   ┌────┐  ┌───┐  ┌───┐    ┌──────┐   │  │
       │       │                   │  │   │XIAO│  │IMU│  │BAR│    │ GPS  │   │  │
       │   ○   │                   │  │   └────┘  └───┘  └───┘    └──────┘   │  │
        ╲     ╱                    │  │                                       │  │
         └───┘                     │  └────────────────────────────────────────┘  │
                                   │         │                            │       │
     ◄─── 50 ───►                  └─────────┴────────────────────────────┴───────┘
        (OD)                              ▲                               ▲
                                       Standoff                       Standoff
     ◄─── 46 ───►                      mount                          mount
        (ID)                            25mm                          125mm
                                      from front                    from front

    DIMENSIONS:
    ─────────────────────────────────────
    Total Length:          150mm
    Outer Diameter:        50mm
    Inner Diameter:        46mm
    Wall Thickness:        2mm

    FEATURES:
    ─────────────────────────────────────
    Front socket:          46mm ID x 10mm deep (receives nose)
    Rear socket:           46mm ID x 10mm deep (receives tail)
    Standoff holes:        M2 clearance (2.2mm) x 4
    Standoff pattern:      Square, 30mm x 30mm
    Standoff positions:    25mm and 125mm from front edge

    STANDOFF HOLE PATTERN (looking from front):
    ─────────────────────────────────────────────
              ┌─────────────┐
              │  ○       ○  │◄─ 2.2mm holes
              │             │
              │      ┼      │◄─ Center axis
              │             │
              │  ○       ○  │
              └─────────────┘
                ◄── 30 ──►
                  (square)

═══════════════════════════════════════════════════════════════════════════════════════
```

### TAIL SECTION - DETAILED DIMENSIONS

```
TAIL SECTION - VIEWS (All dimensions in mm)
═══════════════════════════════════════════════════════════════════════════════════════

    REAR VIEW (looking from behind)          SIDE CROSS-SECTION
    ───────────────────────────────          ──────────────────

              FIN 1 (Top)                    ┌──────────────────────────┐
                 │                           │                          │
                 ▼                           │  ┌────────────────────┐  │
              ┌─────┐                        │  │   SERVO BAYS (x4)  │  │
           ╱──┴─────┴──╲                     │  │  ┌──┐ ┌──┐        │  │
          ╱      │      ╲                    │  │  │S1│ │S2│        │  │
         ╱       │       ╲                   │  │  └──┘ └──┘        │  │
        │   ○────┼────○   │◄─ Fin pivots    │  │  ┌──┐ ┌──┐        │  │
  FIN 4─┤        │        ├─FIN 2           │  │  │S3│ │S4│        │  │
        │   ○────┼────○   │   (45° rotated) │  │  └──┘ └──┘        │  │
         ╲       │       ╱                   │  └────────────────────┘  │
          ╲      │      ╱                    │           │              │◄─ 46mm plug
           ╲─────┴─────╱                     └───────────┴──────────────┘
              FIN 3 (Bottom)                            │
                                                   ◄─── 50 ───►
         ◄───── 50 ─────►
           (body OD)
                                             ◄───────── 50 ─────────►
         ◄──── 120 ─────►                          (length)
         (fin tip to tip)

    DIMENSIONS:
    ─────────────────────────────────────
    Total Length:          50mm
    Body OD:               50mm
    Body ID:               46mm (wire channel)
    Front plug:            46mm OD x 10mm long (fits into body tube)

    SERVO BAY DIMENSIONS:
    ─────────────────────────────────────
    Servo pocket:          23mm L x 12.5mm W x 22mm D (SG90 size)
    Servo spacing:         90° apart (X-configuration)
    Servo axis offset:     15mm from centerline
    Wire channel:          10mm diameter, center

    FIN PIVOT POINTS:
    ─────────────────────────────────────
    Pivot hole diameter:   2.2mm (M2 clearance)
    Pivot distance:        25mm from centerline
    Pivot height:          30mm from front of tail section
    Fins at 45° to vertical (X-config, not + config)

    SERVO POCKET DETAIL:
    ─────────────────────────────────────
         ┌─────────────────┐
         │                 │
         │   ┌─────────┐   │◄─ 23mm
         │   │  SG90   │   │
         │   │  SERVO  │   │
         │   │         │   │
         │   └────┬────┘   │
         │        │        │◄─ Output shaft
         └────────┴────────┘   toward fin
              12.5mm

═══════════════════════════════════════════════════════════════════════════════════════
```

### FIN DESIGN - DETAILED DIMENSIONS

```
FIN DETAIL - ALL VIEWS (All dimensions in mm)
═══════════════════════════════════════════════════════════════════════════════════════

    PLAN VIEW (flat)                        EDGE VIEW
    ────────────────                        ─────────

    ┌─────────────────────────────┐              │
    │                             │              │
    │                             │◄─ 60mm span  ├─┐
    │         ┌───────────┐       │              │ │◄─ 3mm thick
    │         │ PIVOT BOSS│       │              ├─┘
    │         │   ø8mm    │       │              │
    │         │ (raised)  │       │              │
    │         └─────┬─────┘       │
    │               │             │
    │         M2 PIVOT HOLE       │
    │           (ø2.2mm)          │
    │                             │
    └─────────────────────────────┘

    ◄───────── 40mm chord ────────►


    FIN PROFILE (NACA 0006 or flat plate):
    ─────────────────────────────────────────

    Flat plate (simple):
    ┌─────────────────────────────────────────┐
    │                 3mm                      │
    └─────────────────────────────────────────┘

    OR symmetric airfoil (better performance):
              ╱────────────────────────╲
             ╱                          ╲
    ────────╱            3mm             ╲────────
             ╲                          ╱
              ╲────────────────────────╱


    DIMENSIONS:
    ─────────────────────────────────────
    Chord (root to tip):    40mm
    Span (from body):       60mm (35mm exposed + 25mm root in body)
    Thickness:              3mm (constant)

    PIVOT BOSS:
    ─────────────────────────────────────
    Boss diameter:          8mm
    Boss height:            2mm (each side, total 7mm thick at pivot)
    Pivot hole:             2.2mm (M2 clearance)
    Pivot location:         15mm from root edge

    LINKAGE ATTACHMENT:
    ─────────────────────────────────────
    Linkage hole:           1.5mm diameter
    Hole location:          8mm from pivot center
    Toward trailing edge

    FIN PIVOT GEOMETRY:
    ─────────────────────────────────────
              ●◄─ Linkage hole (1.5mm)
              │   8mm from pivot
              │
         ┌────●────┐◄─ Pivot hole (2.2mm)
         │  BOSS   │   at 15mm from root
         └─────────┘
              │
              │
    ══════════╧══════════  ◄─ Root edge (attaches to tail)

═══════════════════════════════════════════════════════════════════════════════════════
```

### SERVO LINKAGE - DETAILED DIMENSIONS

```
SERVO-TO-FIN LINKAGE (All dimensions in mm)
═══════════════════════════════════════════════════════════════════════════════════════

    LINKAGE ASSEMBLY:
    ─────────────────

         FIN                                SERVO
         ───                                ─────

         ●◄─ Linkage hole                   ┌─────────┐
         │   (1.5mm)                        │  SG90   │
         │                                  │         │
    ═════●═════ Fin pivot                   │    ●────┼───● Servo horn
         │                                  │   shaft │    hole
         │                                  │         │
         │      PUSHROD                     └─────────┘
         │    (1mm music wire)
         └──────────────────────────────────────┘

              ◄──────── ~25mm ─────────►


    SERVO HORN DETAIL:
    ─────────────────────────────────────

         ●───●───●───●  ◄─ Use 2nd or 3rd hole
         │              (8-10mm from center)
         ●
         │
         ●◄─ Shaft attachment

    Hole spacing: ~3mm
    Use hole that gives ~15-20° fin deflection
    for 45° servo travel

    PUSHROD:
    ─────────────────────────────────────
    Material:       1mm music wire or 1.2mm steel
    Length:         ~25mm (adjust to fit)
    Ends:           Z-bend (both ends)
    Z-bend length:  3mm

    Z-BEND DETAIL:
    ─────────────────────────────────────
              3mm
            ◄───►
         ┌──┐
         │  │
    ─────┘  └───────────────────────

═══════════════════════════════════════════════════════════════════════════════════════
```

### COMPLETE ASSEMBLY - EXPLODED VIEW

```
EXPLODED ASSEMBLY VIEW
═══════════════════════════════════════════════════════════════════════════════════════

                    NOSE CONE
                    (50mm long)
                        │
                        ▼
                   ┌─────────┐
                  ╱           ╲
                 ╱   Battery   ╲
                │     Bay      │
                │   (35mm D)   │
                └──────┬───────┘
                       │ Press/thread fit
                       │ (46mm socket)
                       ▼
    ┌──────────────────────────────────────────────────┐
    │                  BODY TUBE                        │
    │                  (150mm long)                     │
    │                                                   │
    │    ┌──────────────────────────────────────┐      │
    │    │     ELECTRONICS PCB (mounted on      │      │
    │    │     M2 standoffs, 30x30mm pattern)   │      │
    │    │                                       │      │
    │    │   [XIAO]  [IMU]  [BARO]    [GPS]     │      │
    │    └──────────────────────────────────────┘      │
    │                                                   │
    └───────────────────────┬───────────────────────────┘
                            │ Press/thread fit
                            │ (46mm socket)
                            ▼
                   ┌─────────────────────┐
                   │    TAIL SECTION     │
                   │    (50mm long)      │
                   │                     │
                   │  ┌───┐       ┌───┐  │◄─ Servo bays
                   │  │ S │       │ S │  │
                   │  └─┬─┘       └─┬─┘  │
                   │    │           │    │
                   └────┼───────────┼────┘
                        │           │
              ┌─────────┼───────────┼─────────┐
              │         │           │         │
              ▼         ▼           ▼         ▼
           ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
           │FIN 1│   │FIN 2│   │FIN 3│   │FIN 4│
           │(Top)│   │(Rt) │   │(Bot)│   │(Lt) │
           └─────┘   └─────┘   └─────┘   └─────┘

           Each fin: 40mm chord x 60mm span x 3mm thick
           Mounted at 45° (X-configuration)
           M2 pivot screws

═══════════════════════════════════════════════════════════════════════════════════════
```

### DIMENSION SUMMARY TABLE

```
DIMENSION SUMMARY - ALL PARTS
═══════════════════════════════════════════════════════════════════════════════════════

OVERALL ASSEMBLY
─────────────────────────────────────────────────────────────────
Total Length                    250mm
Body Diameter (OD)              50mm
Body Diameter (ID)              46mm
Fin Span (tip to tip)           120mm
Wall Thickness                  2mm (standard), 3mm (nose tip)

NOSE CONE
─────────────────────────────────────────────────────────────────
Length                          50mm
Base OD                         50mm
Base ID (socket fit)            46mm
Socket depth                    10mm
Battery bay depth               35mm
Battery bay ID                  40mm
Tip diameter                    10mm
Profile                         Tangent ogive

BODY TUBE
─────────────────────────────────────────────────────────────────
Length                          150mm
OD                              50mm
ID                              46mm
Front socket ID                 46mm x 10mm deep
Rear socket ID                  46mm x 10mm deep
Standoff pattern                30mm x 30mm square
Standoff hole size              2.2mm (M2 clearance)
Standoff positions              25mm, 125mm from front

TAIL SECTION
─────────────────────────────────────────────────────────────────
Length                          50mm
OD                              50mm
ID (wire channel)               10mm
Front plug OD                   46mm x 10mm long
Servo pocket                    23mm x 12.5mm x 22mm deep
Fin pivot distance              25mm from center
Fin pivot hole                  2.2mm

FINS (x4)
─────────────────────────────────────────────────────────────────
Chord                           40mm
Span (total)                    60mm
Span (exposed)                  35mm
Thickness                       3mm
Pivot boss diameter             8mm
Pivot boss height               2mm per side
Pivot hole                      2.2mm
Pivot location                  15mm from root
Linkage hole                    1.5mm
Linkage hole location           8mm from pivot

FASTENERS REQUIRED
─────────────────────────────────────────────────────────────────
M2 x 6mm screws                 4 (standoffs)
M2 x 10mm screws                4 (fin pivots)
M2 nuts                         4 (fin pivots)
M2 x 6mm standoffs              4 (PCB mount)

═══════════════════════════════════════════════════════════════════════════════════════
```

## 7.3 Print Settings

| Part | Material | Layer Height | Infill | Walls | Supports |
|------|----------|--------------|--------|-------|----------|
| Nose Cone | PETG | 0.2mm | 15% | 3 | No |
| Body Tube | PETG | 0.2mm | 20% | 3 | No |
| Tail Section | PETG | 0.2mm | 25% | 4 | Yes |
| Fins (x4) | PETG | 0.2mm | 100% | - | No |

---

# 8. Final Assembly

## 8.1 Assembly Sequence

```
FINAL ASSEMBLY STEPS
═══════════════════════════════════════════════════════════════

1. TAIL SECTION
   □ Install 4x SG90 servos in pockets
   □ Secure with M2 screws
   □ Attach control horns
   □ Route servo wires up through center

2. FIN INSTALLATION
   □ Insert fin pivots through tail
   □ Secure with M2 screws/nuts
   □ Attach linkage rods to servo horns
   □ Verify free movement

3. ELECTRONICS INSTALLATION
   □ Mount PCB in body tube on standoffs
   □ Secure GPS module (antenna facing out/up)
   □ Connect servo wires to PCB
   □ Connect battery lead (don't plug battery yet)

4. BODY-TAIL ASSEMBLY
   □ Thread/press tail section to body
   □ Route wires carefully
   □ Secure with M2 screws or friction fit

5. NOSE-BODY ASSEMBLY
   □ Install battery in nose cone
   □ Route battery wire through
   □ Connect battery to power
   □ Thread/press nose to body

6. FINAL CHECKS
   □ Check CG (should be 30-40% from nose)
   □ Verify all fins move freely
   □ Power on, verify startup
   □ Test servo sweep
   □ Check GPS fix outdoors

═══════════════════════════════════════════════════════════════
```

## 8.2 CG (Center of Gravity) Check

```
CG VERIFICATION
═══════════════════════════════════════════════════════════════

         Nose                                    Tail
          │                                        │
          ▼                                        ▼
    ┌─────────────────────────────────────────────────┐
    │                   250mm                          │
    └─────────────────────────────────────────────────┘
               │
               ▼
           CG Point
         (75-100mm from nose)
         (30-40% of length)

To check:
1. Balance Orb on finger or edge
2. CG should be 75-100mm from nose tip
3. If tail-heavy: add weight to nose
4. If nose-heavy: (unlikely) reduce nose weight

A forward CG = stable flight
A rear CG = unstable/tumbling

═══════════════════════════════════════════════════════════════
```

---

# 9. Troubleshooting

## 9.1 Common Issues

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| No power LED | Dead battery, bad connection | Check battery voltage, wiring |
| GPS no fix | Indoor, antenna blocked | Go outside, clear sky view |
| IMU not detected | I2C wiring, wrong address | Check SDA/SCL, AD0 to GND |
| Servos jitter | Power supply weak | Use battery direct, not BEC |
| Servos don't move | Wrong pins, no power | Verify GPIO, check VCC |
| ESP32 won't program | Not in boot mode | Hold BOOT, press RESET |
| WiFi not visible | Code issue | Check AP code, restart |

## 9.2 I2C Debugging

```cpp
// I2C Scanner - upload to diagnose I2C issues (XIAO ESP32S3)
#include <Wire.h>

void setup() {
    Wire.begin(5, 6);  // SDA=D4(GPIO5), SCL=D5(GPIO6)
    Serial.begin(115200);
    Serial.println("\nI2C Scanner (XIAO ESP32S3)");
}

void loop() {
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        byte error = Wire.endTransmission();
        if (error == 0) {
            Serial.printf("Device found at 0x%02X\n", addr);
        }
    }
    Serial.println("Scan complete\n");
    delay(5000);
}

// Expected output:
// Device found at 0x68  (MPU6050)
// Device found at 0x76  (BMP280)
```

---

# Appendix A: Quick Reference

## Pin Summary (XIAO ESP32S3)

| Function | XIAO Pin | GPIO | Wire Color |
|----------|----------|------|------------|
| Servo 1 (Top) | D0 | GPIO1 | Orange |
| Servo 2 (Right) | D1 | GPIO2 | Orange |
| Servo 3 (Bottom) | D2 | GPIO3 | Orange |
| Servo 4 (Left) | D3 | GPIO4 | Orange |
| I2C SDA | D4 | GPIO5 | Blue |
| I2C SCL | D5 | GPIO6 | Purple |
| GPS RX←ESP TX | D6 | GPIO43 | Green |
| GPS TX→ESP RX | D7 | GPIO44 | Yellow |

## I2C Addresses

| Device | Address |
|--------|---------|
| MPU6050 | 0x68 |
| BMP280 | 0x76 |

## Serial Commands

| Command | Function |
|---------|----------|
| T\<lat\>,\<lon\> | Set target coordinates |
| A | Arm |
| R | Release (start guidance) |
| S | Safe (disarm) |
| C | Center servos |

---

**Document Control**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial release |

---

*Build Safe. Test Often. Iterate.*
