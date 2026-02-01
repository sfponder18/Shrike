/*
 * ORB GUIDANCE FIRMWARE v1.0
 * ESP32-S3-DevKit C N16R8 + GY-NEO6MV2 GPS
 *
 * GPS-guided glide munition control system.
 *
 * Features:
 * - GPS navigation to target coordinates
 * - IMU-based attitude stabilization
 * - Barometric altitude measurement
 * - X-fin control mixing
 * - WiFi AP for target upload
 * - Serial command interface
 *
 * Uses native LEDC PWM for servos (no ESP32Servo library needed)
 */

#include <Wire.h>
#include <TinyGPSPlus.h>
#include <MPU6050.h>
#include <Adafruit_BMP280.h>
#include <WiFi.h>

// ============== VERSION ==============
#define FIRMWARE_VERSION "1.0"
#define ORB_ID "ORB_01"

// ============== PIN DEFINITIONS ==============
// ESP32-S3-DevKit C N16R8
#define SERVO1_PIN 4     // GPIO4 - Top fin
#define SERVO2_PIN 5     // GPIO5 - Right fin
#define SERVO3_PIN 6     // GPIO6 - Bottom fin
#define SERVO4_PIN 7     // GPIO7 - Left fin

#define GPS_TX_PIN 16    // ESP TX -> GPS RX
#define GPS_RX_PIN 17    // ESP RX <- GPS TX

#define I2C_SDA 18       // GPIO18
#define I2C_SCL 8        // GPIO8

// ============== GUIDANCE PARAMETERS ==============
#define GUIDANCE_RATE_HZ    20       // Guidance loop rate
#define GUIDANCE_PERIOD_MS  (1000 / GUIDANCE_RATE_HZ)

// PID Gains
#define Kp_HEADING  2.0f     // Heading correction gain
#define Ki_HEADING  0.0f     // Heading integral (usually 0 for glide)
#define Kd_HEADING  0.5f     // Heading derivative (damping)

#define Kp_PITCH    1.5f     // Pitch stabilization gain
#define Kp_ROLL     1.5f     // Roll stabilization gain

// Limits
#define MAX_FIN_DEFLECT    30.0f    // Max fin deflection (degrees from center)
#define TERMINAL_DISTANCE  15.0f    // Distance to enter terminal phase (meters)
#define MIN_ALTITUDE_AGL   5.0f     // Minimum altitude for guidance (meters)

// Glide parameters
#define TARGET_GLIDE_ANGLE -15.0f   // Target pitch angle during glide (degrees)
#define TERMINAL_DIVE_ANGLE -45.0f  // Steeper dive in terminal phase

// ============== SERVO PWM CONFIG ==============
// Using LEDC for servo PWM (50Hz, ~500-2400us pulse)
#define SERVO_FREQ 50
#define SERVO_RESOLUTION 14  // 14-bit resolution (16384 steps)
#define SERVO_MIN_TICKS 410  // ~500us at 50Hz/14-bit
#define SERVO_MAX_TICKS 1966 // ~2400us at 50Hz/14-bit

const int servoPins[4] = {SERVO1_PIN, SERVO2_PIN, SERVO3_PIN, SERVO4_PIN};

// ============== OBJECTS ==============
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
MPU6050 mpu;
Adafruit_BMP280 bmp;

// ============== STATE MACHINE ==============
enum FlightState {
    STATE_IDLE,        // On ground, not armed
    STATE_ARMED,       // Armed, waiting for release
    STATE_GLIDE,       // Active guidance, gliding to target
    STATE_TERMINAL,    // Terminal dive phase
    STATE_COMPLETE     // Mission complete
};

FlightState flightState = STATE_IDLE;
const char* stateNames[] = {"IDLE", "ARMED", "GLIDE", "TERMINAL", "COMPLETE"};

// ============== NAVIGATION DATA ==============
struct {
    double lat;
    double lon;
    double alt;
    float heading;      // GPS course over ground (degrees)
    float speed;        // Ground speed (m/s)
    uint8_t satellites;
    bool valid;
    unsigned long lastUpdate;
} navData;

struct {
    double lat;
    double lon;
    bool set;
    float bearing;      // Calculated bearing to target
    float distance;     // Distance to target (meters)
} target;

// ============== IMU DATA ==============
struct {
    float roll;         // Roll angle (degrees)
    float pitch;        // Pitch angle (degrees)
    float yaw;          // Yaw (not from IMU alone)
    float rollRate;     // Angular rate (deg/s)
    float pitchRate;
    float yawRate;
} attitude;

// ============== BAROMETER DATA ==============
struct {
    float pressure;     // hPa
    float temperature;  // Celsius
    float altitude;     // Meters (barometric)
    float initialAlt;   // Altitude at arm time
    float agl;          // Above ground level estimate
} baroData;

// ============== CONTROL ==============
struct {
    float pitch;        // Commanded pitch deflection
    float roll;         // Commanded roll deflection
    float yaw;          // Commanded yaw deflection
} finCommand;

// Timing
unsigned long lastGuidanceTime = 0;
unsigned long lastTelemetryTime = 0;
unsigned long armTime = 0;

// ============== WIFI ==============
const char* AP_SSID = ORB_ID;
const char* AP_PASS = "12345678";

// ============== SETUP ==============
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("========================================");
    Serial.printf("  ORB GUIDANCE SYSTEM v%s\n", FIRMWARE_VERSION);
    Serial.printf("  ID: %s\n", ORB_ID);
    Serial.println("  ESP32-S3-DevKit C N16R8");
    Serial.println("========================================");
    Serial.println();

    // Initialize I2C
    Wire.begin(I2C_SDA, I2C_SCL);
    delay(100);

    // Initialize GPS
    Serial.println("[INIT] GPS...");
    gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

    // Initialize IMU
    Serial.println("[INIT] IMU...");
    mpu.initialize();
    if (!mpu.testConnection()) {
        Serial.println("[ERROR] MPU6050 not found!");
    } else {
        Serial.println("[OK] MPU6050 connected");
        // Set gyro range to +/-500 deg/s
        mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
        // Set accel range to +/-4g
        mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
    }

    // Initialize Barometer
    Serial.println("[INIT] Barometer...");
    if (!bmp.begin(0x76)) {
        if (!bmp.begin(0x77)) {
            Serial.println("[ERROR] BMP280 not found!");
        }
    } else {
        Serial.println("[OK] BMP280 connected");
        bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                        Adafruit_BMP280::SAMPLING_X2,
                        Adafruit_BMP280::SAMPLING_X16,
                        Adafruit_BMP280::FILTER_X16,
                        Adafruit_BMP280::STANDBY_MS_63);
    }

    // Initialize Servos using LEDC PWM
    Serial.println("[INIT] Servos (LEDC PWM)...");
    for (int i = 0; i < 4; i++) {
        ledcAttach(servoPins[i], SERVO_FREQ, SERVO_RESOLUTION);
    }
    centerServos();
    Serial.println("[OK] Servos initialized");

    // Initialize WiFi AP
    Serial.println("[INIT] WiFi AP...");
    WiFi.softAP(AP_SSID, AP_PASS);
    Serial.printf("[OK] WiFi AP: %s\n", AP_SSID);
    Serial.printf("     IP: %s\n", WiFi.softAPIP().toString().c_str());

    // Initialize state
    target.set = false;
    navData.valid = false;

    Serial.println();
    Serial.println("========================================");
    Serial.println("  SYSTEM READY");
    Serial.println("========================================");
    printHelp();
}

// ============== MAIN LOOP ==============
void loop() {
    // Always read sensors
    readGPS();
    readIMU();
    readBarometer();

    // Process commands
    processSerialCommands();

    // Run guidance at fixed rate
    if (millis() - lastGuidanceTime >= GUIDANCE_PERIOD_MS) {
        lastGuidanceTime = millis();
        runGuidance();
    }

    // Telemetry output (1 Hz)
    if (millis() - lastTelemetryTime >= 1000) {
        lastTelemetryTime = millis();
        printTelemetry();
    }
}

// ============== SENSOR READING ==============
void readGPS() {
    while (gpsSerial.available()) {
        if (gps.encode(gpsSerial.read())) {
            if (gps.location.isValid()) {
                navData.lat = gps.location.lat();
                navData.lon = gps.location.lng();
                navData.heading = gps.course.isValid() ? gps.course.deg() : 0;
                navData.speed = gps.speed.isValid() ? gps.speed.mps() : 0;
                navData.satellites = gps.satellites.value();
                navData.valid = true;
                navData.lastUpdate = millis();

                if (gps.altitude.isValid()) {
                    navData.alt = gps.altitude.meters();
                }

                // Update target calculations if target is set
                if (target.set) {
                    target.bearing = TinyGPSPlus::courseTo(
                        navData.lat, navData.lon,
                        target.lat, target.lon
                    );
                    target.distance = TinyGPSPlus::distanceBetween(
                        navData.lat, navData.lon,
                        target.lat, target.lon
                    );
                }
            }
        }
    }

    // Mark as stale if no update in 3 seconds
    if (millis() - navData.lastUpdate > 3000) {
        navData.valid = false;
    }
}

void readIMU() {
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Convert to real units
    // Accel: 8192 LSB/g for +/-4g range
    float accelX = ax / 8192.0f;
    float accelY = ay / 8192.0f;
    float accelZ = az / 8192.0f;

    // Gyro: 65.5 LSB/(deg/s) for +/-500 deg/s range
    attitude.rollRate = gx / 65.5f;
    attitude.pitchRate = gy / 65.5f;
    attitude.yawRate = gz / 65.5f;

    // Calculate attitude from accelerometer
    // (Simple complementary filter would be better, but this works for testing)
    attitude.roll = atan2(accelY, accelZ) * 180.0f / PI;
    attitude.pitch = atan2(-accelX, sqrt(accelY*accelY + accelZ*accelZ)) * 180.0f / PI;
}

void readBarometer() {
    baroData.pressure = bmp.readPressure() / 100.0f;  // Pa to hPa
    baroData.temperature = bmp.readTemperature();
    baroData.altitude = bmp.readAltitude(1013.25);    // Standard pressure

    // Calculate AGL if we have initial altitude
    if (flightState >= STATE_ARMED) {
        baroData.agl = baroData.altitude - baroData.initialAlt;
    }
}

// ============== GUIDANCE ==============
void runGuidance() {
    switch (flightState) {
        case STATE_IDLE:
            centerServos();
            break;

        case STATE_ARMED:
            centerServos();
            // Could add pre-release checks here
            break;

        case STATE_GLIDE:
            if (target.set && navData.valid) {
                // Calculate heading error
                float headingError = target.bearing - navData.heading;
                // Normalize to -180 to +180
                while (headingError > 180) headingError -= 360;
                while (headingError < -180) headingError += 360;

                // Roll to turn toward target
                finCommand.roll = constrain(Kp_HEADING * headingError,
                                           -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);

                // Pitch for glide angle
                float pitchError = TARGET_GLIDE_ANGLE - attitude.pitch;
                finCommand.pitch = constrain(Kp_PITCH * pitchError,
                                            -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);

                // Roll stabilization (counter unwanted roll)
                finCommand.roll -= Kp_ROLL * attitude.roll * 0.3f;

                // Apply fin commands
                setFins(finCommand.pitch, finCommand.roll, 0);

                // Check for terminal phase
                if (target.distance < TERMINAL_DISTANCE) {
                    Serial.println("[GUIDANCE] Entering TERMINAL phase");
                    flightState = STATE_TERMINAL;
                }
            } else {
                // No valid navigation - hold attitude
                stabilizeAttitude();
            }
            break;

        case STATE_TERMINAL:
            // Steep dive to target
            finCommand.pitch = constrain(Kp_PITCH * (TERMINAL_DIVE_ANGLE - attitude.pitch),
                                        -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);

            // Continue heading correction but reduced
            if (target.set && navData.valid) {
                float headingError = target.bearing - navData.heading;
                while (headingError > 180) headingError -= 360;
                while (headingError < -180) headingError += 360;
                finCommand.roll = constrain(Kp_HEADING * headingError * 0.5f,
                                           -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);
            }

            setFins(finCommand.pitch, finCommand.roll, 0);

            // Check for impact (altitude low or no motion)
            if (baroData.agl < MIN_ALTITUDE_AGL || navData.speed < 1.0f) {
                Serial.println("[GUIDANCE] Mission COMPLETE");
                flightState = STATE_COMPLETE;
            }
            break;

        case STATE_COMPLETE:
            centerServos();
            break;
    }
}

void stabilizeAttitude() {
    // Simple attitude hold when no nav
    finCommand.pitch = constrain(-Kp_PITCH * attitude.pitch,
                                -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);
    finCommand.roll = constrain(-Kp_ROLL * attitude.roll,
                               -MAX_FIN_DEFLECT, MAX_FIN_DEFLECT);
    setFins(finCommand.pitch, finCommand.roll, 0);
}

// ============== FIN CONTROL ==============
void servoWrite(int channel, int angle) {
    angle = constrain(angle, 0, 180);
    int ticks = map(angle, 0, 180, SERVO_MIN_TICKS, SERVO_MAX_TICKS);
    ledcWrite(servoPins[channel], ticks);
}

void setFins(float pitch, float roll, float yaw) {
    /*
     * X-fin configuration (looking from rear):
     *
     *        1 (Top)
     *       / \
     *      /   \
     *     4     2
     *      \   /
     *       \ /
     *        3 (Bottom)
     *
     * Pitch: Fins 1&3 move same direction
     * Roll:  Fins 2&4 move same direction
     * Yaw:   Differential on all fins
     */

    int fin1 = (int)(90 + pitch - roll + yaw);   // Top
    int fin2 = (int)(90 + roll + yaw);           // Right
    int fin3 = (int)(90 - pitch - roll - yaw);   // Bottom
    int fin4 = (int)(90 - roll - yaw);           // Left

    servoWrite(0, constrain(fin1, 45, 135));
    servoWrite(1, constrain(fin2, 45, 135));
    servoWrite(2, constrain(fin3, 45, 135));
    servoWrite(3, constrain(fin4, 45, 135));
}

void centerServos() {
    for (int i = 0; i < 4; i++) {
        servoWrite(i, 90);
    }
    finCommand.pitch = 0;
    finCommand.roll = 0;
    finCommand.yaw = 0;
}

// ============== COMMANDS ==============
void processSerialCommands() {
    if (!Serial.available()) return;

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd.length() == 0) return;

    char firstChar = cmd.charAt(0);

    switch (firstChar) {
        case 'T':  // Target: T<lat>,<lon>
            parseTargetCommand(cmd);
            break;

        case 'A':  // Arm
            if (target.set && navData.valid) {
                flightState = STATE_ARMED;
                baroData.initialAlt = baroData.altitude;
                armTime = millis();
                Serial.println("[CMD] ARMED - Waiting for release");
            } else {
                Serial.println("[CMD] Cannot arm: ");
                if (!target.set) Serial.println("  - No target set");
                if (!navData.valid) Serial.println("  - No GPS fix");
            }
            break;

        case 'R':  // Release
            if (flightState == STATE_ARMED) {
                flightState = STATE_GLIDE;
                Serial.println("[CMD] RELEASED - Guidance active");
            } else {
                Serial.println("[CMD] Cannot release: Not armed");
            }
            break;

        case 'S':  // Safe / Disarm
            flightState = STATE_IDLE;
            target.set = false;
            centerServos();
            Serial.println("[CMD] SAFE - Disarmed, target cleared");
            break;

        case 'C':  // Center servos
            centerServos();
            Serial.println("[CMD] Servos centered");
            break;

        case 'H':  // Help
        case '?':
            printHelp();
            break;

        case 'V':  // Version
            Serial.printf("ORB Guidance v%s, ID: %s\n", FIRMWARE_VERSION, ORB_ID);
            break;

        default:
            Serial.printf("[CMD] Unknown command: %s\n", cmd.c_str());
            break;
    }
}

void parseTargetCommand(String cmd) {
    // Format: T<lat>,<lon>
    // Example: T51.5074,-0.1278

    int commaPos = cmd.indexOf(',');
    if (commaPos < 2) {
        Serial.println("[CMD] Invalid target format. Use: T<lat>,<lon>");
        return;
    }

    String latStr = cmd.substring(1, commaPos);
    String lonStr = cmd.substring(commaPos + 1);

    target.lat = latStr.toDouble();
    target.lon = lonStr.toDouble();

    if (target.lat == 0 && target.lon == 0) {
        Serial.println("[CMD] Invalid coordinates");
        return;
    }

    target.set = true;

    // Calculate initial bearing and distance if we have GPS
    if (navData.valid) {
        target.bearing = TinyGPSPlus::courseTo(
            navData.lat, navData.lon,
            target.lat, target.lon
        );
        target.distance = TinyGPSPlus::distanceBetween(
            navData.lat, navData.lon,
            target.lat, target.lon
        );
        Serial.printf("[CMD] Target set: %.6f, %.6f\n", target.lat, target.lon);
        Serial.printf("      Bearing: %.1f deg, Distance: %.1f m\n",
                      target.bearing, target.distance);
    } else {
        Serial.printf("[CMD] Target set: %.6f, %.6f (no GPS for bearing)\n",
                      target.lat, target.lon);
    }
}

// ============== TELEMETRY ==============
void printTelemetry() {
    Serial.print("[");
    Serial.print(stateNames[flightState]);
    Serial.print("] ");

    // GPS
    if (navData.valid) {
        Serial.printf("GPS:%.5f,%.5f ", navData.lat, navData.lon);
        Serial.printf("Hdg:%.0f Spd:%.1f Sat:%d | ",
                      navData.heading, navData.speed, navData.satellites);
    } else {
        Serial.printf("GPS:NoFix Sat:%d | ", gps.satellites.value());
    }

    // Attitude
    Serial.printf("R:%.1f P:%.1f | ", attitude.roll, attitude.pitch);

    // Altitude
    Serial.printf("Alt:%.1f AGL:%.1f | ", baroData.altitude, baroData.agl);

    // Target info
    if (target.set) {
        Serial.printf("Tgt:%.1fm @%.0f", target.distance, target.bearing);
    }

    Serial.println();
}

void printHelp() {
    Serial.println();
    Serial.println("=== ORB COMMANDS ===");
    Serial.println("T<lat>,<lon>  Set target (e.g., T51.5074,-0.1278)");
    Serial.println("A             Arm (requires target + GPS fix)");
    Serial.println("R             Release (start guidance)");
    Serial.println("S             Safe (disarm, clear target)");
    Serial.println("C             Center all servos");
    Serial.println("H or ?        Show this help");
    Serial.println("V             Show version");
    Serial.println();
}
