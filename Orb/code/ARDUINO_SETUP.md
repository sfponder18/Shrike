# Arduino IDE Setup Guide
## For Seeed XIAO ESP32C3

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

1. **Tools > Board > esp32 > XIAO_ESP32C3**

2. Configure these settings in the Tools menu:
   ```
   Board:              XIAO_ESP32C3
   USB CDC On Boot:    Enabled
   CPU Frequency:      160MHz (WiFi)
   Core Debug Level:   None
   Erase All Flash:    Disabled
   Flash Mode:         QIO
   Flash Size:         4MB (32Mb)
   Partition Scheme:   Default 4MB with spiffs
   Upload Speed:       921600
   ```

   **Key settings for XIAO ESP32C3:**
   - Flash Size: 4MB (XIAO has 4MB flash)
   - No PSRAM option (XIAO ESP32C3 doesn't have PSRAM)
   - CPU: 160MHz (RISC-V single core)

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

## Step 5: Connect Your XIAO ESP32C3

1. Connect the XIAO ESP32C3 to your computer via USB-C
   - XIAO has a single USB-C port

2. Your computer should detect it automatically
   - Windows: Check Device Manager for new COM port
   - Look for "USB Serial Device (COMx)" or similar

3. In Arduino IDE: **Tools > Port > COMx** (select the new port)

---

## Step 6: Upload Test Firmware

1. Open the test sketch:
   **File > Open** -> Navigate to:
   ```
   SwarmDrones/Orb/code/orb_test/orb_test.ino
   ```

2. Click **Upload** (right arrow button) or press Ctrl+U

3. If upload fails with "Failed to connect":
   - Hold the **BOOT** button on the XIAO
   - While holding BOOT, press and release the **RST** button
   - Release BOOT after upload starts
   - This puts the XIAO into bootloader mode

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
   ORB TEST FIRMWARE v1.1
   Seeed XIAO ESP32C3
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
   SwarmDrones/Orb/code/orb_guidance/orb_guidance.ino
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

### "Failed to connect to ESP32-C3"
- Use BOOT + RST button sequence (see Step 6)
- Try a different USB cable (some cables are charge-only)
- Make sure USB CDC On Boot is Enabled in board settings

### "No I2C devices found"
- Check wiring: SDA = D4 (GPIO6), SCL = D5 (GPIO7)
- Ensure 3.3V power to sensors
- Check for loose connections

### "GPS: No data received"
- Check wiring: GPS TX->D7 (GPIO20), GPS RX->D6 (GPIO21)
- GPS needs 3.3V (not 5V!)
- Test outdoors with clear sky view
- First fix can take 30-60 seconds

### "Servos don't move"
- Check servo power (needs 5V+, not 3.3V)
- Verify signal wire connections to correct pins:
  - Servo 1 -> D0 (GPIO2)
  - Servo 2 -> D1 (GPIO3)
  - Servo 3 -> D2 (GPIO4)
  - Servo 4 -> D3 (GPIO5)
- Try individual servo test (`1`, `2`, `3`, `4` commands)

### "BMP280 not found"
- Check CSB pin connected to 3.3V (for address 0x76)
- If CSB is GND, try address 0x77 (code checks both)

### "Upload speed errors"
- Reduce upload speed: Tools > Upload Speed > 115200

---

## Pin Reference

```
XIAO ESP32C3 Pin Assignments for Orb:

D0 (GPIO2)  -> Servo 1 (Top)
D1 (GPIO3)  -> Servo 2 (Right)
D2 (GPIO4)  -> Servo 3 (Bottom)
D3 (GPIO5)  -> Servo 4 (Left)
D4 (GPIO6)  -> I2C SDA (IMU + Baro)
D5 (GPIO7)  -> I2C SCL (IMU + Baro)
D6 (GPIO21) -> GPS RX (ESP TX to GPS)
D7 (GPIO20) -> GPS TX (GPS TX to ESP)
3V3         -> All sensor power
GND         -> Common ground
```

---

## XIAO ESP32C3 Specifications

| Feature | Specification |
|---------|---------------|
| MCU | ESP32-C3 (RISC-V) |
| Clock | 160 MHz |
| Flash | 4 MB |
| SRAM | 400 KB |
| WiFi | 802.11 b/g/n |
| Bluetooth | BLE 5.0 |
| GPIO | 11 usable pins |
| Size | 21 x 17.5 mm |
| Weight | ~3g |
| USB | Type-C (native USB) |
