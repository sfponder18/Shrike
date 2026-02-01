# Orb Wiring Guide
## Seeed XIAO ESP32C3 + GY-NEO6MV2 GPS

**Your Components:**
- MCU: Seeed XIAO ESP32C3 (4MB Flash, RISC-V, Single USB-C)
- GPS: GY-NEO6MV2 (NEO-6M with ceramic antenna)
- IMU: GY-521 (MPU6050)
- Barometer: GY-BMP280
- Servos: SG90 x4
- Power: 2S LiPo (7.4V) + AMS1117-3.3V regulator

---

## Pin Assignments

```
Seeed XIAO ESP32C3 - ORB PINOUT
================================================================

                        USB-C
                          |
              +-----------+-----------+
              |                       |
              |   Seeed XIAO ESP32C3  |
              |       (21x17.5mm)     |
              |                       |
              +-----------------------+
              |                       |
   D0  ------| GPIO2  (SERVO 1 Top)  |------ 5V
   D1  ------| GPIO3  (SERVO 2 Right)|------ GND
   D2  ------| GPIO4  (SERVO 3 Bot)  |------ 3V3
   D3  ------| GPIO5  (SERVO 4 Left) |------ D10 (GPIO10)
   D4  ------| GPIO6  (I2C SDA)      |------ D9  (GPIO9)
   D5  ------| GPIO7  (I2C SCL)      |------ D8  (GPIO8)
   D6  ------| GPIO21 (GPS RX<-TX)   |------ D7  (GPIO20 GPS TX->RX)
              |                       |
              +-----------------------+

================================================================
```

---

## Wiring Table

| Function | XIAO Pin | GPIO | Wire Color | Destination |
|----------|----------|------|------------|-------------|
| **SERVOS** |
| Servo 1 (Top) | D0 | GPIO2 | Orange | SG90 Signal |
| Servo 2 (Right) | D1 | GPIO3 | Orange | SG90 Signal |
| Servo 3 (Bottom) | D2 | GPIO4 | Orange | SG90 Signal |
| Servo 4 (Left) | D3 | GPIO5 | Orange | SG90 Signal |
| **GPS (GY-NEO6MV2)** |
| GPS TX (data out) | D7 | GPIO20 | Yellow | NEO6M TX pin |
| GPS RX (data in) | D6 | GPIO21 | Green | NEO6M RX pin |
| **I2C BUS** |
| SDA | D4 | GPIO6 | Blue | MPU6050 SDA, BMP280 SDA |
| SCL | D5 | GPIO7 | Purple | MPU6050 SCL, BMP280 SCL |
| **POWER** |
| 3.3V | 3V3 pin | - | Red | All sensors VCC |
| GND | GND | - | Black | All grounds |
| 5V (Battery) | Direct | - | Red | Servo VCC (all 4) |

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
        |    |    +----------> XIAO D7 (GPIO20) - GPS sends data
        |    +---------------> XIAO D6 (GPIO21) - GPS receives data
        +--------------------> 3.3V (red) - DO NOT use 5V!

Baud Rate: 9600 (default)
Protocol: NMEA 0183
```

**Important:** The TX/RX labeling on GPS modules refers to the GPS perspective:
- GPS TX = GPS transmits data OUT -> connect to ESP RX (D7/GPIO20)
- GPS RX = GPS receives data IN -> connect to ESP TX (D6/GPIO21)

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
       |   |   |   +----------------> XIAO D4 (GPIO6 SDA)
       |   |   +--------------------> XIAO D5 (GPIO7 SCL)
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
       |    |    |    +-----------> XIAO D4 (GPIO6 shared SDA)
       |    |    +----------------> XIAO D5 (GPIO7 shared SCL)
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
        |  |  +---> Signal to XIAO GPIO
        |  +------> 5V from battery (or BEC)
        +---------> GND (common with XIAO)

Servo Assignments:
  Servo 1 (Top)    -> D0 (GPIO2)
  Servo 2 (Right)  -> D1 (GPIO3)
  Servo 3 (Bottom) -> D2 (GPIO4)
  Servo 4 (Left)   -> D3 (GPIO5)
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
| XIAO   |      | GPS      |      | IMU+Baro |
| 3V3 in |      | VCC      |      | VCC      |
+--------+      +----------+      +----------+

GND: All grounds connected together (common ground)

NOTES:
- SG90 servos can tolerate 4.8-6V, but work at 7.4V briefly
- For reliability, add a 5V BEC between battery and servos
- XIAO ESP32C3 can be powered via USB-C or 3V3 pin
- GPS module: USE 3.3V ONLY (5V may damage it)
```

---

## Complete Wiring Checklist

### Power Section
- [ ] Battery + (7.4V) -> AMS1117 VIN
- [ ] Battery + (7.4V) -> Servo VCC (all 4) [or through BEC]
- [ ] Battery - -> Common GND rail
- [ ] AMS1117 VOUT (3.3V) -> XIAO 3V3 pin
- [ ] AMS1117 VOUT (3.3V) -> GPS VCC
- [ ] AMS1117 VOUT (3.3V) -> MPU6050 VCC
- [ ] AMS1117 VOUT (3.3V) -> BMP280 VCC
- [ ] AMS1117 VOUT (3.3V) -> BMP280 CSB
- [ ] AMS1117 GND -> Common GND

### GPS (GY-NEO6MV2)
- [ ] GPS VCC -> 3.3V rail
- [ ] GPS GND -> GND rail
- [ ] GPS TX -> XIAO D7 (GPIO20) (yellow)
- [ ] GPS RX -> XIAO D6 (GPIO21) (green)

### IMU (GY-521 / MPU6050)
- [ ] IMU VCC -> 3.3V rail
- [ ] IMU GND -> GND rail
- [ ] IMU SDA -> XIAO D4 (GPIO6) (blue)
- [ ] IMU SCL -> XIAO D5 (GPIO7) (purple)
- [ ] IMU AD0 -> GND (sets address 0x68)

### Barometer (BMP280)
- [ ] BARO VCC -> 3.3V rail
- [ ] BARO GND -> GND rail
- [ ] BARO SDA -> XIAO D4 (GPIO6) (shared, blue)
- [ ] BARO SCL -> XIAO D5 (GPIO7) (shared, purple)
- [ ] BARO CSB -> 3.3V rail (sets address 0x76)

### Servos (x4)
- [ ] Servo 1 Signal (orange) -> XIAO D0 (GPIO2)
- [ ] Servo 2 Signal (orange) -> XIAO D1 (GPIO3)
- [ ] Servo 3 Signal (orange) -> XIAO D2 (GPIO4)
- [ ] Servo 4 Signal (orange) -> XIAO D3 (GPIO5)
- [ ] All Servo VCC (red) -> Battery + (or 5V BEC)
- [ ] All Servo GND (brown) -> Common GND

---

## Breadboard Test Setup

Before soldering, test on a breadboard:

```
BREADBOARD LAYOUT
================================

    [3.3V RAIL] +++++++++++++++++++++++++++++++
    [GND RAIL]  --------------------------------

    +-------+  +-------+  +-------+  +--------+
    | XIAO  |  |GY-521 |  |BMP280 |  |AMS1117 |
    |ESP32C3|  | IMU   |  | Baro  |  | 3.3V   |
    |       |  |       |  |       |  |        |
    +---+---+  +---+---+  +---+---+  +---+----+
        |          |          |          |
        +----------+----------+----------+
                   I2C Bus (SDA/SCL)

    +------------------+
    |  GY-NEO6MV2 GPS  |
    | [Ceramic Antenna]|
    +--------+---------+
             |
        UART (TX/RX)

    [Servos connect off-board with long wires]

    [GND RAIL]  --------------------------------
    [5V RAIL for servos] +++++++++++++++++++++++
```

---

## Quick Reference Card

```
Seeed XIAO ESP32C3 - ORB PIN SUMMARY
=========================================

D0 (GPIO2)  -> Servo 1 (Top)      [PWM]
D1 (GPIO3)  -> Servo 2 (Right)    [PWM]
D2 (GPIO4)  -> Servo 3 (Bottom)   [PWM]
D3 (GPIO5)  -> Servo 4 (Left)     [PWM]
D4 (GPIO6)  -> I2C SDA            [I2C]
D5 (GPIO7)  -> I2C SCL            [I2C]
D6 (GPIO21) -> GPS RX (ESP TX)    [UART1 TX]
D7 (GPIO20) -> GPS TX (ESP RX)    [UART1 RX]
3V3         -> All sensor VCC
GND         -> Common ground

I2C Devices:
  0x68 = MPU6050 (IMU)
  0x76 = BMP280 (Barometer)

GPS: 9600 baud, NMEA protocol
=========================================
```

---

## XIAO ESP32C3 vs ESP32-S3 Comparison

| Feature | XIAO ESP32C3 | ESP32-S3-DevKit |
|---------|--------------|-----------------|
| Size | 21 x 17.5mm | ~70 x 25mm |
| Weight | ~3g | ~10g |
| Flash | 4MB | 16MB |
| PSRAM | None | 8MB |
| USB Ports | Single Type-C | Dual Type-C |
| GPIO Count | 11 usable | 45 available |
| CPU | RISC-V Single Core | Xtensa Dual Core |
| CPU Speed | 160MHz | 240MHz |
| Price | ~$5 | ~$10 |
