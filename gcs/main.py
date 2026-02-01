#!/usr/bin/env python3
"""
SwarmDrones Ground Control Station
Main entry point

Usage:
    python -m gcs.main
    or
    python gcs/main.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gcs.app import GCSMainWindow


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Set application font
    font = QFont("Consolas", 10)
    app.setFont(font)

    # Create and show main window
    window = GCSMainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
