# Orb Wiring Guide
## ESP32-S3-DevKit C N16R8 + GY-NEO6MV2 GPS

**Your Components:**
- MCU: Hailege ESP32-S3-DevKit C N16R8 (16MB Flash, 8MB PSRAM, Dual Type-C)
- GPS: GY-NEO6MV2 (NEO-6M with ceramic antenna)
- IMU: GY-521 (MPU6050)
- Barometer: GY-BMP280
- Servos: SG90 x4
- Power: 2S LiPo (7.4V) + AMS1117-3.3V regulator

---

## Pin Assignments

```
ESP32-S3-DevKit C N16R8 - ORB PINOUT
================================================================

                    USB-C (UART)              USB-C (JTAG)
                         |                         |
              +----------+---------+   +-----------+---------+
              |                    |   |                     |
              |   ESP32-S3-DevKit  |   |         C           |
              |        N16R8       |   |                     |
              +--------------------+---+---------------------+
              |                                              |
   3V3  ------| 3V3                                    GND  |------ GND
   3V3  ------| 3V3                                    43   |------ (TX0)
   RST  ------| EN                                     44   |------ (RX0)
    4   ------| GPIO4   (SERVO 1 - Top)                1    |------
    5   ------| GPIO5   (SERVO 2 - Right)              2    |------
    6   ------| GPIO6   (SERVO 3 - Bottom)            42    |------
    7   ------| GPIO7   (SERVO 4 - Left)              41    |------
   15   ------| GPIO15                                40    |------
   16   ------| GPIO16  (GPS RX <- ESP TX)            39    |------
   17   ------| GPIO17  (GPS TX -> ESP RX)            38    |------
   18   ------| GPIO18  (I2C SDA)                     37    |------
    8   ------| GPIO8   (I2C SCL)                     36    |------
    3   ------| GPIO3                                 35    |------
   46   ------| GPIO46                                 0    |------ BOOT
    9   ------| GPIO9                                 45    |------
   10   ------| GPIO10                                48    |------
   11   ------| GPIO11                                47    |------
   12   ------| GPIO12                                21    |------
   13   ------| GPIO13                                14    |------
   14   ------| GPIO14                                13    |------
    5V ------| 5V                                    GND   |------ GND
   GND ------| GND                                    GND   |------ GND
              |                                              |
              +----------------------------------------------+

================================================================
```

---

## Wiring Table

| Function | ESP32-S3 GPIO | Wire Color | Destination |
|----------|---------------|------------|-------------|
| **SERVOS** |
| Servo 1 (Top) | GPIO4 | Orange | SG90 Signal |
| Servo 2 (Right) | GPIO5 | Orange | SG90 Signal |
| Servo 3 (Bottom) | GPIO6 | Orange | SG90 Signal |
| Servo 4 (Left) | GPIO7 | Orange | SG90 Signal |
| **GPS (GY-NEO6MV2)** |
| GPS TX (data out) | GPIO17 | Yellow | NEO6M TX pin |
| GPS RX (data in) | GPIO16 | Green | NEO6M RX pin |
| **I2C BUS** |
| SDA | GPIO18 | Blue | MPU6050 SDA, BMP280 SDA |
| SCL | GPIO8 | Purple | MPU6050 SCL, BMP280 SCL |
| **POWER** |
| 3.3V | 3V3 pin | Red | All sensors VCC |
| GND | GND | Black | All grounds |
| 5V (Battery) | Direct | Red | Servo VCC (all 4) |

---

## Component Wiring Details

### GY-NEO6MV2 GPS Module

```
GY-NEO6MV2 GPS MODULE
================================

    +-------------------------+
    |   Ceramic GPS Antenna   |
    |      [===========]      |
    |                         |
    |      +-----------+      |
    |      |  NEO-6M   |      |
    |      |   Chip    |      |
    |      +-----------+      |
    |                         |
    |  VCC  RX   TX   GND     |
    +---+----+----+----+------+
        |    |    |    |
        |    |    |    +-----> GND (black)
        |    |    +----------> ESP32 GPIO17 (yellow) - GPS sends data
        |    +---------------> ESP32 GPIO16 (green)  - GPS receives data
        +--------------------> 3.3V (red) - DO NOT use 5V!

Baud Rate: 9600 (default)
Protocol: NMEA 0183
```

**Important:** The TX/RX labeling on GPS modules refers to the GPS perspective:
- GPS TX = GPS transmits data OUT -> connect to ESP RX (GPIO17)
- GPS RX = GPS receives data IN -> connect to ESP TX (GPIO16)

### GY-521 IMU (MPU6050)

```
GY-521 MPU6050 MODULE
================================

    +-------------------------+
    |        GY-521           |
    |      +---------+        |
    |      | MPU6050 |        |
    |      +---------+        |
    |                         |
    | VCC GND SCL SDA XDA XCL AD0 INT
    +--+---+---+---+---+---+---+--+
       |   |   |   |   |   |   |  |
       |   |   |   |   |   |   |  +-> (not used)
       |   |   |   |   |   |   +----> GND (I2C addr 0x68)
       |   |   |   |   |   +--------> (not used)
       |   |   |   |   +------------> (not used)
       |   |   |   +----------------> ESP32 GPIO18 (SDA)
       |   |   +--------------------> ESP32 GPIO8 (SCL)
       |   +------------------------> GND
       +----------------------------> 3.3V

I2C Address: 0x68 (when AD0 = GND)
```

### GY-BMP280 Barometer

```
GY-BMP280 BAROMETER MODULE
================================

    +-------------------------+
    |       GY-BMP280         |
    |      +---------+        |
    |      | BMP280  |        |
    |      +---------+        |
    |                         |
    | VCC  GND  SCL  SDA  CSB  SDO
    +--+----+----+----+----+----+--
       |    |    |    |    |    |
       |    |    |    |    |    +-> (not used in I2C mode)
       |    |    |    |    +------> 3.3V (selects I2C mode, addr 0x76)
       |    |    |    +-----------> ESP32 GPIO18 (shared SDA)
       |    |    +----------------> ESP32 GPIO8 (shared SCL)
       |    +---------------------> GND
       +--------------------------> 3.3V

I2C Address: 0x76 (when CSB = VCC)
```

### SG90 Servos

```
SG90 SERVO WIRING (x4)
================================

Wire Colors:
  Brown  = GND
  Red    = VCC (5V from battery or BEC)
  Orange = Signal (PWM)

    +-------------+
    |    SG90     |
    |   [Motor]   |
    |  [Gearbox]  |
    +------+------+
           |
      +----+----+
      | B  R  O |   <- Wire connector
      +----+----+
        |  |  |
        |  |  +---> Signal to ESP32 GPIO
        |  +------> 5V from battery (or BEC)
        +---------> GND (common with ESP32)

Servo Assignments:
  Servo 1 (Top)    -> GPIO4
  Servo 2 (Right)  -> GPIO5
  Servo 3 (Bottom) -> GPIO6
  Servo 4 (Left)   -> GPIO7
```

---

## Power Circuit

```
POWER DISTRIBUTION
================================

                 2S LiPo Battery
                 (7.4V 350mAh)
                      |
                      | JST-PH connector
                      v
    +-----------------+------------------+
    |                 |                  |
    |                 |                  |
    v                 v                  v
+--------+      +-----------+      +----------+
| Servos |      | AMS1117   |      | (future  |
| VCC x4 |      | 3.3V LDO  |      |  BEC 5V) |
| (7.4V) |      |           |      +----------+
+--------+      +-----+-----+
                      |
                      | 3.3V
                      v
    +-----------------+------------------+
    |                 |                  |
    v                 v                  v
+--------+      +----------+      +----------+
| ESP32  |      | GPS      |      | IMU+Baro |
| 3V3 in |      | VCC      |      | VCC      |
+--------+      +----------+      +----------+

GND: All grounds connected together (common ground)

NOTES:
- SG90 servos can tolerate 4.8-6V, but work at 7.4V briefly
- For reliability, add a 5V BEC between battery and servos
- ESP32-S3-DevKit C has onboard regulator, but use external
  AMS1117 to handle sensor current without stressing ESP32
- GPS module: USE 3.3V ONLY (5V may damage it)
```

---

## Complete Wiring Checklist

### Power Section
- [ ] Battery + (7.4V) -> AMS1117 VIN
- [ ] Battery + (7.4V) -> Servo VCC (all 4) [or through BEC]
- [ ] Battery - -> Common GND rail
- [ ] AMS1117 VOUT (3.3V) -> ESP32 3V3 pin
- [ ] AMS1117 VOUT (3.3V) -> GPS VCC
- [ ] AMS1117 VOUT (3.3V) -> MPU6050 VCC
- [ ] AMS1117 VOUT (3.3V) -> BMP280 VCC
- [ ] AMS1117 VOUT (3.3V) -> BMP280 CSB
- [ ] AMS1117 GND -> Common GND

### GPS (GY-NEO6MV2)
- [ ] GPS VCC -> 3.3V rail
- [ ] GPS GND -> GND rail
- [ ] GPS TX -> ESP32 GPIO17 (yellow)
- [ ] GPS RX -> ESP32 GPIO16 (green)

### IMU (GY-521 / MPU6050)
- [ ] IMU VCC -> 3.3V rail
- [ ] IMU GND -> GND rail
- [ ] IMU SDA -> ESP32 GPIO18 (blue)
- [ ] IMU SCL -> ESP32 GPIO8 (purple)
- [ ] IMU AD0 -> GND (sets address 0x68)

### Barometer (BMP280)
- [ ] BARO VCC -> 3.3V rail
- [ ] BARO GND -> GND rail
- [ ] BARO SDA -> ESP32 GPIO18 (shared, blue)
- [ ] BARO SCL -> ESP32 GPIO8 (shared, purple)
- [ ] BARO CSB -> 3.3V rail (sets address 0x76)

### Servos (x4)
- [ ] Servo 1 Signal (orange) -> ESP32 GPIO4
- [ ] Servo 2 Signal (orange) -> ESP32 GPIO5
- [ ] Servo 3 Signal (orange) -> ESP32 GPIO6
- [ ] Servo 4 Signal (orange) -> ESP32 GPIO7
- [ ] All Servo VCC (red) -> Battery + (or 5V BEC)
- [ ] All Servo GND (brown) -> Common GND

---

## Quick Reference Card

```
ESP32-S3-DevKit C N16R8 - ORB PIN SUMMARY
=========================================

GPIO4  -> Servo 1 (Top)      [PWM]
GPIO5  -> Servo 2 (Right)    [PWM]
GPIO6  -> Servo 3 (Bottom)   [PWM]
GPIO7  -> Servo 4 (Left)     [PWM]
GPIO16 -> GPS RX (ESP TX)    [UART1 TX]
GPIO17 -> GPS TX (ESP RX)    [UART1 RX]
GPIO18 -> I2C SDA            [I2C]
GPIO8  -> I2C SCL            [I2C]
3V3    -> All sensor VCC
GND    -> Common ground

I2C Devices:
  0x68 = MPU6050 (IMU)
  0x76 = BMP280 (Barometer)

GPS: 9600 baud, NMEA protocol
=========================================
```
