"""Tests for ReaderController.

This module tests the ReaderController class, which coordinates between
the EPUBBook model and UI views. Tests use mocks to isolate the controller
logic from the actual book parsing and UI components.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from PyQt6.QtCore import QObject

from ereader.controllers.reader_controller import ReaderController
from ereader.exceptions import InvalidEPUBError, CorruptedEPUBError


class TestReaderControllerInit:
    """Test ReaderController initialization."""

    def test_init_creates_controller(self):
        """Test that controller initializes successfully."""
        controller = ReaderController()

        assert controller is not None
        assert isinstance(controller, QObject)
        assert controller._book is None
        assert controller._current_chapter_index == 0

    def test_init_has_required_signals(self):
        """Test that controller defines all required signals."""
        controller = ReaderController()

        # Verify signals exist
        assert hasattr(controller, 'book_loaded')
        assert hasattr(controller, 'chapter_changed')
        assert hasattr(controller, 'navigation_state_changed')
        assert hasattr(controller, 'content_ready')
        assert hasattr(controller, 'error_occurred')


class TestReaderControllerOpenBook:
    """Test opening books with ReaderController."""

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_success(self, mock_epub_class):
        """Test successfully opening a valid EPUB book."""
        # Setup mock book
        mock_book = MagicMock()
        mock_book.title = "Test Book"
        mock_book.authors = ["Test Author"]
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_content.return_value = "<p>Chapter 1 content</p>"
        mock_epub_class.return_value = mock_book

        # Setup controller with signal spies
        controller = ReaderController()
        book_loaded_spy = Mock()
        content_ready_spy = Mock()
        chapter_changed_spy = Mock()
        navigation_state_spy = Mock()

        controller.book_loaded.connect(book_loaded_spy)
        controller.content_ready.connect(content_ready_spy)
        controller.chapter_changed.connect(chapter_changed_spy)
        controller.navigation_state_changed.connect(navigation_state_spy)

        # Open book
        controller.open_book("/path/to/book.epub")

        # Verify EPUBBook was created with correct path
        mock_epub_class.assert_called_once_with("/path/to/book.epub")

        # Verify controller state
        assert controller._book == mock_book
        assert controller._current_chapter_index == 0

        # Verify signals were emitted
        book_loaded_spy.assert_called_once_with("Test Book", "Test Author")
        content_ready_spy.assert_called_once_with("<p>Chapter 1 content</p>")
        chapter_changed_spy.assert_called_once_with(1, 5)  # 1-based for display
        navigation_state_spy.assert_called_once_with(False, True)  # can't go back, can go forward

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_with_multiple_authors(self, mock_epub_class):
        """Test opening a book with multiple authors."""
        mock_book = MagicMock()
        mock_book.title = "Test Book"
        mock_book.authors = ["Author One", "Author Two", "Author Three"]
        mock_book.get_chapter_count.return_value = 1
        mock_book.get_chapter_content.return_value = "<p>Content</p>"
        mock_epub_class.return_value = mock_book

        controller = ReaderController()
        book_loaded_spy = Mock()
        controller.book_loaded.connect(book_loaded_spy)

        controller.open_book("/path/to/book.epub")

        # Verify authors are joined with commas
        book_loaded_spy.assert_called_once_with("Test Book", "Author One, Author Two, Author Three")

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_with_no_authors(self, mock_epub_class):
        """Test opening a book with empty authors list."""
        mock_book = MagicMock()
        mock_book.title = "Test Book"
        mock_book.authors = []
        mock_book.get_chapter_count.return_value = 1
        mock_book.get_chapter_content.return_value = "<p>Content</p>"
        mock_epub_class.return_value = mock_book

        controller = ReaderController()
        book_loaded_spy = Mock()
        controller.book_loaded.connect(book_loaded_spy)

        controller.open_book("/path/to/book.epub")

        # Verify default author is used
        book_loaded_spy.assert_called_once_with("Test Book", "Unknown Author")

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_file_not_found(self, mock_epub_class):
        """Test opening a non-existent file."""
        mock_epub_class.side_effect = FileNotFoundError("File not found")

        controller = ReaderController()
        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller.open_book("/nonexistent/book.epub")

        # Verify error signal was emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "File Not Found"
        assert "/nonexistent/book.epub" in args[1]

        # Verify no book was loaded
        assert controller._book is None

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_invalid_epub(self, mock_epub_class):
        """Test opening an invalid EPUB file."""
        mock_epub_class.side_effect = InvalidEPUBError("Not a valid EPUB")

        controller = ReaderController()
        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller.open_book("/path/to/invalid.epub")

        # Verify error signal was emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Invalid EPUB"
        assert "Not a valid EPUB" in args[1]

        # Verify no book was loaded
        assert controller._book is None

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_corrupted_epub(self, mock_epub_class):
        """Test opening a corrupted EPUB file."""
        mock_epub_class.side_effect = CorruptedEPUBError("EPUB is corrupted")

        controller = ReaderController()
        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller.open_book("/path/to/corrupted.epub")

        # Verify error signal was emitted with appropriate message
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Invalid EPUB"

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_unexpected_error(self, mock_epub_class):
        """Test handling of unexpected errors during book opening."""
        mock_epub_class.side_effect = RuntimeError("Unexpected error")

        controller = ReaderController()
        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller.open_book("/path/to/book.epub")

        # Verify error signal was emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Error"
        assert "Unexpected error" in args[1]


class TestReaderControllerNavigation:
    """Test chapter navigation functionality."""

    def _setup_controller_with_book(self, chapter_count: int = 5):
        """Helper to create controller with a mock book loaded."""
        mock_book = MagicMock()
        mock_book.title = "Test Book"
        mock_book.authors = ["Test Author"]
        mock_book.get_chapter_count.return_value = chapter_count
        mock_book.get_chapter_content.side_effect = lambda idx: f"<p>Chapter {idx + 1}</p>"

        controller = ReaderController()
        controller._book = mock_book
        controller._current_chapter_index = 0

        return controller, mock_book

    def test_next_chapter_moves_forward(self):
        """Test navigating to the next chapter."""
        controller, mock_book = self._setup_controller_with_book(5)

        content_spy = Mock()
        chapter_changed_spy = Mock()
        nav_state_spy = Mock()

        controller.content_ready.connect(content_spy)
        controller.chapter_changed.connect(chapter_changed_spy)
        controller.navigation_state_changed.connect(nav_state_spy)

        # Navigate to next chapter
        controller.next_chapter()

        # Verify state updated
        assert controller._current_chapter_index == 1

        # Verify signals emitted
        content_spy.assert_called_once_with("<p>Chapter 2</p>")
        chapter_changed_spy.assert_called_once_with(2, 5)  # 1-based
        nav_state_spy.assert_called_once_with(True, True)  # can go both ways

    def test_next_chapter_at_last_chapter_does_nothing(self):
        """Test that next_chapter does nothing when at last chapter."""
        controller, _ = self._setup_controller_with_book(3)
        controller._current_chapter_index = 2  # Last chapter (0-indexed)

        content_spy = Mock()
        controller.content_ready.connect(content_spy)

        # Try to go to next (should do nothing)
        controller.next_chapter()

        # Verify no change
        assert controller._current_chapter_index == 2
        content_spy.assert_not_called()

    def test_next_chapter_with_no_book_loaded(self):
        """Test next_chapter with no book loaded."""
        controller = ReaderController()
        content_spy = Mock()
        controller.content_ready.connect(content_spy)

        # Should not crash, just do nothing
        controller.next_chapter()

        content_spy.assert_not_called()

    def test_previous_chapter_moves_backward(self):
        """Test navigating to the previous chapter."""
        controller, mock_book = self._setup_controller_with_book(5)
        controller._current_chapter_index = 2  # Start at chapter 3

        content_spy = Mock()
        chapter_changed_spy = Mock()
        nav_state_spy = Mock()

        controller.content_ready.connect(content_spy)
        controller.chapter_changed.connect(chapter_changed_spy)
        controller.navigation_state_changed.connect(nav_state_spy)

        # Navigate to previous chapter
        controller.previous_chapter()

        # Verify state updated
        assert controller._current_chapter_index == 1

        # Verify signals emitted
        content_spy.assert_called_once_with("<p>Chapter 2</p>")
        chapter_changed_spy.assert_called_once_with(2, 5)  # 1-based
        nav_state_spy.assert_called_once_with(True, True)  # can go both ways

    def test_previous_chapter_at_first_chapter_does_nothing(self):
        """Test that previous_chapter does nothing when at first chapter."""
        controller, _ = self._setup_controller_with_book(3)
        controller._current_chapter_index = 0  # First chapter

        content_spy = Mock()
        controller.content_ready.connect(content_spy)

        # Try to go to previous (should do nothing)
        controller.previous_chapter()

        # Verify no change
        assert controller._current_chapter_index == 0
        content_spy.assert_not_called()

    def test_previous_chapter_with_no_book_loaded(self):
        """Test previous_chapter with no book loaded."""
        controller = ReaderController()
        content_spy = Mock()
        controller.content_ready.connect(content_spy)

        # Should not crash, just do nothing
        controller.previous_chapter()

        content_spy.assert_not_called()

    def test_navigation_through_entire_book(self):
        """Test navigating forward through all chapters."""
        controller, _ = self._setup_controller_with_book(3)

        # Navigate through all chapters
        for expected_index in range(1, 3):
            controller.next_chapter()
            assert controller._current_chapter_index == expected_index

        # Try to go past last chapter
        controller.next_chapter()
        assert controller._current_chapter_index == 2  # Still at last

    def test_navigation_backward_through_entire_book(self):
        """Test navigating backward through all chapters."""
        controller, _ = self._setup_controller_with_book(3)
        controller._current_chapter_index = 2  # Start at last

        # Navigate backward through all chapters
        for expected_index in [1, 0]:
            controller.previous_chapter()
            assert controller._current_chapter_index == expected_index

        # Try to go before first chapter
        controller.previous_chapter()
        assert controller._current_chapter_index == 0  # Still at first


class TestReaderControllerNavigationState:
    """Test navigation state updates."""

    def _setup_controller_with_book(self, chapter_count: int):
        """Helper to create controller with a mock book loaded."""
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = chapter_count
        mock_book.get_chapter_content.return_value = "<p>Content</p>"

        controller = ReaderController()
        controller._book = mock_book
        controller._current_chapter_index = 0

        return controller, mock_book

    def test_navigation_state_at_first_chapter(self):
        """Test navigation state when at first chapter."""
        controller, _ = self._setup_controller_with_book(5)

        nav_state_spy = Mock()
        controller.navigation_state_changed.connect(nav_state_spy)

        controller._update_navigation_state()

        nav_state_spy.assert_called_once_with(False, True)  # can't go back, can go forward

    def test_navigation_state_at_middle_chapter(self):
        """Test navigation state when at a middle chapter."""
        controller, _ = self._setup_controller_with_book(5)
        controller._current_chapter_index = 2

        nav_state_spy = Mock()
        controller.navigation_state_changed.connect(nav_state_spy)

        controller._update_navigation_state()

        nav_state_spy.assert_called_once_with(True, True)  # can go both ways

    def test_navigation_state_at_last_chapter(self):
        """Test navigation state when at last chapter."""
        controller, _ = self._setup_controller_with_book(5)
        controller._current_chapter_index = 4  # Last chapter

        nav_state_spy = Mock()
        controller.navigation_state_changed.connect(nav_state_spy)

        controller._update_navigation_state()

        nav_state_spy.assert_called_once_with(True, False)  # can go back, can't go forward

    def test_navigation_state_with_single_chapter_book(self):
        """Test navigation state with a single-chapter book."""
        controller, _ = self._setup_controller_with_book(1)

        nav_state_spy = Mock()
        controller.navigation_state_changed.connect(nav_state_spy)

        controller._update_navigation_state()

        nav_state_spy.assert_called_once_with(False, False)  # can't go either way

    def test_navigation_state_with_no_book(self):
        """Test navigation state when no book is loaded."""
        controller = ReaderController()

        nav_state_spy = Mock()
        controller.navigation_state_changed.connect(nav_state_spy)

        controller._update_navigation_state()

        nav_state_spy.assert_called_once_with(False, False)  # can't navigate


class TestReaderControllerChapterLoading:
    """Test chapter loading and error handling."""

    def test_load_chapter_success(self):
        """Test successfully loading a chapter."""
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_content.return_value = "<p>Chapter content</p>"

        controller = ReaderController()
        controller._book = mock_book

        content_spy = Mock()
        chapter_spy = Mock()
        nav_spy = Mock()

        controller.content_ready.connect(content_spy)
        controller.chapter_changed.connect(chapter_spy)
        controller.navigation_state_changed.connect(nav_spy)

        controller._load_chapter(2)

        # Verify content was fetched
        mock_book.get_chapter_content.assert_called_once_with(2)

        # Verify signals emitted
        content_spy.assert_called_once_with("<p>Chapter content</p>")
        chapter_spy.assert_called_once_with(3, 5)  # 1-based display
        nav_spy.assert_called_once()

    def test_load_chapter_invalid_index(self):
        """Test loading a chapter with invalid index."""
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_content.side_effect = IndexError("Index out of range")

        controller = ReaderController()
        controller._book = mock_book

        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller._load_chapter(10)  # Invalid index

        # Verify error signal emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Chapter Not Found"
        assert "11" in args[1]  # 1-based in error message

    def test_load_chapter_corrupted_content(self):
        """Test handling of corrupted chapter content."""
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_content.side_effect = CorruptedEPUBError("Chapter file missing")

        controller = ReaderController()
        controller._book = mock_book

        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller._load_chapter(2)

        # Verify error signal emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Chapter Load Error"

    def test_load_chapter_with_no_book(self):
        """Test _load_chapter when no book is loaded."""
        controller = ReaderController()

        content_spy = Mock()
        controller.content_ready.connect(content_spy)

        # Should not crash, just do nothing
        controller._load_chapter(0)

        content_spy.assert_not_called()

    def test_load_chapter_unexpected_error(self):
        """Test handling of unexpected errors during chapter loading."""
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_content.side_effect = RuntimeError("Unexpected error")

        controller = ReaderController()
        controller._book = mock_book

        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        controller._load_chapter(2)

        # Verify error signal emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Error"
        assert "Unexpected error" in args[1]
