"""Reading position model for tracking user's location in a book.

This module provides the ReadingPosition dataclass and NavigationMode enum
for storing and managing the user's current reading position within a book.
"""

from dataclasses import dataclass
from enum import Enum


class NavigationMode(Enum):
    """Navigation modes for the reader.

    SCROLL: Continuous scrolling mode (Phase 1 behavior).
    PAGE: Discrete page navigation mode (Phase 2).
    """

    SCROLL = "scroll"
    PAGE = "page"


@dataclass
class ReadingPosition:
    """Represents a position within a book.

    This dataclass stores the user's reading position, including both
    chapter-level and within-chapter position information. It supports
    both scroll-based and page-based navigation modes.

    Attributes:
        chapter_index: Zero-based chapter index.
        page_number: Zero-based page number within chapter (for page mode).
        scroll_offset: Exact scroll position in pixels (for precision).
        mode: Current navigation mode (SCROLL or PAGE).
    """

    chapter_index: int
    page_number: int = 0
    scroll_offset: int = 0
    mode: NavigationMode = NavigationMode.SCROLL

    def __str__(self) -> str:
        """Human-readable position string.

        Returns:
            Formatted string showing chapter and position in 1-indexed format.
            In page mode: "Chapter X, Page Y"
            In scroll mode: "Chapter X, Ypx"
        """
        # Convert 0-indexed to 1-indexed for display
        chapter_display = self.chapter_index + 1

        if self.mode == NavigationMode.PAGE:
            page_display = self.page_number + 1
            return f"Chapter {chapter_display}, Page {page_display}"
        else:
            return f"Chapter {chapter_display}, {self.scroll_offset}px"
