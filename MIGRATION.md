# Shrike Migration Guide

This document tracks the migration from SwarmDrones to Shrike architecture.

---

## Folder Mapping

| SwarmDrones (Legacy) | Shrike (New) | Status | Notes |
|---------------------|--------------|--------|-------|
| `Bird/` | `Carrier/` | To migrate | Fixed-wing becomes Carrier |
| `Chick/` | `Scout/` | To migrate | Multirotor becomes Scout |
| `Orb/` | `Scout/strike/` | To migrate | Orb code → Scout terminal guidance |
| `gcs/` | `gcs/` | Keep, extend | Add EW panel, TDOA, strike auth |
| `docs/` | `docs/` | Keep, extend | EW concepts added |
| `Sandbox/` | `Sandbox/` | Keep | EW panel prototype lives here |
| `tools/` | `tools/` | Keep | Utility scripts |

---

## New Folder Structure

```
Shrike/
├── Carrier/                  # NEW - Fixed-wing carrier
│   ├── airframe/            # CAD, build (from Bird/)
│   ├── avionics/            # Autopilot (from Bird/)
│   ├── deploy_mechanism/    # NEW - Scout deployment
│   └── ew_payload/          # NEW - Carrier EW suite
│
├── Scout/                    # NEW - Deployable multirotor
│   ├── airframe/            # Folding frame (new design)
│   ├── avionics/            # FC, compute (from Chick/)
│   ├── ew_payload/          # SDR, antennas (new)
│   ├── camera/              # Recon payload (from Chick/)
│   └── strike/              # Terminal guidance (from Orb/)
│
├── Bird/                     # LEGACY - to be migrated to Carrier/
├── Chick/                    # LEGACY - to be migrated to Scout/
├── Orb/                      # LEGACY - to be migrated to Scout/strike/
```

---

## Migration Tasks

### Phase 1: Documentation (Current)
- [x] Create Shrike README
- [x] Copy EW concept documents
- [x] Create new folder structure
- [ ] Update SwarmDrones_Design_Document → Shrike_Design_Document
- [ ] Create Carrier design document
- [ ] Create Scout design document

### Phase 2: Carrier Development
- [ ] Migrate Bird/ airframe docs to Carrier/airframe/
- [ ] Migrate Bird/ avionics config to Carrier/avionics/
- [ ] Design deploy mechanism (new)
- [ ] Integrate Carrier EW payload (B205mini)
- [ ] Update Carrier to carry Scouts internally

### Phase 3: Scout Development
- [ ] Design folding 5" airframe (new)
- [ ] Migrate Chick/ avionics concepts to Scout/avionics/
- [ ] Integrate Scout EW payload (PlutoSDR or B205mini)
- [ ] Migrate Orb/ guidance code to Scout/strike/
- [ ] Adapt Orb guidance for multirotor terminal dive

### Phase 4: GCS Updates
- [ ] Add EW display panel (from Sandbox/)
- [ ] Implement TDOA processing
- [ ] Add strike authorization workflow
- [ ] Update vehicle models for Carrier/Scout
- [ ] Add deploy command interface

### Phase 5: Integration
- [ ] Carrier ↔ Scout communication protocol
- [ ] Deploy mechanism testing
- [ ] Multi-Scout coordination
- [ ] Full system integration test

---

## What Can Be Deleted (After Migration)

Once migration is complete:
- `Bird/` → content moved to `Carrier/`
- `Chick/` → content moved to `Scout/`
- `Orb/` → content moved to `Scout/strike/`
- `SwarmDrones_Design_Document.md` → superseded by Shrike docs
- Old EW brainstorm files → consolidated in `docs/EW_Concepts/`

**Do not delete until migration verified.**

---

## Key Concept Changes

| SwarmDrones Concept | Shrike Concept | Change |
|--------------------|----------------|--------|
| Bird carries Chicks | Carrier deploys Scouts | Internal bay, drop deploy |
| Chick = recon only | Scout = EW + recon + strike | Multi-role |
| Orb = dedicated munition | Scout (strike mode) | Same platform, mode switch |
| EW = future capability | EW = core capability | S/C band integrated |
| GCS = vehicle control | GCS = vehicle + EW + strike | Extended UI |

---

## Reference Documents

- [Concept 3: Carrier-Deployed Strike/EW](docs/EW_Concepts/Concept_3_Carrier_Strike_EW.md) — Primary architecture reference
- [EW System Brainstorm](docs/EW_Concepts/EW_Node_Brainstorm.md) — EW capability background
- [Original Design Document](SwarmDrones_Design_Document.md) — Legacy reference

---

## Notes

The legacy folders (`Bird/`, `Chick/`, `Orb/`) are retained during migration. Code and documentation should be gradually moved to the new structure while ensuring nothing breaks.

The `Orb/code/` directory contains working Arduino guidance code that should be adapted for Scout strike mode rather than rewritten from scratch.
