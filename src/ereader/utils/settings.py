"""Reading settings persistence using QSettings.

This module provides the ReaderSettings class for saving and loading
reading positions, navigation mode preferences, and other user settings.
"""

import logging

from PyQt6.QtCore import QSettings

from ereader.models.reading_position import NavigationMode, ReadingPosition

logger = logging.getLogger(__name__)


class ReaderSettings:
    """Manages persistent reader settings using QSettings.

    This class handles saving and loading reading positions for books,
    default navigation mode preferences, and other user settings.
    Uses QSettings for cross-platform persistence.
    """

    def __init__(self) -> None:
        """Initialize ReaderSettings with QSettings instance."""
        self._settings = QSettings("EReader", "EReader")
        logger.debug("Initialized ReaderSettings")

    def save_reading_position(
        self, book_path: str, position: ReadingPosition
    ) -> None:
        """Save reading position for a specific book.

        Args:
            book_path: Absolute path to the book file.
            position: ReadingPosition to save.
        """
        # Use book path as unique key
        key_prefix = f"books/{book_path}"

        self._settings.setValue(f"{key_prefix}/chapter_index", position.chapter_index)
        self._settings.setValue(f"{key_prefix}/page_number", position.page_number)
        self._settings.setValue(f"{key_prefix}/scroll_offset", position.scroll_offset)
        self._settings.setValue(f"{key_prefix}/mode", position.mode.value)

        # Sync to disk immediately
        self._settings.sync()

        logger.debug(
            f"Saved reading position for {book_path}: {position}"
        )

    def load_reading_position(self, book_path: str) -> ReadingPosition | None:
        """Load reading position for a specific book.

        Args:
            book_path: Absolute path to the book file.

        Returns:
            ReadingPosition if found, None if no saved position exists.
        """
        key_prefix = f"books/{book_path}"

        # Check if position exists
        if not self._settings.contains(f"{key_prefix}/chapter_index"):
            logger.debug(f"No saved position found for {book_path}")
            return None

        # Load position data
        chapter_index = self._settings.value(f"{key_prefix}/chapter_index", type=int)
        page_number = self._settings.value(f"{key_prefix}/page_number", type=int)
        scroll_offset = self._settings.value(f"{key_prefix}/scroll_offset", type=int)
        mode_value = self._settings.value(f"{key_prefix}/mode", type=str)

        # Convert mode string back to enum
        mode = NavigationMode(mode_value)

        position = ReadingPosition(
            chapter_index=chapter_index,
            page_number=page_number,
            scroll_offset=scroll_offset,
            mode=mode,
        )

        logger.debug(f"Loaded reading position for {book_path}: {position}")
        return position

    def get_default_navigation_mode(self) -> NavigationMode:
        """Get the default navigation mode preference.

        Returns:
            NavigationMode (defaults to SCROLL if not set).
        """
        mode_value = self._settings.value(
            "preferences/default_navigation_mode", NavigationMode.SCROLL.value, type=str
        )
        mode = NavigationMode(mode_value)
        logger.debug(f"Default navigation mode: {mode.value}")
        return mode

    def set_default_navigation_mode(self, mode: NavigationMode) -> None:
        """Set the default navigation mode preference.

        Args:
            mode: NavigationMode to set as default.
        """
        self._settings.setValue("preferences/default_navigation_mode", mode.value)
        self._settings.sync()
        logger.debug(f"Set default navigation mode to: {mode.value}")

    def clear_all_settings(self) -> None:
        """Clear all saved settings (for testing purposes).

        This removes all saved reading positions and preferences.
        """
        self._settings.clear()
        self._settings.sync()
        logger.debug("Cleared all settings")
