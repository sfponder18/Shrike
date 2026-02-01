# Orb Firmware

GPS-guided glide munition control system with support for multiple ESP32 boards.

## Folder Structure

```
code/
├── README.md                    <- You are here
├── esp32s3/                     <- ESP32-S3-DevKit C N16R8 version
│   ├── WIRING_GUIDE.md
│   ├── ARDUINO_SETUP.md
│   ├── orb_guidance/
│   │   └── orb_guidance.ino     <- Main flight firmware
│   ├── orb_test/
│   │   └── orb_test.ino         <- Hardware test firmware
│   └── orb_calibration/
│       └── orb_calibration.ino  <- IMU calibration tool
│
├── xiao_esp32c3/                <- Seeed XIAO ESP32C3 version
│   ├── WIRING_GUIDE.md
│   ├── ARDUINO_SETUP.md
│   ├── orb_guidance/
│   │   └── orb_guidance.ino
│   ├── orb_test/
│   │   └── orb_test.ino
│   └── orb_calibration/
│       └── orb_calibration.ino
│
├── orb_calibration/             <- (Legacy - use board-specific folder)
│   └── orb_visualizer.py        <- Python 3D visualization tool
│
└── pcb/                         <- PCB design files
    ├── ORB_PCB_SPEC.md
    └── EASYEDA_GUIDE.md
```

## Choose Your Board

### ESP32-S3-DevKit C N16R8
- **Size:** ~70 x 25mm
- **Flash:** 16MB
- **PSRAM:** 8MB
- **GPIOs:** 45 available
- **CPU:** Dual-core 240MHz (Xtensa)
- **Best for:** Development, testing, feature-rich builds

**Use firmware from:** `esp32s3/`

### Seeed XIAO ESP32C3
- **Size:** 21 x 17.5mm
- **Weight:** ~3g
- **Flash:** 4MB
- **GPIOs:** 11 usable
- **CPU:** Single-core 160MHz (RISC-V)
- **Best for:** Small/lightweight builds, production

**Use firmware from:** `xiao_esp32c3/`

## Pin Comparison

| Function | ESP32-S3 | XIAO ESP32C3 |
|----------|----------|--------------|
| Servo 1 | GPIO4 | D0 (GPIO2) |
| Servo 2 | GPIO5 | D1 (GPIO3) |
| Servo 3 | GPIO6 | D2 (GPIO4) |
| Servo 4 | GPIO7 | D3 (GPIO5) |
| I2C SDA | GPIO18 | D4 (GPIO6) |
| I2C SCL | GPIO8 | D5 (GPIO7) |
| GPS TX | GPIO16 | D6 (GPIO21) |
| GPS RX | GPIO17 | D7 (GPIO20) |

## Getting Started

1. Choose your board folder (`esp32s3/` or `xiao_esp32c3/`)
2. Read the `ARDUINO_SETUP.md` in that folder
3. Read the `WIRING_GUIDE.md` for hardware connections
4. Upload `orb_test.ino` first to verify wiring
5. Run `orb_calibration.ino` to calibrate the IMU
6. Upload `orb_guidance.ino` for full flight firmware

## Required Libraries

Install via Arduino Library Manager:
- **TinyGPSPlus** by Mikal Hart
- **MPU6050** by Electronic Cats
- **Adafruit BMP280 Library** by Adafruit

## Hardware Components

- GPS: GY-NEO6MV2 (NEO-6M)
- IMU: GY-521 (MPU6050)
- Barometer: GY-BMP280
- Servos: SG90 x4
- Power: 2S LiPo (7.4V) + AMS1117-3.3V regulator
