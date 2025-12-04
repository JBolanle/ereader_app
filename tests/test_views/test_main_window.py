"""Integration tests for MainWindow keyboard navigation and signal chain.

This module tests the complete integration of keyboard shortcuts and the
signal chain from BookViewer → ReaderController → MainWindow, ensuring
that all components work together correctly.
"""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from ereader.views.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp):
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    yield window
    window.close()


@pytest.fixture
def main_window_with_book(main_window):
    """Create a MainWindow with a mock book loaded."""
    # Create mock book
    mock_book = MagicMock()
    mock_book.filepath = "/path/to/test.epub"
    mock_book.title = "Test Book"
    mock_book.authors = ["Test Author"]
    mock_book.get_chapter_count.return_value = 5
    mock_book.get_chapter_href.return_value = "text/chapter0.html"
    mock_book.get_chapter_content.return_value = "<html><body><p>Test content</p></body></html>"

    # Set mock book in controller
    main_window._controller._book = mock_book
    main_window._controller._current_chapter_index = 2  # Chapter 3

    # Set scrollable content in viewer
    long_html = "<html><body>"
    for i in range(200):
        long_html += f"<p>Paragraph {i} with scrollable content.</p>"
    long_html += "</body></html>"
    main_window._book_viewer.set_content(long_html)
    main_window.show()
    main_window.resize(800, 600)

    # Process events to ensure layout is calculated
    QApplication.processEvents()

    # Reset to top
    main_window._book_viewer.scroll_to_top()
    QApplication.processEvents()

    return main_window


class TestMainWindowSignalChain:
    """Test the complete signal chain for scroll position updates."""

    def test_scroll_updates_status_bar_via_signal_chain(self, main_window_with_book):
        """Test that scrolling updates status bar through full signal chain.

        Tests the complete flow:
        BookViewer scroll → emit scroll_position_changed →
        Controller.on_scroll_changed → emit reading_progress_changed →
        MainWindow._on_progress_changed → update status bar
        """
        window = main_window_with_book

        # Scroll down in BookViewer
        window._book_viewer.scroll_by_pages(0.5)
        QApplication.processEvents()

        # Verify status bar updated with progress string
        status_text = window.statusBar().currentMessage()
        assert "Chapter 3 of 5" in status_text
        assert "%" in status_text
        assert "through chapter" in status_text

    def test_scroll_to_bottom_updates_status_bar(self, main_window_with_book):
        """Test that scrolling to bottom shows 100% in status bar."""
        window = main_window_with_book

        # Scroll to bottom
        window._book_viewer.scroll_to_bottom()
        QApplication.processEvents()

        # Verify status bar shows 100%
        status_text = window.statusBar().currentMessage()
        assert "Chapter 3 of 5 • 100% through chapter" in status_text

    def test_scroll_to_top_updates_status_bar(self, main_window_with_book):
        """Test that scrolling to top shows 0% in status bar."""
        window = main_window_with_book

        # First scroll down
        window._book_viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        # Then scroll to top
        window._book_viewer.scroll_to_top()
        QApplication.processEvents()

        # Verify status bar shows 0%
        status_text = window.statusBar().currentMessage()
        assert "Chapter 3 of 5 • 0% through chapter" in status_text

    @patch('ereader.controllers.reader_controller.resolve_images_in_html')
    def test_chapter_navigation_resets_scroll_percentage(self, mock_resolve, main_window_with_book):
        """Test that navigating chapters resets scroll to 0% in status bar."""
        mock_resolve.side_effect = lambda content, *args, **kwargs: content
        window = main_window_with_book

        # Scroll down in current chapter
        window._book_viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        # Verify not at 0%
        status_text = window.statusBar().currentMessage()
        assert "0% through chapter" not in status_text

        # Navigate to next chapter
        window._controller.next_chapter()
        QApplication.processEvents()

        # Verify status shows new chapter at 0%
        status_text = window.statusBar().currentMessage()
        assert "Chapter 4 of 5 • 0% through chapter" in status_text


class TestMainWindowKeyboardShortcuts:
    """Test keyboard shortcuts are properly wired to actions.

    Note: These tests verify that the methods connected to shortcuts work correctly.
    Direct QTest.keyPress() doesn't reliably trigger QShortcut in headless tests,
    so we test the underlying functionality that shortcuts invoke.
    """

    def test_down_arrow_scrolls_viewer(self, main_window_with_book):
        """Test scroll down action (triggered by Down arrow shortcut)."""
        window = main_window_with_book
        scrollbar = window._book_viewer._renderer.verticalScrollBar()

        # Get initial scroll position
        initial_scroll = scrollbar.value()

        # Directly call the method that Down arrow shortcut triggers
        window._book_viewer.scroll_by_pages(0.5)
        QApplication.processEvents()

        # Verify scrolled down
        final_scroll = scrollbar.value()
        assert final_scroll > initial_scroll

    def test_up_arrow_scrolls_viewer(self, main_window_with_book):
        """Test scroll up action (triggered by Up arrow shortcut)."""
        window = main_window_with_book

        # First scroll down to have room to scroll up
        window._book_viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        scrollbar = window._book_viewer._renderer.verticalScrollBar()
        initial_scroll = scrollbar.value()

        # Directly call the method that Up arrow shortcut triggers
        window._book_viewer.scroll_by_pages(-0.5)
        QApplication.processEvents()

        # Verify scrolled up
        final_scroll = scrollbar.value()
        assert final_scroll < initial_scroll

    def test_page_down_scrolls_full_page(self, main_window_with_book):
        """Test page down action (triggered by PageDown shortcut)."""
        window = main_window_with_book
        scrollbar = window._book_viewer._renderer.verticalScrollBar()

        initial_scroll = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Directly call the method that PageDown shortcut triggers
        window._book_viewer.scroll_by_pages(1.0)
        QApplication.processEvents()

        # Verify scrolled down by approximately one page
        final_scroll = scrollbar.value()
        scroll_amount = final_scroll - initial_scroll
        # Allow some tolerance for rounding
        assert abs(scroll_amount - page_step) <= 2

    def test_page_up_scrolls_full_page(self, main_window_with_book):
        """Test page up action (triggered by PageUp shortcut)."""
        window = main_window_with_book

        # First scroll down
        window._book_viewer.scroll_by_pages(3.0)
        QApplication.processEvents()

        scrollbar = window._book_viewer._renderer.verticalScrollBar()
        initial_scroll = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Directly call the method that PageUp shortcut triggers
        window._book_viewer.scroll_by_pages(-1.0)
        QApplication.processEvents()

        # Verify scrolled up by approximately one page
        final_scroll = scrollbar.value()
        scroll_amount = initial_scroll - final_scroll
        assert abs(scroll_amount - page_step) <= 2

    def test_home_jumps_to_top(self, main_window_with_book):
        """Test jump to top action (triggered by Home key shortcut)."""
        window = main_window_with_book

        # Scroll down first
        window._book_viewer.scroll_by_pages(3.0)
        QApplication.processEvents()

        scrollbar = window._book_viewer._renderer.verticalScrollBar()
        assert scrollbar.value() > scrollbar.minimum()

        # Directly call the method that Home shortcut triggers
        window._book_viewer.scroll_to_top()
        QApplication.processEvents()

        # Verify at top
        assert scrollbar.value() == scrollbar.minimum()

    def test_end_jumps_to_bottom(self, main_window_with_book):
        """Test jump to bottom action (triggered by End key shortcut)."""
        window = main_window_with_book
        scrollbar = window._book_viewer._renderer.verticalScrollBar()

        # Ensure not at bottom
        window._book_viewer.scroll_to_top()
        QApplication.processEvents()
        assert scrollbar.value() < scrollbar.maximum()

        # Directly call the method that End shortcut triggers
        window._book_viewer.scroll_to_bottom()
        QApplication.processEvents()

        # Verify at bottom
        assert scrollbar.value() == scrollbar.maximum()

    @patch('ereader.controllers.reader_controller.resolve_images_in_html')
    def test_right_arrow_navigates_to_next_chapter(self, mock_resolve, main_window_with_book):
        """Test next chapter navigation (triggered by Right arrow shortcut)."""
        mock_resolve.side_effect = lambda content, *args, **kwargs: content
        window = main_window_with_book

        # Current chapter is 3 (index 2)
        assert window._controller._current_chapter_index == 2

        # Directly call the method that Right arrow shortcut triggers
        window._controller.next_chapter()
        QApplication.processEvents()

        # Verify navigated to next chapter
        assert window._controller._current_chapter_index == 3

    @patch('ereader.controllers.reader_controller.resolve_images_in_html')
    def test_left_arrow_navigates_to_previous_chapter(self, mock_resolve, main_window_with_book):
        """Test previous chapter navigation (triggered by Left arrow shortcut)."""
        mock_resolve.side_effect = lambda content, *args, **kwargs: content
        window = main_window_with_book

        # Current chapter is 3 (index 2)
        assert window._controller._current_chapter_index == 2

        # Directly call the method that Left arrow shortcut triggers
        window._controller.previous_chapter()
        QApplication.processEvents()

        # Verify navigated to previous chapter
        assert window._controller._current_chapter_index == 1


class TestMainWindowKeyboardShortcutBoundaries:
    """Test keyboard shortcuts respect boundaries."""

    def test_previous_chapter_at_first_chapter_does_nothing(self, main_window):
        """Test previous chapter navigation at first chapter (Left arrow boundary)."""
        # Setup book at first chapter
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/test.epub"
        mock_book.get_chapter_count.return_value = 5

        main_window._controller._book = mock_book
        main_window._controller._current_chapter_index = 0  # First chapter

        # Try to navigate to previous chapter (what Left arrow would trigger)
        main_window._controller.previous_chapter()
        QApplication.processEvents()

        # Verify still at first chapter
        assert main_window._controller._current_chapter_index == 0

    def test_next_chapter_at_last_chapter_does_nothing(self, main_window):
        """Test next chapter navigation at last chapter (Right arrow boundary)."""
        # Setup book at last chapter
        mock_book = MagicMock()
        mock_book.filepath = "/path/to/test.epub"
        mock_book.get_chapter_count.return_value = 5

        main_window._controller._book = mock_book
        main_window._controller._current_chapter_index = 4  # Last chapter (0-indexed)

        # Try to navigate to next chapter (what Right arrow would trigger)
        main_window._controller.next_chapter()
        QApplication.processEvents()

        # Verify still at last chapter
        assert main_window._controller._current_chapter_index == 4
