# Sandbox GCS Styles
# Imports base styles and adds EW-specific styles

from gcs.styles import DARK_STYLE

# EW Panel specific styles
EW_STYLES = """
/* EW Panel Specific Styles */

QFrame#ew_panel {
    background-color: #1e1e3a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
}

QFrame#spectrum_display {
    background-color: #0a0a1a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
}

QFrame#waterfall_display {
    background-color: #0a0a1a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
}

QFrame#ep_status_panel {
    background-color: #1e1e3a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
    padding: 8px;
}

QFrame#df_geometry_panel {
    background-color: #1e1e3a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
}

QFrame#emitter_detail_panel {
    background-color: #1e1e3a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
    padding: 8px;
}

/* Criticality bar colors */
QProgressBar#crit_low {
    background-color: #2a2a4a;
}
QProgressBar#crit_low::chunk {
    background-color: #4a6a4a;
}

QProgressBar#crit_medium {
    background-color: #2a2a4a;
}
QProgressBar#crit_medium::chunk {
    background-color: #6a6a4a;
}

QProgressBar#crit_high {
    background-color: #2a2a4a;
}
QProgressBar#crit_high::chunk {
    background-color: #8a6a4a;
}

QProgressBar#crit_critical {
    background-color: #2a2a4a;
}
QProgressBar#crit_critical::chunk {
    background-color: #8a4a4a;
}

/* EP Status indicators */
QLabel#threat_low {
    color: #4ade80;
    font-weight: bold;
}

QLabel#threat_medium {
    color: #facc15;
    font-weight: bold;
}

QLabel#threat_high {
    color: #fb923c;
    font-weight: bold;
}

QLabel#threat_critical {
    color: #f87171;
    font-weight: bold;
}

/* Emitter type colors */
QLabel#emitter_tactical {
    color: #fb923c;
}

QLabel#emitter_benign {
    color: #6b7280;
}

QLabel#emitter_suspicious {
    color: #facc15;
}

QLabel#emitter_friendly {
    color: #4ade80;
}

/* Action buttons */
QPushButton#ew_target_btn {
    background-color: #4a2a6a;
    border-color: #6a4a8a;
}

QPushButton#ew_target_btn:hover {
    background-color: #5a3a7a;
}

QPushButton#ew_investigate_btn {
    background-color: #2a4a6a;
    border-color: #4a6a8a;
}

QPushButton#ew_investigate_btn:hover {
    background-color: #3a5a7a;
}

QPushButton#ew_ignore_btn {
    background-color: #3a3a4a;
    border-color: #5a5a6a;
}

/* Hop status */
QLabel#hop_ready {
    color: #4ade80;
}

QLabel#hop_pending {
    color: #facc15;
}

QLabel#hop_active {
    color: #fb923c;
}
"""

# Combined styles
SANDBOX_STYLE = DARK_STYLE + EW_STYLES
