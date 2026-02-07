# Companion Computer Trade Study

**Project:** Shrike
**Date:** 2026-02-07
**Purpose:** Evaluate low-SWaP companion computers for Carrier and Scout platforms

---

## 1. Requirements

### Carrier Requirements (Higher Capability)
| Requirement | Priority | Notes |
|-------------|----------|-------|
| AI/ML inference | High | Object detection, signal processing |
| Camera interfaces | High | Multiple MIPI-CSI for sensors |
| SDR data throughput | High | USB 3.0 minimum |
| Flight controller integration | Medium | PX4/ArduPilot compatible |
| Weight | Medium | <150g acceptable |
| Power consumption | Medium | <25W acceptable |
| Cost | Low | Up to $1,500 acceptable |

### Scout Requirements (Lower SWaP)
| Requirement | Priority | Notes |
|-------------|----------|-------|
| Weight | **Critical** | <50g ideal, <100g acceptable |
| Power consumption | **Critical** | <10W ideal |
| AI/ML inference | Medium | Basic detection sufficient |
| SDR data throughput | Medium | USB 2.0 acceptable |
| Cost | High | Target <$200 per Scout |
| Flight controller integration | Low | Separate FC acceptable |

---

## 2. Candidate Platforms

### Tier 1: Purpose-Built Drone Computers

#### ModalAI VOXL 2
| Spec | Value |
|------|-------|
| **Processor** | Qualcomm QRB5165 (8-core Kryo 585, up to 3.09 GHz) |
| **GPU** | Adreno 650 |
| **AI Accelerator** | Hexagon 698 NPU — **15 TOPS** |
| **RAM** | 8 GB LPDDR5 |
| **Camera** | 7× simultaneous MIPI-CSI inputs |
| **Weight** | **16g** |
| **Size** | 70 × 36 mm |
| **Power** | ~10W typical |
| **FC Integration** | **Integrated** (PX4 on DSP) |
| **IMU/Baro** | **Integrated** (TDK ICM-42688, ICP-10111) |
| **Connectivity** | USB 3.0, UART, I2C, SPI, WiFi 6, optional 5G |
| **Price** | **$1,270** (board only), $1,370 (dev kit) |

**Pros:**
- Lightest option (16g)
- Integrated flight controller — no separate FC needed
- Purpose-built for drones
- 7 camera inputs
- Strong AI performance (15 TOPS)
- Excellent software ecosystem (PX4, ROS, Docker)

**Cons:**
- Most expensive option
- Qualcomm ecosystem (some learning curve)
- Overkill for simple Scout applications

**Best for:** Carrier (primary), High-end Scout variants

---

#### Qualcomm Flight RB5
| Spec | Value |
|------|-------|
| **Processor** | Qualcomm QRB5165 (same as VOXL 2) |
| **GPU** | Adreno 650 |
| **AI Accelerator** | Hexagon NPU — **15 TOPS** |
| **RAM** | 8 GB LPDDR4x |
| **Camera** | Dual 14-bit ISP, up to 200 MP |
| **Weight** | ~50g (varies by config) |
| **Power** | ~10-15W |
| **FC Integration** | Yes (PX4/ArduPilot) |
| **Connectivity** | WiFi 6, optional 5G |
| **Price** | ~$1,000-1,500 |

**Pros:**
- Same core silicon as VOXL 2
- 5G capability option
- Strong AI performance

**Cons:**
- Heavier than VOXL 2
- Less integrated (separate FC may be needed)
- Reference design, less polished than VOXL 2

**Best for:** Alternative to VOXL 2 if 5G is critical

---

### Tier 2: High-Performance Embedded AI

#### NVIDIA Jetson Orin NX (16GB)
| Spec | Value |
|------|-------|
| **Processor** | 8-core ARM Cortex-A78AE |
| **GPU** | NVIDIA Ampere (1024 CUDA, 32 Tensor cores) |
| **AI Accelerator** | Tensor cores — **100 TOPS** (up to 157 TOPS at 25W) |
| **RAM** | 16 GB LPDDR5 |
| **Camera** | Up to 6× CSI (via carrier board) |
| **Weight** | ~50g (module only), ~150g with carrier |
| **Size** | 69.6 × 45 mm (module) |
| **Power** | 10-25W configurable |
| **FC Integration** | **None** — needs separate Pixhawk |
| **Price** | **~$700** (module), ~$900 with carrier |

**Pros:**
- **Best AI performance** (100+ TOPS)
- CUDA/TensorRT ecosystem
- Strong for computer vision, ML
- Good price/performance

**Cons:**
- Heavier with carrier board
- No integrated FC — adds weight and complexity
- Higher power consumption at full performance

**Best for:** Carrier (if heavy AI processing needed), Ground station compute

---

#### NVIDIA Jetson Orin Nano (8GB)
| Spec | Value |
|------|-------|
| **Processor** | 6-core ARM Cortex-A78AE |
| **GPU** | NVIDIA Ampere (1024 CUDA, 32 Tensor cores) |
| **AI Accelerator** | Tensor cores — **40-67 TOPS** |
| **RAM** | 8 GB LPDDR5 |
| **Weight** | ~50g (module only), ~140g with carrier |
| **Power** | 7-15W configurable |
| **FC Integration** | **None** |
| **Price** | **$249** (dev kit, 2024 pricing) |

**Pros:**
- Excellent price/performance ($249 dev kit)
- 40-67 TOPS AI performance
- Full CUDA ecosystem
- Lower power than Orin NX

**Cons:**
- Still needs carrier board (adds weight)
- No integrated FC
- 140g+ with carrier — too heavy for Scout

**Best for:** Carrier (budget option), Development/testing

---

### Tier 3: Budget/Lightweight Options

#### Raspberry Pi 5 (8GB)
| Spec | Value |
|------|-------|
| **Processor** | Broadcom BCM2712 (4-core Cortex-A76 @ 2.4 GHz) |
| **GPU** | VideoCore VII |
| **AI Accelerator** | **None** (requires add-on) |
| **RAM** | 8 GB LPDDR4X |
| **Camera** | 2× MIPI-CSI |
| **Weight** | **~50g** |
| **Power** | 5-10W |
| **FC Integration** | **None** |
| **Price** | **$80** |

**Pros:**
- Cheapest option
- Huge software ecosystem
- Lightweight
- Good general-purpose compute

**Cons:**
- **No AI accelerator** without add-on
- No integrated FC
- Limited camera inputs
- Weak for ML inference without Hailo

**Best for:** Scout (basic), Development, Budget builds

---

#### Raspberry Pi 5 + Hailo-8
| Spec | Value |
|------|-------|
| **Base** | Raspberry Pi 5 |
| **AI Accelerator** | Hailo-8 — **26 TOPS** |
| **Combined Weight** | ~70-80g |
| **Combined Power** | 7-12W |
| **Price** | **$80 + $100 = $180** |

**Pros:**
- Strong AI (26 TOPS) at low cost
- Familiar Pi ecosystem
- Lightweight combination

**Cons:**
- Two-board solution (more complex)
- No FC integration
- M.2 HAT adds bulk

**Best for:** Scout (enhanced), Budget Carrier

---

#### Raspberry Pi Zero 2W
| Spec | Value |
|------|-------|
| **Processor** | Broadcom BCM2710A1 (4-core Cortex-A53 @ 1 GHz) |
| **RAM** | 512 MB |
| **Weight** | **~10g** |
| **Power** | 1-3W |
| **Price** | **$15** |

**Pros:**
- **Lightest compute option** (10g)
- Very low power
- Extremely cheap

**Cons:**
- Very limited compute (512 MB RAM!)
- USB 2.0 only
- No AI capability
- Struggles with real-time processing

**Best for:** Scout (minimal), Simple telemetry relay

---

### Tier 4: Alternative SBCs

#### Khadas Edge2 (RK3588S)
| Spec | Value |
|------|-------|
| **Processor** | RK3588S (4× A76 @ 2.25 GHz, 4× A55 @ 1.8 GHz) |
| **GPU** | Mali-G610 |
| **AI Accelerator** | **6 TOPS** NPU |
| **RAM** | 8 or 16 GB LPDDR4X |
| **Camera** | 3× MIPI-CSI (up to 48 MP each) |
| **Weight** | ~50g |
| **Power** | 5-15W |
| **Price** | **$200-300** |

**Pros:**
- Good balance of price/performance
- 6 TOPS NPU
- Multiple camera inputs
- RK3588 well-supported in Linux

**Cons:**
- No FC integration
- Smaller ecosystem than Jetson/Pi
- NPU support still maturing

**Best for:** Scout (enhanced), Budget Carrier alternative

---

#### Google Coral Dev Board
| Spec | Value |
|------|-------|
| **Processor** | NXP i.MX 8M (4-core Cortex-A53 @ 1.5 GHz) |
| **AI Accelerator** | Edge TPU — **4 TOPS** |
| **RAM** | 1-4 GB LPDDR4 |
| **Power** | 2-4W |
| **Price** | **$150** |

**Pros:**
- Very low power (2-4W)
- Efficient Edge TPU for inference
- Good for specific ML models

**Cons:**
- Limited to TensorFlow Lite models
- Lower general compute
- 4 TOPS is modest
- Limited availability

**Best for:** Scout (if TFLite is acceptable), Low-power applications

---

### Tier 5: Integrated Solutions

#### Holybro Pixhawk RPi CM4 Baseboard
| Spec | Value |
|------|-------|
| **Compute** | Raspberry Pi CM4 (user-supplied) |
| **FC Integration** | **Integrated Pixhawk 6X** |
| **Interfaces** | USB 3.0, HDMI, GbE, UART, CAN, I2C, GPIO |
| **Weight** | ~100g (with CM4 and FC) |
| **Price** | **$450** (baseboard) + CM4 (~$75-100) |

**Pros:**
- **Single-board FC + Companion**
- Pixhawk 6X quality FC
- CM4 swappable
- PX4 compatible out of box

**Cons:**
- CM4 has no AI accelerator
- Total weight ~100g+
- CM4 is older than Pi 5

**Best for:** Carrier (simple), Development platform

---

## 3. Comparison Matrix

| Platform | AI (TOPS) | Weight | Power | FC Integrated | Cameras | Price | Score* |
|----------|-----------|--------|-------|---------------|---------|-------|--------|
| **VOXL 2** | 15 | **16g** | 10W | **Yes** | 7 | $1,270 | ★★★★★ |
| Jetson Orin NX | **100+** | 150g | 25W | No | 6 | $900 | ★★★★☆ |
| Jetson Orin Nano | 40-67 | 140g | 15W | No | 6 | $249 | ★★★★☆ |
| RB5 | 15 | 50g | 15W | Yes | 4 | $1,200 | ★★★☆☆ |
| RPi 5 + Hailo-8 | 26 | 80g | 12W | No | 2 | $180 | ★★★★☆ |
| Khadas Edge2 | 6 | 50g | 10W | No | 3 | $250 | ★★★☆☆ |
| Holybro CM4 | 0** | 100g | 8W | **Yes** | 2 | $550 | ★★★☆☆ |
| RPi Zero 2W | 0 | **10g** | 2W | No | 1 | $15 | ★★☆☆☆ |

*Score based on Carrier suitability (weight, AI, integration)
**CM4 has no AI accelerator; could add Coral USB

---

## 4. Recommendations

### For Carrier

**Primary: ModalAI VOXL 2** ($1,270)
- Best weight (16g)
- Integrated FC eliminates separate board
- 15 TOPS sufficient for SDR processing + CV
- 7 cameras for full sensor suite
- Purpose-built for autonomous drones

**Alternative: Jetson Orin Nano + Pixhawk 6C** (~$450 total)
- Better AI performance (40-67 TOPS) if needed
- Lower cost
- Accepts heavier weight (140g + 50g = 190g)

**Budget: RPi 5 + Hailo-8 + Pixhawk 6C** (~$380 total)
- 26 TOPS AI at low cost
- Heavier and more complex
- Good for prototyping

### For Scout

**Primary: Raspberry Pi Zero 2W** ($15)
- Minimal weight (10g)
- Sufficient for basic telemetry and camera
- Offload heavy processing to Carrier/GCS
- Matches Scout attritable philosophy

**Enhanced: Raspberry Pi 5** ($80)
- Better compute for on-board processing
- 50g still acceptable for 5" quad
- Can add Hailo-8 if AI needed ($180 total)

**Not Recommended for Scout:**
- VOXL 2: Too expensive for attritable platform
- Jetson: Too heavy with carrier board
- Any >100g solution: Weight penalty too high

---

## 5. Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SHRIKE COMPUTE ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   CARRIER                          │   SCOUT                            │
│   ════════                         │   ═════                            │
│   ModalAI VOXL 2                   │   Raspberry Pi Zero 2W             │
│   • 16g                            │   • 10g                            │
│   • 15 TOPS                        │   • Basic compute                  │
│   • Integrated FC                  │   • Camera streaming               │
│   • 7 cameras                      │   • SDR control                    │
│   • SDR processing                 │   • Mesh relay                     │
│   • Multi-Scout coordination       │                                    │
│   • Geolocation processing         │   Offload heavy processing         │
│                                    │   to Carrier/GCS                   │
│   Price: $1,270                    │   Price: $15                       │
│                                    │                                    │
│   OR Budget:                       │   OR Enhanced:                     │
│   RPi 5 + Hailo-8 + Pixhawk        │   Raspberry Pi 5                   │
│   • ~150g total                    │   • 50g                            │
│   • 26 TOPS                        │   • Better on-board processing     │
│   • Price: ~$380                   │   • Price: $80                     │
│                                    │                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Cost Impact on System

### Option A: VOXL 2 Carrier + Pi Zero Scouts
| Platform | Compute | Cost | Weight |
|----------|---------|------|--------|
| Carrier | VOXL 2 | $1,270 | 16g |
| Scout ×6 | Pi Zero 2W | $90 | 60g total |
| **Total** | | **$1,360** | 76g compute |

### Option B: Budget Carrier + Pi Zero Scouts
| Platform | Compute | Cost | Weight |
|----------|---------|------|--------|
| Carrier | RPi 5 + Hailo-8 + Pixhawk 6C | $380 | ~150g |
| Scout ×6 | Pi Zero 2W | $90 | 60g total |
| **Total** | | **$470** | 210g compute |

### Option C: Mid-Range Everything
| Platform | Compute | Cost | Weight |
|----------|---------|------|--------|
| Carrier | Jetson Orin Nano + Pixhawk 6C | $450 | ~190g |
| Scout ×6 | RPi 5 | $480 | 300g total |
| **Total** | | **$930** | 490g compute |

---

## 7. Sources

- [ModalAI VOXL 2 Product Page](https://www.modalai.com/products/voxl-2)
- [NVIDIA Jetson Orin Module Comparison](https://connecttech.com/orin-module-comparison/)
- [Top 5 Companion Computers for UAVs - ModalAI](https://www.modalai.com/blogs/blog/top-5-companion-computers-for-uavs)
- [Jetson Orin Nano vs Raspberry Pi 5](https://thinkrobotics.com/blogs/learn/nvidia-jetson-orin-nano-vs-raspberry-pi-5-the-ultimate-edge-computing-showdown)
- [Qualcomm Flight RB5 Platform](https://www.qualcomm.com/internet-of-things/products/flight-rb5-platform)
- [Khadas Edge2](https://www.khadas.com/edge2)
- [Raspberry Pi AI Kit (Hailo-8)](https://www.raspberrypi.com/products/ai-kit/)
- [Google Coral Dev Board Datasheet](https://www.coral.ai/docs/dev-board/datasheet/)
- [Holybro Pixhawk RPi CM4 Baseboard](https://holybro.com/products/pixhawk-rpi-cm4-baseboard)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-07 | Initial trade study |
