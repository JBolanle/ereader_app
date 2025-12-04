"""Tests for async chapter loading."""

import pytest
from unittest.mock import Mock, patch

from ereader.models.epub import EPUBBook
from ereader.utils.async_loader import AsyncChapterLoader
from ereader.utils.cache_manager import CacheManager


@pytest.fixture
def mock_book(tmp_path):
    """Create a mock EPUBBook for testing."""
    # Create a minimal EPUB structure
    epub_path = tmp_path / "test.epub"
    epub_path.write_bytes(b"")  # Empty file for now

    book = Mock(spec=EPUBBook)
    book.filepath = str(epub_path)
    book.get_chapter_content = Mock(return_value="<html><body>Test chapter</body></html>")
    book.get_chapter_href = Mock(return_value="chapter1.xhtml")

    return book


@pytest.fixture
def cache_manager():
    """Create a CacheManager for testing."""
    return CacheManager(
        rendered_maxsize=5,
        raw_maxsize=10,
        image_max_memory_mb=10,
        total_memory_threshold_mb=100,
    )


class TestAsyncChapterLoaderInitialization:
    """Tests for AsyncChapterLoader initialization."""

    def test_initialization(self, mock_book, cache_manager, qtbot):
        """Test that loader initializes correctly."""
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

        assert loader._book is mock_book
        assert loader._cache_manager is cache_manager
        assert loader._chapter_index == 0
        assert loader._cancelled is False

    def test_initialization_with_parent(self, mock_book, cache_manager, qtbot):
        """Test that loader initializes with parent QObject."""
        from PyQt6.QtCore import QObject

        parent = QObject()
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0, parent=parent)

        # Parent is set via QThread constructor
        assert loader._book is mock_book
        assert loader.parent() is parent


class TestAsyncChapterLoaderCacheHit:
    """Tests for AsyncChapterLoader with cached content."""

    def test_rendered_cache_hit(self, mock_book, cache_manager, qtbot):
        """Test that cached content loads instantly."""
        # Pre-populate rendered cache
        cache_key = f"{mock_book.filepath}:0"
        cache_manager.rendered_chapters.set(cache_key, "<html>cached</html>")

        # Create loader
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

        # Wait for content_ready signal
        with qtbot.waitSignal(loader.content_ready, timeout=1000) as blocker:
            loader.start()

        # Verify cached content emitted
        assert blocker.args[0] == "<html>cached</html>"

        # Verify book was not accessed (cache hit)
        mock_book.get_chapter_content.assert_not_called()

    def test_raw_cache_hit(self, mock_book, cache_manager, qtbot):
        """Test that raw cached content is re-rendered."""
        # Pre-populate only raw cache
        cache_key = f"{mock_book.filepath}:0"
        raw_html = "<html><body>Raw content</body></html>"
        cache_manager.raw_chapters.set(cache_key, raw_html)

        # Mock image resolution to return input unchanged
        with patch("ereader.utils.async_loader.resolve_images_in_html") as mock_resolve:
            mock_resolve.return_value = "<html><body>Rendered content</body></html>"

            # Create loader
            loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

            # Wait for content_ready signal
            with qtbot.waitSignal(loader.content_ready, timeout=1000) as blocker:
                loader.start()

            # Verify rendered content emitted
            assert blocker.args[0] == "<html><body>Rendered content</body></html>"

            # Verify raw cache was used (book not accessed for content)
            mock_book.get_chapter_content.assert_not_called()

            # Verify image resolution was called
            mock_resolve.assert_called_once_with(raw_html, mock_book, chapter_href="chapter1.xhtml")


class TestAsyncChapterLoaderCacheMiss:
    """Tests for AsyncChapterLoader with no cached content."""

    def test_complete_cache_miss(self, mock_book, cache_manager, qtbot):
        """Test that missing content loads from EPUB."""
        # Mock image resolution
        with patch("ereader.utils.async_loader.resolve_images_in_html") as mock_resolve:
            mock_resolve.return_value = "<html><body>Resolved content</body></html>"

            # Create loader
            loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

            # Wait for content_ready signal
            with qtbot.waitSignal(loader.content_ready, timeout=1000) as blocker:
                loader.start()

            # Verify resolved content emitted
            assert blocker.args[0] == "<html><body>Resolved content</body></html>"

            # Verify book was accessed
            mock_book.get_chapter_content.assert_called_once_with(0)

            # Verify image resolution was called
            mock_resolve.assert_called_once()

    def test_cache_population(self, mock_book, cache_manager, qtbot):
        """Test that both caches are populated after load."""
        # Mock image resolution
        with patch("ereader.utils.async_loader.resolve_images_in_html") as mock_resolve:
            mock_resolve.return_value = "<html><body>Resolved content</body></html>"

            # Create loader
            loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

            # Wait for content_ready signal
            with qtbot.waitSignal(loader.content_ready, timeout=1000):
                loader.start()

            # Verify caches were populated
            cache_key = f"{mock_book.filepath}:0"
            assert cache_manager.raw_chapters.get(cache_key) is not None
            assert cache_manager.rendered_chapters.get(cache_key) == "<html><body>Resolved content</body></html>"


class TestAsyncChapterLoaderCancellation:
    """Tests for AsyncChapterLoader cancellation."""

    def test_cancel_before_start(self, mock_book, cache_manager, qtbot):
        """Test that cancelling before start prevents loading."""
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)
        loader.cancel()  # Cancel immediately

        # Start the thread
        loader.start()
        loader.wait(500)  # Wait for thread to finish

        # Verify book was not accessed
        mock_book.get_chapter_content.assert_not_called()

    def test_cancel_during_load(self, mock_book, cache_manager, qtbot):
        """Test that cancellation aborts loading gracefully."""
        # Make get_chapter_content slow to allow cancellation
        def slow_load(index):
            import time
            time.sleep(0.1)
            return "<html>slow content</html>"

        mock_book.get_chapter_content.side_effect = slow_load

        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)
        loader.start()

        # Cancel immediately after start
        loader.cancel()

        # Wait for thread to finish
        loader.wait(1000)

        # Thread should complete (cooperative cancellation)
        assert not loader.isRunning()


class TestAsyncChapterLoaderErrorHandling:
    """Tests for AsyncChapterLoader error handling."""

    def test_book_read_error(self, mock_book, cache_manager, qtbot):
        """Test that errors emit error_occurred signal."""
        # Make get_chapter_content raise an exception
        mock_book.get_chapter_content.side_effect = RuntimeError("Failed to read EPUB")

        # Create loader
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

        # Wait for error_occurred signal
        with qtbot.waitSignal(loader.error_occurred, timeout=1000) as blocker:
            loader.start()

        # Verify error title and message
        title, message = blocker.args
        assert title == "Chapter Load Error"
        assert "Failed to load chapter 1" in message
        assert "Failed to read EPUB" in message

    def test_image_resolution_error(self, mock_book, cache_manager, qtbot):
        """Test that image resolution errors are handled."""
        # Mock image resolution to raise an exception
        with patch("ereader.utils.async_loader.resolve_images_in_html") as mock_resolve:
            mock_resolve.side_effect = ValueError("Invalid image data")

            # Create loader
            loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

            # Wait for error_occurred signal
            with qtbot.waitSignal(loader.error_occurred, timeout=1000) as blocker:
                loader.start()

            # Verify error was emitted
            title, message = blocker.args
            assert title == "Chapter Load Error"
            assert "Invalid image data" in message

    def test_invalid_chapter_index(self, mock_book, cache_manager, qtbot):
        """Test handling of invalid chapter index."""
        # Make get_chapter_href raise an exception for invalid index
        mock_book.get_chapter_href.side_effect = IndexError("Chapter index out of range")

        # Create loader with invalid index
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=999)

        # Wait for error_occurred signal
        with qtbot.waitSignal(loader.error_occurred, timeout=1000) as blocker:
            loader.start()

        # Verify error was emitted
        title, message = blocker.args
        assert title == "Chapter Load Error"
        assert "Chapter index out of range" in message


class TestAsyncChapterLoaderSignals:
    """Tests for AsyncChapterLoader signals."""

    def test_content_ready_signal_args(self, mock_book, cache_manager, qtbot):
        """Test that content_ready signal has correct arguments."""
        # Pre-populate cache
        cache_key = f"{mock_book.filepath}:0"
        test_html = "<html><body>Signal test</body></html>"
        cache_manager.rendered_chapters.set(cache_key, test_html)

        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

        # Wait for signal with blocker to capture args
        with qtbot.waitSignal(loader.content_ready, timeout=1000) as blocker:
            loader.start()

        # Verify signal args
        assert len(blocker.args) == 1
        assert blocker.args[0] == test_html

    def test_error_signal_args(self, mock_book, cache_manager, qtbot):
        """Test that error_occurred signal has correct arguments."""
        mock_book.get_chapter_content.side_effect = RuntimeError("Test error")

        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

        # Wait for error signal
        with qtbot.waitSignal(loader.error_occurred, timeout=1000) as blocker:
            loader.start()

        # Verify signal args (title, message)
        assert len(blocker.args) == 2
        assert isinstance(blocker.args[0], str)  # title
        assert isinstance(blocker.args[1], str)  # message

    def test_finished_signal(self, mock_book, cache_manager, qtbot):
        """Test that finished signal is emitted when thread completes."""
        # Pre-populate cache for fast completion
        cache_key = f"{mock_book.filepath}:0"
        cache_manager.rendered_chapters.set(cache_key, "<html>test</html>")

        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)

        # Wait for finished signal (QThread built-in signal)
        with qtbot.waitSignal(loader.finished, timeout=1000):
            loader.start()

        # Thread should not be running
        assert not loader.isRunning()


class TestAsyncChapterLoaderThreadSafety:
    """Tests for thread safety of AsyncChapterLoader."""

    def test_concurrent_cache_access(self, mock_book, cache_manager, qtbot):
        """Test that cache can be accessed concurrently from UI and loader thread."""
        # Start loader in background
        loader = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)
        loader.start()

        # Access cache from UI thread while loader is running
        cache_key = f"{mock_book.filepath}:1"
        cache_manager.rendered_chapters.set(cache_key, "<html>ui thread</html>")

        # Wait for loader to finish
        loader.wait(1000)

        # Verify both operations succeeded
        assert cache_manager.rendered_chapters.get(cache_key) == "<html>ui thread</html>"

    def test_multiple_sequential_loads(self, mock_book, cache_manager, qtbot):
        """Test that multiple sequential loads work correctly."""
        with patch("ereader.utils.async_loader.resolve_images_in_html") as mock_resolve:
            mock_resolve.return_value = "<html>resolved</html>"

            # Load chapter 0
            loader1 = AsyncChapterLoader(mock_book, cache_manager, chapter_index=0)
            with qtbot.waitSignal(loader1.content_ready, timeout=1000):
                loader1.start()

            # Load chapter 1
            loader2 = AsyncChapterLoader(mock_book, cache_manager, chapter_index=1)
            with qtbot.waitSignal(loader2.content_ready, timeout=1000):
                loader2.start()

            # Verify both chapters were loaded
            assert cache_manager.rendered_chapters.get(f"{mock_book.filepath}:0") is not None
            assert cache_manager.rendered_chapters.get(f"{mock_book.filepath}:1") is not None
