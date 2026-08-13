"""
Entry point application for AREPO (Enigmistica Suite).
Initializes PySide6 application loop and MainWindow.
"""

import sys
import os

# Ensure project root directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AREPO - Enigmistica Suite")
    app.setOrganizationName("BibiezDelBubez")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
