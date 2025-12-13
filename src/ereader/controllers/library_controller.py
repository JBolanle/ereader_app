"""Library controller for managing book collection state.

This module provides the LibraryController class that coordinates between
the library database (LibraryRepository) and library views. It manages
import workflows, filtering, and library state.
"""

import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from ereader.exceptions import EReaderError
from ereader.models.book_metadata import BookMetadata
from ereader.models.epub import EPUBBook
from ereader.models.library_database import DatabaseError, LibraryRepository
from ereader.models.library_filter import LibraryFilter

logger = logging.getLogger(__name__)


class LibraryController(QObject):
    """Controller for managing library state and operations.

    This controller owns the library state and coordinates between the
    LibraryRepository (database) and library views. It handles import
    workflows, search/filter operations, and book management.

    Signals:
        library_loaded: Emitted when library is loaded.
            Args: list of BookMetadata
        import_started: Emitted when import begins.
            Args: total_files (int)
        import_progress: Emitted for each file during import.
            Args: current (int), total (int), filename (str)
        import_completed: Emitted when import finishes.
            Args: succeeded (int), failed (int)
        import_error: Emitted when a file fails to import.
            Args: filename (str), error_message (str)
        filter_changed: Emitted when filter is applied.
            Args: filtered list of BookMetadata
        error_occurred: Emitted for critical errors.
            Args: error title (str), error message (str)
    """

    # Signals
    library_loaded = pyqtSignal(list)  # list[BookMetadata]
    import_started = pyqtSignal(int)  # total_files
    import_progress = pyqtSignal(int, int, str)  # current, total, filename
    import_completed = pyqtSignal(int, int)  # succeeded, failed
    import_error = pyqtSignal(str, str)  # filename, error_message
    filter_changed = pyqtSignal(list)  # filtered list[BookMetadata]
    error_occurred = pyqtSignal(str, str)  # error title, message

    def __init__(self, repository: LibraryRepository) -> None:
        """Initialize the library controller.

        Args:
            repository: LibraryRepository instance for database operations.
        """
        super().__init__()
        logger.debug("Initializing LibraryController")

        self._repository = repository
        self._current_filter = LibraryFilter()
        self._all_books: list[BookMetadata] = []

        logger.debug("LibraryController initialized")

    def load_library(self) -> None:
        """Load all books from the library.

        Retrieves all books from the database and emits library_loaded signal.
        This should be called when the application starts or when returning
        to the library view.

        Emits:
            library_loaded: With list of all books.
            error_occurred: If database operation fails.
        """
        logger.debug("Loading library")

        try:
            self._all_books = self._repository.get_all_books()
            logger.info("Library loaded: %d books", len(self._all_books))
            self.library_loaded.emit(self._all_books)

        except DatabaseError as e:
            error_msg = f"Failed to load library: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Database Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error loading library: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def import_books(self, filepaths: list[str]) -> None:
        """Import books into library (synchronous for Phase 1).

        Parses EPUB metadata for each file and adds it to the database.
        Emits progress signals during the import process.

        Args:
            filepaths: List of absolute paths to EPUB files.

        Emits:
            import_started: When import begins.
            import_progress: For each file being processed.
            import_error: When a file fails to import.
            import_completed: When all files are processed.
            library_loaded: After successful import with updated library.
        """
        total = len(filepaths)
        succeeded = 0
        failed = 0

        logger.info("Starting import of %d books", total)
        self.import_started.emit(total)

        for i, filepath in enumerate(filepaths, 1):
            filename = Path(filepath).name
            logger.debug("Importing file %d of %d: %s", i, total, filename)
            self.import_progress.emit(i, total, filename)

            try:
                # Check if book already in library
                abs_path = str(Path(filepath).absolute())

                # Parse EPUB to get metadata
                book = EPUBBook(filepath)

                # Create metadata record
                metadata = BookMetadata(
                    id=0,  # Will be set by database
                    title=book.title,
                    author=", ".join(book.authors) if book.authors else None,
                    file_path=abs_path,
                    cover_path=None,  # Phase 2: Extract covers
                    added_date=datetime.now(),
                    last_opened_date=None,
                    reading_progress=0.0,
                    current_chapter_index=0,
                    scroll_position=0,
                    status="not_started",
                    file_size=Path(filepath).stat().st_size,
                )

                # Add to database
                book_id = self._repository.add_book(metadata)
                logger.info("Successfully imported: %s (ID: %d)", filename, book_id)
                succeeded += 1

            except DatabaseError as e:
                # Database error (likely duplicate)
                error_msg = str(e)
                logger.warning("Failed to import %s: %s", filename, error_msg)
                self.import_error.emit(filename, error_msg)
                failed += 1

            except FileNotFoundError:
                error_msg = "File not found"
                logger.warning("Failed to import %s: %s", filename, error_msg)
                self.import_error.emit(filename, error_msg)
                failed += 1

            except EReaderError as e:
                # EPUB parsing error
                error_msg = f"Not a valid EPUB: {e}"
                logger.warning("Failed to import %s: %s", filename, error_msg)
                self.import_error.emit(filename, error_msg)
                failed += 1

            except Exception as e:
                # Unexpected error
                error_msg = f"Unexpected error: {e}"
                logger.exception("Failed to import %s", filename)
                self.import_error.emit(filename, error_msg)
                failed += 1

        logger.info("Import completed: %d succeeded, %d failed", succeeded, failed)
        self.import_completed.emit(succeeded, failed)

        # Reload library if any books were successfully imported
        if succeeded > 0:
            self.load_library()

    def delete_book(self, book_id: int) -> None:
        """Delete a book from the library.

        Args:
            book_id: Database ID of the book to delete.

        Emits:
            library_loaded: After successful deletion with updated library.
            error_occurred: If deletion fails.
        """
        logger.debug("Deleting book with ID: %d", book_id)

        try:
            self._repository.delete_book(book_id)
            logger.info("Book %d deleted successfully", book_id)

            # Reload library
            self.load_library()

        except DatabaseError as e:
            error_msg = f"Failed to delete book: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Database Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error deleting book: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def set_filter(self, filter_obj: LibraryFilter) -> None:
        """Apply filter to library.

        Args:
            filter_obj: Filter and sort criteria.

        Emits:
            filter_changed: With filtered list of books.
            error_occurred: If filter operation fails.
        """
        logger.debug("Applying filter: %s", filter_obj)

        try:
            self._current_filter = filter_obj

            # Get filtered books from repository
            filtered_books = self._repository.filter_books(filter_obj)
            logger.debug("Filter result: %d books", len(filtered_books))

            self.filter_changed.emit(filtered_books)

        except DatabaseError as e:
            error_msg = f"Failed to apply filter: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Database Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error applying filter: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def search(self, query: str) -> None:
        """Search books by title or author.

        Args:
            query: Search query string.

        Emits:
            filter_changed: With search results.
            error_occurred: If search fails.
        """
        logger.debug("Searching for: %s", query)

        try:
            # Update current filter with search query
            self._current_filter.search_query = query

            # Perform search
            results = self._repository.search_books(query)
            logger.debug("Search found %d results", len(results))

            self.filter_changed.emit(results)

        except DatabaseError as e:
            error_msg = f"Search failed: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Database Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error during search: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def update_reading_position(
        self, book_id: int, chapter_index: int, scroll_position: int, progress: float
    ) -> None:
        """Update reading position for a book.

        This should be called by the ReaderController when the user's
        reading position changes.

        Args:
            book_id: Database ID of the book.
            chapter_index: Current chapter index (0-based).
            scroll_position: Scroll position within chapter (pixels).
            progress: Overall reading progress (0.0 to 100.0).

        Emits:
            error_occurred: If update fails.
        """
        logger.debug("Updating reading position for book %d", book_id)

        try:
            self._repository.update_reading_position(
                book_id, chapter_index, scroll_position, progress
            )
            logger.debug("Reading position updated for book %d", book_id)

        except DatabaseError as e:
            error_msg = f"Failed to update reading position: {e}"
            logger.error(error_msg)
            # Don't emit error_occurred for position updates (non-critical)
            # Just log the error

        except Exception as e:
            error_msg = f"Unexpected error updating reading position: {e}"
            logger.exception(error_msg)
            # Don't emit error_occurred for position updates (non-critical)

    def get_book_count(self) -> int:
        """Get the total number of books in the library.

        Returns:
            Number of books in library.
        """
        return len(self._all_books)
