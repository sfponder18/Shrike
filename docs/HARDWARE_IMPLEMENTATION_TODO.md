# Hardware Implementation To-Do List

**Last Updated:** 2026-01-25
**Status:** Pre-Hardware Development
**Target:** V1 Hardware Deployment

---

## Overview

This document tracks all items that must be completed before deploying the GCS with real hardware. Items are organized by priority and component.

---

## Priority 1: Critical Path (Must Have)

### 1.1 LoRa Mesh Communication
**File:** `gcs/comms/lora_manager.py`

- [ ] **Serial Connection** (Line 133-152)
  - [ ] Implement `connect()` with pyserial
  - [ ] Add connection error handling and retry logic
  - [ ] Implement `disconnect()` cleanup
  - [ ] Add connection status monitoring

- [ ] **Send Commands** (Lines 164-306)
  - [ ] Implement `send_target_to_chick()` - write packet to serial
  - [ ] Implement `send_arm_command()` - write packet to serial
  - [ ] Implement `send_disarm_command()` - write packet to serial
  - [ ] Implement `send_release_command()` - write packet to serial
  - [ ] Add ACK waiting and retry logic for all commands
  - [ ] Add command timeout handling

- [ ] **Receive Messages**
  - [ ] Implement serial read loop (background thread)
  - [ ] Parse incoming TELEM messages
  - [ ] Parse incoming ACK messages
  - [ ] Parse incoming STATUS messages
  - [ ] Parse incoming ALERT messages
  - [ ] Emit appropriate signals on message receipt

- [ ] **Testing**
  - [ ] Test with T-Beam hardware on bench
  - [ ] Verify packet encoding/decoding
  - [ ] Test mesh node discovery
  - [ ] Verify RSSI/SNR reporting

### 1.2 Video Streaming
**File:** `gcs/comms/video_manager.py`

- [ ] **RTSP Capture** (Lines 102-128)
  - [ ] Implement `start_stream()` with OpenCV
  - [ ] Add GStreamer pipeline for low-latency RTSP
  - [ ] Implement capture thread with frame queue
  - [ ] Add reconnection logic on stream loss
  - [ ] Handle resolution/FPS negotiation

- [ ] **Stream Management**
  - [ ] Implement proper `stop_stream()` cleanup
  - [ ] Add stream health monitoring
  - [ ] Implement frame drop detection
  - [ ] Add latency measurement

- [ ] **Testing**
  - [ ] Test with Pi 5 RTSP server
  - [ ] Verify latency < 200ms target
  - [ ] Test stream switching between sources
  - [ ] Test recovery from network interruption

### 1.3 MAVLink Hardware Connection
**File:** `gcs/comms/mavlink_manager.py`

- [ ] **MLRS Serial** (Lines 199-236)
  - [ ] Test `connect_mlrs()` with actual MLRS TX module
  - [ ] Verify multi-vehicle addressing over shared bus
  - [ ] Test command latency and reliability
  - [ ] Add MLRS-specific error handling

- [ ] **4G/Tailscale Backup** (Lines 238-276)
  - [ ] Test `connect_backup()` with Tailscale connection
  - [ ] Implement automatic failover from MLRS to 4G
  - [ ] Add connection quality monitoring
  - [ ] Test failback to MLRS when available

- [ ] **Connection Resilience**
  - [ ] Add heartbeat timeout detection per vehicle
  - [ ] Implement automatic reconnection attempts
  - [ ] Add connection state machine (connecting/connected/degraded/lost)
  - [ ] Emit warnings on degraded connection

---

## Priority 2: Safety Features (Must Have)

### 2.1 Failsafe Implementation
**File:** `gcs/comms/mavlink_manager.py` (new section needed)

- [ ] **Connection Loss Failsafe**
  - [ ] Define timeout thresholds (e.g., 5s warning, 15s RTL)
  - [ ] Implement automatic RTL on connection loss
  - [ ] Add operator override to cancel auto-RTL
  - [ ] Log all failsafe activations

- [ ] **Geofence Enforcement**
  - [ ] Add geofence definition (center point + radius or polygon)
  - [ ] Check vehicle position against geofence on each telemetry update
  - [ ] Warn operator when vehicle approaches boundary
  - [ ] Optional: auto-RTL on geofence breach

- [ ] **Altitude Limits**
  - [ ] Define min/max altitude per vehicle type
  - [ ] Reject commands that would exceed limits
  - [ ] Warn operator when approaching limits

### 2.2 Pre-Flight Checks
**File:** `Sandbox/gcs_sandbox/app.py` - `_on_preflight()` method

- [ ] **Blocking Checks**
  - [ ] Verify GPS 3D fix on all vehicles
  - [ ] Verify battery above minimum threshold
  - [ ] Verify LoRa mesh connectivity to all nodes
  - [ ] Verify MAVLink connection to all vehicles
  - [ ] Verify EKF status is healthy

- [ ] **Warning Checks**
  - [ ] Check weather/wind conditions (if available)
  - [ ] Verify mission is uploaded
  - [ ] Check for obstacles in mission path (if terrain data available)

- [ ] **Enforcement**
  - [ ] Block ARM command until critical checks pass
  - [ ] Add operator override with confirmation dialog

### 2.3 Emergency Stop
**File:** New file needed: `gcs/comms/safety_manager.py`

- [ ] **Software E-Stop**
  - [ ] Add global LAND ALL command (Ctrl+L or dedicated button)
  - [ ] Add global DISARM ALL command (with double-confirmation)
  - [ ] Implement kill switch integration (USB HID device)

- [ ] **Hardware Integration**
  - [ ] Define physical kill switch protocol
  - [ ] Implement USB HID listener for kill switch
  - [ ] Test kill switch response time

---

## Priority 3: Operational Features (Should Have)

### 3.1 Formation Tracking for Hardware
**File:** `gcs/comms/mavlink_manager.py` (Lines 1252-1281)

- [ ] **LoRa-Based Position Sharing**
  - [ ] Define position broadcast message format
  - [ ] Implement Bird position broadcast via LoRa
  - [ ] Implement Chick position reception and formation calculation
  - [ ] Add fallback to MAVLink-based tracking if LoRa fails

- [ ] **Formation Health Monitoring**
  - [ ] Track formation cohesion metrics
  - [ ] Warn if Chick falls too far behind
  - [ ] Implement automatic formation reform

### 3.2 Prosecution/EW Integration
**File:** `Sandbox/gcs_sandbox/comms/ew_manager.py`

- [ ] **Real DF Integration**
  - [ ] Define interface for real SDR/DF hardware
  - [ ] Replace simulated bearing data with real sensor input
  - [ ] Implement proper triangulation algorithm
  - [ ] Add CEP calculation from real data

- [ ] **Target Tracking State Machine**
  - [ ] Add timeout for stale tracks
  - [ ] Implement track fusion from multiple sensors
  - [ ] Add track quality scoring

### 3.3 Telemetry Logging
**File:** New file needed: `gcs/comms/telemetry_logger.py`

- [ ] **Flight Recording**
  - [ ] Log all telemetry to timestamped file
  - [ ] Log all commands sent
  - [ ] Log all mode changes and events
  - [ ] Implement log rotation

- [ ] **Replay Capability**
  - [ ] Implement telemetry file reader
  - [ ] Add replay mode for post-flight analysis

---

## Priority 4: Nice to Have

### 4.1 Enhanced Map Features
- [ ] Offline map tile caching
- [ ] Terrain elevation overlay
- [ ] Weather radar overlay
- [ ] Airspace boundaries display

### 4.2 Mission Planning Enhancements
- [ ] Terrain-following altitude mode
- [ ] Survey pattern generator
- [ ] Time-on-target planning
- [ ] Fuel/battery planning with reserves

### 4.3 Multi-GCS Support
- [ ] Define GCS-to-GCS communication protocol
- [ ] Implement primary/secondary GCS roles
- [ ] Add handoff capability

---

## Testing Checklist

### Bench Testing
- [ ] All LoRa commands send/receive correctly
- [ ] Video streams start/stop reliably
- [ ] MAVLink connections work over MLRS
- [ ] MAVLink connections work over 4G/Tailscale
- [ ] Failsafe triggers correctly on connection loss
- [ ] Pre-flight checks block ARM when appropriate

### Ground Testing (Motors Disabled)
- [ ] Full system integration test
- [ ] GPS acquisition and telemetry flow
- [ ] Mode changes work correctly
- [ ] Mission upload/download works
- [ ] EW panel receives simulated data

### Flight Testing
- [ ] Single vehicle hover test
- [ ] Single vehicle mission test
- [ ] Multi-vehicle formation test
- [ ] Chick launch sequence test
- [ ] Failsafe activation test (controlled)
- [ ] Full prosecution workflow test

---

## Dependencies to Install

```bash
# Required for hardware operation
pip install pyserial          # LoRa T-Beam serial
pip install opencv-python     # Video capture
pip install av                # RTSP streaming (alternative)
pip install pymavlink         # MAVLink protocol (already installed for SITL)

# Optional
pip install meshtastic        # If using Meshtastic firmware on T-Beams
```

---

## Hardware Required

| Item | Quantity | Purpose | Status |
|------|----------|---------|--------|
| T-Beam v1.1 | 4 | LoRa mesh nodes (GCS, Bird, Chick1, Chick2) | |
| MLRS TX Module | 1 | MAVLink radio link | |
| MLRS RX Module | 3 | MAVLink receivers on vehicles | |
| USB Kill Switch | 1 | Emergency stop | |
| 4G Modem | 1 | Backup link (Bird Pi 5) | |

---

## Notes

- All simulation-mode code should remain for development and testing
- Use feature flags or connection mode checks to switch between sim/hardware
- Always test changes in simulation before hardware
- Document any hardware-specific quirks discovered during integration

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-25 | Claude | Initial document created from code review |
