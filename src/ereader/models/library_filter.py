"""Library filter model for search and organization.

This module provides the LibraryFilter dataclass for storing the current
filter, sort, and search state of the library view.
"""

from dataclasses import dataclass


@dataclass
class LibraryFilter:
    """Active filter and sort state for library view.

    This dataclass stores the current filtering, sorting, and search
    criteria applied to the library. Used by LibraryController and
    LibraryRepository to determine which books to display.

    Attributes:
        search_query: Text search query (searches title and author).
        collection_id: Filter by collection ID (None = all books).
        status: Filter by reading status (None = all statuses).
        author: Filter by author name (None = all authors).
        sort_by: Sort criterion ("recent", "title", "author", "progress", "added_date_desc").
        view_mode: Display mode ("grid" or "list").
        days_since_opened: Only books opened in last N days (None = all books).
            Used by "Recent Reads" smart collection.
    """

    search_query: str = ""
    collection_id: int | None = None
    status: str | None = None
    author: str | None = None
    sort_by: str = "recent"
    view_mode: str = "grid"
    days_since_opened: int | None = None

    def has_active_filters(self) -> bool:
        """Check if any filters are active.

        Returns:
            True if search query or any filter is active, False otherwise.
        """
        return bool(
            self.search_query
            or self.collection_id is not None
            or self.status is not None
            or self.author is not None
        )
