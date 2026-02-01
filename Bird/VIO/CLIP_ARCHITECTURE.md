# CLIP Localization Architecture
## Bird Platform Implementation

**Version:** 0.1
**Date:** 2026-01-22
**Status:** Draft
**Parent:** [COMPANION_COMPUTER_FEATURES.md](COMPANION_COMPUTER_FEATURES.md) (CC-VIO)

---

## 1. Overview

This document specifies the architecture for CLIP-based visual localization on the Bird platform (Jetson Orin). The system provides absolute position estimates in GNSS-denied environments by matching aerial imagery against pre-computed reference embeddings.

### 1.1 Reference Implementation

Based on [CLIP-UAV-localization](https://github.com/codebra721/CLIP-UAV-localization):

| Metric | Reference Result |
|--------|------------------|
| Position error (avg) | 39.2 m |
| Heading error (avg) | 15.9° |
| Test area | 2.23 km² |
| Input resolution | 224×224 px |
| Model base | GeoCLIP |

### 1.2 Goals

| Goal | Target |
|------|--------|
| Inference rate | ≥5 Hz |
| Latency | <150 ms end-to-end |
| Position accuracy | <50 m (90th percentile) |
| Heading accuracy | <20° (90th percentile) |
| Power budget | <15 W (inference only) |

---

## 2. System Context

```
                                    ┌─────────────────────┐
                                    │    Ground Station   │
                                    │  (Map Preparation)  │
                                    └──────────┬──────────┘
                                               │
                                    Map embeddings (offline)
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                            BIRD UAV                                  │
│                                                                      │
│  ┌──────────┐    ┌────────────────────────────────────────────────┐ │
│  │  Camera  │───▶│           CLIP LOCALIZATION MODULE             │ │
│  │ (nadir)  │    │                                                │ │
│  └──────────┘    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │ │
│                  │  │  Image   │  │  CLIP    │  │   Position   │ │ │
│  ┌──────────┐    │  │ Capture  │─▶│ Encoder  │─▶│   Decoder    │ │ │
│  │   IMU    │───▶│  └──────────┘  └──────────┘  └──────────────┘ │ │
│  └──────────┘    │                                    │          │ │
│                  │                                    ▼          │ │
│  ┌──────────┐    │                          ┌──────────────────┐ │ │
│  │   GPS    │───▶│                          │  State Estimator │ │ │
│  │(if avail)│    │                          │      (EKF)       │ │ │
│  └──────────┘    │                          └────────┬─────────┘ │ │
│                  └───────────────────────────────────┼───────────┘ │
│                                                      │             │
│                                                      ▼             │
│                                           ┌──────────────────┐     │
│                                           │ Flight Controller│     │
│                                           │   (PX4/Ardupilot)│     │
│                                           └──────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architecture

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CLIP LOCALIZATION MODULE                           │
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐   │
│  │   Camera    │     │   Frame     │     │      Preprocessor       │   │
│  │   Input     │────▶│   Buffer    │────▶│  - Resize (224×224)     │   │
│  │             │     │  (3 frames) │     │  - Normalize            │   │
│  └─────────────┘     └─────────────┘     │  - GPU transfer         │   │
│                                          └────────────┬────────────┘   │
│                                                       │                 │
│                                                       ▼                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     INFERENCE ENGINE                              │  │
│  │  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐  │  │
│  │  │  Image Encoder │    │    Location    │    │    Heading     │  │  │
│  │  │   (ViT-B/32)   │───▶│    Decoder     │    │    Decoder     │  │  │
│  │  │   TensorRT     │    │    (MLP)       │    │    (MLP)       │  │  │
│  │  └────────────────┘    └───────┬────────┘    └───────┬────────┘  │  │
│  │                                │                     │            │  │
│  └────────────────────────────────┼─────────────────────┼────────────┘  │
│                                   │                     │               │
│                                   ▼                     ▼               │
│                          ┌─────────────────────────────────────────┐   │
│                          │            Post-Processor               │   │
│                          │  - Coordinate transform                 │   │
│                          │  - Temporal smoothing                   │   │
│                          │  - Confidence estimation                │   │
│                          └───────────────────┬─────────────────────┘   │
│                                              │                         │
│                                              ▼                         │
│                                   ┌───────────────────┐                │
│                                   │  Position Output  │                │
│                                   │  (lat, lon, hdg,  │                │
│                                   │   confidence)     │                │
│                                   └───────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Components

#### 3.2.1 Camera Input

| Parameter | Value |
|-----------|-------|
| Orientation | Nadir (downward-facing) |
| Sensor | IMX477 or equivalent |
| Resolution | 1920×1080 (capture) |
| Frame rate | 30 fps (capture), 5-10 fps (inference) |
| Interface | MIPI CSI-2 |

**Requirements:**
- Fixed downward mount (no gimbal required for localization)
- Global shutter preferred (reduces motion blur)
- Sufficient light sensitivity for varied conditions

#### 3.2.2 Frame Buffer

Circular buffer holding recent frames for:
- Frame selection (sharpest, least motion blur)
- Temporal consistency checks
- Fallback if inference fails

| Parameter | Value |
|-----------|-------|
| Buffer size | 3 frames |
| Selection criteria | Laplacian variance (sharpness) |

#### 3.2.3 Preprocessor

Prepares frames for inference:

```python
transforms = Compose([
    Resize((224, 224)),
    ToTensor(),
    Normalize(mean=[0.48145466, 0.4578275, 0.40821073],
              std=[0.26862954, 0.26130258, 0.27577711])  # CLIP stats
])
```

| Operation | Time (est.) |
|-----------|-------------|
| Resize | <1 ms |
| Normalize | <1 ms |
| GPU transfer | <2 ms |

#### 3.2.4 Inference Engine

**Model Architecture (GeoCLIP-based):**

| Component | Architecture | Parameters |
|-----------|--------------|------------|
| Image Encoder | ViT-B/32 | ~86M |
| Location Decoder | MLP (3 layers) | ~1M |
| Heading Decoder | MLP (2 layers) | ~0.5M |
| **Total** | | ~87.5M |

**Output:**
- Latitude (float32)
- Longitude (float32)
- Heading angle (float32, degrees)
- Top-k candidates for confidence estimation

#### 3.2.5 Post-Processor

| Function | Description |
|----------|-------------|
| Coordinate transform | Model output → WGS84 |
| Temporal smoothing | Gaussian filter (σ=3 frames) |
| Outlier rejection | Mahalanobis distance check |
| Confidence estimation | Based on top-k spread |

**Confidence Calculation:**
```
confidence = 1.0 - (std(top_k_positions) / max_expected_std)
```

---

## 4. Optimization Strategy

### 4.1 TensorRT Conversion

```
PyTorch (.pt) → ONNX (.onnx) → TensorRT (.engine)
```

| Stage | Tool | Output |
|-------|------|--------|
| Export | torch.onnx.export | geoclip.onnx |
| Optimize | trtexec | geoclip_fp16.engine |
| Validate | Custom script | Accuracy report |

**TensorRT Options:**

```bash
trtexec --onnx=geoclip.onnx \
        --saveEngine=geoclip_fp16.engine \
        --fp16 \
        --workspace=4096 \
        --buildOnly
```

### 4.2 Precision Comparison

| Precision | Size | Inference Time* | Accuracy Loss |
|-----------|------|-----------------|---------------|
| FP32 | ~350 MB | ~80 ms | Baseline |
| FP16 | ~175 MB | ~35 ms | <1% |
| INT8 | ~90 MB | ~20 ms | 2-5% |

*Estimated for Jetson Orin NX

**Recommendation:** Use FP16 for balance of speed and accuracy. INT8 available as fallback for power-constrained operation.

### 4.3 Memory Layout

| Allocation | Size | Location |
|------------|------|----------|
| TensorRT engine | ~175 MB | GPU |
| Input buffer | ~600 KB | GPU (pinned) |
| Output buffer | ~64 B | GPU (pinned) |
| Frame buffer | ~18 MB | System RAM |
| **Total GPU** | ~176 MB | |

---

## 5. Data Flow

### 5.1 Inference Pipeline

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│ Camera │───▶│ Select │───▶│Preproc │───▶│Inference│───▶│ Output │
│ 30 fps │    │ 10 fps │    │ GPU    │    │TensorRT│    │        │
└────────┘    └────────┘    └────────┘    └────────┘    └────────┘
    │              │             │             │             │
    │         Frame selection    │        ~35ms FP16        │
    │         (sharpness)        │                          │
    │                            │                          │
    └────────────────────────────┴──────────────────────────┘
                    Total latency target: <100ms
```

### 5.2 Timing Budget

| Stage | Budget | Notes |
|-------|--------|-------|
| Frame capture | 10 ms | Triggered, not continuous |
| Frame selection | 5 ms | Laplacian variance |
| Preprocessing | 5 ms | Resize, normalize, transfer |
| Inference | 35 ms | TensorRT FP16 |
| Post-processing | 5 ms | Smoothing, transform |
| **Total** | **60 ms** | Allows 15+ Hz theoretical |
| IPC overhead | 10 ms | ZeroMQ to state estimator |
| **End-to-end** | **70 ms** | Target: <100 ms |

---

## 6. Integration

### 6.1 Output Interface

Published via ZeroMQ PUB socket:

```protobuf
message ClipPosition {
    double timestamp = 1;      // Unix timestamp
    double latitude = 2;       // WGS84 degrees
    double longitude = 3;      // WGS84 degrees
    float heading = 4;         // Degrees, 0=North, CW positive
    float confidence = 5;      // 0.0 - 1.0
    uint32 sequence = 6;       // Frame sequence number
}
```

| Parameter | Value |
|-----------|-------|
| Socket | tcp://127.0.0.1:5555 |
| Topic | "clip/position" |
| Rate | 5-10 Hz |

### 6.2 State Estimator Integration

The CLIP output feeds into the VIO state estimator (EKF) as a position measurement:

| EKF Input | From CLIP | Noise Model |
|-----------|-----------|-------------|
| Position (lat, lon) | Yes | σ = f(confidence), typ. 30-50m |
| Heading | Yes | σ = f(confidence), typ. 15-25° |
| Velocity | No | Derived from consecutive positions |

**Measurement Model:**
```
z = [lat, lon, heading]
R = diag([σ_pos², σ_pos², σ_hdg²])  # Scaled by 1/confidence
```

### 6.3 Flight Controller Output

After fusion, the state estimator outputs to FC via MAVLink:

```
VISION_POSITION_ESTIMATE (#102)
  - usec: timestamp
  - x, y, z: NED position (meters, from reference)
  - roll, pitch, yaw: orientation (radians)
  - covariance: 21-element upper triangle
```

---

## 7. Map Management

### 7.1 Reference Embeddings

The CLIP model compares live imagery against pre-computed reference embeddings covering the operational area.

| Parameter | Value |
|-----------|-------|
| Grid resolution | ~10m spacing |
| Embedding dimension | 512 (CLIP ViT-B/32) |
| Storage per point | 2 KB (512 × float32) |

**Coverage Requirements:**

| Area | Grid Points | Storage |
|------|-------------|---------|
| 1 km² | ~10,000 | ~20 MB |
| 10 km² | ~100,000 | ~200 MB |
| 100 km² | ~1,000,000 | ~2 GB |

### 7.2 Map Structure

```
/opt/swarmdrones/maps/
├── index.json              # Map metadata, bounds
├── region_001/
│   ├── embeddings.bin      # Binary embedding data
│   ├── coordinates.bin     # Corresponding lat/lon
│   └── metadata.json       # Region info
├── region_002/
│   └── ...
```

### 7.3 Runtime Loading

| Strategy | Description |
|----------|-------------|
| Full preload | Load entire map at startup (small areas) |
| Region-based | Load regions near current position |
| Streaming | Load on-demand with LRU cache |

**Default:** Region-based with 2 km² active window

---

## 8. Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Low confidence (<0.3) | Confidence output | Increase R in EKF, warn |
| No valid output | Timeout (>500ms) | Skip measurement, log |
| Position jump (>100m) | Delta check | Reject as outlier |
| Camera failure | Frame timeout | Disable CLIP, alert |
| Model crash | Process monitor | Restart inference engine |

**Graceful Degradation:**
1. CLIP + GPS + IMU → Full fusion
2. CLIP + IMU → Visual-inertial (no GPS)
3. GPS + IMU → Traditional (no vision)
4. IMU only → Dead reckoning (emergency)

---

## 9. Configuration

```yaml
# /etc/swarmdrones/clip_config.yaml

clip:
  enabled: true

  model:
    path: /opt/swarmdrones/models/geoclip_fp16.engine
    precision: fp16  # fp32, fp16, int8

  camera:
    device: /dev/video0
    resolution: [1920, 1080]
    fps: 30

  inference:
    rate_hz: 10
    batch_size: 1

  preprocessing:
    resize: [224, 224]
    normalize: true

  postprocessing:
    temporal_smooth: true
    smooth_sigma: 3
    outlier_rejection: true
    outlier_threshold_m: 100

  map:
    path: /opt/swarmdrones/maps/
    preload_radius_m: 1000

  output:
    socket: tcp://127.0.0.1:5555
    topic: clip/position

  thresholds:
    min_confidence: 0.3
    position_sigma_m: 40
    heading_sigma_deg: 18
```

---

## 10. Testing & Validation

### 10.1 Offline Validation

| Test | Dataset | Success Criteria |
|------|---------|------------------|
| Accuracy | CCU-UAV test set | <50m position, <20° heading |
| Inference speed | Synthetic | >10 Hz sustained |
| Memory usage | Runtime profile | <500 MB total |

### 10.2 Hardware-in-Loop

| Test | Setup | Success Criteria |
|------|-------|------------------|
| Latency | Jetson + camera | <100ms end-to-end |
| Thermal | Sustained inference | <80°C junction |
| Power | Power meter | <15W average |

### 10.3 Flight Validation

| Test | Conditions | Success Criteria |
|------|------------|------------------|
| GPS-available | Open field | CLIP matches GPS ±50m |
| GPS-denied | Simulate jamming | Maintains position estimate |
| Transition | GPS dropout/restore | Smooth handoff |

---

## 11. Development Roadmap

### Phase 1: Model Porting
- [ ] Export PyTorch model to ONNX
- [ ] Convert to TensorRT (FP16)
- [ ] Validate accuracy on Jetson
- [ ] Benchmark inference speed

### Phase 2: Pipeline Integration
- [ ] Implement camera capture
- [ ] Build preprocessing pipeline
- [ ] Integrate inference engine
- [ ] Implement post-processing

### Phase 3: System Integration
- [ ] ZeroMQ output publisher
- [ ] EKF measurement input
- [ ] MAVLink output
- [ ] Configuration system

### Phase 4: Validation
- [ ] Offline accuracy testing
- [ ] HIL testing on bench
- [ ] Tethered flight testing
- [ ] Full flight validation

---

## 12. References

1. [CLIP-UAV-localization](https://github.com/codebra721/CLIP-UAV-localization) - Reference implementation
2. [GeoCLIP Paper](https://arxiv.org/abs/2309.16020) - Base architecture
3. [TensorRT Documentation](https://developer.nvidia.com/tensorrt)
4. [PX4 External Vision](https://docs.px4.io/main/en/ros/external_position_estimation.html)
5. [MAVLink VISION_POSITION_ESTIMATE](https://mavlink.io/en/messages/common.html#VISION_POSITION_ESTIMATE)

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-22 | - | Initial draft |
