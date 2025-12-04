"""Tests for BookViewer scroll methods and signal emission.

This module tests the BookViewer class scroll functionality, including
scroll_by_pages, scroll_to_top, scroll_to_bottom, get_scroll_percentage,
and the scroll_position_changed signal.

Uses pytest-qt for Qt widget testing with qtbot fixture.
"""

import pytest

from ereader.views.book_viewer import BookViewer


@pytest.fixture
def viewer(qtbot):
    """Create a BookViewer instance for testing.

    Args:
        qtbot: pytest-qt fixture for Qt widget testing

    Returns:
        BookViewer: A viewer instance managed by qtbot
    """
    viewer = BookViewer()
    qtbot.addWidget(viewer)
    return viewer


@pytest.fixture
def viewer_with_scrollable_content(qtbot, viewer):
    """Create a BookViewer with content that requires scrolling.

    Args:
        qtbot: pytest-qt fixture for Qt widget testing
        viewer: BookViewer fixture

    Returns:
        BookViewer: A viewer with scrollable content
    """
    # Generate long content to ensure scrollbar is active
    long_html = "<html><body>"
    for i in range(200):
        long_html += f"<p>Paragraph {i} with some content to make the chapter scrollable.</p>"
    long_html += "</body></html>"

    viewer.set_content(long_html)
    viewer.show()
    viewer.resize(800, 600)

    # Wait for layout calculation
    qtbot.wait(10)

    # Reset to top after content load
    viewer.scroll_to_top()
    qtbot.wait(10)

    return viewer


class TestBookViewerScrollByPages:
    """Test scroll_by_pages method."""

    def test_scroll_by_pages_down_half_page(self, qtbot, viewer_with_scrollable_content):
        """Test scrolling down by half a page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Start at top
        initial_value = scrollbar.value()
        assert initial_value == scrollbar.minimum()

        # Scroll down half page
        viewer.scroll_by_pages(0.5)
        qtbot.wait(10)

        # Verify scrolled down
        new_value = scrollbar.value()
        expected_scroll = int(0.5 * scrollbar.pageStep())
        assert new_value > initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1  # Allow 1px rounding error

    def test_scroll_by_pages_down_full_page(self, qtbot, viewer_with_scrollable_content):
        """Test scrolling down by a full page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        initial_value = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Scroll down one page
        viewer.scroll_by_pages(1.0)
        qtbot.wait(10)

        new_value = scrollbar.value()
        expected_scroll = page_step
        assert new_value > initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1

    def test_scroll_by_pages_up_half_page(self, qtbot, viewer_with_scrollable_content):
        """Test scrolling up by half a page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # First scroll down to middle
        viewer.scroll_by_pages(2.0)
        qtbot.wait(10)

        initial_value = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Scroll up half page
        viewer.scroll_by_pages(-0.5)
        qtbot.wait(10)

        new_value = scrollbar.value()
        expected_scroll = int(-0.5 * page_step)
        assert new_value < initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1

    def test_scroll_by_pages_up_full_page(self, qtbot, viewer_with_scrollable_content):
        """Test scrolling up by a full page."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # First scroll down
        viewer.scroll_by_pages(2.0)
        qtbot.wait(10)

        initial_value = scrollbar.value()
        page_step = scrollbar.pageStep()

        # Scroll up one page
        viewer.scroll_by_pages(-1.0)
        qtbot.wait(10)

        new_value = scrollbar.value()
        expected_scroll = -page_step
        assert new_value < initial_value
        assert abs(new_value - (initial_value + expected_scroll)) <= 1

    def test_scroll_boundary_clamp_top(self, qtbot, viewer_with_scrollable_content):
        """Test scrolling past top is clamped to minimum."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Ensure at top
        viewer.scroll_to_top()
        qtbot.wait(10)

        minimum = scrollbar.minimum()
        assert scrollbar.value() == minimum

        # Try to scroll past top
        viewer.scroll_by_pages(-1.0)
        qtbot.wait(10)

        # Should still be at minimum
        assert scrollbar.value() == minimum

    def test_scroll_boundary_clamp_bottom(self, qtbot, viewer_with_scrollable_content):
        """Test scrolling past bottom is clamped to maximum."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Scroll to bottom
        viewer.scroll_to_bottom()
        qtbot.wait(10)

        maximum = scrollbar.maximum()
        assert scrollbar.value() == maximum

        # Try to scroll past bottom
        viewer.scroll_by_pages(1.0)
        qtbot.wait(10)

        # Should still be at maximum
        assert scrollbar.value() == maximum


class TestBookViewerScrollToTopBottom:
    """Test scroll_to_top and scroll_to_bottom methods."""

    def test_scroll_to_top(self, qtbot, viewer_with_scrollable_content):
        """Test jumping to top of chapter."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # First scroll to middle
        viewer.scroll_by_pages(2.0)
        qtbot.wait(10)
        assert scrollbar.value() > scrollbar.minimum()

        # Jump to top
        viewer.scroll_to_top()
        qtbot.wait(10)

        assert scrollbar.value() == scrollbar.minimum()

    def test_scroll_to_bottom(self, qtbot, viewer_with_scrollable_content):
        """Test jumping to bottom of chapter."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Ensure not at bottom
        viewer.scroll_to_top()
        qtbot.wait(10)
        assert scrollbar.value() < scrollbar.maximum()

        # Jump to bottom
        viewer.scroll_to_bottom()
        qtbot.wait(10)

        assert scrollbar.value() == scrollbar.maximum()


class TestBookViewerGetScrollPercentage:
    """Test get_scroll_percentage method."""

    def test_get_scroll_percentage_at_top(self, qtbot, viewer_with_scrollable_content):
        """Test percentage calculation at top."""
        viewer = viewer_with_scrollable_content

        viewer.scroll_to_top()
        qtbot.wait(10)

        percentage = viewer.get_scroll_percentage()
        assert percentage == 0.0

    def test_get_scroll_percentage_at_bottom(self, qtbot, viewer_with_scrollable_content):
        """Test percentage calculation at bottom."""
        viewer = viewer_with_scrollable_content

        viewer.scroll_to_bottom()
        qtbot.wait(10)

        percentage = viewer.get_scroll_percentage()
        assert percentage == 100.0

    def test_get_scroll_percentage_in_middle(self, qtbot, viewer_with_scrollable_content):
        """Test percentage calculation in middle of content."""
        viewer = viewer_with_scrollable_content
        scrollbar = viewer._renderer.verticalScrollBar()

        # Set to approximate middle
        middle_value = (scrollbar.minimum() + scrollbar.maximum()) // 2
        scrollbar.setValue(middle_value)
        qtbot.wait(10)

        percentage = viewer.get_scroll_percentage()

        # Should be roughly 50% (allow some tolerance)
        assert 40 <= percentage <= 60

    def test_get_scroll_percentage_no_scroll(self, qtbot, viewer):
        """Test percentage when content fits viewport (no scrolling needed)."""
        # Set short content that doesn't require scrolling
        short_html = "<html><body><p>Short content</p></body></html>"
        viewer.set_content(short_html)
        viewer.show()
        viewer.resize(800, 600)
        qtbot.wait(10)

        scrollbar = viewer._renderer.verticalScrollBar()

        # Verify content is not scrollable
        if scrollbar.maximum() == scrollbar.minimum():
            percentage = viewer.get_scroll_percentage()
            assert percentage == 0.0

    def test_get_scroll_percentage_division_by_zero_protection(self, qtbot, viewer):
        """Test that get_scroll_percentage handles zero range (max == min) correctly.

        This explicitly tests the division by zero protection when
        scrollbar.maximum() == scrollbar.minimum(), which occurs when
        content fits entirely within the viewport.
        """
        # Set minimal content to ensure no scrolling
        minimal_html = "<html><body><p>.</p></body></html>"
        viewer.set_content(minimal_html)
        viewer.show()
        viewer.resize(800, 600)
        qtbot.wait(10)

        scrollbar = viewer._renderer.verticalScrollBar()

        # Explicitly verify we have a zero range (division by zero condition)
        assert scrollbar.maximum() == scrollbar.minimum(), \
            "Test requires non-scrollable content (max == min)"

        # This should NOT raise ZeroDivisionError
        percentage = viewer.get_scroll_percentage()

        # Should return 0.0 for non-scrollable content
        assert percentage == 0.0


class TestBookViewerScrollSignal:
    """Test scroll_position_changed signal emission using pytest-qt."""

    def test_scroll_position_changed_signal_emitted_on_scroll(
        self, qtbot, viewer_with_scrollable_content
    ):
        """Test signal emission when scrolling using qtbot.waitSignal."""
        viewer = viewer_with_scrollable_content

        # Use qtbot.waitSignal for proper signal testing
        with qtbot.waitSignal(viewer.scroll_position_changed, timeout=1000) as blocker:
            viewer.scroll_by_pages(0.5)

        # Verify emitted value is a float between 0 and 100
        emitted_percentage = blocker.args[0]
        assert isinstance(emitted_percentage, float)
        assert 0 <= emitted_percentage <= 100

    def test_scroll_position_changed_signal_on_scroll_to_top(
        self, qtbot, viewer_with_scrollable_content
    ):
        """Test signal emission when jumping to top."""
        viewer = viewer_with_scrollable_content

        # First scroll down
        viewer.scroll_by_pages(2.0)
        qtbot.wait(10)

        # Wait for signal when scrolling to top
        with qtbot.waitSignal(viewer.scroll_position_changed, timeout=1000) as blocker:
            viewer.scroll_to_top()

        # Verify signal was emitted with 0.0
        emitted_percentage = blocker.args[0]
        assert emitted_percentage == 0.0

    def test_scroll_position_changed_signal_on_scroll_to_bottom(
        self, qtbot, viewer_with_scrollable_content
    ):
        """Test signal emission when jumping to bottom."""
        viewer = viewer_with_scrollable_content

        # Wait for signal when scrolling to bottom
        with qtbot.waitSignal(viewer.scroll_position_changed, timeout=1000) as blocker:
            viewer.scroll_to_bottom()

        # Verify signal was emitted with 100.0
        emitted_percentage = blocker.args[0]
        assert emitted_percentage == 100.0

    def test_scroll_position_changed_signal_on_content_change(
        self, qtbot, viewer_with_scrollable_content
    ):
        """Test signal emission when content changes (resets to top)."""
        viewer = viewer_with_scrollable_content

        # Scroll down first
        viewer.scroll_by_pages(2.0)
        qtbot.wait(10)

        # Wait for signal when content changes (should reset scroll to top)
        with qtbot.waitSignal(viewer.scroll_position_changed, timeout=1000):
            new_html = "<html><body><p>New content</p></body></html>"
            viewer.set_content(new_html)
