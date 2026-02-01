/*
 * ORB CALIBRATION FIRMWARE
 * Seeed XIAO ESP32C3
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
#include <Preferences.h>

// ============== PIN DEFINITIONS ==============
// Seeed XIAO ESP32C3
#define SERVO1_PIN 2     // D0 (GPIO2) - Top fin
#define SERVO2_PIN 3     // D1 (GPIO3) - Right fin
#define SERVO3_PIN 4     // D2 (GPIO4) - Bottom fin
#define SERVO4_PIN 5     // D3 (GPIO5) - Left fin
#define I2C_SDA 6        // D4 (GPIO6) - XIAO default SDA
#define I2C_SCL 7        // D5 (GPIO7) - XIAO default SCL

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
    float gyroBias[3];
    float accelBias[3];
    float mountOffset[3];
    int8_t servoTrim[4];
    bool valid;
} calibration;

// ============== AXIS MAPPING ==============
int8_t axisMap[3] = {0, 1, 2};
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
    return -1;
}

// ============== STATE ==============
float roll = 0, pitch = 0, yaw = 0;
int16_t ax, ay, az, gx, gy, gz;
float accelRaw[3], gyroRaw[3];
float accelX, accelY, accelZ;
float gyroX, gyroY, gyroZ;
int servoPos[4] = {90, 90, 90, 90};
bool streamingEnabled = true;
unsigned long lastStreamTime = 0;
int streamRate = 50;
float alpha = 0.98;
unsigned long lastUpdateTime = 0;

void setup() {
    Serial.begin(115200);

    unsigned long startWait = millis();
    while (!Serial && (millis() - startWait < 3000)) {
        delay(10);
    }
    delay(500);

    Serial.println();
    Serial.println("*** XIAO ESP32C3 BOOT OK ***");
    Serial.flush();

    Serial.println("=================================");
    Serial.println("  ORB CALIBRATION TOOL v1.1");
    Serial.println("  Seeed XIAO ESP32C3");
    Serial.println("=================================");
    Serial.println();

    // Initialize I2C
    Serial.println("[INIT] I2C bus...");
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);
    delay(100);
    Serial.println("[OK] I2C ready");

    // Initialize IMU
    Serial.println("[INIT] MPU6050...");
    mpu.initialize();
    if (!mpu.testConnection()) {
        Serial.println("[ERROR] MPU6050 not found!");
    } else {
        Serial.println("[OK] MPU6050 connected");
        mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
        mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
    }

    // Initialize Barometer
    Serial.println("[INIT] BMP280...");
    bool bmpFound = bmp.begin(0x76);
    if (!bmpFound) bmpFound = bmp.begin(0x77);
    if (bmpFound) {
        Serial.println("[OK] BMP280 connected");
    } else {
        Serial.println("[WARN] BMP280 not found");
    }

    // Initialize Servos
    Serial.println("[INIT] Servos...");
    for (int i = 0; i < 4; i++) {
        ledcAttach(servoPins[i], SERVO_FREQ, SERVO_RESOLUTION);
    }
    centerServos();

    // Load calibration
    loadCalibration();
    if (calibration.valid) {
        Serial.println("[CAL] Loaded saved calibration");
    } else {
        Serial.println("[CAL] No calibration found - run 'cal' command");
    }

    lastUpdateTime = micros();
    printHelp();
}

void loop() {
    readIMU();
    calculateOrientation();
    processCommands();

    if (streamingEnabled && (millis() - lastStreamTime >= streamRate)) {
        lastStreamTime = millis();
        streamData();
    }
}

float getAxisValue(float* data, int8_t axis) {
    int idx = axis % 3;
    float val = data[idx];
    return (axis >= 3) ? -val : val;
}

void readIMU() {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    accelRaw[0] = ax / 8192.0f - calibration.accelBias[0];
    accelRaw[1] = ay / 8192.0f - calibration.accelBias[1];
    accelRaw[2] = az / 8192.0f - calibration.accelBias[2];

    gyroRaw[0] = (gx - calibration.gyroBias[0]) / 65.5f;
    gyroRaw[1] = (gy - calibration.gyroBias[1]) / 65.5f;
    gyroRaw[2] = (gz - calibration.gyroBias[2]) / 65.5f;

    accelX = getAxisValue(accelRaw, axisMap[0]);
    accelY = getAxisValue(accelRaw, axisMap[1]);
    accelZ = getAxisValue(accelRaw, axisMap[2]);

    gyroX = getAxisValue(gyroRaw, axisMap[0]);
    gyroY = getAxisValue(gyroRaw, axisMap[1]);
    gyroZ = getAxisValue(gyroRaw, axisMap[2]);
}

void calculateOrientation() {
    unsigned long now = micros();
    float dt = (now - lastUpdateTime) / 1000000.0f;
    lastUpdateTime = now;
    if (dt > 0.1) dt = 0.1;

    float accelRoll = atan2(accelY, accelZ) * 180.0f / PI;
    float accelPitch = atan2(-accelX, sqrt(accelY*accelY + accelZ*accelZ)) * 180.0f / PI;

    roll = alpha * (roll + gyroX * dt) + (1.0f - alpha) * accelRoll;
    pitch = alpha * (pitch + gyroY * dt) + (1.0f - alpha) * accelPitch;
    yaw += gyroZ * dt;

    roll -= calibration.mountOffset[0];
    pitch -= calibration.mountOffset[1];
    yaw -= calibration.mountOffset[2];

    while (yaw > 180) yaw -= 360;
    while (yaw < -180) yaw += 360;
}

void streamData() {
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

    if (cmd == "help" || cmd == "?") printHelp();
    else if (cmd == "cal") runCalibration();
    else if (cmd == "calgyro") calibrateGyro();
    else if (cmd == "calaccel") calibrateAccel();
    else if (cmd == "save") saveCalibration();
    else if (cmd == "load") { loadCalibration(); applyCalibration(); }
    else if (cmd == "clear") clearCalibration();
    else if (cmd == "status") printStatus();
    else if (cmd == "stream on") { streamingEnabled = true; Serial.println("[OK] Streaming enabled"); }
    else if (cmd == "stream off") { streamingEnabled = false; Serial.println("[OK] Streaming disabled"); }
    else if (cmd.startsWith("rate ")) {
        streamRate = constrain(cmd.substring(5).toInt(), 10, 1000);
        Serial.printf("[OK] Stream rate: %d ms\n", streamRate);
    }
    else if (cmd == "center") { centerServos(); Serial.println("[OK] Servos centered"); }
    else if (cmd == "sweep") servoSweep();
    else if (cmd.startsWith("servo ")) {
        int num = cmd.substring(6, 7).toInt();
        int angle = cmd.substring(8).toInt();
        if (num >= 1 && num <= 4) {
            setServo(num - 1, angle);
            Serial.printf("[OK] Servo %d -> %d\n", num, angle);
        }
    }
    else if (cmd.startsWith("trim ")) {
        int num = cmd.substring(5, 6).toInt();
        int offset = cmd.substring(7).toInt();
        if (num >= 1 && num <= 4) {
            calibration.servoTrim[num - 1] = constrain(offset, -20, 20);
            Serial.printf("[OK] Servo %d trim: %d\n", num, calibration.servoTrim[num - 1]);
        }
    }
    else if (cmd == "resetyaw") { yaw = 0; Serial.println("[OK] Yaw reset"); }
    else if (cmd == "zero") {
        roll = pitch = yaw = 0;
        lastUpdateTime = micros();
        Serial.println("[OK] Orientation zeroed");
    }
    else if (cmd == "setmount") {
        calibration.mountOffset[0] += roll;
        calibration.mountOffset[1] += pitch;
        calibration.mountOffset[2] += yaw;
        roll = pitch = yaw = 0;
        Serial.println("[OK] Mount offset saved");
    }
    else if (cmd == "clearmount") {
        calibration.mountOffset[0] = calibration.mountOffset[1] = calibration.mountOffset[2] = 0;
        Serial.println("[OK] Mount offsets cleared");
    }
    else if (cmd == "axes") {
        Serial.printf("Roll=%s Pitch=%s Yaw=%s\n",
                      axisNames[axisMap[0]], axisNames[axisMap[1]], axisNames[axisMap[2]]);
    }
}

void runCalibration() {
    Serial.println("\n=== FULL CALIBRATION ===");
    Serial.println("Keep Orb still on a level surface...");
    delay(3000);
    calibrateGyro();
    delay(500);
    calibrateAccel();
    roll = pitch = yaw = 0;
    lastUpdateTime = micros();
    Serial.println("Calibration complete. Use 'save' to store.");
}

void calibrateGyro() {
    Serial.println("[CAL] Gyro calibration...");
    float gxSum = 0, gySum = 0, gzSum = 0;
    const int samples = 1000;

    for (int i = 0; i < samples; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        gxSum += gx;
        gySum += gy;
        gzSum += gz;
        if (i % 100 == 0) Serial.printf("  Progress: %d%%\n", i / 10);
        delay(2);
    }

    calibration.gyroBias[0] = gxSum / samples;
    calibration.gyroBias[1] = gySum / samples;
    calibration.gyroBias[2] = gzSum / samples;
    Serial.printf("[CAL] Gyro bias: %.1f, %.1f, %.1f\n",
                  calibration.gyroBias[0], calibration.gyroBias[1], calibration.gyroBias[2]);
}

void calibrateAccel() {
    Serial.println("[CAL] Accel calibration...");
    float axSum = 0, aySum = 0, azSum = 0;
    const int samples = 1000;

    for (int i = 0; i < samples; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        axSum += ax / 8192.0f;
        aySum += ay / 8192.0f;
        azSum += az / 8192.0f;
        if (i % 100 == 0) Serial.printf("  Progress: %d%%\n", i / 10);
        delay(2);
    }

    calibration.accelBias[0] = axSum / samples;
    calibration.accelBias[1] = aySum / samples;
    calibration.accelBias[2] = (azSum / samples) - 1.0f;
    calibration.valid = true;
    Serial.printf("[CAL] Accel bias: %.4f, %.4f, %.4f g\n",
                  calibration.accelBias[0], calibration.accelBias[1], calibration.accelBias[2]);
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
    prefs.putBool("valid", true);
    prefs.end();
    Serial.println("[OK] Calibration saved");
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
    }
    prefs.end();
}

void applyCalibration() {
    if (calibration.valid) {
        Serial.println("[OK] Calibration applied");
    } else {
        Serial.println("[WARN] No valid calibration");
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
    Serial.println("\n=== STATUS ===");
    Serial.printf("IMU: R=%.1f P=%.1f Y=%.1f\n", roll, pitch, yaw);
    Serial.printf("Cal: %s\n", calibration.valid ? "VALID" : "NOT SET");
    Serial.printf("Baro: %.1f hPa, %.1f C\n", bmp.readPressure() / 100.0f, bmp.readTemperature());
    Serial.printf("Servos: [%d] [%d] [%d] [%d]\n", servoPos[0], servoPos[1], servoPos[2], servoPos[3]);
}

void printHelp() {
    Serial.println("\n=== COMMANDS ===");
    Serial.println("cal/calgyro/calaccel - Calibration");
    Serial.println("save/load/clear - NVS management");
    Serial.println("stream on/off - Data streaming");
    Serial.println("center/sweep - Servo control");
    Serial.println("servo <1-4> <angle> - Set servo");
    Serial.println("status - Show status");
    Serial.println("help - This help");
    Serial.println();
}

void setServo(int channel, int angle) {
    angle = constrain(angle + calibration.servoTrim[channel], 0, 180);
    servoPos[channel] = angle;
    int ticks = map(angle, 0, 180, SERVO_MIN_TICKS, SERVO_MAX_TICKS);
    ledcWrite(servoPins[channel], ticks);
}

void centerServos() {
    for (int i = 0; i < 4; i++) setServo(i, 90);
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
