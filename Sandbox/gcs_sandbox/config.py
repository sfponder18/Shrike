# Sandbox GCS Configuration
# Imports base config and adds EW-specific settings

# Import everything from parent config
from gcs.config import *

# =============================================================================
# EW CONFIGURATION
# =============================================================================

# Criticality scoring weights (V1 - from EW_System_V1_Context.md)
EW_CRITICALITY_WEIGHTS = {
    "known_signature": 0.35,      # Matches preloaded threat library
    "band_overlap": 0.20,         # Direct threat to own comms/nav
    "proximity": 0.15,            # Geographically relevant
    "signal_strength": 0.10,      # Stronger = closer/more powerful
    "new_emitter": 0.10,          # Anomaly detection
    "rapid_change": 0.10,         # Adaptive adversary indicator
}

# Criticality thresholds
EW_CRITICALITY_LEVELS = {
    "CRITICAL": 80,    # Auto multi-sensor coordination + EP response
    "HIGH": 60,        # Operator alert, recommend action
    "MEDIUM": 40,      # Track and log
    "LOW": 0,          # Background catalog
}

# Guard bands (guaranteed dwell time)
EW_GUARD_BANDS = [
    {"name": "mLRS", "start_mhz": 863, "end_mhz": 870},
    {"name": "T-Beam", "start_mhz": 863, "end_mhz": 870},
    {"name": "ELRS", "start_mhz": 2400, "end_mhz": 2500},
    {"name": "GPS L1", "start_mhz": 1575.42 - 10, "end_mhz": 1575.42 + 10},
    {"name": "GPS L2", "start_mhz": 1227.60 - 10, "end_mhz": 1227.60 + 10},
]

# Sweep bands (tactical spectrum)
EW_SWEEP_BANDS = [
    {"name": "VHF Low", "start_mhz": 30, "end_mhz": 88},
    {"name": "VHF High", "start_mhz": 136, "end_mhz": 174},
    {"name": "UHF", "start_mhz": 400, "end_mhz": 470},
    {"name": "ISM/Cell", "start_mhz": 860, "end_mhz": 930},
    {"name": "L-Band", "start_mhz": 1200, "end_mhz": 1400},
]

# EP Configuration
EP_PACKET_LOSS_THRESHOLD = 0.50  # 50% packet loss triggers hop
EP_HOP_TABLE_SIZE = 16           # Number of entries in hop table

# Modulation types for classification
EW_MODULATION_TYPES = [
    "AM", "FM", "FSK", "PSK", "QAM", "OFDM", "FHSS", "DSSS", "LoRa", "Unknown"
]

# Emitter types for classification
EW_EMITTER_TYPES = [
    "TACTICAL_RADIO",
    "RADAR",
    "DATA_LINK",
    "JAMMER",
    "BEACON",
    "MESH_NODE",
    "CELLULAR",
    "WIFI",
    "BROADCAST",
    "UNKNOWN_SUSPICIOUS",
    "UNKNOWN_BENIGN",
    "FRIENDLY",
]

# Signal purpose classification
EW_SIGNAL_PURPOSES = [
    "VOICE",
    "DATA_LINK",
    "RADAR",
    "BEACON",
    "JAMMER",
    "NAVIGATION",
    "C2_LINK",
    "ISR",
    "UNKNOWN",
]

# Known threat signatures (simplified for V1)
EW_THREAT_LIBRARY = [
    {
        "id": "THREAT_001",
        "name": "Generic UHF Tactical",
        "freq_range": (400, 470),
        "modulation": ["FM", "FSK"],
        "purpose": "TACTICAL_RADIO",
        "threat_level": "HOSTILE",
    },
    {
        "id": "THREAT_002",
        "name": "Drone Control Link",
        "freq_range": (2400, 2483),
        "modulation": ["FHSS", "OFDM"],
        "purpose": "DATA_LINK",
        "threat_level": "HOSTILE",
    },
    {
        "id": "THREAT_003",
        "name": "VHF Military Radio",
        "freq_range": (30, 88),
        "modulation": ["FM", "AM"],
        "purpose": "VOICE",
        "threat_level": "HOSTILE",
    },
]

# Known benign signatures
EW_BENIGN_LIBRARY = [
    {
        "id": "BENIGN_001",
        "name": "FM Broadcast",
        "freq_range": (88, 108),
        "modulation": ["FM"],
        "purpose": "BROADCAST",
    },
    {
        "id": "BENIGN_002",
        "name": "WiFi 2.4GHz",
        "freq_range": (2400, 2483),
        "modulation": ["OFDM"],
        "purpose": "DATA_LINK",
    },
    {
        "id": "BENIGN_003",
        "name": "Marine VHF",
        "freq_range": (156, 163),
        "modulation": ["FM"],
        "purpose": "VOICE",
    },
]
