"""Entry point for the e-reader application.

This module provides the main entry point for running the e-reader GUI application.
It initializes the PyQt6 QApplication and shows the main window.

Usage:
    python -m ereader
    uv run python -m ereader
"""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from ereader.views.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Initialize and run the e-reader application.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    logger.info("Starting e-reader application")

    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setApplicationName("E-Reader")
    app.setOrganizationName("E-Reader")

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("Application started successfully")

    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
