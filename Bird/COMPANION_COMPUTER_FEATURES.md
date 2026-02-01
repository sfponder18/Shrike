# Companion Computer Feature Specification
## SwarmDrones Platform

**Version:** 0.1
**Date:** 2026-01-22
**Status:** Draft

---

## 1. Purpose

This document defines the feature set managed by the companion computer (CC) onboard SwarmDrones UAV platforms. The CC serves as the intelligence layer between sensors, payloads, and the flight controller.

---

## 2. Platform Variants

| Platform | Hardware | Role |
|----------|----------|------|
| **Bird** | Raspberry Pi 5 | MAVLink relay, video streaming, mesh coordinator |
| **Chick** | Pi Zero 2W | Sensor relay, mesh node, SDR interface |

*Note: Jetson upgrade path available for v2 AI features (see Future_Capabilities.md)*

---

## 3. Feature Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    COMPANION COMPUTER                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│   │    MESH      │  │     ISR      │  │     VIO      │        │
│   │  NETWORKING  │  │   PAYLOAD    │  │  NAVIGATION  │        │
│   └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│   │   FLIGHT     │  │   HEALTH     │  │   PAYLOAD    │        │
│   │  CONTROLLER  │  │  MONITORING  │  │  MANAGEMENT  │        │
│   └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Feature Definitions

### 4.1 Mesh Networking

**ID:** CC-MESH
**Priority:** P0 (Critical)
**Platforms:** Bird, Chick

#### Description
Manages ad-hoc mesh network between swarm units and ground control. Provides resilient communication without centralized infrastructure.

#### Capabilities

| Capability | Description |
|------------|-------------|
| Mesh formation | Auto-discovery and joining of nearby nodes |
| Multi-hop routing | Forward packets through intermediate nodes |
| Link quality monitoring | Track RSSI, latency, packet loss per link |
| Bandwidth management | Prioritize critical traffic (position, commands) |
| Encryption | End-to-end encryption for all swarm traffic |

#### Interfaces

| Interface | Direction | Data |
|-----------|-----------|------|
| Radio hardware | Bidirectional | Raw packets |
| Internal services | Bidirectional | Application messages |
| Ground station | Bidirectional | Telemetry, commands |

#### Message Types

| Type | Priority | Rate | Description |
|------|----------|------|-------------|
| Position broadcast | High | 5 Hz | Own position to swarm |
| Heartbeat | High | 1 Hz | Node alive status |
| Command relay | Critical | Event | GCS commands |
| Telemetry | Medium | 1 Hz | Health data upstream |
| Payload data | Low | Variable | ISR products |

#### Transport Options

| Transport | Range | Bandwidth | Use Case |
|-----------|-------|-----------|----------|
| WiFi mesh (802.11s) | 500m | High | Primary, short range |
| LoRa | 5+ km | Low | Backup, long range |
| LTE/5G | Cell coverage | High | GCS backhaul |

---

### 4.2 ISR (Intelligence, Surveillance, Reconnaissance)

**ID:** CC-ISR
**Priority:** P1 (High)
**Platforms:** Bird (full), Chick (relay only)

#### Description
Manages imaging sensors and onboard processing for surveillance and reconnaissance missions.

#### Capabilities

| Capability | Bird | Chick |
|------------|------|-------|
| Camera control (gimbal, zoom, capture) | Yes | Yes |
| Video streaming | Yes | Yes |
| Onboard detection (YOLO/similar) | Yes | No |
| Target tracking | Yes | No |
| Image storage | Yes | Limited |
| Geotag injection | Yes | Yes |

#### Sensor Support

| Sensor Type | Interface | Notes |
|-------------|-----------|-------|
| RGB camera (gimbal) | MIPI CSI / USB | Primary ISR sensor |
| Thermal camera | USB / RTSP | Optional payload |
| Multispectral | USB | Mission-specific |

#### Processing Pipeline

```
Camera → Capture → [Detection] → [Tracking] → Encode → Stream/Store
                       ↓              ↓
                   Detections    Track updates
                       ↓              ↓
                   ─────────→ Mesh broadcast
```

#### Output Products

| Product | Format | Destination |
|---------|--------|-------------|
| Live video stream | H.264/H.265 | GCS via mesh |
| Detection alerts | Protobuf | GCS, swarm |
| Geotagged snapshots | JPEG + metadata | Local storage, GCS |
| Track reports | Protobuf | GCS |

---

### 4.3 VIO / Visual Navigation

**ID:** CC-VIO
**Priority:** P0 (Critical)
**Platforms:** Bird (full), Chick (limited)

#### Description
Provides visual-inertial odometry and GNSS-denied localization using camera and IMU data. Includes CLIP-based absolute positioning.

#### Capabilities

| Capability | Bird | Chick | Description |
|------------|------|-------|-------------|
| Visual odometry | Yes | Yes | Relative motion estimation |
| CLIP localization | Yes | No* | Absolute position from imagery |
| Sensor fusion | Yes | Yes | Combine visual + IMU + GPS |
| Terrain-relative nav | Yes | No | Altitude from ground features |

*Chick may offload CLIP inference to Bird via mesh

#### Subsystems

| Subsystem | Description | Document |
|-----------|-------------|----------|
| CLIP Localization | Absolute positioning via learned embeddings | [CLIP_ARCHITECTURE.md](CLIP_ARCHITECTURE.md) |
| Visual Odometry | Frame-to-frame motion estimation | TBD |
| State Estimator | EKF fusion of all navigation sources | TBD |

#### Output to Flight Controller

| MAVLink Message | Rate | Content |
|-----------------|------|---------|
| VISION_POSITION_ESTIMATE | 10-30 Hz | Position, orientation |
| VISION_SPEED_ESTIMATE | 10-30 Hz | Velocity |
| ODOMETRY | 30 Hz | Full state (if supported) |

---

### 4.4 Flight Controller Interface

**ID:** CC-FC
**Priority:** P0 (Critical)
**Platforms:** Bird, Chick

#### Description
Bidirectional communication with autopilot for telemetry, commands, and external navigation input.

#### Capabilities

| Capability | Description |
|------------|-------------|
| MAVLink bridge | Serial/UDP MAVLink 2.0 communication |
| Telemetry relay | Forward FC telemetry to mesh/GCS |
| Command injection | Accept commands from GCS, execute locally |
| Vision input | Send external position estimates to EKF |
| Mode management | Request mode changes, monitor state |
| Parameter access | Read/write autopilot parameters |

#### Supported Autopilots

| Autopilot | Support Level |
|-----------|---------------|
| PX4 | Primary |
| ArduPilot | Secondary |

#### Connection

| Interface | Protocol | Notes |
|-----------|----------|-------|
| UART (TELEM2) | MAVLink 2.0 | Primary, lowest latency |
| UDP | MAVLink 2.0 | Alternative via Ethernet |

---

### 4.5 Health Monitoring

**ID:** CC-HEALTH
**Priority:** P1 (High)
**Platforms:** Bird, Chick

#### Description
Monitors system health, manages faults, and provides diagnostics.

#### Monitored Subsystems

| Subsystem | Metrics |
|-----------|---------|
| Companion computer | CPU, GPU, memory, temperature, storage |
| Flight controller | Heartbeat, EKF status, battery |
| Cameras | Frame rate, connection status |
| Mesh radio | Link quality, connected peers |
| Navigation | Fix status, accuracy estimates |

#### Fault Response

| Fault | Severity | Response |
|-------|----------|----------|
| CC overheat | Warning | Throttle processing, alert GCS |
| FC heartbeat lost | Critical | Attempt reconnect, alert GCS |
| Mesh isolated | Warning | Attempt alternate links |
| VIO divergence | Warning | Fall back to GPS-only, alert |
| Storage full | Warning | Delete oldest logs, alert GCS |

#### Telemetry

| Data | Rate | Destination |
|------|------|-------------|
| System health summary | 1 Hz | GCS via mesh |
| Detailed diagnostics | On request | GCS |
| Fault alerts | Event-driven | GCS, local log |

---

### 4.6 Payload Management

**ID:** CC-PAYLOAD
**Priority:** P2 (Medium)
**Platforms:** Bird, Chick

#### Description
Generic interface for mission-specific payloads (drop mechanisms, specialized sensors, etc.).

#### Capabilities

| Capability | Description |
|------------|-------------|
| Payload discovery | Detect connected payloads |
| Command relay | Forward payload commands from GCS |
| Status reporting | Report payload state to GCS |
| Power management | Control payload power rails |

#### Interfaces

| Interface | Use Case |
|-----------|----------|
| USB | General peripherals |
| GPIO | Simple actuators, triggers |
| UART | Serial devices |
| CAN | Industrial payloads |

---

## 5. Software Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │  Mesh   │ │   ISR   │ │   VIO   │ │ Health  │ │ Payload │      │
│  │ Manager │ │ Manager │ │ Manager │ │ Monitor │ │ Manager │      │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘      │
│       └──────────┬┴──────────┬┴───────────┴──────────┬┘            │
│                  │           │                       │              │
├──────────────────▼───────────▼───────────────────────▼──────────────┤
│                       MESSAGE BUS (ZeroMQ)                          │
├─────────────────────────────────────────────────────────────────────┤
│                         SERVICE LAYER                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ MAVLink  │ │  Camera  │ │  Radio   │ │   IMU    │               │
│  │  Bridge  │ │  Driver  │ │  Driver  │ │  Driver  │               │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
├─────────────────────────────────────────────────────────────────────┤
│                        HARDWARE LAYER                               │
│     UART          CSI/USB        WiFi/LoRa        SPI/I2C          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Configuration

All features configurable via YAML:

```yaml
# /etc/swarmdrones/cc_config.yaml

platform: bird  # bird | chick

mesh:
  enabled: true
  node_id: auto
  wifi:
    interface: wlan0
    channel: 36
  lora:
    enabled: false

isr:
  enabled: true
  camera:
    device: /dev/video0
    resolution: [1920, 1080]
  detection:
    enabled: true
    model: yolov8n

vio:
  enabled: true
  clip:
    enabled: true
    model_path: /opt/models/geoclip.engine
  visual_odom:
    enabled: true

fc:
  connection: /dev/ttyTHS1
  baudrate: 921600
  sysid: 1
  compid: 191
```

---

## 7. Future Features (Placeholder)

| Feature | ID | Description | Status |
|---------|-----|-------------|--------|
| Autonomous mission execution | CC-AUTO | Waypoint/behavior execution | Planned |
| Collision avoidance | CC-AVOID | Sense-and-avoid using depth | Planned |
| Swarm coordination | CC-SWARM | Formation, task allocation | Planned |
| Edge compute offload | CC-OFFLOAD | Distribute inference across swarm | Planned |
| Secure boot | CC-SECURE | Verified boot chain | Planned |

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-22 | - | Initial draft |
