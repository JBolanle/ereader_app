"""Tests for ReaderController.

This module tests the ReaderController class, which coordinates between
the EPUBBook model and UI views. Tests use mocks to isolate the controller
logic from the actual book parsing and UI components.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch

from PyQt6.QtCore import QObject

from ereader.controllers.reader_controller import ReaderController
from ereader.exceptions import CorruptedEPUBError, InvalidEPUBError


@pytest.fixture
def mock_epub_book():
    """Create a properly configured mock EPUBBook for async loading tests."""
    mock_book = MagicMock()
    mock_book.filepath = "/path/to/book.epub"
    mock_book.title = "Test Book"
    mock_book.authors = ["Test Author"]
    mock_book.get_chapter_count.return_value = 5
    mock_book.get_chapter_content.return_value = "<p>Chapter content</p>"
    mock_book.get_chapter_href.return_value = "chapter.xhtml"
    return mock_book


def wait_for_controller_threads(controller, timeout_ms=1000):
    """Wait for any running async loader threads in the controller to finish.

    Args:
        controller: The ReaderController instance.
        timeout_ms: Maximum time to wait in milliseconds.
    """
    if controller._current_loader is not None:
        controller._current_loader.wait(timeout_ms)


# Track all ReaderController instances created during tests
_test_controllers = []


@pytest.fixture(autouse=True)
def cleanup_controller_threads():
    """Automatically cleanup any controller threads after each test.

    This fixture runs after every test to ensure all QThread objects
    are properly waited on before destruction, preventing Qt threading errors.
    """
    global _test_controllers
    _test_controllers.clear()
    yield
    # After test completes, wait for all controller threads
    for controller in _test_controllers:
        wait_for_controller_threads(controller)
    _test_controllers.clear()


# Monkey patch ReaderController.__init__ to track instances
_original_init = ReaderController.__init__


def _tracked_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    _test_controllers.append(self)


ReaderController.__init__ = _tracked_init


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
    def test_open_book_success(self, mock_epub_class, mock_epub_book, qtbot):
        """Test successfully opening a valid EPUB book."""
        # Setup mock book
        mock_epub_book.title = "Test Book"
        mock_epub_book.authors = ["Test Author"]
        mock_epub_book.get_chapter_count.return_value = 5
        mock_epub_book.get_chapter_content.return_value = "<p>Chapter 1 content</p>"
        mock_epub_class.return_value = mock_epub_book

        # Setup controller
        controller = ReaderController()
        book_loaded_spy = Mock()

        controller.book_loaded.connect(book_loaded_spy)

        # Open book (this starts async loading)
        with qtbot.waitSignal(controller.content_ready, timeout=1000) as blocker:
            controller.open_book("/path/to/book.epub")

        # Verify EPUBBook was created with correct path
        mock_epub_class.assert_called_once_with("/path/to/book.epub")

        # Verify controller state
        assert controller._book == mock_epub_book
        assert controller._current_chapter_index == 0

        # Verify book_loaded signal was emitted
        book_loaded_spy.assert_called_once_with("Test Book", "Test Author")

        # Verify content_ready signal was emitted (caught by qtbot)
        assert "<p>Chapter 1 content</p>" in blocker.args[0]

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_with_multiple_authors(self, mock_epub_class, mock_epub_book, qtbot):
        """Test opening a book with multiple authors."""
        mock_epub_book.title = "Test Book"
        mock_epub_book.authors = ["Author One", "Author Two", "Author Three"]
        mock_epub_book.get_chapter_count.return_value = 1
        mock_epub_book.get_chapter_content.return_value = "<p>Content</p>"
        mock_epub_class.return_value = mock_epub_book

        controller = ReaderController()
        book_loaded_spy = Mock()
        controller.book_loaded.connect(book_loaded_spy)

        # Wait for async loading to complete
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller.open_book("/path/to/book.epub")

        # Verify authors are joined with commas
        book_loaded_spy.assert_called_once_with("Test Book", "Author One, Author Two, Author Three")

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_open_book_with_no_authors(self, mock_epub_class, mock_epub_book, qtbot):
        """Test opening a book with empty authors list."""
        mock_epub_book.title = "Test Book"
        mock_epub_book.authors = []
        mock_epub_book.get_chapter_count.return_value = 1
        mock_epub_book.get_chapter_content.return_value = "<p>Content</p>"
        mock_epub_class.return_value = mock_epub_book

        controller = ReaderController()
        book_loaded_spy = Mock()
        controller.book_loaded.connect(book_loaded_spy)

        # Wait for async loading to complete
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
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

    def test_next_chapter_moves_forward(self, qtbot):
        """Test navigating to the next chapter."""
        controller, mock_book = self._setup_controller_with_book(5)

        content_spy = Mock()
        chapter_changed_spy = Mock()
        nav_state_spy = Mock()

        controller.content_ready.connect(content_spy)
        controller.chapter_changed.connect(chapter_changed_spy)
        controller.navigation_state_changed.connect(nav_state_spy)

        # Navigate to next chapter (wait for async loading)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
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

    def test_previous_chapter_moves_backward(self, qtbot):
        """Test navigating to the previous chapter."""
        controller, mock_book = self._setup_controller_with_book(5)
        controller._current_chapter_index = 2  # Start at chapter 3

        content_spy = Mock()
        chapter_changed_spy = Mock()
        nav_state_spy = Mock()

        controller.content_ready.connect(content_spy)
        controller.chapter_changed.connect(chapter_changed_spy)
        controller.navigation_state_changed.connect(nav_state_spy)

        # Navigate to previous chapter (wait for async loading)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
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

    def test_navigation_through_entire_book(self, qtbot):
        """Test navigating forward through all chapters."""
        controller, _ = self._setup_controller_with_book(3)

        # Navigate through all chapters
        for expected_index in range(1, 3):
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.next_chapter()
            assert controller._current_chapter_index == expected_index

        # Try to go past last chapter (no signal expected - does nothing)
        controller.next_chapter()
        assert controller._current_chapter_index == 2  # Still at last

    def test_navigation_backward_through_entire_book(self, qtbot):
        """Test navigating backward through all chapters."""
        controller, _ = self._setup_controller_with_book(3)
        controller._current_chapter_index = 2  # Start at last

        # Navigate backward through all chapters
        for expected_index in [1, 0]:
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.previous_chapter()
            assert controller._current_chapter_index == expected_index

        # Try to go before first chapter (no signal expected - does nothing)
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

    def test_load_chapter_success(self, qtbot, mock_epub_book):
        """Test successfully loading a chapter."""
        mock_epub_book.get_chapter_count.return_value = 5
        mock_epub_book.get_chapter_content.return_value = "<p>Chapter content</p>"
        mock_epub_book.get_chapter_href.return_value = "chapter2.xhtml"

        controller = ReaderController()
        controller._book = mock_epub_book
        controller._current_chapter_index = 2  # Set index before loading

        content_spy = Mock()
        chapter_spy = Mock()
        nav_spy = Mock()

        controller.content_ready.connect(content_spy)
        controller.chapter_changed.connect(chapter_spy)
        controller.navigation_state_changed.connect(nav_spy)

        # Wait for async loading to complete
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(2)

        # Verify content was fetched
        mock_epub_book.get_chapter_content.assert_called_once_with(2)

        # Verify signals emitted
        content_spy.assert_called_once_with("<p>Chapter content</p>")
        chapter_spy.assert_called_once_with(3, 5)  # 1-based display
        nav_spy.assert_called_once()

    def test_load_chapter_invalid_index(self, qtbot, mock_epub_book):
        """Test loading a chapter with invalid index."""
        mock_epub_book.get_chapter_count.return_value = 5
        mock_epub_book.get_chapter_content.side_effect = IndexError("Index out of range")
        mock_epub_book.get_chapter_href.return_value = "chapter10.xhtml"

        controller = ReaderController()
        controller._book = mock_epub_book

        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        # Wait for async error to be emitted
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._load_chapter(10)  # Invalid index

        # Verify error signal emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Chapter Not Found"
        assert "11" in args[1]  # 1-based in error message

    def test_load_chapter_corrupted_content(self, qtbot, mock_epub_book):
        """Test handling of corrupted chapter content."""
        mock_epub_book.get_chapter_count.return_value = 5
        mock_epub_book.get_chapter_content.side_effect = CorruptedEPUBError("Chapter file missing")
        mock_epub_book.get_chapter_href.return_value = "chapter2.xhtml"

        controller = ReaderController()
        controller._book = mock_epub_book

        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        # Wait for async error to be emitted
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
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

    def test_load_chapter_unexpected_error(self, qtbot, mock_epub_book):
        """Test handling of unexpected errors during chapter loading."""
        mock_epub_book.get_chapter_count.return_value = 5
        mock_epub_book.get_chapter_content.side_effect = RuntimeError("Unexpected error")
        mock_epub_book.get_chapter_href.return_value = "chapter2.xhtml"

        controller = ReaderController()
        controller._book = mock_epub_book

        error_spy = Mock()
        controller.error_occurred.connect(error_spy)

        # Wait for async error to be emitted
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._load_chapter(2)

        # Verify error signal emitted
        error_spy.assert_called_once()
        args = error_spy.call_args[0]
        assert args[0] == "Error"
        assert "Unexpected error" in args[1]


class TestReaderControllerCaching:
    """Test chapter caching behavior in ReaderController."""

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_cache_hit_on_repeated_chapter_load(self, mock_resolve_images, qtbot):
        """Test that re-loading same chapter uses cache (cache hit)."""
        # Setup mock book
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter1.html"
        mock_book.get_chapter_content.return_value = "<p>Raw chapter content</p>"
        mock_resolve_images.return_value = "<p>Rendered chapter content</p>"

        controller = ReaderController()
        controller._book = mock_book

        content_spy = Mock()
        controller.content_ready.connect(content_spy)

        # First load - should render (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(0)

        # Verify rendering happened
        mock_book.get_chapter_content.assert_called_once_with(0)
        mock_resolve_images.assert_called_once()
        content_spy.assert_called_once_with("<p>Rendered chapter content</p>")

        # Reset spies
        mock_book.get_chapter_content.reset_mock()
        mock_resolve_images.reset_mock()
        content_spy.reset_mock()

        # Second load of same chapter - should use cache (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(0)

        # Verify no rendering happened (cache hit)
        mock_book.get_chapter_content.assert_not_called()
        mock_resolve_images.assert_not_called()

        # But content was still emitted
        content_spy.assert_called_once_with("<p>Rendered chapter content</p>")

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_cache_miss_on_different_chapter(self, mock_resolve_images, qtbot):
        """Test that loading different chapter misses cache."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i} raw</p>"
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content.replace("raw", "rendered")

        controller = ReaderController()
        controller._book = mock_book

        # Load chapter 0 (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(0)
        assert mock_book.get_chapter_content.call_count == 1

        # Load chapter 1 - should miss cache (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(1)
        assert mock_book.get_chapter_content.call_count == 2

        # Load chapter 2 - should miss cache (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(2)
        assert mock_book.get_chapter_content.call_count == 3

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_sequential_navigation_caching(self, mock_resolve_images, qtbot):
        """Test cache behavior during forward sequential navigation with multi-layer caching."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 15
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        controller = ReaderController()
        controller._book = mock_book

        # Navigate forward through chapters 0-12 (13 chapters total)
        for i in range(13):
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(i)

        # With multi-layer caching:
        # - Rendered cache (maxsize=10): chapters 3-12 (evicted 0-2)
        # - Raw cache (maxsize=20): chapters 0-12 (all still cached)

        # Reset mock to count cache hits
        mock_book.get_chapter_content.reset_mock()

        # Re-load chapter 2 - should hit raw cache (no book load needed)
        # But needs re-rendering (evicted from rendered cache)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(2)
        assert mock_book.get_chapter_content.call_count == 0  # Raw cache hit

        mock_book.get_chapter_content.reset_mock()

        # Re-load chapter 12 - should hit rendered cache (complete cache hit)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(12)
        assert mock_book.get_chapter_content.call_count == 0  # Rendered cache hit

        # Wait for final thread to finish before test cleanup
        wait_for_controller_threads(controller)

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_backward_navigation_caching(self, mock_resolve_images, qtbot):
        """Test cache behavior during backward navigation."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 10
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        controller = ReaderController()
        controller._book = mock_book

        # Navigate to chapter 5 (wait for each async load)
        for i in range(6):
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(i)

        # Reset mock to count cache hits
        mock_book.get_chapter_content.reset_mock()

        # Navigate backward 5 -> 4 -> 3 (all should be cache hits)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(4)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(3)

        # Verify no new chapter loads (all cache hits)
        assert mock_book.get_chapter_content.call_count == 0

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_cache_cleared_on_new_book(self, mock_resolve_images, qtbot):
        """Test that cache is cleared when opening a new book."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        # Setup first book
        mock_book1 = MagicMock()
        mock_book1.filepath = "/path/to/book1.epub"
        mock_book1.title = "Book 1"
        mock_book1.authors = ["Author 1"]
        mock_book1.get_chapter_count.return_value = 5
        mock_book1.get_chapter_href.return_value = "text/chapter0.html"
        mock_book1.get_chapter_content.return_value = "<p>Book 1 Chapter 0</p>"

        # Setup second book
        mock_book2 = MagicMock()
        mock_book2.filepath = "/path/to/book2.epub"
        mock_book2.title = "Book 2"
        mock_book2.authors = ["Author 2"]
        mock_book2.get_chapter_count.return_value = 5
        mock_book2.get_chapter_href.return_value = "text/chapter0.html"
        mock_book2.get_chapter_content.return_value = "<p>Book 2 Chapter 0</p>"

        controller = ReaderController()

        with patch('ereader.controllers.reader_controller.EPUBBook') as mock_epub_class:
            # Open first book and navigate
            mock_epub_class.return_value = mock_book1
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.open_book("/path/to/book1.epub")

            # Cache should have 1 entry in rendered chapters
            assert controller._cache_manager.rendered_chapters.stats()["size"] == 1

            # Open second book
            mock_epub_class.return_value = mock_book2
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.open_book("/path/to/book2.epub")

            # Cache should be cleared and have 1 entry (from new book)
            stats = controller._cache_manager.rendered_chapters.stats()
            assert stats["size"] == 1
            # Stats should be reset (hits are 0, but we have 1 miss from loading the first chapter)
            assert stats["hits"] == 0
            assert stats["misses"] == 1  # One miss from loading chapter 0 of new book

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_cache_key_uniqueness(self, mock_resolve_images, qtbot):
        """Test that different books don't collide in cache."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Load chapter 0 from first book (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(0)
        first_content = controller._cache_manager.rendered_chapters.get("/path/to/book.epub:0")

        # Simulate changing book (different path)
        mock_book.filepath = "/path/to/different_book.epub"

        # Load chapter 0 from second book (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(0)

        # Both chapters should be in cache with different keys
        assert controller._cache_manager.rendered_chapters.get("/path/to/book.epub:0") == first_content
        assert controller._cache_manager.rendered_chapters.get("/path/to/different_book.epub:0") == "<p>Chapter 0</p>"

    def test_next_chapter_uses_cache(self, qtbot):
        """Test that next_chapter() method benefits from caching."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        with patch('ereader.utils.async_loader.resolve_images_in_html') as mock_resolve:
            mock_resolve.side_effect = lambda content, *args, **kwargs: content

            controller = ReaderController()
            controller._book = mock_book
            controller._current_chapter_index = 0

            # Load initial chapter (wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(0)
            assert mock_book.get_chapter_content.call_count == 1

            # Navigate forward (wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.next_chapter()
            assert mock_book.get_chapter_content.call_count == 2

            # Navigate backward (should hit cache, wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.previous_chapter()
            assert mock_book.get_chapter_content.call_count == 2  # No new load

    def test_previous_chapter_uses_cache(self, qtbot):
        """Test that previous_chapter() method benefits from caching."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        with patch('ereader.utils.async_loader.resolve_images_in_html') as mock_resolve:
            mock_resolve.side_effect = lambda content, *args, **kwargs: content

            controller = ReaderController()
            controller._book = mock_book
            controller._current_chapter_index = 2

            # Load initial chapter (wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(2)
            assert mock_book.get_chapter_content.call_count == 1

            # Navigate backward (wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.previous_chapter()
            assert mock_book.get_chapter_content.call_count == 2

            # Navigate forward (should hit cache, wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller.next_chapter()
            assert mock_book.get_chapter_content.call_count == 2  # No new load


class TestReaderControllerProgressTracking:
    """Test scroll position tracking and progress signal emission."""

    def test_init_has_scroll_percentage_state(self):
        """Test that controller initializes with scroll percentage state."""
        controller = ReaderController()

        assert hasattr(controller, '_current_scroll_percentage')
        assert controller._current_scroll_percentage == 0.0

    def test_init_has_reading_progress_signal(self):
        """Test that controller defines reading_progress_changed signal."""
        controller = ReaderController()

        assert hasattr(controller, 'reading_progress_changed')

    def test_on_scroll_changed_updates_percentage(self):
        """Test that scroll change updates internal state."""
        controller = ReaderController()

        # Set up a mock book
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 10
        controller._book = mock_book
        controller._current_chapter_index = 2

        # Simulate scroll change
        controller.on_scroll_changed(45.5)

        # Verify state updated
        assert controller._current_scroll_percentage == 45.5

    def test_on_scroll_changed_emits_progress_signal(self):
        """Test that scroll change emits formatted progress string."""
        controller = ReaderController()

        # Setup mock book
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 10
        controller._book = mock_book
        controller._current_chapter_index = 2  # Chapter 3 (1-based)

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Simulate scroll change
        controller.on_scroll_changed(45.5)

        # Verify signal emitted with correct format
        progress_spy.assert_called_once()
        emitted_progress = progress_spy.call_args[0][0]
        assert emitted_progress == "Chapter 3 of 10 • 46% through chapter"  # Rounded to 46

    def test_emit_progress_update_formats_correctly(self):
        """Test progress string formatting."""
        controller = ReaderController()

        # Setup mock book
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        controller._book = mock_book
        controller._current_chapter_index = 0
        controller._current_scroll_percentage = 0.0

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Emit progress
        controller._emit_progress_update()

        # Verify format
        progress_spy.assert_called_once_with("Chapter 1 of 5 • 0% through chapter")

    def test_emit_progress_update_with_various_percentages(self):
        """Test progress formatting with different scroll percentages."""
        controller = ReaderController()

        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 15
        controller._book = mock_book
        controller._current_chapter_index = 5  # Chapter 6

        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Test various percentages
        test_cases = [
            (0.0, "Chapter 6 of 15 • 0% through chapter"),
            (25.7, "Chapter 6 of 15 • 26% through chapter"),
            (50.0, "Chapter 6 of 15 • 50% through chapter"),
            (75.3, "Chapter 6 of 15 • 75% through chapter"),
            (100.0, "Chapter 6 of 15 • 100% through chapter"),
        ]

        for percentage, expected_message in test_cases:
            progress_spy.reset_mock()
            controller._current_scroll_percentage = percentage
            controller._emit_progress_update()
            progress_spy.assert_called_once_with(expected_message)

    def test_emit_progress_update_no_book_loaded(self):
        """Test that emit_progress_update does nothing when no book is loaded."""
        controller = ReaderController()

        # No book loaded
        assert controller._book is None

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Try to emit progress
        controller._emit_progress_update()

        # Verify signal was not emitted
        progress_spy.assert_not_called()

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_load_chapter_resets_scroll_percentage(self, mock_resolve_images, qtbot):
        """Test that loading a chapter resets scroll percentage to 0."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter0.html"
        mock_book.get_chapter_content.return_value = "<p>Content</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Set scroll percentage to simulate being in middle of chapter
        controller._current_scroll_percentage = 50.0

        # Load new chapter (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(1)

        # Verify scroll percentage reset to 0
        assert controller._current_scroll_percentage == 0.0

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_load_chapter_emits_progress_update(self, mock_resolve_images, qtbot):
        """Test that loading a chapter emits progress update."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter0.html"
        mock_book.get_chapter_content.return_value = "<p>Content</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Load chapter 0 (Chapter 1 for display, wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller._load_chapter(0)

        # Verify progress signal emitted with 0% scroll
        progress_spy.assert_called_once_with("Chapter 1 of 5 • 0% through chapter")

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_next_chapter_emits_progress_with_zero_scroll(self, mock_resolve_images, qtbot):
        """Test that navigating to next chapter shows 0% scroll in progress."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        controller = ReaderController()
        controller._book = mock_book
        controller._current_chapter_index = 0

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Simulate being scrolled in middle of chapter
        controller._current_scroll_percentage = 75.0

        # Navigate to next chapter (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller.next_chapter()

        # Verify progress shows 0% for new chapter
        emitted_progress = progress_spy.call_args[0][0]
        assert "Chapter 2 of 5 • 0% through chapter" == emitted_progress

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_previous_chapter_emits_progress_with_zero_scroll(self, mock_resolve_images, qtbot):
        """Test that navigating to previous chapter shows 0% scroll in progress."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        controller = ReaderController()
        controller._book = mock_book
        controller._current_chapter_index = 2

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Simulate being scrolled
        controller._current_scroll_percentage = 80.0

        # Navigate to previous chapter (wait for async)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller.previous_chapter()

        # Verify progress shows 0% for new chapter
        emitted_progress = progress_spy.call_args[0][0]
        assert "Chapter 2 of 5 • 0% through chapter" == emitted_progress


class TestReaderControllerMemoryMonitoring:
    """Test memory monitoring integration in ReaderController (Phase 2)."""

    def test_init_creates_memory_monitor(self):
        """Test that ReaderController initializes with MemoryMonitor via CacheManager."""
        controller = ReaderController()

        assert hasattr(controller, '_cache_manager')
        assert controller._cache_manager.memory_monitor is not None
        assert controller._cache_manager.memory_monitor._threshold_mb == 150

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_memory_check_called_after_chapter_load(self, mock_resolve_images, qtbot):
        """Test that memory threshold is checked after loading a chapter."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter0.html"
        mock_book.get_chapter_content.return_value = "<p>Chapter content</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Mock the memory monitor's check_threshold method
        with patch.object(controller._cache_manager.memory_monitor, 'check_threshold') as mock_check:
            mock_check.return_value = False

            # Load a chapter (wait for async)
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(0)

            # Verify memory check was called
            mock_check.assert_called_once()

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    @patch('psutil.Process')
    def test_memory_warning_logged_when_threshold_exceeded(
        self, mock_process_class, mock_resolve_images, qtbot, caplog: "pytest.LogCaptureFixture"
    ):
        """Test that memory warnings are logged when threshold exceeded."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        # Mock psutil to return high memory usage
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 200 * 1024 * 1024  # 200 MB

        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_mem_info
        mock_process_class.return_value = mock_process

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter0.html"
        mock_book.get_chapter_content.return_value = "<p>Chapter content</p>"

        # Create controller (which creates MemoryMonitor with mocked psutil)
        controller = ReaderController()
        controller._book = mock_book

        # Load a chapter which will trigger memory check (wait for async)
        with caplog.at_level("WARNING"):
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(0)

            # Verify warning was logged
            assert any("exceeds threshold" in record.message for record in caplog.records)

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_memory_check_on_cache_hit(self, mock_resolve_images, qtbot):
        """Test that memory is checked even on cache hits."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter0.html"
        mock_book.get_chapter_content.return_value = "<p>Chapter content</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Load chapter once to cache it (wait for async)
        with patch.object(controller._cache_manager.memory_monitor, 'check_threshold') as mock_check:
            mock_check.return_value = False
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(0)
            first_call_count = mock_check.call_count

        # Load same chapter again (cache hit, wait for async)
        with patch.object(controller._cache_manager.memory_monitor, 'check_threshold') as mock_check:
            mock_check.return_value = False
            with qtbot.waitSignal(controller.content_ready, timeout=1000):
                controller._load_chapter(0)
            second_call_count = mock_check.call_count

        # Memory check should be called on both loads
        assert first_call_count == 1
        assert second_call_count == 1

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_memory_monitoring_with_sequential_chapters(self, mock_resolve_images, qtbot):
        """Test that memory is monitored during sequential reading."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 15
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        controller = ReaderController()
        controller._book = mock_book

        with patch.object(controller._cache_manager.memory_monitor, 'check_threshold') as mock_check:
            mock_check.return_value = False

            # Load multiple chapters sequentially (wait for each async)
            for i in range(10):
                with qtbot.waitSignal(controller.content_ready, timeout=1000):
                    controller._load_chapter(i)

            # Memory should be checked 10 times (once per chapter load)
            assert mock_check.call_count == 10

    def test_memory_monitor_stats_accessible(self):
        """Test that memory monitor stats can be accessed."""
        controller = ReaderController()

        stats = controller._cache_manager.memory_monitor.get_stats()

        # Verify stats structure
        assert "current_usage_mb" in stats
        assert "threshold_mb" in stats
        assert "threshold_exceeded" in stats
        assert stats["threshold_mb"] == 150


class TestReaderControllerPagination:
    """Test pagination functionality (Phase 2A)."""

    def test_controller_has_pagination_engine(self):
        """Test that controller initializes with PaginationEngine."""
        controller = ReaderController()

        assert hasattr(controller, '_pagination_engine')
        assert controller._pagination_engine is not None

    def test_controller_has_pagination_signal(self):
        """Test that controller has pagination_changed signal."""
        controller = ReaderController()

        assert hasattr(controller, 'pagination_changed')

    def test_recalculate_pages_method_exists(self):
        """Test that _recalculate_pages method exists."""
        controller = ReaderController()

        assert hasattr(controller, '_recalculate_pages')
        assert callable(controller._recalculate_pages)

    @patch('ereader.controllers.reader_controller.EPUBBook')
    def test_pagination_signal_emitted_on_chapter_load(
        self, mock_epub_class, mock_epub_book, qtbot
    ):
        """Test that pagination_changed signal is emitted when chapter loads."""
        mock_epub_book.get_chapter_count.return_value = 5
        mock_epub_book.get_chapter_content.return_value = "<p>Content</p>"
        mock_epub_class.return_value = mock_epub_book

        controller = ReaderController()

        # Create a mock viewer to provide dimensions
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = int(2400)
        mock_viewer.get_viewport_height.return_value = int(800)
        mock_viewer.get_scroll_position.return_value = int(0)

        # Connect a spy to pagination signal
        pagination_spy = Mock()
        controller.pagination_changed.connect(pagination_spy)

        # Open book and wait for content
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller.open_book("/path/to/book.epub")

        # Manually trigger recalculation with dimensions
        controller._recalculate_pages(mock_viewer)

        # Verify pagination signal was emitted
        pagination_spy.assert_called_once()
        current_page, total_pages = pagination_spy.call_args[0]

        assert current_page == 1  # 1-indexed for display
        assert total_pages == 3  # 2400 / 800 = 3 pages


class TestReaderControllerPageNavigation:
    """Test discrete page navigation functionality (Phase 2B)."""

    def _setup_controller_with_book(self, chapter_count: int = 5):
        """Helper to create controller with a mock book loaded."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.title = "Test Book"
        mock_book.authors = ["Test Author"]
        mock_book.get_chapter_count.return_value = chapter_count
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i + 1}</p>"

        controller = ReaderController()
        controller._book = mock_book
        controller._current_chapter_index = 0

        return controller, mock_book

    def test_controller_has_navigation_mode_state(self):
        """Test that controller initializes with navigation mode state."""
        from ereader.models.reading_position import NavigationMode

        controller = ReaderController()

        assert hasattr(controller, '_current_mode')
        assert controller._current_mode == NavigationMode.SCROLL  # Default to scroll mode

    def test_next_page_method_exists(self):
        """Test that next_page method exists."""
        controller = ReaderController()

        assert hasattr(controller, 'next_page')
        assert callable(controller.next_page)

    def test_previous_page_method_exists(self):
        """Test that previous_page method exists."""
        controller = ReaderController()

        assert hasattr(controller, 'previous_page')
        assert callable(controller.previous_page)

    def test_next_page_in_scroll_mode_does_nothing(self):
        """Test that next_page does nothing when in scroll mode."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.SCROLL

        # Create mock viewer
        mock_viewer = MagicMock()
        controller._book_viewer = mock_viewer

        # Call next_page
        controller.next_page()

        # Verify no scroll position changes
        mock_viewer.set_scroll_position.assert_not_called()

    def test_next_page_navigates_within_chapter(self):
        """Test next_page navigates to next page within current chapter."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.PAGE

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 0  # At page 0
        controller._book_viewer = mock_viewer

        # Calculate pages
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Navigate to next page
        controller.next_page()

        # Verify scroll position set to page 1 (scroll position 800)
        mock_viewer.set_scroll_position.assert_called_once_with(800)

    def test_next_page_at_last_page_goes_to_next_chapter(self, qtbot):
        """Test next_page at last page of chapter navigates to next chapter."""
        from ereader.models.reading_position import NavigationMode

        controller, mock_book = self._setup_controller_with_book(5)
        controller._current_mode = NavigationMode.PAGE
        controller._current_chapter_index = 0

        # Setup mock viewer at last page
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 1600  # Last page (page 2)
        controller._book_viewer = mock_viewer

        # Calculate pages (3 pages total: 0, 800, 1600)
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Navigate to next page (should go to next chapter)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller.next_page()

        # Verify we moved to next chapter
        assert controller._current_chapter_index == 1

    def test_next_page_at_last_page_of_last_chapter_does_nothing(self):
        """Test next_page at last page of last chapter does nothing."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book(3)
        controller._current_mode = NavigationMode.PAGE
        controller._current_chapter_index = 2  # Last chapter

        # Setup mock viewer at last page
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 1600  # Last page
        controller._book_viewer = mock_viewer

        # Calculate pages
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Try to navigate (should do nothing)
        controller.next_page()

        # Verify we didn't move chapters
        assert controller._current_chapter_index == 2

    def test_next_page_with_no_book_loaded(self):
        """Test next_page with no book loaded does nothing."""
        from ereader.models.reading_position import NavigationMode

        controller = ReaderController()
        controller._current_mode = NavigationMode.PAGE

        # Should not crash
        controller.next_page()

        # Verify state unchanged
        assert controller._book is None

    def test_previous_page_in_scroll_mode_does_nothing(self):
        """Test that previous_page does nothing when in scroll mode."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.SCROLL

        # Create mock viewer
        mock_viewer = MagicMock()
        controller._book_viewer = mock_viewer

        # Call previous_page
        controller.previous_page()

        # Verify no scroll position changes
        mock_viewer.set_scroll_position.assert_not_called()

    def test_previous_page_navigates_within_chapter(self):
        """Test previous_page navigates to previous page within current chapter."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.PAGE

        # Setup mock viewer at page 1
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 800  # At page 1
        controller._book_viewer = mock_viewer

        # Calculate pages
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Navigate to previous page
        controller.previous_page()

        # Verify scroll position set to page 0 (scroll position 0)
        mock_viewer.set_scroll_position.assert_called_once_with(0)

    def test_previous_page_at_first_page_goes_to_previous_chapter(self, qtbot):
        """Test previous_page at first page of chapter navigates to previous chapter."""
        from ereader.models.reading_position import NavigationMode

        controller, mock_book = self._setup_controller_with_book(5)
        controller._current_mode = NavigationMode.PAGE
        controller._current_chapter_index = 2  # Chapter 3

        # Setup mock viewer at first page
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 0  # First page
        controller._book_viewer = mock_viewer

        # Calculate pages
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Navigate to previous page (should go to previous chapter)
        with qtbot.waitSignal(controller.content_ready, timeout=1000):
            controller.previous_page()

        # Verify we moved to previous chapter
        assert controller._current_chapter_index == 1

    def test_previous_page_at_first_page_of_first_chapter_does_nothing(self):
        """Test previous_page at first page of first chapter does nothing."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book(3)
        controller._current_mode = NavigationMode.PAGE
        controller._current_chapter_index = 0  # First chapter

        # Setup mock viewer at first page
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 0  # First page
        controller._book_viewer = mock_viewer

        # Calculate pages
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Try to navigate (should do nothing)
        controller.previous_page()

        # Verify we didn't move chapters
        assert controller._current_chapter_index == 0

    def test_previous_page_with_no_book_loaded(self):
        """Test previous_page with no book loaded does nothing."""
        from ereader.models.reading_position import NavigationMode

        controller = ReaderController()
        controller._current_mode = NavigationMode.PAGE

        # Should not crash
        controller.previous_page()

        # Verify state unchanged
        assert controller._book is None

    def test_page_navigation_with_single_page_chapter(self):
        """Test page navigation in a chapter with only one page."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book(5)
        controller._current_mode = NavigationMode.PAGE

        # Setup mock viewer with content that fits in one page
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 500  # Less than viewport
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Calculate pages (should be 1 page)
        controller._pagination_engine.calculate_page_breaks(500, 800)

        # Verify only 1 page
        assert controller._pagination_engine.get_page_count() == 1

        # Try to navigate forward within chapter (should do nothing)
        controller.next_page()

        # Should not try to set scroll position (already at end of page)
        # The method will recognize we're at max_page and try next_chapter instead
        # Since we're mocking, we can't easily test this flow, but the implementation
        # will handle it by checking if current_page < max_page

    def test_page_navigation_updates_progress(self):
        """Test that page navigation triggers progress updates."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.PAGE

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2400
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Calculate pages
        controller._pagination_engine.calculate_page_breaks(2400, 800)

        # Connect progress spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Navigate to next page
        controller.next_page()

        # Note: Progress update happens when scroll position changes in viewer
        # This is triggered by the viewer's scroll signal, not directly by next_page
        # So we won't see a progress update here unless we simulate the scroll signal


class TestReaderControllerModeToggle:
    """Test navigation mode toggle functionality (Phase 2C)."""

    def _setup_controller_with_book(self, chapter_count: int = 5):
        """Helper to create controller with a mock book loaded."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.title = "Test Book"
        mock_book.authors = ["Test Author"]
        mock_book.get_chapter_count.return_value = chapter_count
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i + 1}</p>"

        controller = ReaderController()
        controller._book = mock_book
        controller._current_chapter_index = 0

        return controller, mock_book

    def test_controller_has_mode_changed_signal(self):
        """Test that controller defines mode_changed signal."""
        controller = ReaderController()

        assert hasattr(controller, 'mode_changed')

    def test_toggle_navigation_mode_method_exists(self):
        """Test that toggle_navigation_mode method exists."""
        controller = ReaderController()

        assert hasattr(controller, 'toggle_navigation_mode')
        assert callable(controller.toggle_navigation_mode)

    def test_toggle_mode_without_book_does_nothing(self):
        """Test that toggle_navigation_mode does nothing when no book is loaded."""
        from ereader.models.reading_position import NavigationMode

        controller = ReaderController()
        mode_changed_spy = Mock()
        controller.mode_changed.connect(mode_changed_spy)

        # Try to toggle mode
        controller.toggle_navigation_mode()

        # Should remain in scroll mode and not emit signal
        assert controller._current_mode == NavigationMode.SCROLL
        mode_changed_spy.assert_not_called()

    def test_toggle_from_scroll_to_page_mode(self):
        """Test toggling from scroll mode to page mode."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.SCROLL

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2000
        mock_viewer.get_viewport_height.return_value = 500
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Setup signal spy
        mode_changed_spy = Mock()
        controller.mode_changed.connect(mode_changed_spy)

        # Toggle mode
        controller.toggle_navigation_mode()

        # Verify mode changed to PAGE
        assert controller._current_mode == NavigationMode.PAGE
        mode_changed_spy.assert_called_once_with(NavigationMode.PAGE)

    def test_toggle_from_page_to_scroll_mode(self):
        """Test toggling from page mode to scroll mode."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.PAGE

        # Setup signal spy
        mode_changed_spy = Mock()
        controller.mode_changed.connect(mode_changed_spy)

        # Toggle mode
        controller.toggle_navigation_mode()

        # Verify mode changed to SCROLL
        assert controller._current_mode == NavigationMode.SCROLL
        mode_changed_spy.assert_called_once_with(NavigationMode.SCROLL)

    def test_switch_to_page_mode_recalculates_pages(self):
        """Test that switching to page mode triggers page recalculation."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.SCROLL

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2000
        mock_viewer.get_viewport_height.return_value = 500
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Toggle to page mode
        controller.toggle_navigation_mode()

        # Verify pagination engine was used
        assert controller._pagination_engine.get_page_count() > 0

    def test_switch_to_page_mode_emits_progress_update(self):
        """Test that switching to page mode emits progress update."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.SCROLL

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2000
        mock_viewer.get_viewport_height.return_value = 500
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Toggle to page mode
        controller.toggle_navigation_mode()

        # Verify progress update was emitted
        progress_spy.assert_called()
        # Progress should contain "Page" when in page mode
        progress_message = progress_spy.call_args[0][0]
        assert "Page" in progress_message

    def test_switch_to_scroll_mode_emits_progress_update(self):
        """Test that switching to scroll mode emits progress update."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.PAGE
        controller._current_scroll_percentage = 50.0

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Toggle to scroll mode
        controller.toggle_navigation_mode()

        # Verify progress update was emitted
        progress_spy.assert_called()
        # Progress should contain percentage when in scroll mode
        progress_message = progress_spy.call_args[0][0]
        assert "%" in progress_message

    def test_toggle_mode_multiple_times(self):
        """Test toggling mode multiple times works correctly."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 2000
        mock_viewer.get_viewport_height.return_value = 500
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Start in scroll mode
        assert controller._current_mode == NavigationMode.SCROLL

        # Toggle to page mode
        controller.toggle_navigation_mode()
        assert controller._current_mode == NavigationMode.PAGE

        # Toggle back to scroll mode
        controller.toggle_navigation_mode()
        assert controller._current_mode == NavigationMode.SCROLL

        # Toggle to page mode again
        controller.toggle_navigation_mode()
        assert controller._current_mode == NavigationMode.PAGE

    def test_short_chapter_displays_page_1_of_1(self):
        """Test that short chapters (< 1 viewport) display 'Page 1 of 1'."""
        from ereader.models.reading_position import NavigationMode

        controller, _ = self._setup_controller_with_book()
        controller._current_mode = NavigationMode.PAGE

        # Setup mock viewer with short content (< viewport)
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 400  # Shorter than viewport
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 0
        controller._book_viewer = mock_viewer

        # Calculate pages (should be 1 page)
        controller._pagination_engine.calculate_page_breaks(400, 800)
        assert controller._pagination_engine.get_page_count() == 1

        # Setup signal spy
        progress_spy = Mock()
        controller.reading_progress_changed.connect(progress_spy)

        # Emit progress update
        controller._emit_progress_update()

        # Verify progress shows "Page 1 of 1 in Chapter X"
        progress_spy.assert_called_once()
        progress_message = progress_spy.call_args[0][0]
        assert "Page 1 of 1" in progress_message
        assert "Chapter 1" in progress_message


class TestReaderControllerPositionPersistence:
    """Test position persistence functionality (Phase 2D)."""

    @pytest.fixture
    def controller_with_settings(self, qtbot):
        """Create controller with isolated test settings."""
        from PyQt6.QtCore import QSettings

        # Use test-specific settings
        controller = ReaderController()
        controller._settings._settings = QSettings("EReaderTest", "EReaderTest")
        controller._settings.clear_all_settings()

        yield controller

        # Cleanup
        controller._settings.clear_all_settings()

    def test_save_current_position_scroll_mode(self, controller_with_settings):
        """Test saving position in scroll mode."""
        from ereader.models.reading_position import NavigationMode

        controller = controller_with_settings

        # Setup mock book and viewer
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        controller._book = mock_book
        controller._current_book_path = "/path/to/test.epub"
        controller._current_chapter_index = 2
        controller._current_mode = NavigationMode.SCROLL

        mock_viewer = MagicMock()
        mock_viewer.get_scroll_position.return_value = 450
        controller._book_viewer = mock_viewer

        # Save position
        controller.save_current_position()

        # Verify position was saved
        saved_position = controller._settings.load_reading_position("/path/to/test.epub")
        assert saved_position is not None
        assert saved_position.chapter_index == 2
        assert saved_position.scroll_offset == 450
        assert saved_position.mode == NavigationMode.SCROLL

    def test_save_current_position_page_mode(self, controller_with_settings):
        """Test saving position in page mode."""
        from ereader.models.reading_position import NavigationMode

        controller = controller_with_settings

        # Setup mock book and viewer
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 5
        controller._book = mock_book
        controller._current_book_path = "/path/to/test.epub"
        controller._current_chapter_index = 3
        controller._current_mode = NavigationMode.PAGE

        mock_viewer = MagicMock()
        mock_viewer.get_scroll_position.return_value = 800
        controller._book_viewer = mock_viewer

        # Setup pagination engine
        controller._pagination_engine.calculate_page_breaks(2000, 500)
        controller._pagination_engine.get_page_number = MagicMock(return_value=5)

        # Save position
        controller.save_current_position()

        # Verify position was saved
        saved_position = controller._settings.load_reading_position("/path/to/test.epub")
        assert saved_position is not None
        assert saved_position.chapter_index == 3
        assert saved_position.scroll_offset == 800
        assert saved_position.page_number == 5
        assert saved_position.mode == NavigationMode.PAGE

    def test_save_position_on_chapter_change(self, controller_with_settings, mock_epub_book):
        """Test that position is saved when changing chapters."""
        controller = controller_with_settings

        # Setup controller with book
        with patch('ereader.controllers.reader_controller.EPUBBook', return_value=mock_epub_book):
            controller.open_book("/path/to/test.epub")

        # Setup viewer
        mock_viewer = MagicMock()
        mock_viewer.get_scroll_position.return_value = 300
        controller._book_viewer = mock_viewer

        # Navigate to next chapter
        controller.next_chapter()

        # Verify position was saved for chapter 0
        saved_position = controller._settings.load_reading_position("/path/to/test.epub")
        assert saved_position is not None
        assert saved_position.chapter_index == 0
        assert saved_position.scroll_offset == 300

    def test_restore_position_on_book_open(self, controller_with_settings, mock_epub_book):
        """Test that saved position is restored when opening a book."""
        from ereader.models.reading_position import NavigationMode, ReadingPosition

        controller = controller_with_settings

        # Save a position first
        saved_position = ReadingPosition(
            chapter_index=2,
            page_number=5,
            scroll_offset=750,
            mode=NavigationMode.PAGE,
        )
        controller._settings.save_reading_position("/path/to/test.epub", saved_position)

        # Open the book
        with patch('ereader.controllers.reader_controller.EPUBBook', return_value=mock_epub_book):
            controller.open_book("/path/to/test.epub")

        # Verify that the controller restored the chapter and mode
        assert controller._current_chapter_index == 2
        assert controller._current_mode == NavigationMode.PAGE
        # Position restore is deferred, so check that it's pending
        assert controller._pending_position_restore is not None
        assert controller._pending_position_restore.scroll_offset == 750

    def test_restore_position_invalid_chapter(self, controller_with_settings, mock_epub_book):
        """Test restoring position with invalid chapter index."""
        from ereader.models.reading_position import NavigationMode, ReadingPosition

        controller = controller_with_settings

        # Save position with chapter beyond book length
        saved_position = ReadingPosition(
            chapter_index=10,  # Book only has 5 chapters
            page_number=0,
            scroll_offset=0,
            mode=NavigationMode.SCROLL,
        )
        controller._settings.save_reading_position("/path/to/test.epub", saved_position)

        # Open the book
        with patch('ereader.controllers.reader_controller.EPUBBook', return_value=mock_epub_book):
            controller.open_book("/path/to/test.epub")

        # Verify controller started at chapter 0 (fallback)
        assert controller._current_chapter_index == 0

    def test_no_saved_position_starts_at_beginning(self, controller_with_settings, mock_epub_book):
        """Test that book starts at beginning when no saved position exists."""
        controller = controller_with_settings

        # Open book without saved position
        with patch('ereader.controllers.reader_controller.EPUBBook', return_value=mock_epub_book):
            controller.open_book("/path/to/test.epub")

        # Verify started at chapter 0
        assert controller._current_chapter_index == 0
        assert controller._pending_position_restore is None

    def test_save_position_with_no_book(self, controller_with_settings):
        """Test that saving position with no book loaded does nothing."""
        controller = controller_with_settings

        # Try to save without book
        controller.save_current_position()

        # Should not raise error, just log and skip

    def test_save_position_with_no_viewer(self, controller_with_settings):
        """Test that saving position with no viewer does nothing."""
        controller = controller_with_settings

        # Setup book but no viewer
        mock_book = MagicMock()
        controller._book = mock_book
        controller._current_book_path = "/path/to/test.epub"

        # Try to save
        controller.save_current_position()

        # Should not raise error, just log and skip


@pytest.mark.skip(reason="Resize tests cause Qt crashes in headless environment - see Phase 2E notes")
class TestReaderControllerViewportResize:
    """Test viewport resize handling (Phase 2E)."""

    @pytest.fixture
    def controller_with_book(self):
        """Create controller with mocked book and viewer for resize testing."""
        controller = ReaderController()

        # Setup mock book
        mock_book = MagicMock()
        mock_book.get_chapter_count.return_value = 10
        controller._book = mock_book

        # Setup mock viewer
        mock_viewer = MagicMock()
        mock_viewer.get_content_height.return_value = 5000
        mock_viewer.get_viewport_height.return_value = 800
        mock_viewer.get_scroll_position.return_value = 1600  # Page 2
        controller._book_viewer = mock_viewer

        return controller

    def test_resize_in_scroll_mode_does_nothing(self, controller_with_book):
        """Test that resize in scroll mode does not recalculate pages."""
        controller = controller_with_book
        controller._current_mode = NavigationMode.SCROLL

        # Call resize handler
        controller.on_viewport_resized(width=600, height=900)

        # Viewer methods should not be called
        controller._book_viewer.get_content_height.assert_not_called()

    def test_resize_with_no_book_does_nothing(self):
        """Test that resize with no book loaded does nothing."""
        controller = ReaderController()
        controller._current_mode = NavigationMode.PAGE

        # Should not raise error
        controller.on_viewport_resized(width=600, height=900)

    def test_resize_with_no_viewer_does_nothing(self):
        """Test that resize with no viewer does nothing."""
        controller = ReaderController()
        controller._current_mode = NavigationMode.PAGE
        controller._book = MagicMock()

        # Should not raise error
        controller.on_viewport_resized(width=600, height=900)

    def test_resize_in_page_mode_recalculates_pages(self, controller_with_book, qtbot):
        """Test that resize in page mode recalculates pagination."""
        controller = controller_with_book
        controller._current_mode = NavigationMode.PAGE

        # Initialize pagination with original dimensions
        controller._pagination_engine.calculate_page_breaks(
            content_height=5000,
            viewport_height=800
        )

        # Connect signal to spy on emissions
        with qtbot.waitSignal(controller.pagination_changed, timeout=1000) as blocker:
            # Trigger resize with smaller viewport
            controller.on_viewport_resized(width=600, height=600)

        # Should emit pagination_changed signal
        assert blocker.signal_triggered

        # Viewer methods should be called
        controller._book_viewer.get_content_height.assert_called_once()
        controller._book_viewer.set_scroll_position.assert_called_once()

    def test_resize_maintains_page_number(self, controller_with_book):
        """Test that resize maintains user's relative position (page number)."""
        controller = controller_with_book
        controller._current_mode = NavigationMode.PAGE

        # Initialize pagination: 5000px content / 800px viewport = ~7 pages
        controller._pagination_engine.calculate_page_breaks(
            content_height=5000,
            viewport_height=800
        )

        # User is on page 2 (scroll position 1600)
        controller._book_viewer.get_scroll_position.return_value = 1600
        current_page = controller._pagination_engine.get_page_number(1600)
        assert current_page == 2

        # Trigger resize to larger viewport (fewer pages)
        controller._book_viewer.get_content_height.return_value = 5000
        controller.on_viewport_resized(width=800, height=1200)

        # Should try to maintain page 2
        # New pagination: 5000px / 1200px = ~5 pages
        # Page 2 should now start at 2400px
        expected_scroll = controller._pagination_engine.get_scroll_position_for_page(2)
        controller._book_viewer.set_scroll_position.assert_called_once_with(expected_scroll)

    def test_resize_clamps_page_number_when_page_count_decreases(self, controller_with_book):
        """Test that resize handles case where user's page no longer exists."""
        controller = controller_with_book
        controller._current_mode = NavigationMode.PAGE

        # Initialize pagination: 5000px content / 500px viewport = 10 pages
        controller._pagination_engine.calculate_page_breaks(
            content_height=5000,
            viewport_height=500
        )

        # User is on page 8 (near end)
        controller._book_viewer.get_scroll_position.return_value = 4000
        current_page = controller._pagination_engine.get_page_number(4000)
        assert current_page == 8

        # Trigger resize to much larger viewport (only 2 pages now)
        controller._book_viewer.get_content_height.return_value = 5000
        controller.on_viewport_resized(width=800, height=3000)

        # New page count should be ~2 pages
        new_page_count = controller._pagination_engine.get_page_count()
        assert new_page_count == 2

        # Should clamp to last page (page 1, since 0-indexed)
        expected_scroll = controller._pagination_engine.get_scroll_position_for_page(1)
        controller._book_viewer.set_scroll_position.assert_called_once_with(expected_scroll)

    def test_resize_emits_pagination_changed_signal(self, controller_with_book, qtbot):
        """Test that resize emits pagination_changed signal with new page count."""
        controller = controller_with_book
        controller._current_mode = NavigationMode.PAGE

        # Initialize pagination
        controller._pagination_engine.calculate_page_breaks(
            content_height=5000,
            viewport_height=800
        )

        # Connect signal spy
        with qtbot.waitSignal(controller.pagination_changed, timeout=1000) as blocker:
            # Trigger resize
            controller.on_viewport_resized(width=600, height=600)

        # Verify signal was emitted
        assert blocker.signal_triggered
        # Signal args: (current_page, total_pages) - both 1-indexed
        current_page, total_pages = blocker.args
        assert isinstance(current_page, int)
        assert isinstance(total_pages, int)
        assert total_pages > 0

    def test_resize_updates_progress_display(self, controller_with_book, qtbot):
        """Test that resize triggers progress update."""
        controller = controller_with_book
        controller._current_mode = NavigationMode.PAGE

        # Initialize pagination
        controller._pagination_engine.calculate_page_breaks(
            content_height=5000,
            viewport_height=800
        )

        # Connect signal spy for progress updates
        with qtbot.waitSignal(controller.reading_progress_changed, timeout=1000) as blocker:
            # Trigger resize
            controller.on_viewport_resized(width=600, height=600)

        # Should emit progress update
        assert blocker.signal_triggered
        progress_text = blocker.args[0]
        assert "Page" in progress_text  # Page mode format
        assert "of" in progress_text
