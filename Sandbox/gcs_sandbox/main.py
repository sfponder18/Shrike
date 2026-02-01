#!/usr/bin/env python3
"""
SwarmDrones Sandbox GCS - Experimental EW Panel
Main entry point

Usage:
    python -m sandbox.gcs_sandbox.main
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from Sandbox.gcs_sandbox.app import GCSSandboxWindow


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
    window = GCSSandboxWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
