"""Collection model for library organization.

This module provides the Collection dataclass for user-created collections.
Smart collections (Recent Reads, Currently Reading, etc.) are NOT stored as
Collection objects - they are computed queries defined in the SmartCollections helper.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Collection:
    """User-created collection of books.

    Represents a user-defined grouping of books (e.g., "Science Fiction", "To Read").
    Smart collections (Recent Reads, Currently Reading) are NOT stored as Collection
    objects - they are computed queries defined in SmartCollections.

    Attributes:
        id: Database primary key (0 for new collections not yet in database).
        name: Collection name (must be unique).
        created_date: When collection was created.
        color: Optional hex color for UI display (e.g., "#FF5733").
        sort_order: Custom order for sidebar display (lower = higher in list).
        book_count: Number of books in collection (computed, not stored in database).
    """

    id: int
    name: str
    created_date: datetime
    color: str | None = None
    sort_order: int = 0
    book_count: int = 0

    def __str__(self) -> str:
        """Human-readable string representation.

        Returns:
            Formatted string with collection name and book count.
        """
        return f"{self.name} ({self.book_count} books)"
