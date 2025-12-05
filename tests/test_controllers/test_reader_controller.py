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


class TestReaderControllerCaching:
    """Test chapter caching behavior in ReaderController."""

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_cache_hit_on_repeated_chapter_load(self, mock_resolve_images):
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

        # First load - should render
        controller._load_chapter(0)

        # Verify rendering happened
        mock_book.get_chapter_content.assert_called_once_with(0)
        mock_resolve_images.assert_called_once()
        content_spy.assert_called_once_with("<p>Rendered chapter content</p>")

        # Reset spies
        mock_book.get_chapter_content.reset_mock()
        mock_resolve_images.reset_mock()
        content_spy.reset_mock()

        # Second load of same chapter - should use cache
        controller._load_chapter(0)

        # Verify no rendering happened (cache hit)
        mock_book.get_chapter_content.assert_not_called()
        mock_resolve_images.assert_not_called()

        # But content was still emitted
        content_spy.assert_called_once_with("<p>Rendered chapter content</p>")

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_cache_miss_on_different_chapter(self, mock_resolve_images):
        """Test that loading different chapter misses cache."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i} raw</p>"
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content.replace("raw", "rendered")

        controller = ReaderController()
        controller._book = mock_book

        # Load chapter 0
        controller._load_chapter(0)
        assert mock_book.get_chapter_content.call_count == 1

        # Load chapter 1 - should miss cache
        controller._load_chapter(1)
        assert mock_book.get_chapter_content.call_count == 2

        # Load chapter 2 - should miss cache
        controller._load_chapter(2)
        assert mock_book.get_chapter_content.call_count == 3

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_sequential_navigation_caching(self, mock_resolve_images):
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
            controller._load_chapter(i)

        # With multi-layer caching:
        # - Rendered cache (maxsize=10): chapters 3-12 (evicted 0-2)
        # - Raw cache (maxsize=20): chapters 0-12 (all still cached)

        # Reset mock to count cache hits
        mock_book.get_chapter_content.reset_mock()

        # Re-load chapter 2 - should hit raw cache (no book load needed)
        # But needs re-rendering (evicted from rendered cache)
        controller._load_chapter(2)
        assert mock_book.get_chapter_content.call_count == 0  # Raw cache hit

        mock_book.get_chapter_content.reset_mock()

        # Re-load chapter 12 - should hit rendered cache (complete cache hit)
        controller._load_chapter(12)
        assert mock_book.get_chapter_content.call_count == 0  # Rendered cache hit

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_backward_navigation_caching(self, mock_resolve_images):
        """Test cache behavior during backward navigation."""
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 10
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        controller = ReaderController()
        controller._book = mock_book

        # Navigate to chapter 5
        for i in range(6):
            controller._load_chapter(i)

        # Reset mock to count cache hits
        mock_book.get_chapter_content.reset_mock()

        # Navigate backward 5 -> 4 -> 3 (all should be cache hits)
        controller._load_chapter(4)
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
    def test_cache_key_uniqueness(self, mock_resolve_images):
        """Test that different books don't collide in cache."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.side_effect = lambda i: f"text/chapter{i}.html"
        mock_book.get_chapter_content.side_effect = lambda i: f"<p>Chapter {i}</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Load chapter 0 from first book
        controller._load_chapter(0)
        first_content = controller._cache_manager.rendered_chapters.get("/path/to/book.epub:0")

        # Simulate changing book (different path)
        mock_book.filepath = "/path/to/different_book.epub"

        # Load chapter 0 from second book
        controller._load_chapter(0)

        # Both chapters should be in cache with different keys
        assert controller._cache_manager.rendered_chapters.get("/path/to/book.epub:0") == first_content
        assert controller._cache_manager.rendered_chapters.get("/path/to/different_book.epub:0") == "<p>Chapter 0</p>"

    def test_next_chapter_uses_cache(self):
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

            # Load initial chapter
            controller._load_chapter(0)
            assert mock_book.get_chapter_content.call_count == 1

            # Navigate forward
            controller.next_chapter()
            assert mock_book.get_chapter_content.call_count == 2

            # Navigate backward (should hit cache)
            controller.previous_chapter()
            assert mock_book.get_chapter_content.call_count == 2  # No new load

    def test_previous_chapter_uses_cache(self):
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

            # Load initial chapter
            controller._load_chapter(2)
            assert mock_book.get_chapter_content.call_count == 1

            # Navigate backward
            controller.previous_chapter()
            assert mock_book.get_chapter_content.call_count == 2

            # Navigate forward (should hit cache)
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
    def test_load_chapter_resets_scroll_percentage(self, mock_resolve_images):
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

        # Load new chapter
        controller._load_chapter(1)

        # Verify scroll percentage reset to 0
        assert controller._current_scroll_percentage == 0.0

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_load_chapter_emits_progress_update(self, mock_resolve_images):
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

        # Load chapter 0 (Chapter 1 for display)
        controller._load_chapter(0)

        # Verify progress signal emitted with 0% scroll
        progress_spy.assert_called_once_with("Chapter 1 of 5 • 0% through chapter")

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_next_chapter_emits_progress_with_zero_scroll(self, mock_resolve_images):
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

        # Navigate to next chapter
        controller.next_chapter()

        # Verify progress shows 0% for new chapter
        emitted_progress = progress_spy.call_args[0][0]
        assert "Chapter 2 of 5 • 0% through chapter" == emitted_progress

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_previous_chapter_emits_progress_with_zero_scroll(self, mock_resolve_images):
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

        # Navigate to previous chapter
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
    def test_memory_check_called_after_chapter_load(self, mock_resolve_images):
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

            # Load a chapter
            controller._load_chapter(0)

            # Verify memory check was called
            mock_check.assert_called_once()

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    @patch('psutil.Process')
    def test_memory_warning_logged_when_threshold_exceeded(
        self, mock_process_class, mock_resolve_images, caplog: "pytest.LogCaptureFixture"
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

        # Load a chapter which will trigger memory check
        with caplog.at_level("WARNING"):
            controller._load_chapter(0)

            # Verify warning was logged
            assert any("exceeds threshold" in record.message for record in caplog.records)

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_memory_check_on_cache_hit(self, mock_resolve_images):
        """Test that memory is checked even on cache hits."""
        mock_resolve_images.side_effect = lambda content, *args, **kwargs: content

        mock_book = MagicMock()
        mock_book.filepath = "/path/to/book.epub"
        mock_book.get_chapter_count.return_value = 5
        mock_book.get_chapter_href.return_value = "text/chapter0.html"
        mock_book.get_chapter_content.return_value = "<p>Chapter content</p>"

        controller = ReaderController()
        controller._book = mock_book

        # Load chapter once to cache it
        with patch.object(controller._cache_manager.memory_monitor, 'check_threshold') as mock_check:
            mock_check.return_value = False
            controller._load_chapter(0)
            first_call_count = mock_check.call_count

        # Load same chapter again (cache hit)
        with patch.object(controller._cache_manager.memory_monitor, 'check_threshold') as mock_check:
            mock_check.return_value = False
            controller._load_chapter(0)
            second_call_count = mock_check.call_count

        # Memory check should be called on both loads
        assert first_call_count == 1
        assert second_call_count == 1

    @patch('ereader.utils.async_loader.resolve_images_in_html')
    def test_memory_monitoring_with_sequential_chapters(self, mock_resolve_images):
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

            # Load multiple chapters sequentially
            for i in range(10):
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
