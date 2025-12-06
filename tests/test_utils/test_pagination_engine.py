"""Tests for the pagination engine.

This module tests the PaginationEngine class which calculates page breaks
and manages page navigation within chapters.
"""

import pytest

from ereader.utils.pagination_engine import PageBreaks, PaginationEngine


class TestPageBreaks:
    """Test the PageBreaks dataclass."""

    def test_page_breaks_creation(self) -> None:
        """Test creating a PageBreaks instance."""
        breaks = PageBreaks(
            viewport_height=800,
            content_height=2400,
            page_breaks=[0, 800, 1600, 2400],
        )
        assert breaks.viewport_height == 800
        assert breaks.content_height == 2400
        assert breaks.page_breaks == [0, 800, 1600, 2400]

    def test_page_count_property(self) -> None:
        """Test page_count property calculation."""
        breaks = PageBreaks(
            viewport_height=800,
            content_height=2400,
            page_breaks=[0, 800, 1600, 2400],
        )
        # Page count = number of page break positions
        assert breaks.page_count == 4


class TestPaginationEngine:
    """Test the PaginationEngine class."""

    def test_initialization(self) -> None:
        """Test engine initializes with no page breaks."""
        engine = PaginationEngine()
        assert engine._page_breaks is None

    def test_calculate_page_breaks_single_page(self) -> None:
        """Test pagination when content fits in single viewport."""
        engine = PaginationEngine()
        breaks = engine.calculate_page_breaks(
            content_height=500, viewport_height=800
        )

        # Content shorter than viewport = single page
        # Breaks at: [0 (start), 500 (end)]
        assert breaks.viewport_height == 800
        assert breaks.content_height == 500
        assert breaks.page_breaks == [0, 500]
        assert breaks.page_count == 2

    def test_calculate_page_breaks_exact_multiple(self) -> None:
        """Test pagination when content is exact multiple of viewport."""
        engine = PaginationEngine()
        breaks = engine.calculate_page_breaks(
            content_height=2400, viewport_height=800
        )

        # 2400 / 800 = 3 pages exactly
        # Breaks at: [0, 800, 1600, 2400]
        assert breaks.page_breaks == [0, 800, 1600, 2400]
        assert breaks.page_count == 4

    def test_calculate_page_breaks_multiple_pages(self) -> None:
        """Test pagination with multiple pages (not exact multiple)."""
        engine = PaginationEngine()
        breaks = engine.calculate_page_breaks(
            content_height=2500, viewport_height=800
        )

        # 2500 / 800 = 3.125 pages
        # Breaks at: [0, 800, 1600, 2400, 2500]
        assert breaks.page_breaks == [0, 800, 1600, 2400, 2500]
        assert breaks.page_count == 5

    def test_calculate_page_breaks_updates_internal_state(self) -> None:
        """Test that calculate_page_breaks updates internal state."""
        engine = PaginationEngine()
        assert engine._page_breaks is None

        breaks = engine.calculate_page_breaks(
            content_height=1600, viewport_height=800
        )

        # Internal state should be updated
        assert engine._page_breaks is breaks
        assert engine._page_breaks is not None

    def test_get_page_number_no_calculation(self) -> None:
        """Test get_page_number returns 0 when no calculation done."""
        engine = PaginationEngine()
        assert engine.get_page_number(500) == 0

    def test_get_page_number_from_scroll(self) -> None:
        """Test converting scroll position to page number."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2500, viewport_height=800)

        # Page breaks: [0, 800, 1600, 2400, 2500]
        # Page numbers are 0-indexed
        assert engine.get_page_number(0) == 0  # First page
        assert engine.get_page_number(400) == 0  # Middle of first page
        assert engine.get_page_number(799) == 0  # End of first page
        assert engine.get_page_number(800) == 1  # Start of second page
        assert engine.get_page_number(1500) == 1  # Middle of second page
        assert engine.get_page_number(1600) == 2  # Start of third page
        assert engine.get_page_number(2400) == 3  # Start of fourth page
        assert engine.get_page_number(2500) == 3  # End of content

    def test_get_page_number_beyond_content(self) -> None:
        """Test get_page_number with scroll position beyond content."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2400, viewport_height=800)

        # Should return last page for positions beyond content
        assert engine.get_page_number(5000) == 2  # Last page (0-indexed)

    def test_get_scroll_position_for_page_no_calculation(self) -> None:
        """Test get_scroll_position_for_page returns 0 when no calculation."""
        engine = PaginationEngine()
        assert engine.get_scroll_position_for_page(0) == 0
        assert engine.get_scroll_position_for_page(5) == 0

    def test_get_scroll_position_for_page(self) -> None:
        """Test converting page number to scroll position."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2500, viewport_height=800)

        # Page breaks: [0, 800, 1600, 2400, 2500]
        assert engine.get_scroll_position_for_page(0) == 0
        assert engine.get_scroll_position_for_page(1) == 800
        assert engine.get_scroll_position_for_page(2) == 1600
        assert engine.get_scroll_position_for_page(3) == 2400

    def test_get_scroll_position_invalid_page_negative(self) -> None:
        """Test get_scroll_position_for_page with negative page number."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2400, viewport_height=800)

        # Should log warning and return 0
        assert engine.get_scroll_position_for_page(-1) == 0

    def test_get_scroll_position_invalid_page_too_high(self) -> None:
        """Test get_scroll_position_for_page with page number too high."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2400, viewport_height=800)

        # Page breaks: [0, 800, 1600, 2400]
        # Valid pages: 0, 1, 2 (last break is end marker)
        # Page 3 is invalid
        assert engine.get_scroll_position_for_page(3) == 0

    def test_get_page_count_no_calculation(self) -> None:
        """Test get_page_count returns 0 when no calculation done."""
        engine = PaginationEngine()
        assert engine.get_page_count() == 0

    def test_get_page_count(self) -> None:
        """Test get_page_count returns correct count."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2500, viewport_height=800)

        # Page breaks: [0, 800, 1600, 2400, 2500]
        # Pages: 0, 1, 2, 3 = 4 pages (last break is end marker)
        assert engine.get_page_count() == 4

    def test_get_page_count_single_page(self) -> None:
        """Test get_page_count with single page."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=500, viewport_height=800)

        # Page breaks: [0, 500]
        # Pages: 0 = 1 page
        assert engine.get_page_count() == 1

    def test_needs_recalculation_no_calculation(self) -> None:
        """Test needs_recalculation returns True when no calculation done."""
        engine = PaginationEngine()
        assert engine.needs_recalculation(800) is True

    def test_needs_recalculation_same_height(self) -> None:
        """Test needs_recalculation with same viewport height."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2400, viewport_height=800)

        # Same height = no recalculation needed
        assert engine.needs_recalculation(800) is False

    def test_needs_recalculation_different_height(self) -> None:
        """Test needs_recalculation with different viewport height."""
        engine = PaginationEngine()
        engine.calculate_page_breaks(content_height=2400, viewport_height=800)

        # Different height = recalculation needed
        assert engine.needs_recalculation(900) is True
        assert engine.needs_recalculation(700) is True

    def test_recalculation_updates_page_breaks(self) -> None:
        """Test that recalculating updates page breaks correctly."""
        engine = PaginationEngine()

        # First calculation
        breaks1 = engine.calculate_page_breaks(
            content_height=2400, viewport_height=800
        )
        assert breaks1.page_breaks == [0, 800, 1600, 2400]

        # Recalculate with different viewport
        breaks2 = engine.calculate_page_breaks(
            content_height=2400, viewport_height=600
        )
        assert breaks2.page_breaks == [0, 600, 1200, 1800, 2400]

        # Internal state updated
        assert engine._page_breaks is breaks2
        assert engine.get_page_count() == 4
