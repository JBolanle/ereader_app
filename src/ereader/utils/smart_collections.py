"""Smart collections helper for library organization.

This module provides the SmartCollections class that defines built-in smart
collections (Recent Reads, Currently Reading, To Read, Favorites). These
collections are computed dynamically from database queries, not stored as
Collection objects.
"""

import logging

from ereader.models.book_metadata import BookMetadata
from ereader.models.library_database import LibraryRepository
from ereader.models.library_filter import LibraryFilter

logger = logging.getLogger(__name__)


class SmartCollections:
    """Definitions for built-in smart collections.

    Smart collections are dynamic queries over the books database. They are not
    stored in the collections table but are always available in the sidebar.

    Example:
        repository = LibraryRepository(db_path)
        recent_books = SmartCollections.recent_reads(repository)
        currently_reading = SmartCollections.currently_reading(repository)
    """

    @staticmethod
    def recent_reads(repository: LibraryRepository) -> list[BookMetadata]:
        """Get books opened in the last 30 days.

        Args:
            repository: Library repository instance.

        Returns:
            List of books opened in last 30 days, sorted by last opened date.
        """
        logger.debug("Fetching Recent Reads smart collection")

        filter_obj = LibraryFilter(
            days_since_opened=30,
            sort_by="recent"
        )

        books = repository.filter_books(filter_obj)
        logger.debug("Recent Reads found %d books", len(books))
        return books

    @staticmethod
    def currently_reading(repository: LibraryRepository) -> list[BookMetadata]:
        """Get books with status='reading'.

        Args:
            repository: Library repository instance.

        Returns:
            List of books currently being read, sorted by last opened date.
        """
        logger.debug("Fetching Currently Reading smart collection")

        filter_obj = LibraryFilter(
            status="reading",
            sort_by="recent"
        )

        books = repository.filter_books(filter_obj)
        logger.debug("Currently Reading found %d books", len(books))
        return books

    @staticmethod
    def to_read(repository: LibraryRepository) -> list[BookMetadata]:
        """Get books with status='not_started'.

        Args:
            repository: Library repository instance.

        Returns:
            List of books not yet started, sorted by date added (newest first).
        """
        logger.debug("Fetching To Read smart collection")

        filter_obj = LibraryFilter(
            status="not_started",
            sort_by="added_date_desc"
        )

        books = repository.filter_books(filter_obj)
        logger.debug("To Read found %d books", len(books))
        return books

    @staticmethod
    def favorites(repository: LibraryRepository) -> list[BookMetadata]:
        """Get books marked as favorites.

        NOTE: This is a placeholder for future implementation. The books table
        does not currently have an is_favorite column. When that column is added,
        this method will filter for is_favorite=1.

        Args:
            repository: Library repository instance.

        Returns:
            Empty list (placeholder for future implementation).
        """
        logger.debug("Fetching Favorites smart collection (placeholder)")

        # TODO: Add is_favorite column to books table in future schema version
        # Then implement: LibraryFilter(is_favorite=True, sort_by="title")
        return []

    @staticmethod
    def all_books(repository: LibraryRepository) -> list[BookMetadata]:
        """Get all books in the library.

        Args:
            repository: Library repository instance.

        Returns:
            List of all books, sorted by last opened date.
        """
        logger.debug("Fetching All Books")

        filter_obj = LibraryFilter(sort_by="recent")
        books = repository.filter_books(filter_obj)
        logger.debug("All Books found %d books", len(books))
        return books
