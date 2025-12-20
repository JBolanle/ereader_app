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
from ereader.utils.cover_extractor import CoverExtractor

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
    book_removed = pyqtSignal(int, bool)  # book_id, file_deleted
    book_remove_failed = pyqtSignal(int, str)  # book_id, error_message
    book_status_updated = pyqtSignal(int, str)  # book_id, new_status

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

                # Extract cover image (Phase 3)
                cover_data = None
                try:
                    cover_data = CoverExtractor.extract_cover(filepath)
                    if cover_data:
                        logger.debug("Cover extracted for: %s", filename)
                except Exception as e:
                    # Don't fail import if cover extraction fails
                    logger.warning("Failed to extract cover for %s: %s", filename, e)

                # Create metadata record
                metadata = BookMetadata(
                    id=0,  # Will be set by database
                    title=book.title,
                    author=", ".join(book.authors) if book.authors else None,
                    file_path=abs_path,
                    cover_path=None,  # Will be set after saving cover
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

                # Save cover to cache and update database (Phase 3)
                if cover_data:
                    cover_bytes, extension = cover_data
                    cover_path = self._save_cover(book_id, cover_bytes, extension)
                    if cover_path:
                        try:
                            self._repository.update_book(book_id, cover_path=cover_path)
                            logger.debug("Cover saved and database updated for book %d", book_id)
                        except DatabaseError as e:
                            logger.warning("Failed to update cover path for book %d: %s", book_id, e)

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

    def get_book_by_id(self, book_id: int) -> BookMetadata | None:
        """Get book metadata by ID.

        Args:
            book_id: Database ID of book.

        Returns:
            BookMetadata if found, None otherwise.
        """
        logger.debug("Getting book by ID: %d", book_id)

        try:
            return self._repository.get_book(book_id)
        except DatabaseError as e:
            logger.error("Failed to get book %d: %s", book_id, e)
            return None
        except Exception:
            logger.exception("Unexpected error getting book %d", book_id)
            return None

    def remove_book(self, book_id: int, delete_file: bool = False) -> None:
        """Remove book from library, optionally deleting file.

        Args:
            book_id: Database ID of book to remove.
            delete_file: If True, also delete the EPUB file from disk.

        Emits:
            book_removed: On successful removal (book_id, deleted_file).
            book_remove_failed: On failure (book_id, error_message).
        """
        logger.debug("Removing book %d (delete_file=%s)", book_id, delete_file)

        try:
            # Get book metadata before deletion (for file path)
            book = self._repository.get_book(book_id)
            if not book:
                error_msg = f"Book not found: {book_id}"
                logger.error(error_msg)
                self.book_remove_failed.emit(book_id, error_msg)
                return

            # Delete from database
            self._repository.delete_book(book_id)
            logger.info("Book %d deleted from database", book_id)

            # Delete file if requested
            file_deleted = False
            if delete_file:
                try:
                    file_path = Path(book.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        file_deleted = True
                        logger.info("Deleted file: %s", file_path)
                    else:
                        logger.warning("File not found: %s", file_path)
                except OSError as e:
                    # File deletion failed, but database record is already gone
                    error_msg = f"Failed to delete file: {e}"
                    logger.error(error_msg)
                    self.book_remove_failed.emit(book_id, error_msg)
                    return

            # Emit success signal
            self.book_removed.emit(book_id, file_deleted)
            logger.info("Book %d removed successfully", book_id)

        except DatabaseError as e:
            error_msg = f"Failed to remove book from database: {e}"
            logger.error(error_msg)
            self.book_remove_failed.emit(book_id, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error removing book: {e}"
            logger.exception(error_msg)
            self.book_remove_failed.emit(book_id, error_msg)

    def update_book_status(self, book_id: int, new_status: str) -> None:
        """Update book reading status.

        Args:
            book_id: Database ID of book.
            new_status: New status ("not_started", "reading", or "finished").

        Emits:
            book_status_updated: On success (book_id, status).
            error_occurred: On failure.
        """
        logger.debug("Updating book %d status to: %s", book_id, new_status)

        try:
            # Validate status
            valid_statuses = ["not_started", "reading", "finished"]
            if new_status not in valid_statuses:
                error_msg = f"Invalid status: {new_status}"
                logger.error(error_msg)
                self.error_occurred.emit("Update Error", error_msg)
                return

            # Update in database
            self._repository.update_book(book_id, status=new_status)

            # Emit success signal
            self.book_status_updated.emit(book_id, new_status)
            logger.info("Book %d status updated to: %s", book_id, new_status)

        except DatabaseError as e:
            error_msg = f"Failed to update book status: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Update Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error updating book status: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Update Error", error_msg)

    def _save_cover(self, book_id: int, cover_bytes: bytes, extension: str) -> str | None:
        """Save cover image to cache directory.

        Creates ~/.ereader/covers/ directory if it doesn't exist and saves
        the cover image with filename {book_id}.{extension}.

        Args:
            book_id: Database ID of book.
            cover_bytes: Cover image data.
            extension: File extension (jpg, png, etc.).

        Returns:
            Absolute path to saved cover file, or None if save failed.
        """
        try:
            # Create covers directory
            covers_dir = Path.home() / ".ereader" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)

            # Save cover with book_id as filename
            cover_path = covers_dir / f"{book_id}.{extension}"
            cover_path.write_bytes(cover_bytes)

            logger.info("Saved cover for book %d: %s (%d bytes)", book_id, cover_path, len(cover_bytes))
            return str(cover_path)

        except OSError as e:
            logger.error("Failed to save cover for book %d: %s", book_id, e)
            return None
        except Exception:
            logger.exception("Unexpected error saving cover for book %d", book_id)
            return None
