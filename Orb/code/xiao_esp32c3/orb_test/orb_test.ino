/*
 * ORB TEST FIRMWARE
 * Seeed XIAO ESP32C3 + GY-NEO6MV2 GPS
 *
 * Tests all components:
 * - I2C scan for MPU6050 and BMP280
 * - GPS NMEA parsing
 * - Servo sweep
 *
 * Upload this first to verify all wiring is correct.
 *
 * Uses native LEDC PWM for servos (no ESP32Servo library needed)
 */

#include <Wire.h>
#include <TinyGPSPlus.h>
#include <MPU6050.h>
#include <Adafruit_BMP280.h>

// ============== PIN DEFINITIONS ==============
// Seeed XIAO ESP32C3
#define SERVO1_PIN 2     // D0 (GPIO2) - Top fin
#define SERVO2_PIN 3     // D1 (GPIO3) - Right fin
#define SERVO3_PIN 4     // D2 (GPIO4) - Bottom fin
#define SERVO4_PIN 5     // D3 (GPIO5) - Left fin

#define GPS_TX_PIN 21    // D6 (GPIO21) - ESP TX -> GPS RX
#define GPS_RX_PIN 20    // D7 (GPIO20) - ESP RX <- GPS TX

#define I2C_SDA 6        // D4 (GPIO6) - XIAO default SDA
#define I2C_SCL 7        // D5 (GPIO7) - XIAO default SCL

// ============== SERVO PWM CONFIG ==============
#define SERVO_FREQ 50
#define SERVO_RESOLUTION 14
#define SERVO_MIN_TICKS 410
#define SERVO_MAX_TICKS 1966

const int servoPins[4] = {SERVO1_PIN, SERVO2_PIN, SERVO3_PIN, SERVO4_PIN};

// ============== OBJECTS ==============
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
MPU6050 mpu;
Adafruit_BMP280 bmp;

// ============== STATE ==============
bool mpuFound = false;
bool bmpFound = false;

// ============== SERVO FUNCTIONS ==============
void servoSetup() {
    for (int i = 0; i < 4; i++) {
        ledcAttach(servoPins[i], SERVO_FREQ, SERVO_RESOLUTION);
    }
}

void servoWrite(int channel, int angle) {
    angle = constrain(angle, 0, 180);
    int ticks = map(angle, 0, 180, SERVO_MIN_TICKS, SERVO_MAX_TICKS);
    ledcWrite(servoPins[channel], ticks);
}

void servoWriteAll(int angle) {
    for (int i = 0; i < 4; i++) {
        servoWrite(i, angle);
    }
}

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("================================");
    Serial.println("   ORB TEST FIRMWARE v1.1");
    Serial.println("   Seeed XIAO ESP32C3");
    Serial.println("================================");
    Serial.println();

    // Initialize I2C
    Serial.println("[I2C] Initializing...");
    Wire.begin(I2C_SDA, I2C_SCL);
    delay(100);

    // I2C Bus Scan
    Serial.println("[I2C] Scanning bus...");
    scanI2C();

    // Initialize GPS Serial
    Serial.println("\n[GPS] Initializing UART1...");
    gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
    Serial.println("[GPS] GY-NEO6MV2 @ 9600 baud");
    Serial.println("[GPS] Waiting for data...");

    // Initialize MPU6050
    Serial.println("\n[IMU] Initializing MPU6050...");
    mpu.initialize();
    if (mpu.testConnection()) {
        Serial.println("[IMU] MPU6050 connected OK!");
        mpuFound = true;
    } else {
        Serial.println("[IMU] ERROR: MPU6050 not responding!");
        Serial.println("[IMU] Check: SDA->D4(GPIO6), SCL->D5(GPIO7), AD0->GND");
    }

    // Initialize BMP280
    Serial.println("\n[BARO] Initializing BMP280...");
    if (bmp.begin(0x76)) {
        Serial.println("[BARO] BMP280 connected OK!");
        bmpFound = true;
        bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                        Adafruit_BMP280::SAMPLING_X2,
                        Adafruit_BMP280::SAMPLING_X16,
                        Adafruit_BMP280::FILTER_X16,
                        Adafruit_BMP280::STANDBY_MS_500);
    } else {
        Serial.println("[BARO] ERROR: BMP280 not found at 0x76!");
        if (bmp.begin(0x77)) {
            Serial.println("[BARO] Found at alternate address 0x77");
            bmpFound = true;
        }
    }

    // Initialize Servos
    Serial.println("\n[SERVO] Initializing servos (LEDC PWM)...");
    servoSetup();
    servoWriteAll(90);
    Serial.println("[SERVO] All servos centered to 90 degrees");

    Serial.println();
    Serial.println("================================");
    Serial.println("   SETUP COMPLETE");
    Serial.println("================================");
    Serial.println();
    Serial.println("Commands:");
    Serial.println("  s - Servo sweep test");
    Serial.println("  c - Center all servos");
    Serial.println("  i - I2C rescan");
    Serial.println("  g - Show GPS raw data");
    Serial.println("  1-4 - Move individual servo");
    Serial.println();
}

void loop() {
    static unsigned long lastPrint = 0;

    // Read GPS
    while (gpsSerial.available()) {
        gps.encode(gpsSerial.read());
    }

    // Process commands
    if (Serial.available()) {
        processCommand(Serial.read());
    }

    // Print sensor data every 2 seconds
    if (millis() - lastPrint >= 2000) {
        lastPrint = millis();
        printSensorData();
    }
}

void scanI2C() {
    byte count = 0;
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        byte error = Wire.endTransmission();
        if (error == 0) {
            Serial.printf("  Found device at 0x%02X", addr);
            if (addr == 0x68) Serial.print(" <- MPU6050");
            if (addr == 0x69) Serial.print(" <- MPU6050 (AD0=VCC)");
            if (addr == 0x76) Serial.print(" <- BMP280");
            if (addr == 0x77) Serial.print(" <- BMP280 (alt addr)");
            Serial.println();
            count++;
        }
    }
    if (count == 0) {
        Serial.println("  No I2C devices found!");
        Serial.println("  Check wiring: SDA=D4(GPIO6), SCL=D5(GPIO7)");
    } else {
        Serial.printf("  Found %d device(s)\n", count);
    }
}

void printSensorData() {
    Serial.println("--- SENSOR READINGS ---");

    // GPS
    Serial.print("GPS: ");
    if (gps.location.isValid()) {
        Serial.printf("%.6f, %.6f", gps.location.lat(), gps.location.lng());
        if (gps.altitude.isValid()) {
            Serial.printf(" Alt: %.1fm", gps.altitude.meters());
        }
    } else {
        Serial.print("No fix");
    }
    Serial.printf(" | Sats: %d", gps.satellites.value());
    Serial.printf(" | Chars: %lu", gps.charsProcessed());
    if (gps.charsProcessed() < 10) {
        Serial.print(" [Check GPS wiring!]");
    }
    Serial.println();

    // IMU
    if (mpuFound) {
        int16_t ax, ay, az, gx, gy, gz;
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        Serial.printf("IMU: Accel(%6d, %6d, %6d) Gyro(%6d, %6d, %6d)\n",
                      ax, ay, az, gx, gy, gz);

        float roll = atan2(ay, az) * 180.0 / PI;
        float pitch = atan2(-ax, sqrt(ay*ay + az*az)) * 180.0 / PI;
        Serial.printf("     Roll: %.1f deg, Pitch: %.1f deg\n", roll, pitch);
    } else {
        Serial.println("IMU: NOT CONNECTED");
    }

    // Barometer
    if (bmpFound) {
        float pressure = bmp.readPressure() / 100.0;
        float temp = bmp.readTemperature();
        float altitude = bmp.readAltitude(1013.25);
        Serial.printf("BARO: %.1f hPa, %.1f C, Est.Alt: %.1f m\n",
                      pressure, temp, altitude);
    } else {
        Serial.println("BARO: NOT CONNECTED");
    }

    Serial.println();
}

void processCommand(char cmd) {
    switch (cmd) {
        case 's':
        case 'S':
            servoSweepTest();
            break;

        case 'c':
        case 'C':
            centerServos();
            break;

        case 'i':
        case 'I':
            Serial.println("\n[I2C] Rescanning...");
            scanI2C();
            break;

        case 'g':
        case 'G':
            Serial.println("\n[GPS] Showing raw NMEA for 10 seconds...");
            showRawGpsData();
            break;

        case '1':
            testSingleServo(0);
            break;
        case '2':
            testSingleServo(1);
            break;
        case '3':
            testSingleServo(2);
            break;
        case '4':
            testSingleServo(3);
            break;
    }
}

void servoSweepTest() {
    Serial.println("\n[SERVO] Starting sweep test...");

    for (int angle = 90; angle >= 60; angle -= 2) {
        servoWriteAll(angle);
        delay(30);
    }
    Serial.println("  At 60 degrees");
    delay(500);

    for (int angle = 60; angle <= 120; angle += 2) {
        servoWriteAll(angle);
        delay(30);
    }
    Serial.println("  At 120 degrees");
    delay(500);

    for (int angle = 120; angle >= 90; angle -= 2) {
        servoWriteAll(angle);
        delay(30);
    }
    Serial.println("  Back to 90 degrees (center)");
    Serial.println("[SERVO] Sweep test complete!\n");
}

void centerServos() {
    Serial.println("\n[SERVO] Centering all servos...");
    servoWriteAll(90);
    Serial.println("[SERVO] Done.\n");
}

void testSingleServo(int servoNum) {
    const char* names[] = {"Top", "Right", "Bottom", "Left"};
    Serial.printf("\n[SERVO] Testing Servo %d (%s)...\n", servoNum + 1, names[servoNum]);

    for (int angle = 90; angle >= 45; angle -= 5) {
        servoWrite(servoNum, angle);
        delay(50);
    }
    for (int angle = 45; angle <= 135; angle += 5) {
        servoWrite(servoNum, angle);
        delay(50);
    }
    for (int angle = 135; angle >= 90; angle -= 5) {
        servoWrite(servoNum, angle);
        delay(50);
    }
    Serial.printf("[SERVO] Servo %d test complete.\n\n", servoNum + 1);
}

void showRawGpsData() {
    unsigned long startTime = millis();
    int charCount = 0;

    while (millis() - startTime < 10000) {
        while (gpsSerial.available()) {
            char c = gpsSerial.read();
            Serial.print(c);
            gps.encode(c);
            charCount++;
        }
    }

    Serial.println();
    Serial.printf("\n[GPS] Received %d characters in 10 seconds.\n", charCount);
    if (charCount == 0) {
        Serial.println("[GPS] WARNING: No data received!");
        Serial.println("      Check: TX->D7(GPIO20), RX->D6(GPIO21), VCC->3.3V");
    }
    Serial.println();
}
