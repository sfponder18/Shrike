# Arduino IDE Setup Guide
## For ESP32-S3-DevKit C N16R8

---

## Step 1: Install Arduino IDE

1. Download Arduino IDE 2.x from: https://www.arduino.cc/en/software
2. Install and launch

---

## Step 2: Add ESP32 Board Support

1. Open **File > Preferences**
2. In "Additional Boards Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Click OK

4. Open **Tools > Board > Boards Manager**
5. Search for "esp32"
6. Install **"esp32 by Espressif Systems"** (version 2.0.x or later)
7. Wait for installation to complete

---

## Step 3: Select Your Board

1. **Tools > Board > esp32 > ESP32S3 Dev Module**

2. Configure these settings in the Tools menu:
   ```
   Board:              ESP32S3 Dev Module
   USB CDC On Boot:    Enabled
   CPU Frequency:      240MHz (WiFi)
   Core Debug Level:   None
   USB DFU On Boot:    Disabled
   Erase All Flash:    Disabled
   Events Run On:      Core 1
   Flash Mode:         QIO 80MHz
   Flash Size:         16MB (128Mb)
   JTAG Adapter:       Disabled
   Arduino Runs On:    Core 1
   USB Firmware MSC:   Disabled
   Partition Scheme:   Default 4MB with spiffs (or 16MB if available)
   PSRAM:              OPI PSRAM
   Upload Mode:        UART0 / Hardware CDC
   Upload Speed:       921600
   USB Mode:           Hardware CDC and JTAG
   ```

   **Key settings for your N16R8:**
   - Flash Size: 16MB (your board has 16MB flash)
   - PSRAM: OPI PSRAM (your board has 8MB PSRAM)

---

## Step 4: Install Required Libraries

Open **Tools > Manage Libraries** and install:

| Library | Author | Purpose |
|---------|--------|---------|
| **TinyGPSPlus** | Mikal Hart | GPS NMEA parsing |
| **MPU6050** | Electronic Cats | IMU driver |
| **Adafruit BMP280 Library** | Adafruit | Barometer driver |

Also automatically installs:
- Adafruit Unified Sensor (dependency)

**Note:** Servo control uses native ESP32 LEDC PWM - no external library needed.

### Search and Install Each:
1. Search "TinyGPSPlus" -> Install
2. Search "MPU6050" by Electronic Cats -> Install
3. Search "Adafruit BMP280" -> Install (accept dependencies)

---

## Step 5: Connect Your ESP32-S3

1. Connect the ESP32-S3-DevKit C to your computer via USB-C
   - Use the **UART** USB port (typically labeled, or try both)
   - The other port is for JTAG debugging

2. Your computer should detect it automatically
   - Windows: Check Device Manager for new COM port
   - Look for "USB Serial Device (COMx)" or "ESP32-S3"

3. In Arduino IDE: **Tools > Port > COMx** (select the new port)

---

## Step 6: Upload Test Firmware

1. Open the test sketch:
   **File > Open** -> Navigate to:
   ```
   SwarmDrones/Orb/code/esp32s3/orb_test/orb_test.ino
   ```

2. Click **Upload** (right arrow button) or press Ctrl+U

3. If upload fails with "Failed to connect":
   - Hold the **BOOT** button on the ESP32
   - While holding BOOT, press and release the **RST** button
   - Release BOOT after upload starts
   - This puts the ESP32 into bootloader mode

4. Wait for upload to complete:
   ```
   Leaving...
   Hard resetting via RTS pin...
   ```

5. Open **Serial Monitor** (Tools > Serial Monitor)
   - Set baud rate to **115200**
   - You should see the test firmware output

---

## Step 7: Test Output

Expected serial output after upload:

```
================================
   ORB TEST FIRMWARE v1.0
   ESP32-S3-DevKit C N16R8
================================

[I2C] Initializing...
[I2C] Scanning bus...
  Found device at 0x68 <- MPU6050
  Found device at 0x76 <- BMP280
  Found 2 device(s)

[GPS] Initializing UART1...
[GPS] GY-NEO6MV2 @ 9600 baud
[GPS] Waiting for data...

[IMU] Initializing MPU6050...
[IMU] MPU6050 connected OK!

[BARO] Initializing BMP280...
[BARO] BMP280 connected OK!

[SERVO] Initializing servos...
[SERVO] All servos centered to 90 degrees

================================
   SETUP COMPLETE
================================
```

---

## Step 8: Test Commands

In Serial Monitor, type these commands:

| Command | Action |
|---------|--------|
| `s` | Servo sweep test (all 4 servos) |
| `c` | Center all servos |
| `i` | I2C bus rescan |
| `g` | Show raw GPS NMEA data (10 sec) |
| `1` | Test servo 1 only |
| `2` | Test servo 2 only |
| `3` | Test servo 3 only |
| `4` | Test servo 4 only |

---

## Step 9: Upload Guidance Firmware

Once all tests pass:

1. Open guidance sketch:
   ```
   SwarmDrones/Orb/code/esp32s3/orb_guidance/orb_guidance.ino
   ```

2. Upload as before

3. Open Serial Monitor at 115200 baud

4. Test commands:
   - Set a target: `T51.5074,-0.1278` (example: London)
   - Arm: `A`
   - Release: `R`
   - Safe/Disarm: `S`
   - Help: `H`

---

## Troubleshooting

### "Failed to connect to ESP32-S3"
- Use BOOT + RST button sequence (see Step 6)
- Try the other USB-C port on the board
- Try a different USB cable (some cables are charge-only)

### "No I2C devices found"
- Check wiring: SDA = GPIO18, SCL = GPIO8
- Ensure 3.3V power to sensors
- Check for loose connections

### "GPS: No data received"
- Check wiring: TX->GPIO17, RX->GPIO16
- GPS needs 3.3V (not 5V!)
- Test outdoors with clear sky view
- First fix can take 30-60 seconds

### "Servos don't move"
- Check servo power (needs 5V+, not 3.3V)
- Verify signal wire connections to correct GPIOs
- Try individual servo test (`1`, `2`, `3`, `4` commands)

### "BMP280 not found"
- Check CSB pin connected to 3.3V (for address 0x76)
- If CSB is GND, try address 0x77 (code checks both)

### "Upload speed errors"
- Reduce upload speed: Tools > Upload Speed > 115200

---

## ESP32-S3-DevKit C N16R8 Specifications

| Feature | Specification |
|---------|---------------|
| MCU | ESP32-S3 (Xtensa LX7 Dual-Core) |
| Clock | 240 MHz |
| Flash | 16 MB |
| PSRAM | 8 MB (OPI) |
| WiFi | 802.11 b/g/n |
| Bluetooth | BLE 5.0 |
| GPIO | 45 available |
| Size | ~70 x 25 mm |
| USB | Dual Type-C (UART + JTAG) |
