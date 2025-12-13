"""Book metadata model for library management.

This module provides the BookMetadata dataclass for storing lightweight book
information in the library. This is separate from EPUBBook (which parses full
EPUB files) to enable fast library loading without parsing every EPUB.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BookMetadata:
    """Lightweight book metadata for library display.

    This dataclass stores book information loaded from the database,
    not from EPUB files. Used for fast library grid rendering.

    Attributes:
        id: Database primary key (0 for new books not yet in database).
        title: Book title.
        author: Book author(s) as a comma-separated string.
        file_path: Absolute path to EPUB file.
        cover_path: Path to extracted cover image (None for placeholder).
        added_date: When the book was added to the library.
        last_opened_date: When the book was last opened (None if never opened).
        reading_progress: Reading progress from 0.0 to 100.0.
        current_chapter_index: Zero-based chapter index (last read position).
        scroll_position: Pixel position within chapter (last read position).
        status: Reading status ("not_started", "reading", or "finished").
        file_size: EPUB file size in bytes (None if unknown).
    """

    id: int
    title: str
    author: str | None
    file_path: str
    cover_path: str | None
    added_date: datetime
    last_opened_date: datetime | None
    reading_progress: float
    current_chapter_index: int
    scroll_position: int
    status: str
    file_size: int | None

    def __str__(self) -> str:
        """Human-readable string representation.

        Returns:
            Formatted string with title and author.
        """
        author_str = self.author if self.author else "Unknown Author"
        return f"{self.title} by {author_str}"
