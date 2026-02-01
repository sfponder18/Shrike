/*
 * ORB CALIBRATION FIRMWARE
 * ESP32-S3-DevKit C N16R8
 *
 * Features:
 * - IMU calibration (accel + gyro offsets)
 * - Real-time orientation streaming for visualization
 * - Servo testing and trim adjustment
 * - Sensor health checks
 *
 * Streams data in format: $ORB,roll,pitch,yaw,ax,ay,az,gx,gy,gz,servo1,servo2,servo3,servo4*
 */

#include <Wire.h>
#include <MPU6050.h>
#include <Adafruit_BMP280.h>
#include <Preferences.h>  // For storing calibration in NVS

// ============== PIN DEFINITIONS ==============
// ESP32-S3-DevKit C N16R8
#define SERVO1_PIN 4     // GPIO4 - Top fin
#define SERVO2_PIN 5     // GPIO5 - Right fin
#define SERVO3_PIN 6     // GPIO6 - Bottom fin
#define SERVO4_PIN 7     // GPIO7 - Left fin
#define I2C_SDA 18       // GPIO18
#define I2C_SCL 8        // GPIO8

// ============== SERVO PWM CONFIG ==============
#define SERVO_FREQ 50
#define SERVO_RESOLUTION 14
#define SERVO_MIN_TICKS 410
#define SERVO_MAX_TICKS 1966

const int servoPins[4] = {SERVO1_PIN, SERVO2_PIN, SERVO3_PIN, SERVO4_PIN};

// ============== OBJECTS ==============
MPU6050 mpu;
Adafruit_BMP280 bmp;
Preferences prefs;

// ============== CALIBRATION DATA ==============
struct CalibrationData {
    float gyroBias[3];       // X, Y, Z (software bias in raw units)
    float accelBias[3];      // X, Y, Z (software offsets in g)
    float mountOffset[3];    // Roll, Pitch, Yaw mounting offsets in degrees
    int8_t servoTrim[4];     // Servo center trim
    bool valid;
} calibration;

// ============== AXIS MAPPING ==============
// Maps sensor axes to aircraft axes
// axisMap[0] = roll source,  axisMap[1] = pitch source,  axisMap[2] = yaw source
// Values: 0=+X, 1=+Y, 2=+Z, 3=-X, 4=-Y, 5=-Z
int8_t axisMap[3] = {0, 1, 2};  // Default: Roll=X, Pitch=Y, Yaw=Z

const char* axisNames[] = {"+X", "+Y", "+Z", "-X", "-Y", "-Z"};

int8_t parseAxis(String s) {
    s.trim();
    s.toUpperCase();
    if (s == "+X" || s == "X") return 0;
    if (s == "+Y" || s == "Y") return 1;
    if (s == "+Z" || s == "Z") return 2;
    if (s == "-X") return 3;
    if (s == "-Y") return 4;
    if (s == "-Z") return 5;
    Serial.println("[ERROR] Invalid axis. Use: +X +Y +Z -X -Y -Z");
    return -1;
}

// ============== STATE ==============
float roll = 0, pitch = 0, yaw = 0;
int16_t ax, ay, az, gx, gy, gz;
float accelRaw[3];   // Raw calibrated accel X, Y, Z
float gyroRaw[3];    // Raw calibrated gyro X, Y, Z
float accelX, accelY, accelZ;  // Mapped to aircraft frame
float gyroX, gyroY, gyroZ;     // Mapped to aircraft frame
int servoPos[4] = {90, 90, 90, 90};
bool streamingEnabled = true;
unsigned long lastStreamTime = 0;
int streamRate = 50;  // ms between updates (20 Hz)

// Complementary filter
float alpha = 0.98;
unsigned long lastUpdateTime = 0;

void setup() {
    Serial.begin(115200);

    // Wait for USB CDC to be ready (important for ESP32-S3!)
    unsigned long startWait = millis();
    while (!Serial && (millis() - startWait < 3000)) {
        delay(10);
    }
    delay(500);

    // Early debug - this should ALWAYS print if USB is working
    Serial.println();
    Serial.println("*** ESP32-S3 BOOT OK ***");
    Serial.flush();

    Serial.println("=================================");
    Serial.println("  ORB CALIBRATION TOOL v1.0");
    Serial.println("  ESP32-S3-DevKit C N16R8");
    Serial.println("=================================");
    Serial.println();
    Serial.flush();

    // Initialize I2C
    Serial.println("[INIT] I2C bus...");
    Serial.flush();
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);  // 400kHz I2C
    delay(100);
    Serial.println("[OK] I2C ready");
    Serial.flush();

    // Initialize IMU with timeout protection
    Serial.println("[INIT] MPU6050...");
    Serial.flush();
    mpu.initialize();
    if (!mpu.testConnection()) {
        Serial.println("[ERROR] MPU6050 not found!");
    } else {
        Serial.println("[OK] MPU6050 connected");
        mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
        mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
    }
    Serial.flush();

    // Initialize Barometer
    Serial.println("[INIT] BMP280...");
    Serial.flush();
    bool bmpFound = bmp.begin(0x76);
    if (!bmpFound) {
        bmpFound = bmp.begin(0x77);
    }
    if (bmpFound) {
        Serial.println("[OK] BMP280 connected");
    } else {
        Serial.println("[WARN] BMP280 not found");
    }
    Serial.flush();

    // Initialize Servos
    Serial.println("[INIT] Servos...");
    for (int i = 0; i < 4; i++) {
        ledcAttach(servoPins[i], SERVO_FREQ, SERVO_RESOLUTION);
    }
    centerServos();

    // Load calibration from NVS
    loadCalibration();

    // Apply calibration if valid
    if (calibration.valid) {
        Serial.println("[CAL] Loaded saved calibration");
        Serial.printf("[CAL] Accel bias: %.4f, %.4f, %.4f g\n",
                      calibration.accelBias[0], calibration.accelBias[1], calibration.accelBias[2]);
        Serial.printf("[CAL] Gyro bias: %.1f, %.1f, %.1f raw\n",
                      calibration.gyroBias[0], calibration.gyroBias[1], calibration.gyroBias[2]);
    } else {
        Serial.println("[CAL] No calibration found - run 'cal' command");
    }

    lastUpdateTime = micros();

    printHelp();
}

void loop() {
    // Read IMU
    readIMU();

    // Calculate orientation
    calculateOrientation();

    // Process commands
    processCommands();

    // Stream data
    if (streamingEnabled && (millis() - lastStreamTime >= streamRate)) {
        lastStreamTime = millis();
        streamData();
    }
}

float getAxisValue(float* data, int8_t axis) {
    int idx = axis % 3;
    float val = data[idx];
    return (axis >= 3) ? -val : val;  // Negative if axis >= 3
}

void readIMU() {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Convert to real units and apply calibration
    // Accel: 8192 LSB/g for +/-4g range
    accelRaw[0] = ax / 8192.0f - calibration.accelBias[0];
    accelRaw[1] = ay / 8192.0f - calibration.accelBias[1];
    accelRaw[2] = az / 8192.0f - calibration.accelBias[2];

    // Gyro: 65.5 LSB/(deg/s) for +/-500 deg/s range
    // Subtract software bias (in raw units) then convert
    gyroRaw[0] = (gx - calibration.gyroBias[0]) / 65.5f;
    gyroRaw[1] = (gy - calibration.gyroBias[1]) / 65.5f;
    gyroRaw[2] = (gz - calibration.gyroBias[2]) / 65.5f;

    // Apply axis mapping to aircraft frame
    accelX = getAxisValue(accelRaw, axisMap[0]);  // Roll axis accel
    accelY = getAxisValue(accelRaw, axisMap[1]);  // Pitch axis accel
    accelZ = getAxisValue(accelRaw, axisMap[2]);  // Yaw axis accel (vertical)

    gyroX = getAxisValue(gyroRaw, axisMap[0]);    // Roll rate
    gyroY = getAxisValue(gyroRaw, axisMap[1]);    // Pitch rate
    gyroZ = getAxisValue(gyroRaw, axisMap[2]);    // Yaw rate
}

void calculateOrientation() {
    unsigned long now = micros();
    float dt = (now - lastUpdateTime) / 1000000.0f;
    lastUpdateTime = now;

    // Limit dt to prevent issues
    if (dt > 0.1) dt = 0.1;

    // Accelerometer angles
    float accelRoll = atan2(accelY, accelZ) * 180.0f / PI;
    float accelPitch = atan2(-accelX, sqrt(accelY*accelY + accelZ*accelZ)) * 180.0f / PI;

    // Complementary filter
    roll = alpha * (roll + gyroX * dt) + (1.0f - alpha) * accelRoll;
    pitch = alpha * (pitch + gyroY * dt) + (1.0f - alpha) * accelPitch;

    yaw += gyroZ * dt;

    // Apply mounting offsets
    roll -= calibration.mountOffset[0];
    pitch -= calibration.mountOffset[1];
    yaw -= calibration.mountOffset[2];

    // Normalize yaw to -180 to 180
    while (yaw > 180) yaw -= 360;
    while (yaw < -180) yaw += 360;
}

void streamData() {
    // Format: $ORB,roll,pitch,yaw,ax,ay,az,gx,gy,gz,s1,s2,s3,s4,temp,pressure*
    Serial.print("$ORB,");
    Serial.print(roll, 2); Serial.print(",");
    Serial.print(pitch, 2); Serial.print(",");
    Serial.print(yaw, 2); Serial.print(",");
    Serial.print(accelX, 3); Serial.print(",");
    Serial.print(accelY, 3); Serial.print(",");
    Serial.print(accelZ, 3); Serial.print(",");
    Serial.print(gyroX, 2); Serial.print(",");
    Serial.print(gyroY, 2); Serial.print(",");
    Serial.print(gyroZ, 2); Serial.print(",");
    Serial.print(servoPos[0]); Serial.print(",");
    Serial.print(servoPos[1]); Serial.print(",");
    Serial.print(servoPos[2]); Serial.print(",");
    Serial.print(servoPos[3]); Serial.print(",");
    Serial.print(bmp.readTemperature(), 1); Serial.print(",");
    Serial.print(bmp.readPressure() / 100.0f, 1);
    Serial.println("*");
}

void processCommands() {
    if (!Serial.available()) return;

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toLowerCase();

    if (cmd == "help" || cmd == "?") {
        printHelp();
    }
    else if (cmd == "cal") {
        runCalibration();
    }
    else if (cmd == "calgyro") {
        calibrateGyro();
    }
    else if (cmd == "calaccel") {
        calibrateAccel();
    }
    else if (cmd == "save") {
        saveCalibration();
    }
    else if (cmd == "load") {
        loadCalibration();
        applyCalibration();
    }
    else if (cmd == "clear") {
        clearCalibration();
    }
    else if (cmd == "status") {
        printStatus();
    }
    else if (cmd == "stream on") {
        streamingEnabled = true;
        Serial.println("[OK] Streaming enabled");
    }
    else if (cmd == "stream off") {
        streamingEnabled = false;
        Serial.println("[OK] Streaming disabled");
    }
    else if (cmd.startsWith("rate ")) {
        streamRate = cmd.substring(5).toInt();
        streamRate = constrain(streamRate, 10, 1000);
        Serial.printf("[OK] Stream rate: %d ms\n", streamRate);
    }
    else if (cmd == "center") {
        centerServos();
        Serial.println("[OK] Servos centered");
    }
    else if (cmd == "sweep") {
        servoSweep();
    }
    else if (cmd.startsWith("servo ")) {
        // servo <num> <angle>
        int num = cmd.substring(6, 7).toInt();
        int angle = cmd.substring(8).toInt();
        if (num >= 1 && num <= 4) {
            setServo(num - 1, angle);
            Serial.printf("[OK] Servo %d -> %d\n", num, angle);
        }
    }
    else if (cmd.startsWith("trim ")) {
        // trim <num> <offset>
        int num = cmd.substring(5, 6).toInt();
        int offset = cmd.substring(7).toInt();
        if (num >= 1 && num <= 4) {
            calibration.servoTrim[num - 1] = constrain(offset, -20, 20);
            Serial.printf("[OK] Servo %d trim: %d\n", num, calibration.servoTrim[num - 1]);
        }
    }
    else if (cmd == "resetyaw") {
        yaw = 0;
        Serial.println("[OK] Yaw reset to 0");
    }
    else if (cmd == "zero") {
        roll = 0;
        pitch = 0;
        yaw = 0;
        lastUpdateTime = micros();
        Serial.println("[OK] Orientation zeroed");
    }
    else if (cmd.startsWith("mount ")) {
        // mount <roll> <pitch> <yaw>
        // Example: mount 5.5 -2.0 0
        int firstSpace = cmd.indexOf(' ', 6);
        int secondSpace = cmd.indexOf(' ', firstSpace + 1);
        if (firstSpace > 0 && secondSpace > 0) {
            calibration.mountOffset[0] = cmd.substring(6, firstSpace).toFloat();
            calibration.mountOffset[1] = cmd.substring(firstSpace + 1, secondSpace).toFloat();
            calibration.mountOffset[2] = cmd.substring(secondSpace + 1).toFloat();
            Serial.printf("[OK] Mount offsets: R=%.1f P=%.1f Y=%.1f\n",
                          calibration.mountOffset[0], calibration.mountOffset[1], calibration.mountOffset[2]);
        } else {
            Serial.println("[ERROR] Usage: mount <roll> <pitch> <yaw>");
            Serial.printf("        Current: R=%.1f P=%.1f Y=%.1f\n",
                          calibration.mountOffset[0], calibration.mountOffset[1], calibration.mountOffset[2]);
        }
    }
    else if (cmd == "setmount") {
        // Set current orientation as mounting offset
        calibration.mountOffset[0] += roll;
        calibration.mountOffset[1] += pitch;
        calibration.mountOffset[2] += yaw;
        roll = 0;
        pitch = 0;
        yaw = 0;
        Serial.println("[OK] Current orientation saved as mount offset");
        Serial.printf("     Mount offsets: R=%.1f P=%.1f Y=%.1f\n",
                      calibration.mountOffset[0], calibration.mountOffset[1], calibration.mountOffset[2]);
    }
    else if (cmd == "clearmount") {
        calibration.mountOffset[0] = 0;
        calibration.mountOffset[1] = 0;
        calibration.mountOffset[2] = 0;
        Serial.println("[OK] Mount offsets cleared");
    }
    else if (cmd == "axes") {
        Serial.println();
        Serial.println("=== AXIS MAPPING ===");
        Serial.printf("Roll  axis: %s (sensor)\n", axisNames[axisMap[0]]);
        Serial.printf("Pitch axis: %s (sensor)\n", axisNames[axisMap[1]]);
        Serial.printf("Yaw   axis: %s (sensor)\n", axisNames[axisMap[2]]);
        Serial.println();
        Serial.println("Options: +X +Y +Z -X -Y -Z");
        Serial.println("Commands:");
        Serial.println("  roll <axis>   - e.g., roll +Y");
        Serial.println("  pitch <axis>  - e.g., pitch -X");
        Serial.println("  yawaxis <axis>");
        Serial.println();
    }
    else if (cmd.startsWith("roll ") && cmd.length() <= 8) {
        int8_t axis = parseAxis(cmd.substring(5));
        if (axis >= 0) {
            axisMap[0] = axis;
            Serial.printf("[OK] Roll axis = %s\n", axisNames[axis]);
        }
    }
    else if (cmd.startsWith("pitch ") && cmd.length() <= 9) {
        int8_t axis = parseAxis(cmd.substring(6));
        if (axis >= 0) {
            axisMap[1] = axis;
            Serial.printf("[OK] Pitch axis = %s\n", axisNames[axis]);
        }
    }
    else if (cmd.startsWith("yawaxis ") && cmd.length() <= 11) {
        int8_t axis = parseAxis(cmd.substring(8));
        if (axis >= 0) {
            axisMap[2] = axis;
            Serial.printf("[OK] Yaw axis = %s\n", axisNames[axis]);
        }
    }
    else if (cmd == "orient cw90") {
        axisMap[0] = 1;  // Roll = +Y
        axisMap[1] = 3;  // Pitch = -X
        axisMap[2] = 2;  // Yaw = +Z
        Serial.println("[OK] Rotated 90 clockwise");
    }
    else if (cmd == "orient ccw90") {
        axisMap[0] = 4;  // Roll = -Y
        axisMap[1] = 0;  // Pitch = +X
        axisMap[2] = 2;  // Yaw = +Z
        Serial.println("[OK] Rotated 90 counter-clockwise");
    }
    else if (cmd == "orient 180") {
        axisMap[0] = 3;  // Roll = -X
        axisMap[1] = 4;  // Pitch = -Y
        axisMap[2] = 2;  // Yaw = +Z
        Serial.println("[OK] Rotated 180");
    }
    else if (cmd == "orient default") {
        axisMap[0] = 0;  // Roll = +X
        axisMap[1] = 1;  // Pitch = +Y
        axisMap[2] = 2;  // Yaw = +Z
        Serial.println("[OK] Default orientation");
    }
    else if (cmd == "invert roll") {
        axisMap[0] = (axisMap[0] + 3) % 6;  // Toggle +/-
        Serial.printf("[OK] Roll axis = %s\n", axisNames[axisMap[0]]);
    }
    else if (cmd == "invert pitch") {
        axisMap[1] = (axisMap[1] + 3) % 6;
        Serial.printf("[OK] Pitch axis = %s\n", axisNames[axisMap[1]]);
    }
    else if (cmd == "invert yaw") {
        axisMap[2] = (axisMap[2] + 3) % 6;
        Serial.printf("[OK] Yaw axis = %s\n", axisNames[axisMap[2]]);
    }
}

void runCalibration() {
    Serial.println();
    Serial.println("=== FULL CALIBRATION ===");
    Serial.println("Place Orb on a FLAT, LEVEL surface");
    Serial.println("Do NOT move during calibration!");
    Serial.println("Starting in 3 seconds...");
    delay(3000);

    calibrateGyro();
    delay(500);
    calibrateAccel();

    // Reset orientation to zero
    roll = 0;
    pitch = 0;
    yaw = 0;
    lastUpdateTime = micros();

    Serial.println();
    Serial.println("=== CALIBRATION COMPLETE ===");
    Serial.println("Orientation reset to zero");
    Serial.println("Use 'save' to store calibration");
    Serial.println();
}

void calibrateGyro() {
    Serial.println();
    Serial.println("[CAL] Gyroscope calibration...");
    Serial.println("      Keep Orb perfectly still!");

    float gxSum = 0, gySum = 0, gzSum = 0;
    const int samples = 1000;

    for (int i = 0; i < samples; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        gxSum += gx;
        gySum += gy;
        gzSum += gz;

        if (i % 100 == 0) {
            Serial.printf("      Progress: %d%%\n", i / 10);
        }
        delay(2);
    }

    // Software bias: store average raw reading when stationary
    // This gets subtracted in readIMU()
    calibration.gyroBias[0] = gxSum / samples;
    calibration.gyroBias[1] = gySum / samples;
    calibration.gyroBias[2] = gzSum / samples;

    Serial.println("[CAL] Gyro calibration done");
    Serial.printf("      Bias: X=%.1f Y=%.1f Z=%.1f (raw)\n",
                  calibration.gyroBias[0],
                  calibration.gyroBias[1],
                  calibration.gyroBias[2]);
}

void calibrateAccel() {
    Serial.println();
    Serial.println("[CAL] Accelerometer calibration...");
    Serial.println("      Orb must be LEVEL (Z pointing up)!");

    float axSum = 0, aySum = 0, azSum = 0;
    const int samples = 1000;

    for (int i = 0; i < samples; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        axSum += ax / 8192.0f;
        aySum += ay / 8192.0f;
        azSum += az / 8192.0f;

        if (i % 100 == 0) {
            Serial.printf("      Progress: %d%%\n", i / 10);
        }
        delay(2);
    }

    // Target: X=0, Y=0, Z=1.0 (1g pointing up)
    calibration.accelBias[0] = axSum / samples;        // Should be ~0
    calibration.accelBias[1] = aySum / samples;        // Should be ~0
    calibration.accelBias[2] = (azSum / samples) - 1.0f; // Should be ~1, so bias = reading - 1

    calibration.valid = true;

    Serial.println("[CAL] Accel calibration done");
    Serial.printf("      Bias: X=%.4f Y=%.4f Z=%.4f g\n",
                  calibration.accelBias[0],
                  calibration.accelBias[1],
                  calibration.accelBias[2]);
}

void saveCalibration() {
    prefs.begin("orb_cal", false);
    prefs.putFloat("abx", calibration.accelBias[0]);
    prefs.putFloat("aby", calibration.accelBias[1]);
    prefs.putFloat("abz", calibration.accelBias[2]);
    prefs.putFloat("gbx", calibration.gyroBias[0]);
    prefs.putFloat("gby", calibration.gyroBias[1]);
    prefs.putFloat("gbz", calibration.gyroBias[2]);
    prefs.putFloat("mr", calibration.mountOffset[0]);
    prefs.putFloat("mp", calibration.mountOffset[1]);
    prefs.putFloat("my", calibration.mountOffset[2]);
    prefs.putChar("ax0", axisMap[0]);
    prefs.putChar("ax1", axisMap[1]);
    prefs.putChar("ax2", axisMap[2]);
    prefs.putChar("s1", calibration.servoTrim[0]);
    prefs.putChar("s2", calibration.servoTrim[1]);
    prefs.putChar("s3", calibration.servoTrim[2]);
    prefs.putChar("s4", calibration.servoTrim[3]);
    prefs.putBool("valid", true);
    prefs.end();

    Serial.println("[OK] Calibration saved to flash");
}

void loadCalibration() {
    prefs.begin("orb_cal", true);
    calibration.valid = prefs.getBool("valid", false);
    if (calibration.valid) {
        calibration.accelBias[0] = prefs.getFloat("abx", 0);
        calibration.accelBias[1] = prefs.getFloat("aby", 0);
        calibration.accelBias[2] = prefs.getFloat("abz", 0);
        calibration.gyroBias[0] = prefs.getFloat("gbx", 0);
        calibration.gyroBias[1] = prefs.getFloat("gby", 0);
        calibration.gyroBias[2] = prefs.getFloat("gbz", 0);
        calibration.mountOffset[0] = prefs.getFloat("mr", 0);
        calibration.mountOffset[1] = prefs.getFloat("mp", 0);
        calibration.mountOffset[2] = prefs.getFloat("my", 0);
        axisMap[0] = prefs.getChar("ax0", 0);
        axisMap[1] = prefs.getChar("ax1", 1);
        axisMap[2] = prefs.getChar("ax2", 2);
        calibration.servoTrim[0] = prefs.getChar("s1", 0);
        calibration.servoTrim[1] = prefs.getChar("s2", 0);
        calibration.servoTrim[2] = prefs.getChar("s3", 0);
        calibration.servoTrim[3] = prefs.getChar("s4", 0);
    }
    prefs.end();
}

void applyCalibration() {
    if (calibration.valid) {
        // Bias values are applied in readIMU()
        Serial.println("[OK] Calibration applied");
        Serial.printf("     Accel bias: %.4f, %.4f, %.4f g\n",
                      calibration.accelBias[0], calibration.accelBias[1], calibration.accelBias[2]);
        Serial.printf("     Gyro bias: %.1f, %.1f, %.1f raw\n",
                      calibration.gyroBias[0], calibration.gyroBias[1], calibration.gyroBias[2]);
    } else {
        Serial.println("[WARN] No valid calibration to apply");
    }
}

void clearCalibration() {
    prefs.begin("orb_cal", false);
    prefs.clear();
    prefs.end();

    memset(&calibration, 0, sizeof(calibration));

    Serial.println("[OK] Calibration cleared");
}

void printStatus() {
    Serial.println();
    Serial.println("=== ORB STATUS ===");

    // IMU
    Serial.printf("IMU: Roll=%.1f Pitch=%.1f Yaw=%.1f\n", roll, pitch, yaw);
    Serial.printf("     Accel: X=%.3f Y=%.3f Z=%.3f g\n", accelX, accelY, accelZ);
    Serial.printf("     Gyro:  X=%.1f Y=%.1f Z=%.1f deg/s\n", gyroX, gyroY, gyroZ);

    // Calibration
    Serial.printf("Cal: %s\n", calibration.valid ? "VALID" : "NOT SET");
    if (calibration.valid) {
        Serial.printf("     Accel bias: %.4f, %.4f, %.4f g\n",
                      calibration.accelBias[0],
                      calibration.accelBias[1],
                      calibration.accelBias[2]);
        Serial.printf("     Gyro bias: %.1f, %.1f, %.1f raw\n",
                      calibration.gyroBias[0],
                      calibration.gyroBias[1],
                      calibration.gyroBias[2]);
    }
    Serial.printf("Mount: R=%.1f P=%.1f Y=%.1f deg\n",
                  calibration.mountOffset[0],
                  calibration.mountOffset[1],
                  calibration.mountOffset[2]);
    Serial.printf("Axes: Roll=%s Pitch=%s Yaw=%s\n",
                  axisNames[axisMap[0]], axisNames[axisMap[1]], axisNames[axisMap[2]]);

    // Barometer
    Serial.printf("Baro: %.1f hPa, %.1f C\n",
                  bmp.readPressure() / 100.0f,
                  bmp.readTemperature());

    // Servos
    Serial.printf("Servos: [%d] [%d] [%d] [%d]\n",
                  servoPos[0], servoPos[1], servoPos[2], servoPos[3]);
    Serial.printf("Trims:  [%d] [%d] [%d] [%d]\n",
                  calibration.servoTrim[0], calibration.servoTrim[1],
                  calibration.servoTrim[2], calibration.servoTrim[3]);

    Serial.println();
}

void printHelp() {
    Serial.println();
    Serial.println("=== COMMANDS ===");
    Serial.println("Calibration:");
    Serial.println("  cal       - Full IMU calibration");
    Serial.println("  calgyro   - Gyroscope only");
    Serial.println("  calaccel  - Accelerometer only");
    Serial.println("  save      - Save calibration to flash");
    Serial.println("  load      - Load calibration from flash");
    Serial.println("  clear     - Clear saved calibration");
    Serial.println();
    Serial.println("Streaming:");
    Serial.println("  stream on/off - Enable/disable data stream");
    Serial.println("  rate <ms>     - Set stream rate (10-1000 ms)");
    Serial.println();
    Serial.println("Servos:");
    Serial.println("  center         - Center all servos");
    Serial.println("  sweep          - Servo sweep test");
    Serial.println("  servo <1-4> <angle> - Set servo angle");
    Serial.println("  trim <1-4> <offset> - Set servo trim (-20 to +20)");
    Serial.println();
    Serial.println("Mounting:");
    Serial.println("  setmount           - Set current angle as mount offset");
    Serial.println("  mount <r> <p> <y>  - Set mount offsets manually");
    Serial.println("  clearmount         - Clear mount offsets");
    Serial.println();
    Serial.println("Axis Mapping:");
    Serial.println("  axes               - Show current axis mapping");
    Serial.println("  roll/pitch/yawaxis <axis> - Set axis (+X +Y +Z -X -Y -Z)");
    Serial.println("  orient cw90/ccw90/180/default - Quick rotations");
    Serial.println();
    Serial.println("Other:");
    Serial.println("  status    - Show current status");
    Serial.println("  zero      - Zero roll/pitch/yaw");
    Serial.println("  resetyaw  - Reset yaw only");
    Serial.println("  help      - Show this help");
    Serial.println();
}

// ============== SERVO FUNCTIONS ==============
void setServo(int channel, int angle) {
    angle = constrain(angle + calibration.servoTrim[channel], 0, 180);
    servoPos[channel] = angle;
    int ticks = map(angle, 0, 180, SERVO_MIN_TICKS, SERVO_MAX_TICKS);
    ledcWrite(servoPins[channel], ticks);
}

void centerServos() {
    for (int i = 0; i < 4; i++) {
        setServo(i, 90);
    }
}

void servoSweep() {
    Serial.println("[SERVO] Sweep test...");

    for (int angle = 90; angle >= 60; angle -= 2) {
        for (int i = 0; i < 4; i++) setServo(i, angle);
        delay(30);
    }
    delay(300);

    for (int angle = 60; angle <= 120; angle += 2) {
        for (int i = 0; i < 4; i++) setServo(i, angle);
        delay(30);
    }
    delay(300);

    for (int angle = 120; angle >= 90; angle -= 2) {
        for (int i = 0; i < 4; i++) setServo(i, angle);
        delay(30);
    }

    Serial.println("[SERVO] Sweep complete");
}
