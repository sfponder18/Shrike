# Dark Mode Styles for SwarmDrones GCS

DARK_STYLE = """
QMainWindow {
    background-color: #1a1a2e;
}

QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #3a3a5a;
    background-color: #1a1a2e;
}

QTabBar::tab {
    background-color: #2a2a4a;
    color: #a0a0a0;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #3a3a6a;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #4a4a7a;
}

QPushButton {
    background-color: #2a2a4a;
    color: #e0e0e0;
    border: 1px solid #4a4a6a;
    padding: 6px 12px;
    border-radius: 4px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: #3a3a6a;
    border-color: #6a6a8a;
}

QPushButton:pressed {
    background-color: #4a4a7a;
}

QPushButton:checked {
    background-color: #4a6a9a;
    border-color: #6a8aba;
}

QPushButton#mode_button {
    min-width: 50px;
    padding: 4px 8px;
}

QPushButton#mode_button:checked {
    background-color: #2a6a4a;
    border-color: #4a8a6a;
}

QPushButton#arm_button {
    background-color: #4a2a2a;
    border-color: #6a4a4a;
}

QPushButton#arm_button:checked {
    background-color: #8a2a2a;
    border-color: #aa4a4a;
}

QPushButton#release_button {
    background-color: #6a2a2a;
    border-color: #8a4a4a;
}

QPushButton#release_button:hover {
    background-color: #8a3a3a;
}

QPushButton#preflight_button {
    background-color: #2a4a6a;
    border-color: #4a6a8a;
    font-weight: bold;
}

QLabel {
    color: #e0e0e0;
}

QLabel#header {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    padding: 4px;
}

QLabel#status_ok {
    color: #4ade80;
}

QLabel#status_warn {
    color: #facc15;
}

QLabel#status_error {
    color: #f87171;
}

QFrame#panel {
    background-color: #1e1e3a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
}

QFrame#vehicle_card {
    background-color: #2a2a4a;
    border: 2px solid #3a3a5a;
    border-radius: 6px;
    padding: 8px;
}

QFrame#vehicle_card_selected {
    background-color: #2a3a5a;
    border: 2px solid #4a8aba;
    border-radius: 6px;
    padding: 8px;
}

QTableWidget {
    background-color: #1e1e3a;
    alternate-background-color: #2a2a4a;
    gridline-color: #3a3a5a;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #3a4a6a;
}

QHeaderView::section {
    background-color: #2a2a4a;
    color: #a0a0a0;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #3a3a5a;
}

QComboBox {
    background-color: #2a2a4a;
    border: 1px solid #4a4a6a;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2a2a4a;
    border: 1px solid #4a4a6a;
    selection-background-color: #3a4a6a;
}

QProgressBar {
    background-color: #2a2a4a;
    border: 1px solid #3a3a5a;
    border-radius: 3px;
    text-align: center;
    height: 16px;
}

QProgressBar::chunk {
    background-color: #4ade80;
    border-radius: 2px;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a6a;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #1e1e3a;
    border-top: 1px solid #3a3a5a;
}

QMessageBox {
    background-color: #1a1a2e;
}

QMessageBox QPushButton {
    min-width: 80px;
}

QDialog {
    background-color: #1a1a2e;
}

QLineEdit {
    background-color: #2a2a4a;
    border: 1px solid #4a4a6a;
    border-radius: 4px;
    padding: 6px;
    color: #e0e0e0;
}

QLineEdit:focus {
    border-color: #6a8aba;
}
"""
