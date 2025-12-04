"""Tests for BookViewer scroll methods and signal emission.

This module tests the BookViewer class scroll functionality, including
scroll_by_pages, scroll_to_top, scroll_to_bottom, get_scroll_percentage,
and the scroll_position_changed signal.
"""

from unittest.mock import Mock

import pytest
from PyQt6.QtWidgets import QApplication

from ereader.views.book_viewer import BookViewer


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def viewer(qapp):
    """Create a BookViewer instance for testing."""
    return BookViewer()


@pytest.fixture
def viewer_with_scrollable_content(viewer):
    """Create a BookViewer with content that requires scrolling."""
    # Generate long content to ensure scrollbar is active
    long_html = "<html><body>"
    for i in range(200):
        long_html += f"<p>Paragraph {i} with some content to make the chapter scrollable.</p>"
    long_html += "</body></html>"

    viewer.set_content(long_html)
    viewer.show()
    viewer.resize(800, 600)

    # Force layout calculation
    QApplication.processEvents()

    # Reset to top after content load
    viewer.scroll_to_top()
    QApplication.processEvents()

    return viewer


class TestBookViewerScrollByPages:
    """Test scroll_by_pages method."""

    def test_scroll_by_pages_down_half_page(self, viewer_with_scrollable_content):
        """Test scrolling down by half a page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Start at top
        initial_value = scrollbar.value()
        assert initial_value == scrollbar.minimum()

        # Scroll down half page
        viewer.scroll_by_pages(0.5)
        QApplication.processEvents()

        # Verify scrolled down
        new_value = scrollbar.value()
        expected_scroll = int(0.5 * scrollbar.pageStep())
        assert new_value > initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1  # Allow 1px rounding error

    def test_scroll_by_pages_down_full_page(self, viewer_with_scrollable_content):
        """Test scrolling down by a full page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        initial_value = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Scroll down one page
        viewer.scroll_by_pages(1.0)
        QApplication.processEvents()

        new_value = scrollbar.value()
        expected_scroll = page_step
        assert new_value > initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1

    def test_scroll_by_pages_up_half_page(self, viewer_with_scrollable_content):
        """Test scrolling up by half a page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # First scroll down to middle
        viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        initial_value = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Scroll up half page
        viewer.scroll_by_pages(-0.5)
        QApplication.processEvents()

        new_value = scrollbar.value()
        expected_scroll = int(-0.5 * page_step)
        assert new_value < initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1

    def test_scroll_by_pages_up_full_page(self, viewer_with_scrollable_content):
        """Test scrolling up by a full page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # First scroll down
        viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        initial_value = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Scroll up one page
        viewer.scroll_by_pages(-1.0)
        QApplication.processEvents()

        new_value = scrollbar.value()
        expected_scroll = -page_step
        assert new_value < initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1

    def test_scroll_boundary_clamp_top(self, viewer_with_scrollable_content):
        """Test scrolling past top is clamped to minimum."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Ensure at top
        viewer.scroll_to_top()
        QApplication.processEvents()

        minimum = scrollbar.minimum()
        assert scrollbar.value() == minimum

        # Try to scroll past top
        viewer.scroll_by_pages(-1.0)
        QApplication.processEvents()

        # Should still be at minimum
        assert scrollbar.value() == minimum

    def test_scroll_boundary_clamp_bottom(self, viewer_with_scrollable_content):
        """Test scrolling past bottom is clamped to maximum."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Scroll to bottom
        viewer.scroll_to_bottom()
        QApplication.processEvents()

        maximum = scrollbar.maximum()
        assert scrollbar.value() == maximum

        # Try to scroll past bottom
        viewer.scroll_by_pages(1.0)
        QApplication.processEvents()

        # Should still be at maximum
        assert scrollbar.value() == maximum


class TestBookViewerScrollToTopBottom:
    """Test scroll_to_top and scroll_to_bottom methods."""

    def test_scroll_to_top(self, viewer_with_scrollable_content):
        """Test jumping to top of chapter."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # First scroll to middle
        viewer.scroll_by_pages(2.0)
        QApplication.processEvents()
        assert scrollbar.value() > scrollbar.minimum()

        # Jump to top
        viewer.scroll_to_top()
        QApplication.processEvents()

        assert scrollbar.value() == scrollbar.minimum()

    def test_scroll_to_bottom(self, viewer_with_scrollable_content):
        """Test jumping to bottom of chapter."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Ensure not at bottom
        viewer.scroll_to_top()
        QApplication.processEvents()
        assert scrollbar.value() < scrollbar.maximum()

        # Jump to bottom
        viewer.scroll_to_bottom()
        QApplication.processEvents()

        assert scrollbar.value() == scrollbar.maximum()


class TestBookViewerGetScrollPercentage:
    """Test get_scroll_percentage method."""

    def test_get_scroll_percentage_at_top(self, viewer_with_scrollable_content):
        """Test percentage calculation at top."""
        viewer = viewer_with_scrollable_content

        viewer.scroll_to_top()
        QApplication.processEvents()

        percentage = viewer.get_scroll_percentage()
        assert percentage == 0.0

    def test_get_scroll_percentage_at_bottom(self, viewer_with_scrollable_content):
        """Test percentage calculation at bottom."""
        viewer = viewer_with_scrollable_content

        viewer.scroll_to_bottom()
        QApplication.processEvents()

        percentage = viewer.get_scroll_percentage()
        assert percentage == 100.0

    def test_get_scroll_percentage_in_middle(self, viewer_with_scrollable_content):
        """Test percentage calculation in middle of content."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Set to approximate middle
        middle_value = (scrollbar.minimum() + scrollbar.maximum()) // 2
        scrollbar.setValue(middle_value)
        QApplication.processEvents()

        percentage = viewer.get_scroll_percentage()

        # Should be roughly 50% (allow some tolerance)
        assert 40 <= percentage <= 60

    def test_get_scroll_percentage_no_scroll(self, viewer):
        """Test percentage when content fits viewport (no scrolling needed)."""
        # Set short content that doesn't require scrolling
        short_html = "<html><body><p>Short content</p></body></html>"
        viewer.set_content(short_html)
        viewer.show()
        viewer.resize(800, 600)
        QApplication.processEvents()

        scrollbar = viewer._renderer.verticalScrollBar()

        # Verify content is not scrollable
        if scrollbar.maximum() == scrollbar.minimum():
            percentage = viewer.get_scroll_percentage()
            assert percentage == 0.0


class TestBookViewerScrollSignal:
    """Test scroll_position_changed signal emission."""

    def test_scroll_position_changed_signal_emitted_on_scroll(self, viewer_with_scrollable_content):
        """Test signal emission when scrolling."""
        viewer = viewer_with_scrollable_content

        # Setup signal spy
        signal_spy = Mock()
        viewer.scroll_position_changed.connect(signal_spy)

        # Clear any emissions from setup
        signal_spy.reset_mock()

        # Scroll down
        viewer.scroll_by_pages(0.5)
        QApplication.processEvents()

        # Verify signal was emitted
        assert signal_spy.call_count > 0

        # Verify emitted value is a float between 0 and 100
        emitted_percentage = signal_spy.call_args[0][0]
        assert isinstance(emitted_percentage, float)
        assert 0 <= emitted_percentage <= 100

    def test_scroll_position_changed_signal_on_scroll_to_top(self, viewer_with_scrollable_content):
        """Test signal emission when jumping to top."""
        viewer = viewer_with_scrollable_content

        # First scroll down
        viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        # Setup signal spy
        signal_spy = Mock()
        viewer.scroll_position_changed.connect(signal_spy)

        # Jump to top
        viewer.scroll_to_top()
        QApplication.processEvents()

        # Verify signal was emitted with 0.0
        assert signal_spy.called
        emitted_percentage = signal_spy.call_args[0][0]
        assert emitted_percentage == 0.0

    def test_scroll_position_changed_signal_on_scroll_to_bottom(self, viewer_with_scrollable_content):
        """Test signal emission when jumping to bottom."""
        viewer = viewer_with_scrollable_content

        # Setup signal spy
        signal_spy = Mock()
        viewer.scroll_position_changed.connect(signal_spy)

        # Clear any emissions from setup
        signal_spy.reset_mock()

        # Jump to bottom
        viewer.scroll_to_bottom()
        QApplication.processEvents()

        # Verify signal was emitted with 100.0
        assert signal_spy.called
        emitted_percentage = signal_spy.call_args[0][0]
        assert emitted_percentage == 100.0

    def test_scroll_position_changed_signal_on_content_change(self, viewer_with_scrollable_content):
        """Test signal emission when content changes (resets to top)."""
        viewer = viewer_with_scrollable_content

        # Scroll down first
        viewer.scroll_by_pages(2.0)
        QApplication.processEvents()

        # Setup signal spy
        signal_spy = Mock()
        viewer.scroll_position_changed.connect(signal_spy)

        # Change content (should reset scroll to top)
        new_html = "<html><body><p>New content</p></body></html>"
        viewer.set_content(new_html)
        QApplication.processEvents()

        # Verify signal was emitted (content change triggers scroll reset)
        assert signal_spy.called
