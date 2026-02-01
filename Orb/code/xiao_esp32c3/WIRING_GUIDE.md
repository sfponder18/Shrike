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

## Complete Wiring Checklist

### Power Section
- [ ] Battery + (7.4V) -> AMS1117 VIN
- [ ] Battery + (7.4V) -> Servo VCC (all 4)
- [ ] Battery - -> Common GND rail
- [ ] AMS1117 VOUT (3.3V) -> XIAO 3V3 pin
- [ ] AMS1117 VOUT (3.3V) -> GPS VCC
- [ ] AMS1117 VOUT (3.3V) -> MPU6050 VCC
- [ ] AMS1117 VOUT (3.3V) -> BMP280 VCC
- [ ] AMS1117 GND -> Common GND

### GPS (GY-NEO6MV2)
- [ ] GPS VCC -> 3.3V rail
- [ ] GPS GND -> GND rail
- [ ] GPS TX -> XIAO D7 (GPIO20)
- [ ] GPS RX -> XIAO D6 (GPIO21)

### IMU (GY-521 / MPU6050)
- [ ] IMU VCC -> 3.3V rail
- [ ] IMU GND -> GND rail
- [ ] IMU SDA -> XIAO D4 (GPIO6)
- [ ] IMU SCL -> XIAO D5 (GPIO7)
- [ ] IMU AD0 -> GND (sets address 0x68)

### Barometer (BMP280)
- [ ] BARO VCC -> 3.3V rail
- [ ] BARO GND -> GND rail
- [ ] BARO SDA -> XIAO D4 (GPIO6, shared)
- [ ] BARO SCL -> XIAO D5 (GPIO7, shared)
- [ ] BARO CSB -> 3.3V rail (sets address 0x76)

### Servos (x4)
- [ ] Servo 1 Signal -> XIAO D0 (GPIO2)
- [ ] Servo 2 Signal -> XIAO D1 (GPIO3)
- [ ] Servo 3 Signal -> XIAO D2 (GPIO4)
- [ ] Servo 4 Signal -> XIAO D3 (GPIO5)
- [ ] All Servo VCC -> Battery + (or 5V BEC)
- [ ] All Servo GND -> Common GND
