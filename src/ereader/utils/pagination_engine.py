"""Pagination engine for calculating page breaks within chapters.

This module provides the PaginationEngine class which manages the calculation
of page boundaries based on viewport height and content height. It converts
between scroll positions and page numbers for discrete page navigation.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PageBreaks:
    """Page break information for a chapter.

    Attributes:
        viewport_height: Height of the visible viewport in pixels.
        content_height: Total height of the chapter content in pixels.
        page_breaks: List of scroll positions for each page start and end.
    """

    viewport_height: int
    content_height: int
    page_breaks: list[int]

    @property
    def page_count(self) -> int:
        """Number of page break positions in this chapter.

        Returns:
            Number of page break positions (including start and end).
        """
        return len(self.page_breaks)


class PaginationEngine:
    """Engine for calculating page boundaries within chapters.

    This class manages the calculation of page breaks based on viewport
    height and content height. It provides methods to convert between
    scroll positions and page numbers for discrete page navigation.

    The pagination uses a simple algorithm: divide content into viewport-sized
    chunks. Page breaks may occur mid-paragraph (not perfect typography), but
    this is acceptable for a learning project focused on state management.
    """

    def __init__(self) -> None:
        """Initialize the pagination engine."""
        self._page_breaks: PageBreaks | None = None

    def calculate_page_breaks(
        self, content_height: int, viewport_height: int
    ) -> PageBreaks:
        """Calculate page break positions for given dimensions.

        Divides the content into viewport-sized pages and calculates the
        scroll position for each page boundary. The algorithm creates pages
        by incrementing by viewport_height until reaching content_height.

        Args:
            content_height: Total height of the chapter content in pixels.
            viewport_height: Height of the visible viewport in pixels.

        Returns:
            PageBreaks object with calculated break positions.
        """
        page_breaks = [0]  # First page always starts at 0
        current_pos = 0

        # Calculate page breaks at viewport_height intervals
        while current_pos + viewport_height < content_height:
            current_pos += viewport_height
            page_breaks.append(current_pos)

        # Last page break at content height (end marker)
        if page_breaks[-1] != content_height:
            page_breaks.append(content_height)

        self._page_breaks = PageBreaks(
            viewport_height=viewport_height,
            content_height=content_height,
            page_breaks=page_breaks,
        )

        logger.debug(
            "Calculated %d pages (viewport: %dpx, content: %dpx)",
            len(page_breaks) - 1,  # -1 because last break is end marker
            viewport_height,
            content_height,
        )

        return self._page_breaks

    def get_page_number(self, scroll_position: int) -> int:
        """Get page number from scroll position (0-indexed).

        Finds which page the given scroll position belongs to by comparing
        against the calculated page breaks.

        Args:
            scroll_position: Current scroll position in pixels.

        Returns:
            Page number (0-indexed). Returns 0 if no calculation done.
        """
        if self._page_breaks is None:
            return 0

        # Find the page this scroll position belongs to
        for i in range(len(self._page_breaks.page_breaks) - 1):
            if scroll_position < self._page_breaks.page_breaks[i + 1]:
                return i

        # Last page (scroll position at or beyond last break)
        return len(self._page_breaks.page_breaks) - 2

    def get_scroll_position_for_page(self, page_number: int) -> int:
        """Get scroll position for a specific page number.

        Converts a page number to the corresponding scroll position by
        looking up the page break position.

        Args:
            page_number: Page number (0-indexed).

        Returns:
            Scroll position in pixels. Returns 0 if no calculation done
            or if page number is invalid.
        """
        if self._page_breaks is None:
            return 0

        # Validate page number
        # Valid pages: 0 to (page_count - 2) because last break is end marker
        max_page = len(self._page_breaks.page_breaks) - 2
        if page_number < 0 or page_number > max_page:
            logger.warning(
                "Invalid page number: %d (valid range: 0-%d)", page_number, max_page
            )
            return 0

        return self._page_breaks.page_breaks[page_number]

    def get_page_count(self) -> int:
        """Get total number of pages.

        Returns:
            Number of pages in the chapter. Returns 0 if no calculation done.
        """
        if self._page_breaks is None:
            return 0

        # Page count = number of breaks - 1 (last break is end marker)
        return self._page_breaks.page_count - 1

    def needs_recalculation(self, viewport_height: int) -> bool:
        """Check if page breaks need recalculation due to resize.

        Compares the current viewport height with the viewport height used
        for the last calculation.

        Args:
            viewport_height: Current viewport height in pixels.

        Returns:
            True if recalculation needed (no calculation done or height changed).
        """
        if self._page_breaks is None:
            return True

        return self._page_breaks.viewport_height != viewport_height
