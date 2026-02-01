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

---

## Step 3: Select Your Board

1. **Tools > Board > esp32 > XIAO_ESP32C3**

2. Configure these settings:
   ```
   Board:              XIAO_ESP32C3
   USB CDC On Boot:    Enabled
   CPU Frequency:      160MHz (WiFi)
   Core Debug Level:   None
   Flash Mode:         QIO
   Flash Size:         4MB (32Mb)
   Partition Scheme:   Default 4MB with spiffs
   Upload Speed:       921600
   ```

---

## Step 4: Install Required Libraries

Open **Tools > Manage Libraries** and install:

| Library | Author | Purpose |
|---------|--------|---------|
| **TinyGPSPlus** | Mikal Hart | GPS NMEA parsing |
| **MPU6050** | Electronic Cats | IMU driver |
| **Adafruit BMP280 Library** | Adafruit | Barometer driver |

---

## Step 5: Upload Test Firmware

1. Connect XIAO ESP32C3 via USB-C
2. Select the correct COM port: **Tools > Port > COMx**
3. Open: `xiao_esp32c3/orb_test/orb_test.ino`
4. Click **Upload**

If upload fails:
- Hold **BOOT** button
- Press and release **RST** button
- Release **BOOT** after upload starts

---

## Step 6: Expected Output

```
================================
   ORB TEST FIRMWARE v1.1
   Seeed XIAO ESP32C3
================================

[I2C] Scanning bus...
  Found device at 0x68 <- MPU6050
  Found device at 0x76 <- BMP280

[GPS] GY-NEO6MV2 @ 9600 baud
[IMU] MPU6050 connected OK!
[BARO] BMP280 connected OK!
[SERVO] All servos centered

================================
   SETUP COMPLETE
================================
```

---

## Troubleshooting

### "No I2C devices found"
- Check wiring: SDA = D4 (GPIO6), SCL = D5 (GPIO7)

### "GPS: No data received"
- Check wiring: GPS TX->D7 (GPIO20), GPS RX->D6 (GPIO21)

### "Servos don't move"
- Verify servo connections:
  - Servo 1 -> D0 (GPIO2)
  - Servo 2 -> D1 (GPIO3)
  - Servo 3 -> D2 (GPIO4)
  - Servo 4 -> D3 (GPIO5)

---

## XIAO ESP32C3 Specifications

| Feature | Specification |
|---------|---------------|
| MCU | ESP32-C3 (RISC-V) |
| Clock | 160 MHz |
| Flash | 4 MB |
| WiFi | 802.11 b/g/n |
| Bluetooth | BLE 5.0 |
| GPIO | 11 usable pins |
| Size | 21 x 17.5 mm |
| Weight | ~3g |
