"""Database utility functions for library management.

This module provides helper functions for database path resolution and
initialization, following platform-specific conventions for user data storage.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_library_db_path() -> Path:
    """Get platform-appropriate path for library database.

    Returns the standard user data directory location for each platform:
    - macOS: ~/Library/Application Support/EReader/library.db
    - Windows: %APPDATA%/EReader/library.db
    - Linux: ~/.local/share/ereader/library.db

    The directory is created if it doesn't exist.

    Returns:
        Absolute path to the library database file.

    Raises:
        OSError: If the directory cannot be created.
    """
    logger.debug("Determining library database path for platform: %s", sys.platform)

    if sys.platform == "darwin":  # macOS
        data_dir = Path.home() / "Library" / "Application Support" / "EReader"
    elif sys.platform == "win32":  # Windows
        import os

        appdata = os.getenv("APPDATA")
        if appdata:
            data_dir = Path(appdata) / "EReader"
        else:
            # Fallback if APPDATA not set (rare)
            data_dir = Path.home() / "EReader"
    else:  # Linux and other Unix-like systems
        data_dir = Path.home() / ".local" / "share" / "ereader"

    logger.debug("Library data directory: %s", data_dir)

    # Create directory if it doesn't exist
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured data directory exists: %s", data_dir)
    except OSError as e:
        logger.error("Failed to create data directory %s: %s", data_dir, e)
        raise

    db_path = data_dir / "library.db"
    logger.debug("Library database path: %s", db_path)

    return db_path
