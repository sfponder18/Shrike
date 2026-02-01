# EasyEDA PCB Design Guide

## Quick Start

EasyEDA is free, web-based, and exports directly to JLCPCB.

**URL:** https://easyeda.com/editor

---

## Step 1: Create Account & Project

1. Go to https://easyeda.com
2. Sign up (free) or use Google login
3. Click **File > New > Project**
4. Name it "Orb_Controller"

---

## Step 2: Create Schematic

1. Click **File > New > Schematic**

### Add Components

Use the **Library** panel (left side) to search and place:

| Search Term | Component | Quantity |
|-------------|-----------|----------|
| "2.54mm 1x20 female" | Pin Header Female 1x20 | 2 |
| "2.54mm 1x4 female" | Pin Header Female 1x4 | 1 |
| "2.54mm 1x8 female" | Pin Header Female 1x8 | 1 |
| "2.54mm 1x6 female" | Pin Header Female 1x6 | 1 |
| "2.54mm 1x3 male" | Pin Header Male 1x3 | 4 |
| "JST-PH 2P" | JST Connector 2-pin | 1 |
| "AMS1117-3.3" | Voltage Regulator | 1 |

### Wire the Schematic

Create these nets (use the Wire tool or Net Labels):

**Power Nets:**
```
VBATT (Battery+) → AMS1117 VIN, All servo VCC pins
GND → Everything's ground, IMU AD0 pin
3V3 (AMS1117 OUT) → GPS VCC, IMU VCC, BARO VCC, BARO CSB
```

**Signal Nets:**
```
SDA → ESP32 pin 11 (GPIO18), IMU SDA, BARO SDA
SCL → ESP32 pin 10 (GPIO8), IMU SCL, BARO SCL
GPS_TX → ESP32 pin 8 (GPIO17), GPS TX
GPS_RX → ESP32 pin 7 (GPIO16), GPS RX
SERVO1 → ESP32 pin 4 (GPIO4), Servo1 Signal
SERVO2 → ESP32 pin 5 (GPIO5), Servo2 Signal
SERVO3 → ESP32 pin 6 (GPIO6), Servo3 Signal
SERVO4 → ESP32 pin 7 (GPIO7), Servo4 Signal
```

**Tip:** Use **Net Labels** instead of drawing wires everywhere. Click the Net Label tool, type the net name, and place it on each pin that connects to that net.

---

## Step 3: Convert to PCB

1. Click **Design > Convert to PCB**
2. Set board size: **70mm x 50mm**
3. Click **OK**

You'll see all components with "ratsnest" lines showing what needs to connect.

---

## Step 4: Arrange Components

Suggested layout:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│    [═══════════ ESP32 LEFT HEADER ═══════════]              │
│                                                              │
│    [═══════════ ESP32 RIGHT HEADER ══════════]              │
│                                                              │
│                                                              │
│  [GPS]     [IMU]      [BARO]        [S1][S2][S3][S4]        │
│  1x4       1x8        1x6           Servo headers           │
│                                                              │
│                                                              │
│  [BATT]                              [AMS1117]              │
│  JST                                 Regulator              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

1. Place ESP32 headers in center-top (these are the two 1x20 female headers, spaced to match DevKit C pin spacing - about 25.4mm apart)
2. Place sensor headers below
3. Place servo connectors on the right edge
4. Place battery connector and regulator at bottom

---

## Step 5: Route Traces

### Auto-Route (Easy Way)
1. Click **Route > Auto Route**
2. Let it run
3. Review results

### Manual Route (Better Results)
1. Use **Track** tool
2. Power traces (VBATT, 3V3, GND): **0.5mm or wider**
3. Signal traces: **0.3mm**

**Ground Pour (Recommended):**
1. Click **Copper Area** tool
2. Draw rectangle around entire board
3. Set Net to **GND**
4. This fills empty space with ground copper

---

## Step 6: Design Rule Check

1. Click **Design > Check DRC**
2. Fix any errors (usually clearance issues)
3. Re-run until clean

---

## Step 7: Export & Order

1. Click **Fabrication > PCB Fabrication File (Gerber)**
2. Review the preview
3. Click **Order at JLCPCB**

### JLCPCB Settings:
- Layers: 2
- Dimensions: 70 x 50 mm
- PCB Qty: 5 (minimum)
- Thickness: 1.6mm
- Color: Green (cheapest) or your choice
- Surface Finish: HASL
- Copper Weight: 1oz

**Cost:** ~$2-5 for boards + $5-15 shipping
**Time:** 1-2 days production + 5-10 days shipping

---

## Alternative: Order My Design

If you'd rather not design it yourself, I can create the complete EasyEDA project. Just say the word and I'll generate the JSON file you can import directly.
