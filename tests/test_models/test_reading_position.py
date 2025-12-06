"""Tests for the reading position model.

This module tests the ReadingPosition dataclass and NavigationMode enum
which track the user's reading position within a book.
"""

import pytest

from ereader.models.reading_position import NavigationMode, ReadingPosition


class TestNavigationMode:
    """Test the NavigationMode enum."""

    def test_scroll_mode_value(self) -> None:
        """Test SCROLL mode has correct value."""
        assert NavigationMode.SCROLL.value == "scroll"

    def test_page_mode_value(self) -> None:
        """Test PAGE mode has correct value."""
        assert NavigationMode.PAGE.value == "page"

    def test_from_string(self) -> None:
        """Test creating NavigationMode from string value."""
        assert NavigationMode("scroll") == NavigationMode.SCROLL
        assert NavigationMode("page") == NavigationMode.PAGE


class TestReadingPosition:
    """Test the ReadingPosition dataclass."""

    def test_creation_minimal(self) -> None:
        """Test creating a reading position with minimal parameters."""
        pos = ReadingPosition(chapter_index=2)

        assert pos.chapter_index == 2
        assert pos.page_number == 0  # Default
        assert pos.scroll_offset == 0  # Default
        assert pos.mode == NavigationMode.SCROLL  # Default

    def test_creation_full(self) -> None:
        """Test creating a reading position with all parameters."""
        pos = ReadingPosition(
            chapter_index=3,
            page_number=5,
            scroll_offset=1200,
            mode=NavigationMode.PAGE,
        )

        assert pos.chapter_index == 3
        assert pos.page_number == 5
        assert pos.scroll_offset == 1200
        assert pos.mode == NavigationMode.PAGE

    def test_string_representation_page_mode(self) -> None:
        """Test string representation in page mode."""
        pos = ReadingPosition(
            chapter_index=2, page_number=5, mode=NavigationMode.PAGE
        )

        # Chapter and page are 0-indexed internally, but display as 1-indexed
        assert str(pos) == "Chapter 3, Page 6"

    def test_string_representation_scroll_mode(self) -> None:
        """Test string representation in scroll mode."""
        pos = ReadingPosition(
            chapter_index=2, scroll_offset=1200, mode=NavigationMode.SCROLL
        )

        # Chapter is 0-indexed internally, but displays as 1-indexed
        assert str(pos) == "Chapter 3, 1200px"

    def test_string_representation_first_chapter(self) -> None:
        """Test string representation for first chapter (0-indexed)."""
        pos = ReadingPosition(chapter_index=0, mode=NavigationMode.PAGE)

        assert str(pos) == "Chapter 1, Page 1"

    def test_string_representation_zero_offset(self) -> None:
        """Test string representation with zero scroll offset."""
        pos = ReadingPosition(chapter_index=0, mode=NavigationMode.SCROLL)

        assert str(pos) == "Chapter 1, 0px"

    def test_equality(self) -> None:
        """Test that two ReadingPosition instances can be compared."""
        pos1 = ReadingPosition(
            chapter_index=2,
            page_number=5,
            scroll_offset=1200,
            mode=NavigationMode.PAGE,
        )
        pos2 = ReadingPosition(
            chapter_index=2,
            page_number=5,
            scroll_offset=1200,
            mode=NavigationMode.PAGE,
        )
        pos3 = ReadingPosition(chapter_index=3, page_number=5)

        assert pos1 == pos2  # Same values
        assert pos1 != pos3  # Different chapter

    def test_immutability_via_dataclass(self) -> None:
        """Test that ReadingPosition behaves as a dataclass."""
        pos = ReadingPosition(chapter_index=2)

        # Can modify (dataclass is mutable by default, which is fine for this use)
        pos.page_number = 10
        assert pos.page_number == 10

    def test_mode_defaults_to_scroll(self) -> None:
        """Test that mode defaults to SCROLL when not specified."""
        pos = ReadingPosition(chapter_index=0)

        assert pos.mode == NavigationMode.SCROLL
