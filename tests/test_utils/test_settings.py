"""Tests for ReaderSettings class."""

import pytest
from PyQt6.QtCore import QSettings

from ereader.models.reading_position import NavigationMode, ReadingPosition
from ereader.utils.settings import ReaderSettings


@pytest.fixture
def settings(qtbot):
    """Create a ReaderSettings instance with a unique QSettings organization.

    This ensures each test has isolated settings that don't interfere
    with other tests or the actual application.
    """
    # Use a test-specific organization name to isolate settings
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    original_org = QSettings().organizationName()

    # Create settings with test organization
    settings_instance = ReaderSettings()
    settings_instance._settings = QSettings("EReaderTest", "EReaderTest")

    # Clear any existing test data
    settings_instance.clear_all_settings()

    yield settings_instance

    # Cleanup
    settings_instance.clear_all_settings()


class TestReaderSettings:
    """Tests for ReaderSettings persistence."""

    def test_initialization(self):
        """Test that ReaderSettings initializes correctly."""
        settings = ReaderSettings()
        assert settings._settings is not None
        assert isinstance(settings._settings, QSettings)

    def test_save_and_load_reading_position(self, settings):
        """Test saving and loading a reading position."""
        book_path = "/path/to/test_book.epub"
        position = ReadingPosition(
            chapter_index=5,
            page_number=12,
            scroll_offset=450,
            mode=NavigationMode.PAGE,
        )

        # Save position
        settings.save_reading_position(book_path, position)

        # Load position
        loaded_position = settings.load_reading_position(book_path)

        # Verify
        assert loaded_position is not None
        assert loaded_position.chapter_index == 5
        assert loaded_position.page_number == 12
        assert loaded_position.scroll_offset == 450
        assert loaded_position.mode == NavigationMode.PAGE

    def test_load_nonexistent_position(self, settings):
        """Test loading position for a book with no saved position."""
        book_path = "/path/to/nonexistent_book.epub"

        loaded_position = settings.load_reading_position(book_path)

        assert loaded_position is None

    def test_save_multiple_books(self, settings):
        """Test saving positions for multiple books independently."""
        book1_path = "/path/to/book1.epub"
        book2_path = "/path/to/book2.epub"

        position1 = ReadingPosition(
            chapter_index=1,
            page_number=5,
            scroll_offset=100,
            mode=NavigationMode.SCROLL,
        )
        position2 = ReadingPosition(
            chapter_index=3,
            page_number=8,
            scroll_offset=200,
            mode=NavigationMode.PAGE,
        )

        # Save both positions
        settings.save_reading_position(book1_path, position1)
        settings.save_reading_position(book2_path, position2)

        # Load and verify both
        loaded1 = settings.load_reading_position(book1_path)
        loaded2 = settings.load_reading_position(book2_path)

        assert loaded1 is not None
        assert loaded1.chapter_index == 1
        assert loaded1.mode == NavigationMode.SCROLL

        assert loaded2 is not None
        assert loaded2.chapter_index == 3
        assert loaded2.mode == NavigationMode.PAGE

    def test_overwrite_existing_position(self, settings):
        """Test that saving a new position overwrites the old one."""
        book_path = "/path/to/book.epub"

        # Save initial position
        position1 = ReadingPosition(
            chapter_index=1, page_number=2, scroll_offset=100, mode=NavigationMode.SCROLL
        )
        settings.save_reading_position(book_path, position1)

        # Save new position for same book
        position2 = ReadingPosition(
            chapter_index=5, page_number=10, scroll_offset=500, mode=NavigationMode.PAGE
        )
        settings.save_reading_position(book_path, position2)

        # Load and verify it's the new position
        loaded = settings.load_reading_position(book_path)
        assert loaded is not None
        assert loaded.chapter_index == 5
        assert loaded.page_number == 10
        assert loaded.mode == NavigationMode.PAGE

    def test_save_scroll_mode_position(self, settings):
        """Test saving a position in scroll mode."""
        book_path = "/path/to/book.epub"
        position = ReadingPosition(
            chapter_index=2,
            page_number=0,  # Not used in scroll mode
            scroll_offset=1234,
            mode=NavigationMode.SCROLL,
        )

        settings.save_reading_position(book_path, position)
        loaded = settings.load_reading_position(book_path)

        assert loaded is not None
        assert loaded.mode == NavigationMode.SCROLL
        assert loaded.scroll_offset == 1234

    def test_save_page_mode_position(self, settings):
        """Test saving a position in page mode."""
        book_path = "/path/to/book.epub"
        position = ReadingPosition(
            chapter_index=3,
            page_number=15,
            scroll_offset=800,  # Still tracked for precision
            mode=NavigationMode.PAGE,
        )

        settings.save_reading_position(book_path, position)
        loaded = settings.load_reading_position(book_path)

        assert loaded is not None
        assert loaded.mode == NavigationMode.PAGE
        assert loaded.page_number == 15
        assert loaded.scroll_offset == 800

    def test_get_default_navigation_mode_not_set(self, settings):
        """Test getting default navigation mode when not set."""
        mode = settings.get_default_navigation_mode()
        assert mode == NavigationMode.SCROLL

    def test_set_and_get_default_navigation_mode_scroll(self, settings):
        """Test setting and getting SCROLL as default mode."""
        settings.set_default_navigation_mode(NavigationMode.SCROLL)
        mode = settings.get_default_navigation_mode()
        assert mode == NavigationMode.SCROLL

    def test_set_and_get_default_navigation_mode_page(self, settings):
        """Test setting and getting PAGE as default mode."""
        settings.set_default_navigation_mode(NavigationMode.PAGE)
        mode = settings.get_default_navigation_mode()
        assert mode == NavigationMode.PAGE

    def test_change_default_navigation_mode(self, settings):
        """Test changing the default navigation mode."""
        # Set to PAGE
        settings.set_default_navigation_mode(NavigationMode.PAGE)
        assert settings.get_default_navigation_mode() == NavigationMode.PAGE

        # Change to SCROLL
        settings.set_default_navigation_mode(NavigationMode.SCROLL)
        assert settings.get_default_navigation_mode() == NavigationMode.SCROLL

    def test_clear_all_settings(self, settings):
        """Test clearing all settings."""
        book_path = "/path/to/book.epub"
        position = ReadingPosition(
            chapter_index=1, page_number=2, scroll_offset=100, mode=NavigationMode.SCROLL
        )

        # Save some data
        settings.save_reading_position(book_path, position)
        settings.set_default_navigation_mode(NavigationMode.PAGE)

        # Verify data exists
        assert settings.load_reading_position(book_path) is not None
        assert settings.get_default_navigation_mode() == NavigationMode.PAGE

        # Clear all
        settings.clear_all_settings()

        # Verify data is gone
        assert settings.load_reading_position(book_path) is None
        # Default mode should reset to SCROLL
        assert settings.get_default_navigation_mode() == NavigationMode.SCROLL

    def test_position_with_zero_values(self, settings):
        """Test saving position with zero values (e.g., first page)."""
        book_path = "/path/to/book.epub"
        position = ReadingPosition(
            chapter_index=0,
            page_number=0,
            scroll_offset=0,
            mode=NavigationMode.PAGE,
        )

        settings.save_reading_position(book_path, position)
        loaded = settings.load_reading_position(book_path)

        assert loaded is not None
        assert loaded.chapter_index == 0
        assert loaded.page_number == 0
        assert loaded.scroll_offset == 0

    def test_book_path_with_special_characters(self, settings):
        """Test saving position for book path with special characters."""
        book_path = "/path/to/My Book (2023) - Author's Name.epub"
        position = ReadingPosition(
            chapter_index=2, page_number=5, scroll_offset=300, mode=NavigationMode.SCROLL
        )

        settings.save_reading_position(book_path, position)
        loaded = settings.load_reading_position(book_path)

        assert loaded is not None
        assert loaded.chapter_index == 2
