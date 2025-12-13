"""Entry point for the e-reader application.

This module provides the main entry point for running the e-reader GUI application.
It initializes the PyQt6 QApplication and shows the main window.

Usage:
    python -m ereader
    uv run python -m ereader

Environment Variables:
    EREADER_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR).
                       Default: INFO
"""

import logging
import os
import sys

from PyQt6.QtWidgets import QApplication

from ereader.views.main_window import MainWindow

# Configure logging
log_level = os.getenv("EREADER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
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

    # Initialize library database (Phase 1 library)
    try:
        from ereader.controllers.library_controller import LibraryController
        from ereader.models.library_database import LibraryRepository
        from ereader.utils.database_utils import get_library_db_path

        db_path = get_library_db_path()
        logger.info("Library database path: %s", db_path)

        repository = LibraryRepository(db_path)
        library_controller = LibraryController(repository)

        logger.info("Library system initialized successfully")
    except Exception as e:
        # If library init fails, log error but continue without library
        logger.error("Failed to initialize library system: %s", e)
        logger.warning("Continuing without library support")
        repository = None
        library_controller = None

    # Create and show main window with library support
    window = MainWindow(repository=repository, library_controller=library_controller)
    window.show()

    logger.info("Application started successfully")

    # Run event loop
    exit_code = app.exec()

    # Clean up library resources
    if repository is not None:
        try:
            repository.close()
            logger.info("Library database closed")
        except Exception as e:
            logger.error("Error closing library database: %s", e)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
