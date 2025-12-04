"""Reader controller for coordinating book display and navigation.

This module provides the ReaderController class that serves as the coordinator
between the EPUBBook model and the view components. It owns all reading state
and orchestrates the flow of data between model and views.
"""

import logging

from PyQt6.QtCore import QObject, pyqtSignal

from ereader.exceptions import EReaderError
from ereader.models.epub import EPUBBook
from ereader.utils.cache import ChapterCache
from ereader.utils.html_resources import resolve_images_in_html
from ereader.utils.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        """Initialize the reader controller."""
        super().__init__()
        logger.debug("Initializing ReaderController")

        # Reading state
        self._book: EPUBBook | None = None
        self._current_chapter_index: int = 0
        self._current_scroll_percentage: float = 0.0

        # Chapter caching for performance
        self._chapter_cache = ChapterCache(maxsize=10)

        # Memory monitoring
        self._memory_monitor = MemoryMonitor(threshold_mb=150)

        logger.debug("ReaderController initialized")

    def open_book(self, filepath: str) -> None:
        """Open an EPUB book file.

        Loads the EPUB file, extracts metadata, and displays the first chapter.
        Emits signals to update the UI with book information and content.

        Args:
            filepath: Path to the EPUB file to open.
        """
        logger.info("Opening book: %s", filepath)

        try:
            # Load the EPUB file
            self._book = EPUBBook(filepath)
            logger.debug("Book loaded successfully: %s", self._book.title)

            # Reset to first chapter
            self._current_chapter_index = 0

            # Clear cache when opening a new book
            self._chapter_cache.clear()
            logger.debug("Chapter cache cleared for new book")

            # Get book metadata
            title = self._book.title
            author = ", ".join(self._book.authors) if self._book.authors else "Unknown Author"

            # Notify views about the loaded book
            logger.debug("Emitting book_loaded signal: %s by %s", title, author)
            self.book_loaded.emit(title, author)

            # Load and display the first chapter
            self._load_chapter(0)

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

        Increments the chapter index and loads the next chapter content.
        Does nothing if already at the last chapter or no book is loaded.
        """
        if self._book is None:
            logger.warning("next_chapter called with no book loaded")
            return

        max_index = self._book.get_chapter_count() - 1
        if self._current_chapter_index < max_index:
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

        Decrements the chapter index and loads the previous chapter content.
        Does nothing if already at the first chapter or no book is loaded.
        """
        if self._book is None:
            logger.warning("previous_chapter called with no book loaded")
            return

        if self._current_chapter_index > 0:
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
        """Load and display a specific chapter.

        Fetches the chapter content from the book model and emits signals
        to update the UI with the new content and navigation state.
        Uses LRU cache to avoid re-rendering recently viewed chapters.

        Args:
            index: Zero-based chapter index to load.
        """
        if self._book is None:
            logger.error("_load_chapter called with no book loaded")
            return

        try:
            logger.debug("Loading chapter %d", index)

            # Generate cache key
            cache_key = f"{self._book.filepath}:{index}"

            # Try cache first
            cached_html = self._chapter_cache.get(cache_key)
            if cached_html is not None:
                logger.debug("Using cached chapter %d", index)
                content = cached_html
            else:
                # Cache miss - render and store
                logger.debug("Cache miss - rendering chapter %d", index)

                # Get chapter href and content
                chapter_href = self._book.get_chapter_href(index)
                raw_content = self._book.get_chapter_content(index)
                logger.debug(
                    "Chapter content loaded (href: %s, length: %d bytes)",
                    chapter_href,
                    len(raw_content)
                )

                # Resolve image references in HTML
                # Pass chapter href so images are resolved relative to the chapter file
                content = resolve_images_in_html(raw_content, self._book, chapter_href=chapter_href)
                logger.debug("Image resources resolved, final length: %d bytes", len(content))

                # Store in cache
                self._chapter_cache.set(cache_key, content)
                logger.debug("Chapter %d cached", index)

            # Log cache statistics
            stats = self._chapter_cache.stats()
            logger.debug(
                "Cache stats: size=%d/%d, hits=%d, misses=%d, hit_rate=%.1f%%",
                stats["size"],
                stats["maxsize"],
                stats["hits"],
                stats["misses"],
                stats["hit_rate"]
            )

            # Check memory usage and log warnings if needed
            self._memory_monitor.check_threshold()

            # Emit content to views
            self.content_ready.emit(content)

            # Reset scroll percentage (new chapter always starts at top)
            self._current_scroll_percentage = 0.0

            # Update chapter position info
            total_chapters = self._book.get_chapter_count()
            self.chapter_changed.emit(index + 1, total_chapters)  # 1-based for display

            # Emit progress update
            self._emit_progress_update()

            # Update navigation button states
            self._update_navigation_state()

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
        """Emit formatted reading progress string.

        Formats the current chapter position and scroll percentage into
        a user-friendly progress string and emits the reading_progress_changed signal.
        """
        if self._book is None:
            return

        current = self._current_chapter_index + 1  # 1-based for display
        total = self._book.get_chapter_count()
        scroll_pct = self._current_scroll_percentage

        progress = f"Chapter {current} of {total} • {scroll_pct:.0f}% through chapter"
        logger.debug("Emitting progress update: %s", progress)
        self.reading_progress_changed.emit(progress)
