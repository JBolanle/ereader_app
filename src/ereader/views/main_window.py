"""Main window for the e-reader application.

This module provides the top-level application window (QMainWindow) that serves
as the container for all UI components.
"""

import logging

from PyQt6.QtWidgets import QMainWindow

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for the e-reader.

    This is the top-level window that contains the menu bar, status bar,
    and all other UI components. It serves as the primary user interface
    for the application.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        logger.debug("Initializing MainWindow")

        # Set window properties
        self.setWindowTitle("E-Reader")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        logger.debug("MainWindow initialized successfully")
