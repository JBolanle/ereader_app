"""Reader controller for coordinating book display and navigation.

This module provides the ReaderController class that serves as the coordinator
between the EPUBBook model and the view components. It owns all reading state
and orchestrates the flow of data between model and views.
"""

import logging

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from ereader.exceptions import EReaderError
from ereader.models.epub import EPUBBook
from ereader.models.reading_position import NavigationMode, ReadingPosition
from ereader.utils.async_loader import AsyncChapterLoader
from ereader.utils.cache_manager import CacheManager
from ereader.utils.pagination_engine import PaginationEngine
from ereader.utils.settings import ReaderSettings

logger = logging.getLogger(__name__)

# Position restore delay - wait for content rendering to complete
_POSITION_RESTORE_DELAY_MS = 100


class ReaderController(QObject):
    """Controller for managing book reading state and coordinating views.

    This controller owns the reading state (current book and chapter position)
    and coordinates between the EPUBBook model and UI views. Views are stateless
    and only display what the controller tells them.

    Signals:
        book_loaded: Emitted when a book is successfully opened.
            Args: title (str), author (str)
        chapter_changed: Emitted when the current chapter changes.
            Args: current chapter number (int), total chapters (int)
        navigation_state_changed: Emitted when navigation availability changes.
            Args: can_go_back (bool), can_go_forward (bool)
        content_ready: Emitted when chapter content is ready to display.
            Args: html content (str)
        reading_progress_changed: Emitted when reading progress changes.
            Args: formatted progress string (str)
        error_occurred: Emitted when an error needs to be shown to the user.
            Args: error title (str), error message (str)
    """

    # Signals for communicating with views
    book_loaded = pyqtSignal(str, str)  # title, author
    chapter_changed = pyqtSignal(int, int)  # current, total
    navigation_state_changed = pyqtSignal(bool, bool)  # can_back, can_forward
    content_ready = pyqtSignal(str)  # html content
    reading_progress_changed = pyqtSignal(str)  # formatted progress string
    error_occurred = pyqtSignal(str, str)  # error title, message
    pagination_changed = pyqtSignal(int, int)  # current_page, total_pages (Phase 2A)
    mode_changed = pyqtSignal(object)  # NavigationMode (Phase 2C)

    def __init__(self) -> None:
        """Initialize the reader controller."""
        super().__init__()
        logger.debug("Initializing ReaderController")

        # Reading state
        self._book: EPUBBook | None = None
        self._current_chapter_index: int = 0
        self._current_scroll_percentage: float = 0.0
        self._current_book_path: str | None = None  # Track book path for settings

        # Multi-layer caching with shared memory budget
        self._cache_manager = CacheManager(
            rendered_maxsize=10,
            raw_maxsize=20,
            image_max_memory_mb=50,
            total_memory_threshold_mb=150,
        )

        # Track current async loader (for cancellation)
        self._current_loader: AsyncChapterLoader | None = None

        # Pagination state (Phase 2A)
        self._pagination_engine = PaginationEngine()

        # Navigation mode state (Phase 2B)
        self._current_mode: NavigationMode = NavigationMode.SCROLL

        # Reference to book viewer (set by MainWindow when connecting signals)
        self._book_viewer = None

        # Settings for persistence (Phase 2D)
        self._settings = ReaderSettings()
        self._pending_position_restore: ReadingPosition | None = None

        logger.debug("ReaderController initialized")

    def open_book(self, filepath: str) -> None:
        """Open an EPUB book file.

        Loads the EPUB file, extracts metadata, and displays the saved position
        (or first chapter if no saved position). Emits signals to update the UI
        with book information and content.

        Args:
            filepath: Path to the EPUB file to open.
        """
        logger.info("Opening book: %s", filepath)

        try:
            # Load the EPUB file
            self._book = EPUBBook(filepath)
            self._current_book_path = filepath
            logger.debug("Book loaded successfully: %s", self._book.title)

            # Clear all caches when opening a new book
            self._cache_manager.clear_all()
            logger.debug("All caches cleared for new book")

            # Load saved position or start at beginning (Phase 2D)
            saved_position = self._settings.load_reading_position(filepath)
            if saved_position is not None:
                logger.info("Restoring saved position: %s", saved_position)
                # Validate chapter index is within bounds
                max_chapter = self._book.get_chapter_count() - 1
                if saved_position.chapter_index > max_chapter:
                    logger.warning(
                        "Saved chapter index %d exceeds book length (%d chapters), starting at chapter 0",
                        saved_position.chapter_index,
                        max_chapter + 1,
                    )
                    self._current_chapter_index = 0
                    self._current_mode = saved_position.mode
                else:
                    self._current_chapter_index = saved_position.chapter_index
                    self._current_mode = saved_position.mode
                    # Store position details for restoration after chapter loads
                    self._pending_position_restore = saved_position
            else:
                logger.debug("No saved position found, starting at chapter 0")
                self._current_chapter_index = 0
                # Use default navigation mode from settings
                self._current_mode = self._settings.get_default_navigation_mode()
                self._pending_position_restore = None

            # Get book metadata
            title = self._book.title
            author = ", ".join(self._book.authors) if self._book.authors else "Unknown Author"

            # Notify views about the loaded book
            logger.debug("Emitting book_loaded signal: %s by %s", title, author)
            self.book_loaded.emit(title, author)

            # Load the appropriate chapter
            self._load_chapter(self._current_chapter_index)

        except FileNotFoundError:
            error_msg = f"Could not find file: {filepath}"
            logger.error(error_msg)
            self.error_occurred.emit("File Not Found", error_msg)

        except EReaderError as e:
            error_msg = f"Failed to open EPUB: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Invalid EPUB", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error opening book: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def next_chapter(self) -> None:
        """Navigate to the next chapter.

        Saves current position, increments the chapter index, and loads
        the next chapter content. Does nothing if already at the last
        chapter or no book is loaded.
        """
        if self._book is None:
            logger.warning("next_chapter called with no book loaded")
            return

        max_index = self._book.get_chapter_count() - 1
        if self._current_chapter_index < max_index:
            # Save position before navigating away (Phase 2D)
            self.save_current_position()

            logger.debug(
                "Navigating to next chapter: %d -> %d",
                self._current_chapter_index,
                self._current_chapter_index + 1,
            )
            self._current_chapter_index += 1
            self._load_chapter(self._current_chapter_index)
        else:
            logger.debug("Already at last chapter, cannot go forward")

    def previous_chapter(self) -> None:
        """Navigate to the previous chapter.

        Saves current position, decrements the chapter index, and loads
        the previous chapter content. Does nothing if already at the first
        chapter or no book is loaded.
        """
        if self._book is None:
            logger.warning("previous_chapter called with no book loaded")
            return

        if self._current_chapter_index > 0:
            # Save position before navigating away (Phase 2D)
            self.save_current_position()

            logger.debug(
                "Navigating to previous chapter: %d -> %d",
                self._current_chapter_index,
                self._current_chapter_index - 1,
            )
            self._current_chapter_index -= 1
            self._load_chapter(self._current_chapter_index)
        else:
            logger.debug("Already at first chapter, cannot go back")

    def _load_chapter(self, index: int) -> None:
        """Load and display a specific chapter using async loading.

        Creates a background thread to load chapter content without blocking
        the UI. Shows loading indicator while loading (future enhancement).

        Args:
            index: Zero-based chapter index to load.
        """
        if self._book is None:
            logger.error("_load_chapter called with no book loaded")
            return

        try:
            logger.debug("Starting async load for chapter %d", index)

            # Cancel any pending load
            if self._current_loader is not None and self._current_loader.isRunning():
                logger.debug("Cancelling previous async load")
                self._current_loader.cancel()
                self._current_loader.wait(100)  # Wait up to 100ms for cleanup

            # Create async loader
            self._current_loader = AsyncChapterLoader(
                book=self._book,
                cache_manager=self._cache_manager,
                chapter_index=index,
                parent=self,
            )

            # Connect signals
            self._current_loader.content_ready.connect(self._on_content_ready)
            self._current_loader.error_occurred.connect(self._on_loader_error)
            self._current_loader.finished.connect(self._on_loader_finished)

            # TODO: Show loading indicator (emit signal to UI)
            # self.loading_started.emit()

            # Start async loading
            self._current_loader.start()

        except IndexError:
            error_msg = f"Chapter {index + 1} does not exist"
            logger.error(error_msg)
            self.error_occurred.emit("Chapter Not Found", error_msg)

        except EReaderError as e:
            error_msg = f"Failed to load chapter {index + 1}: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("Chapter Load Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected error loading chapter {index + 1}: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def _on_content_ready(self, html: str) -> None:
        """Handle content_ready signal from AsyncChapterLoader.

        This runs on the UI thread via Qt's signal/slot mechanism.
        If there's a pending position restore (from saved settings), it will
        be applied after the content is emitted.

        Args:
            html: Rendered HTML with resolved images.
        """
        logger.debug("Content ready, emitting to views")

        # TODO: Hide loading indicator
        # self.loading_finished.emit()

        # Emit content to views (BookViewer will call setHtml)
        self.content_ready.emit(html)

        # Restore saved position if pending (Phase 2D)
        if self._pending_position_restore is not None and self._book_viewer is not None:
            logger.debug("Restoring scroll position: %s", self._pending_position_restore)
            # Use QTimer to defer position restoration until after content is fully rendered
            position = self._pending_position_restore
            QTimer.singleShot(_POSITION_RESTORE_DELAY_MS, lambda: self._restore_position(position))
            self._pending_position_restore = None
        else:
            # Reset scroll percentage (new chapter always starts at top)
            self._current_scroll_percentage = 0.0

        # Update chapter position info
        if self._book is not None:
            total_chapters = self._book.get_chapter_count()
            self.chapter_changed.emit(self._current_chapter_index + 1, total_chapters)

            # Emit progress update
            self._emit_progress_update()

            # Update navigation button states
            self._update_navigation_state()

            # Log cache statistics
            self._cache_manager.log_stats()

            # Check memory usage
            self._cache_manager.check_memory_threshold()

    def _on_loader_error(self, title: str, message: str) -> None:
        """Handle error_occurred signal from AsyncChapterLoader.

        Args:
            title: Error dialog title.
            message: Error message.
        """
        logger.error("Async loader error: %s - %s", title, message)

        # TODO: Hide loading indicator
        # self.loading_finished.emit()

        # Forward error to UI
        self.error_occurred.emit(title, message)

    def _on_loader_finished(self) -> None:
        """Handle finished signal from AsyncChapterLoader.

        Cleanup when thread completes (success or error).
        """
        logger.debug("Async loader finished")
        # Thread will be garbage collected when no longer referenced

    def _update_navigation_state(self) -> None:
        """Update the navigation button enabled/disabled state.

        Emits a signal indicating whether the user can navigate backward
        or forward from the current chapter position.
        """
        if self._book is None:
            self.navigation_state_changed.emit(False, False)
            return

        can_go_back = self._current_chapter_index > 0
        can_go_forward = self._current_chapter_index < self._book.get_chapter_count() - 1

        logger.debug("Navigation state: back=%s, forward=%s", can_go_back, can_go_forward)
        self.navigation_state_changed.emit(can_go_back, can_go_forward)

    def on_scroll_changed(self, percentage: float) -> None:
        """Handle scroll position changes from BookViewer.

        Updates internal scroll state and emits formatted progress string.
        This is a public slot method that can be connected to signals.

        Args:
            percentage: Scroll position from 0-100.
        """
        logger.debug("Scroll position changed: %.1f%%", percentage)
        self._current_scroll_percentage = percentage
        self._emit_progress_update()

    def _emit_progress_update(self) -> None:
        """Emit formatted reading progress string (Phase 2B).

        Formats the current chapter position and scroll percentage into
        a user-friendly progress string. Format changes based on navigation mode:
        - Page mode: "Page X of Y in Chapter Z"
        - Scroll mode: "Chapter X of Y • Z% through chapter"
        """
        if self._book is None:
            return

        current_chapter = self._current_chapter_index + 1  # 1-based for display
        total_chapters = self._book.get_chapter_count()

        if self._current_mode == NavigationMode.PAGE and self._book_viewer is not None:
            # Page mode: Show page numbers
            try:
                current_scroll = self._book_viewer.get_scroll_position()
                current_page = self._pagination_engine.get_page_number(current_scroll) + 1  # 1-based
                total_pages = self._pagination_engine.get_page_count()

                progress = f"Page {current_page} of {total_pages} in Chapter {current_chapter}"
                logger.debug("Emitting progress update (page mode): %s", progress)
                self.reading_progress_changed.emit(progress)
            except Exception as e:
                logger.error("Error getting page information: %s", e)
                # Fall back to scroll mode display
                scroll_pct = self._current_scroll_percentage
                progress = f"Chapter {current_chapter} of {total_chapters} • {scroll_pct:.0f}% through chapter"
                self.reading_progress_changed.emit(progress)
        else:
            # Scroll mode: Show percentage through chapter
            scroll_pct = self._current_scroll_percentage
            progress = f"Chapter {current_chapter} of {total_chapters} • {scroll_pct:.0f}% through chapter"
            logger.debug("Emitting progress update (scroll mode): %s", progress)
            self.reading_progress_changed.emit(progress)

    def _recalculate_pages(self, viewer) -> None:
        """Recalculate page breaks for current chapter (Phase 2A).

        This method gets the content and viewport dimensions from the viewer,
        calculates page breaks using the pagination engine, and emits the
        pagination_changed signal with the current page information.

        Args:
            viewer: BookViewer instance to get dimensions from.
        """
        if self._book is None:
            logger.debug("Cannot recalculate pages: no book loaded")
            return

        try:
            # Get dimensions from viewer
            content_height = viewer.get_content_height()
            viewport_height = viewer.get_viewport_height()

            logger.debug(
                "Recalculating pages: content=%dpx, viewport=%dpx",
                content_height,
                viewport_height,
            )

            # Calculate page breaks
            self._pagination_engine.calculate_page_breaks(
                content_height=content_height, viewport_height=viewport_height
            )

            # Get current scroll position to determine current page
            scroll_position = viewer.get_scroll_position()
            current_page = self._pagination_engine.get_page_number(scroll_position)
            total_pages = self._pagination_engine.get_page_count()

            # Emit signal with 1-indexed page numbers for display
            logger.debug(
                "Pagination calculated: page %d of %d", current_page + 1, total_pages
            )
            self.pagination_changed.emit(current_page + 1, total_pages)

        except Exception as e:
            logger.error("Error recalculating pages: %s", e)
            # Don't propagate error - pagination is non-critical for Phase 2A

    def next_page(self) -> None:
        """Navigate to next page in page mode (Phase 2B).

        If in scroll mode, this method does nothing.
        If at the last page of the current chapter, navigates to the next chapter.
        If at the last page of the last chapter, does nothing.
        """
        # Only works in page mode
        if self._current_mode != NavigationMode.PAGE:
            logger.debug("next_page called in scroll mode, ignoring")
            return

        if self._book is None:
            logger.warning("next_page called with no book loaded")
            return

        if self._book_viewer is None:
            logger.warning("next_page called with no book viewer")
            return

        try:
            # Get current scroll position and page number
            current_scroll = self._book_viewer.get_scroll_position()
            current_page = self._pagination_engine.get_page_number(current_scroll)
            max_page = self._pagination_engine.get_page_count() - 1

            logger.debug(
                "next_page: current_page=%d, max_page=%d", current_page, max_page
            )

            if current_page < max_page:
                # Move to next page in current chapter
                new_scroll_pos = self._pagination_engine.get_scroll_position_for_page(
                    current_page + 1
                )
                logger.debug("Navigating to page %d (scroll: %d)", current_page + 1, new_scroll_pos)
                self._book_viewer.set_scroll_position(new_scroll_pos)
            else:
                # At last page of chapter, try to go to next chapter
                logger.debug("At last page, attempting to navigate to next chapter")
                self.next_chapter()

        except Exception as e:
            logger.error("Error navigating to next page: %s", e)

    def previous_page(self) -> None:
        """Navigate to previous page in page mode (Phase 2B).

        If in scroll mode, this method does nothing.
        If at the first page of the current chapter, navigates to the previous chapter.
        If at the first page of the first chapter, does nothing.
        """
        # Only works in page mode
        if self._current_mode != NavigationMode.PAGE:
            logger.debug("previous_page called in scroll mode, ignoring")
            return

        if self._book is None:
            logger.warning("previous_page called with no book loaded")
            return

        if self._book_viewer is None:
            logger.warning("previous_page called with no book viewer")
            return

        try:
            # Get current scroll position and page number
            current_scroll = self._book_viewer.get_scroll_position()
            current_page = self._pagination_engine.get_page_number(current_scroll)

            logger.debug("previous_page: current_page=%d", current_page)

            if current_page > 0:
                # Move to previous page in current chapter
                new_scroll_pos = self._pagination_engine.get_scroll_position_for_page(
                    current_page - 1
                )
                logger.debug("Navigating to page %d (scroll: %d)", current_page - 1, new_scroll_pos)
                self._book_viewer.set_scroll_position(new_scroll_pos)
            else:
                # At first page of chapter, try to go to previous chapter
                logger.debug("At first page, attempting to navigate to previous chapter")
                self.previous_chapter()

        except Exception as e:
            logger.error("Error navigating to previous page: %s", e)

    def toggle_navigation_mode(self) -> None:
        """Toggle between scroll and page navigation modes (Phase 2C).

        Switches the navigation mode and emits signals to update the UI.
        When switching to page mode, calculates page breaks for the current chapter.
        """
        if self._book is None:
            logger.warning("toggle_navigation_mode called with no book loaded")
            return

        if self._current_mode == NavigationMode.SCROLL:
            self._switch_to_page_mode()
        else:
            self._switch_to_scroll_mode()

    def _switch_to_page_mode(self) -> None:
        """Switch to discrete page navigation mode.

        Calculates page breaks for the current chapter and updates the UI
        to show page-based progress.
        """
        logger.info("Switching to page mode")
        self._current_mode = NavigationMode.PAGE

        # Calculate pages for current chapter if viewer is available
        if self._book_viewer is not None:
            self._recalculate_pages(self._book_viewer)

        # Notify UI components of mode change
        self.mode_changed.emit(NavigationMode.PAGE)

        # Update progress display to show page format
        self._emit_progress_update()

        logger.debug("Switched to page mode")

    def _switch_to_scroll_mode(self) -> None:
        """Switch to continuous scroll navigation mode.

        Updates the UI to show scroll-based progress.
        """
        logger.info("Switching to scroll mode")
        self._current_mode = NavigationMode.SCROLL

        # Notify UI components of mode change
        self.mode_changed.emit(NavigationMode.SCROLL)

        # Update progress display to show scroll format
        self._emit_progress_update()

        logger.debug("Switched to scroll mode")

    def _restore_position(self, position: ReadingPosition) -> None:
        """Restore a saved reading position (Phase 2D).

        This method is called after chapter content is loaded to restore
        the exact scroll position and navigation mode from saved settings.

        Args:
            position: ReadingPosition to restore.
        """
        if self._book_viewer is None:
            logger.warning("Cannot restore position: no book viewer available")
            return

        try:
            # Restore scroll position
            self._book_viewer.set_scroll_position(position.scroll_offset)
            logger.debug(
                "Restored scroll position to %dpx (page %d in %s mode)",
                position.scroll_offset,
                position.page_number,
                position.mode.value,
            )

            # If in page mode, recalculate pages and emit mode change
            if position.mode == NavigationMode.PAGE:
                self._recalculate_pages(self._book_viewer)
                self.mode_changed.emit(NavigationMode.PAGE)
            else:
                self.mode_changed.emit(NavigationMode.SCROLL)

            # Update progress display
            self._emit_progress_update()

        except (ValueError, RuntimeError, AttributeError) as e:
            # ValueError: Invalid position data
            # RuntimeError: Qt widget operation failed
            # AttributeError: Widget not properly initialized
            logger.error("Error restoring position: %s", e)
        except Exception as e:
            # Catch any unexpected errors to prevent crashes
            logger.error("Unexpected error restoring position: %s", e)

    def save_current_position(self) -> None:
        """Save the current reading position to settings (Phase 2D).

        This method should be called when:
        - Changing chapters
        - Closing the application
        - Navigation mode changes

        The position is only saved if a book is currently open.
        """
        if self._book is None or self._current_book_path is None:
            logger.debug("No book loaded, skipping position save")
            return

        if self._book_viewer is None:
            logger.debug("No book viewer available, skipping position save")
            return

        try:
            # Get current scroll position
            scroll_offset = self._book_viewer.get_scroll_position()

            # Get current page number (if in page mode)
            if self._current_mode == NavigationMode.PAGE:
                page_number = self._pagination_engine.get_page_number(scroll_offset)
            else:
                page_number = 0

            # Create position object
            position = ReadingPosition(
                chapter_index=self._current_chapter_index,
                page_number=page_number,
                scroll_offset=scroll_offset,
                mode=self._current_mode,
            )

            # Save to settings
            self._settings.save_reading_position(self._current_book_path, position)
            logger.debug("Saved reading position: %s", position)

        except (ValueError, RuntimeError, AttributeError) as e:
            # ValueError: Invalid position data
            # RuntimeError: Qt widget operation or QSettings failed
            # AttributeError: Widget not properly initialized
            logger.error("Error saving position: %s", e)
        except Exception as e:
            # Catch any unexpected errors to prevent crashes
            logger.error("Unexpected error saving position: %s", e)
