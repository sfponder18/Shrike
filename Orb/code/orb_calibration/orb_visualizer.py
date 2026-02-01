#!/usr/bin/env python3
"""
ORB Calibration & Visualization Tool v1.3
"""

import sys
import math
import time
import traceback
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt6.QtCore import QPoint
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

import serial
import serial.tools.list_ports

from OpenGL.GL import *
from OpenGL.GLU import *


def debug_print(msg):
    """Print with timestamp - disabled"""
    pass  # Disabled to stop console spam


@dataclass
class OrbData:
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 0.0
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    servo1: int = 90
    servo2: int = 90
    servo3: int = 90
    servo4: int = 90
    temperature: float = 0.0
    pressure: float = 0.0


class SerialThread(QThread):
    data_received = pyqtSignal(OrbData)
    log_message = pyqtSignal(str)
    debug_message = pyqtSignal(str)
    connection_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.port = ""
        self.mutex = QMutex()
        self.data_count = 0
        self.error_count = 0
        debug_print("SerialThread initialized")

    def connect_port(self, port: str, baud: int = 115200):
        debug_print(f"Attempting to connect to {port} at {baud} baud")
        self.debug_message.emit(f"Connecting to {port}...")
        try:
            self.serial = serial.Serial(port, baud, timeout=0.1)
            self.port = port
            self.running = True
            self.connection_changed.emit(True)
            self.log_message.emit(f"Connected to {port}")
            self.debug_message.emit(f"SUCCESS: Connected to {port}")
            debug_print(f"Connected successfully to {port}")
            self.start()
            return True
        except Exception as e:
            err_msg = f"Connection failed: {e}"
            debug_print(err_msg)
            self.debug_message.emit(f"ERROR: {err_msg}")
            self.log_message.emit(err_msg)
            self.connection_changed.emit(False)
            return False

    def disconnect_port(self):
        debug_print("Disconnecting...")
        self.running = False

        # Wait for thread to stop (non-blocking check)
        try:
            if self.isRunning():
                debug_print("Waiting for thread to stop...")
                if not self.wait(1000):
                    debug_print("Thread didn't stop, terminating...")
                    self.terminate()
                    self.wait(500)
        except:
            pass

        # Close serial safely
        try:
            if self.mutex.tryLock(500):
                try:
                    if self.serial and self.serial.is_open:
                        self.serial.close()
                        debug_print("Serial port closed")
                except:
                    pass
                self.serial = None
                self.mutex.unlock()
        except:
            pass

        try:
            self.connection_changed.emit(False)
        except:
            pass
        debug_print("Disconnect complete")

    def send_command(self, cmd: str):
        debug_print(f"Sending command: {cmd}")
        if not self.mutex.tryLock(200):  # 200ms timeout
            debug_print("Could not acquire mutex for send")
            self.debug_message.emit("WARN: Send skipped (busy)")
            return
        try:
            if self.serial and self.serial.is_open:
                self.serial.write(f"{cmd}\n".encode())
                self.serial.flush()
                self.log_message.emit(f"> {cmd}")
                self.debug_message.emit(f"TX: {cmd}")
            else:
                self.debug_message.emit("ERROR: Serial not open")
        except Exception as e:
            debug_print(f"Send error: {e}")
            self.debug_message.emit(f"ERROR: Send failed")
        finally:
            try:
                self.mutex.unlock()
            except:
                pass

    def run(self):
        debug_print("Serial thread started")
        self.debug_message.emit("Serial thread running...")
        buffer = ""
        loop_count = 0
        locked = False

        while self.running:
            loop_count += 1
            try:
                # Check serial with safe locking
                locked = self.mutex.tryLock(100)  # 100ms timeout
                if locked:
                    bytes_waiting = 0
                    if self.serial and self.serial.is_open:
                        try:
                            bytes_waiting = self.serial.in_waiting
                            if bytes_waiting > 0:
                                chunk = self.serial.read(min(bytes_waiting, 512))
                                if chunk:
                                    buffer += chunk.decode('utf-8', errors='ignore')
                        except serial.SerialException as se:
                            self.error_count += 1
                            debug_print(f"Serial read error: {se}")
                        except Exception as e:
                            self.error_count += 1
                            debug_print(f"Read error: {e}")
                    self.mutex.unlock()
                    locked = False

                # Limit buffer size to prevent memory issues
                if len(buffer) > 10000:
                    buffer = buffer[-5000:]

                # Process complete lines (limit per loop)
                lines_processed = 0
                while '\n' in buffer and lines_processed < 10:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            self.process_line(line)
                        except Exception as e:
                            debug_print(f"Process line error: {e}")
                        lines_processed += 1

                # Debug output every 200 loops
                if loop_count % 200 == 0:
                    self.debug_message.emit(f"Loop {loop_count}: buf={len(buffer)}, data={self.data_count}, err={self.error_count}")

                # Sleep to prevent CPU spin
                self.msleep(10)

            except Exception as e:
                if locked:
                    try:
                        self.mutex.unlock()
                    except:
                        pass
                    locked = False
                self.error_count += 1
                debug_print(f"Thread error: {e}")
                self.msleep(100)

        debug_print("Serial thread stopped")
        try:
            self.debug_message.emit("Serial thread stopped")
        except:
            pass

    def process_line(self, line: str):
        if line.startswith("$ORB,") and line.endswith("*"):
            data = self.parse_orb_data(line)
            if data:
                self.data_count += 1
                self.data_received.emit(data)
        else:
            self.log_message.emit(line)

    def parse_orb_data(self, line: str) -> Optional[OrbData]:
        try:
            content = line[5:-1]
            parts = content.split(',')
            if len(parts) >= 15:
                return OrbData(
                    roll=float(parts[0]),
                    pitch=float(parts[1]),
                    yaw=float(parts[2]),
                    accel_x=float(parts[3]),
                    accel_y=float(parts[4]),
                    accel_z=float(parts[5]),
                    gyro_x=float(parts[6]),
                    gyro_y=float(parts[7]),
                    gyro_z=float(parts[8]),
                    servo1=int(float(parts[9])),
                    servo2=int(float(parts[10])),
                    servo3=int(float(parts[11])),
                    servo4=int(float(parts[12])),
                    temperature=float(parts[13]),
                    pressure=float(parts[14])
                )
            else:
                self.debug_message.emit(f"Parse: not enough parts ({len(parts)})")
        except Exception as e:
            self.error_count += 1
            self.debug_message.emit(f"Parse error: {e}")
        return None


class AttitudeIndicator2D(QWidget):
    def __init__(self):
        super().__init__()
        self.roll = 0.0
        self.pitch = 0.0
        self.setMinimumSize(200, 200)
        self.paint_count = 0
        debug_print("AttitudeIndicator2D initialized")

    def set_attitude(self, roll: float, pitch: float, yaw: float = 0):
        self.roll = max(-90, min(90, roll))
        self.pitch = max(-90, min(90, pitch))
        self.update()

    def paintEvent(self, event):
        self.paint_count += 1
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            w, h = self.width(), self.height()
            cx, cy = w // 2, h // 2
            radius = min(w, h) // 2 - 10

            # Background
            painter.fillRect(0, 0, w, h, QColor(30, 30, 30))

            # Save and rotate
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(-self.roll)

            pitch_offset = int(self.pitch * 2)

            # Sky
            painter.setBrush(QBrush(QColor(50, 120, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(-w, -h + pitch_offset, w * 2, h)

            # Ground
            painter.setBrush(QBrush(QColor(139, 90, 43)))
            painter.drawRect(-w, pitch_offset, w * 2, h)

            # Horizon line
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(-radius, pitch_offset, radius, pitch_offset)

            painter.restore()

            # Aircraft symbol
            painter.setPen(QPen(QColor(255, 200, 0), 3))
            painter.drawLine(cx - 40, cy, cx - 10, cy)
            painter.drawLine(cx + 10, cy, cx + 40, cy)
            painter.drawLine(cx, cy, cx, cy + 10)

            # Border
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            # Values
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(5, 15, f"R:{self.roll:+.1f}")
            painter.drawText(5, 30, f"P:{self.pitch:+.1f}")

        except Exception as e:
            debug_print(f"Paint error: {e}")


class Orb3DView(QOpenGLWidget):
    """3D view of the Orb showing body and fins"""

    def __init__(self):
        super().__init__()
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.servos = [90, 90, 90, 90]  # Fin deflections
        self.setMinimumSize(250, 250)

    def set_attitude(self, roll: float, pitch: float, yaw: float):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.update()

    def set_servos(self, s1: int, s2: int, s3: int, s4: int):
        self.servos = [s1, s2, s3, s4]
        self.update()

    def initializeGL(self):
        glClearColor(0.15, 0.15, 0.15, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Light position
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 10.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / h if h > 0 else 1
        gluPerspective(45, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera position - looking at orb from behind and slightly above
        gluLookAt(0, -4, 2,   # Eye position
                  0, 0, 0,     # Look at
                  0, 0, 1)     # Up vector

        # Apply attitude rotations
        glRotatef(self.yaw, 0, 0, 1)    # Yaw around Z
        glRotatef(self.pitch, 1, 0, 0)  # Pitch around X
        glRotatef(self.roll, 0, 1, 0)   # Roll around Y (forward axis)

        # Draw Orb body (sphere)
        glColor3f(0.3, 0.3, 0.35)
        self.draw_sphere(0.5, 20, 20)

        # Draw nose cone
        glColor3f(0.4, 0.4, 0.45)
        glPushMatrix()
        glTranslatef(0, 0.5, 0)
        glRotatef(-90, 1, 0, 0)
        self.draw_cone(0.3, 0.6, 16)
        glPopMatrix()

        # Draw 4 fins at 90 degree intervals
        fin_angles = [0, 90, 180, 270]  # Positions around the body
        fin_colors = [
            (0.8, 0.2, 0.2),  # Fin 1 - Red (top)
            (0.2, 0.8, 0.2),  # Fin 2 - Green (right)
            (0.2, 0.2, 0.8),  # Fin 3 - Blue (bottom)
            (0.8, 0.8, 0.2),  # Fin 4 - Yellow (left)
        ]

        for i, (angle, color) in enumerate(zip(fin_angles, fin_colors)):
            glPushMatrix()
            glRotatef(angle, 0, 1, 0)  # Rotate around body axis

            # Position fin at back of orb
            glTranslatef(0.5, -0.3, 0)

            # Apply fin deflection (servo angle - 90 gives deflection from center)
            deflection = (self.servos[i] - 90) * 0.5  # Scale deflection
            glRotatef(deflection, 0, 1, 0)

            # Draw fin
            glColor3f(*color)
            self.draw_fin()

            glPopMatrix()

        # Draw direction arrow (forward indicator)
        glColor3f(1.0, 1.0, 1.0)
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        glVertex3f(0, 1.2, 0)
        glVertex3f(0, 1.5, 0)
        glVertex3f(0, 1.5, 0)
        glVertex3f(0.1, 1.35, 0)
        glVertex3f(0, 1.5, 0)
        glVertex3f(-0.1, 1.35, 0)
        glEnd()
        glEnable(GL_LIGHTING)

    def draw_sphere(self, radius, slices, stacks):
        quad = gluNewQuadric()
        gluSphere(quad, radius, slices, stacks)
        gluDeleteQuadric(quad)

    def draw_cone(self, base, height, slices):
        quad = gluNewQuadric()
        gluCylinder(quad, base, 0.0, height, slices, 1)
        gluDeleteQuadric(quad)

    def draw_fin(self):
        # Draw a simple fin shape
        glBegin(GL_QUADS)
        # Main fin surface
        glNormal3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0.4, 0, 0)
        glVertex3f(0.3, -0.5, 0)
        glVertex3f(0, -0.3, 0)

        # Back side
        glNormal3f(0, 0, -1)
        glVertex3f(0, -0.3, 0)
        glVertex3f(0.3, -0.5, 0)
        glVertex3f(0.4, 0, 0)
        glVertex3f(0, 0, 0)
        glEnd()

        # Fin edge for thickness
        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glVertex3f(0.4, 0, -0.02)
        glVertex3f(0.4, 0, 0.02)
        glVertex3f(0.3, -0.5, 0.02)
        glVertex3f(0.3, -0.5, -0.02)
        glEnd()


class OrbVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        debug_print("OrbVisualizer __init__ start")
        self.setWindowTitle("Orb Calibration Tool")
        self.setMinimumSize(1000, 600)

        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.on_data_received, Qt.ConnectionType.QueuedConnection)
        self.serial_thread.log_message.connect(self.on_log_message, Qt.ConnectionType.QueuedConnection)
        self.serial_thread.debug_message.connect(self.on_debug_message, Qt.ConnectionType.QueuedConnection)
        self.serial_thread.connection_changed.connect(self.on_connection_changed, Qt.ConnectionType.QueuedConnection)

        self.current_data = OrbData()
        self.update_count = 0
        self.gui_update_count = 0

        debug_print("Creating UI...")
        self.init_ui()
        debug_print("UI created")

        # Timers
        self.port_timer = QTimer()
        self.port_timer.timeout.connect(self.refresh_ports)
        self.port_timer.start(3000)

        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)

        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.heartbeat)
        self.heartbeat_timer.start(500)

        debug_print("OrbVisualizer __init__ complete")

    def heartbeat(self):
        """Proves GUI is responsive"""
        self.gui_update_count += 1
        self.heartbeat_label.setText(f"GUI Heartbeat: {self.gui_update_count}")

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left - Visualization (two views side by side)
        left_panel = QVBoxLayout()

        # Views container
        views_layout = QHBoxLayout()

        # Attitude indicator (left)
        self.horizon_widget = AttitudeIndicator2D()
        views_layout.addWidget(self.horizon_widget)

        # 3D Orb view (right)
        self.orb_3d = Orb3DView()
        views_layout.addWidget(self.orb_3d)

        left_panel.addLayout(views_layout, stretch=1)

        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setFont(QFont("Consolas", 10))
        left_panel.addWidget(self.fps_label)

        self.heartbeat_label = QLabel("GUI Heartbeat: 0")
        self.heartbeat_label.setFont(QFont("Consolas", 10))
        self.heartbeat_label.setStyleSheet("color: lime;")
        left_panel.addWidget(self.heartbeat_label)

        main_layout.addLayout(left_panel, stretch=1)

        # Right - Controls with tabs
        right_panel = QVBoxLayout()

        # Connection
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        conn_layout.addWidget(self.port_combo)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        right_panel.addWidget(conn_group)

        # Data display
        data_group = QGroupBox("Data")
        data_layout = QVBoxLayout(data_group)
        self.roll_label = QLabel("Roll:  0.0")
        self.pitch_label = QLabel("Pitch: 0.0")
        self.yaw_label = QLabel("Yaw:   0.0")
        self.accel_label = QLabel("Accel: 0, 0, 0")
        self.gyro_label = QLabel("Gyro:  0, 0, 0")
        self.servo_label = QLabel("Servos: 90 90 90 90")
        for lbl in [self.roll_label, self.pitch_label, self.yaw_label, self.accel_label, self.gyro_label, self.servo_label]:
            lbl.setFont(QFont("Consolas", 10))
            data_layout.addWidget(lbl)
        right_panel.addWidget(data_group)

        # Buttons
        btn_group = QGroupBox("Commands")
        btn_layout = QGridLayout(btn_group)
        buttons = [
            ("cal", 0, 0), ("zero", 0, 1),
            ("setmount", 1, 0), ("clearmount", 1, 1),
            ("center", 2, 0), ("sweep", 2, 1),
            ("save", 3, 0), ("status", 3, 1),
        ]
        for cmd, row, col in buttons:
            btn = QPushButton(cmd)
            btn.clicked.connect(lambda checked, c=cmd: self.send_command(c))
            btn_layout.addWidget(btn, row, col)
        right_panel.addWidget(btn_group)

        # Orientation
        orient_group = QGroupBox("Board Orientation")
        orient_layout = QVBoxLayout(orient_group)

        # Rotation presets row
        preset_layout = QHBoxLayout()
        self.orient_combo = QComboBox()
        self.orient_combo.addItems(["default", "cw90", "ccw90", "180"])
        preset_layout.addWidget(self.orient_combo)
        orient_btn = QPushButton("Apply")
        orient_btn.clicked.connect(self.apply_orientation)
        preset_layout.addWidget(orient_btn)
        orient_layout.addLayout(preset_layout)

        # Invert buttons row
        invert_layout = QHBoxLayout()
        invert_layout.addWidget(QLabel("Invert:"))
        for axis in ["roll", "pitch", "yawaxis"]:
            btn = QPushButton(axis.replace("axis", "").capitalize())
            btn.clicked.connect(lambda checked, a=axis: self.invert_axis(a))
            invert_layout.addWidget(btn)
        orient_layout.addLayout(invert_layout)

        right_panel.addWidget(orient_group)

        # Command input
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Command...")
        self.cmd_input.returnPressed.connect(self.send_input_command)
        cmd_layout.addWidget(self.cmd_input)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_input_command)
        cmd_layout.addWidget(send_btn)
        right_panel.addLayout(cmd_layout)

        # Tabs for logs
        tabs = QTabWidget()

        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        tabs.addTab(self.log_text, "Log")

        # Debug tab
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFont(QFont("Consolas", 8))
        self.debug_text.setStyleSheet("background-color: #1a1a2e; color: #0f0;")
        tabs.addTab(self.debug_text, "Debug")

        right_panel.addWidget(tabs, stretch=1)

        # Clear buttons
        clear_layout = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        clear_layout.addWidget(clear_log_btn)
        clear_debug_btn = QPushButton("Clear Debug")
        clear_debug_btn.clicked.connect(self.debug_text.clear)
        clear_layout.addWidget(clear_debug_btn)
        right_panel.addLayout(clear_layout)

        main_layout.addLayout(right_panel, stretch=1)

        self.refresh_ports()
        self.on_debug_message("GUI initialized")

    def refresh_ports(self):
        try:
            current = self.port_combo.currentText()
            self.port_combo.clear()
            ports = serial.tools.list_ports.comports()
            for port in ports:
                self.port_combo.addItem(f"{port.device} - {port.description}")
            for i in range(self.port_combo.count()):
                if current and self.port_combo.itemText(i).startswith(current.split(" - ")[0]):
                    self.port_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            self.on_debug_message(f"Port refresh error: {e}")

    def toggle_connection(self):
        debug_print("toggle_connection called")
        self.on_debug_message("Toggle connection...")
        if self.serial_thread.running:
            self.serial_thread.disconnect_port()
        else:
            port_text = self.port_combo.currentText()
            if port_text:
                port = port_text.split(" - ")[0]
                self.serial_thread.connect_port(port)

    def on_connection_changed(self, connected: bool):
        debug_print(f"on_connection_changed: {connected}")
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self.port_combo.setEnabled(not connected)
        self.on_debug_message(f"Connection state: {connected}")

    def on_data_received(self, data: OrbData):
        try:
            self.current_data = data
            self.update_count += 1

            # Update 2D attitude indicator
            self.horizon_widget.set_attitude(data.roll, data.pitch, data.yaw)

            # Update 3D Orb view
            self.orb_3d.set_attitude(data.roll, data.pitch, data.yaw)
            self.orb_3d.set_servos(data.servo1, data.servo2, data.servo3, data.servo4)

            self.roll_label.setText(f"Roll:  {data.roll:+6.1f}")
            self.pitch_label.setText(f"Pitch: {data.pitch:+6.1f}")
            self.yaw_label.setText(f"Yaw:   {data.yaw:+6.1f}")
            self.accel_label.setText(f"Accel: {data.accel_x:.2f}, {data.accel_y:.2f}, {data.accel_z:.2f}")
            self.gyro_label.setText(f"Gyro:  {data.gyro_x:.1f}, {data.gyro_y:.1f}, {data.gyro_z:.1f}")
            self.servo_label.setText(f"Servos: {data.servo1} {data.servo2} {data.servo3} {data.servo4}")
        except Exception as e:
            self.on_debug_message(f"Data update error: {e}")

    def on_log_message(self, msg: str):
        try:
            if not msg or not isinstance(msg, str):
                return
            if len(msg) > 500:
                msg = msg[:500] + "..."
            if self.log_text.document().blockCount() > 100:
                self.log_text.clear()
            self.log_text.append(msg)
        except:
            pass

    def on_debug_message(self, msg: str):
        try:
            if not msg or not isinstance(msg, str):
                return
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if self.debug_text.document().blockCount() > 200:
                self.debug_text.clear()
            self.debug_text.append(f"[{ts}] {msg}")
        except:
            pass

    def update_fps(self):
        fps = self.update_count
        self.update_count = 0
        self.fps_label.setText(f"Data FPS: {fps} | Paints: {self.horizon_widget.paint_count}")
        self.horizon_widget.paint_count = 0

    def send_command(self, cmd: str):
        self.on_debug_message(f"Sending: {cmd}")
        self.serial_thread.send_command(cmd)

    def send_input_command(self):
        cmd = self.cmd_input.text().strip()
        if cmd:
            self.send_command(cmd)
            self.cmd_input.clear()

    def apply_orientation(self):
        orient = self.orient_combo.currentText()
        self.send_command(f"orient {orient}")

    def invert_axis(self, axis):
        self.send_command(f"invert {axis.replace('axis', '')}")

    def closeEvent(self, event):
        debug_print("closeEvent - shutting down")
        try:
            self.port_timer.stop()
            self.fps_timer.stop()
            self.heartbeat_timer.stop()
        except:
            pass
        try:
            self.serial_thread.disconnect_port()
        except:
            pass
        event.accept()


def main():
    debug_print("Application starting...")

    app = None
    window = None

    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        # Dark theme
        palette = app.palette()
        palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(palette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(palette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(palette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(palette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
        app.setPalette(palette)

        debug_print("Creating main window...")
        window = OrbVisualizer()
        window.show()
        debug_print("Window shown, entering event loop")

        result = app.exec()
        debug_print(f"Event loop exited with code {result}")
        sys.exit(result)

    except KeyboardInterrupt:
        debug_print("Keyboard interrupt")
        if window:
            window.close()
        sys.exit(0)
    except Exception as e:
        debug_print(f"FATAL ERROR: {e}\n{traceback.format_exc()}")
        if window:
            try:
                window.serial_thread.disconnect_port()
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
