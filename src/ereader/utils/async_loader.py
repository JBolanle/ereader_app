"""Async chapter loading for non-blocking UI during EPUB chapter loads.

This module provides AsyncChapterLoader, a QThread-based background loader
that moves CPU-intensive chapter loading and image resolution off the UI thread.
"""

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from ereader.exceptions import CorruptedEPUBError
from ereader.utils.html_resources import resolve_images_in_html

if TYPE_CHECKING:
    from ereader.models.book import EPUBBook
    from ereader.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class AsyncChapterLoader(QThread):
    """Background thread for loading and rendering chapter content.

    This thread handles the CPU-intensive work of loading chapter HTML
    and resolving image references to base64 data URLs. By moving this
    work off the UI thread, the application stays responsive during loading.

    The thread operates autonomously once started - it checks caches,
    loads from the EPUB if needed, resolves images, updates caches, and
    emits a signal when content is ready.

    Signals:
        content_ready: Emitted when chapter HTML is fully prepared and ready
            to display. Args: html (str)
        error_occurred: Emitted if loading fails. Args: title (str), message (str)

    Thread Safety:
        - Reads from EPUBBook (ZipFile access) - using single-loader-at-a-time pattern
        - Writes to CacheManager - requires thread-safe cache implementation (locks)
        - Does NOT access UI widgets (only emits signals)

    Example:
        >>> loader = AsyncChapterLoader(book, cache_manager, chapter_index=0)
        >>> loader.content_ready.connect(on_content_ready)
        >>> loader.error_occurred.connect(on_error)
        >>> loader.start()
    """

    # Signals for communicating with UI thread
    content_ready = pyqtSignal(str)  # HTML ready to display
    error_occurred = pyqtSignal(str, str)  # error title, message

    def __init__(
        self,
        book: "EPUBBook",
        cache_manager: "CacheManager",
        chapter_index: int,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the async chapter loader.

        Args:
            book: The EPUBBook to load content from.
            cache_manager: Cache manager for rendered/raw chapters and images.
            chapter_index: Zero-based index of chapter to load.
            parent: Optional parent QObject for automatic cleanup.
        """
        super().__init__(parent)
        self._book = book
        self._cache_manager = cache_manager
        self._chapter_index = chapter_index
        self._cancelled = False  # Flag for cooperative cancellation

    def run(self) -> None:
        """Execute chapter loading in background thread.

        This method runs in a separate thread. It must NOT access UI widgets
        directly - only emit signals to communicate with the UI thread.

        Flow:
            1. Check rendered cache (fast path)
            2. If miss, check raw cache
            3. If miss, load raw HTML from EPUB
            4. Resolve images (CPU-intensive, happens off UI thread)
            5. Update caches
            6. Emit content_ready signal

        All errors are caught and emitted via error_occurred signal.
        """
        try:
            # Generate cache key
            cache_key = f"{self._book.filepath}:{self._chapter_index}"

            # Check if cancelled before starting work
            if self._cancelled:
                logger.debug(
                    "Async loader: cancelled before start (chapter %d)", self._chapter_index
                )
                return

            # Try rendered chapters cache first (fast path)
            cached_html = self._cache_manager.rendered_chapters.get(cache_key)
            if cached_html is not None:
                logger.debug("Async loader: cache hit for chapter %d", self._chapter_index)
                self.content_ready.emit(cached_html)
                return

            # Check cancellation again (user might have navigated away)
            if self._cancelled:
                logger.debug(
                    "Async loader: cancelled after cache check (chapter %d)",
                    self._chapter_index,
                )
                return

            # Cache miss - get chapter href for image resolution
            chapter_href = self._book.get_chapter_href(self._chapter_index)

            # Try raw content cache
            cached_raw = self._cache_manager.raw_chapters.get(cache_key)
            if cached_raw is not None:
                logger.debug("Async loader: raw cache hit for chapter %d", self._chapter_index)
                raw_content = cached_raw
            else:
                # Complete miss - load from book
                logger.debug("Async loader: loading chapter %d from EPUB", self._chapter_index)
                raw_content = self._book.get_chapter_content(self._chapter_index)

                # Store raw content in cache (thread-safe with locks)
                self._cache_manager.raw_chapters.set(cache_key, raw_content)

            # Check cancellation before expensive image resolution
            if self._cancelled:
                logger.debug(
                    "Async loader: cancelled before image resolution (chapter %d)",
                    self._chapter_index,
                )
                return

            # Resolve image references (CPU-intensive, but we're in background thread!)
            logger.debug("Async loader: resolving images for chapter %d", self._chapter_index)
            content = resolve_images_in_html(raw_content, self._book, chapter_href=chapter_href)

            # Store rendered content in cache (thread-safe with locks)
            self._cache_manager.rendered_chapters.set(cache_key, content)

            # Final cancellation check before emitting
            if self._cancelled:
                logger.debug(
                    "Async loader: cancelled before emit (chapter %d)", self._chapter_index
                )
                return

            # Emit signal to UI thread
            logger.debug("Async loader: chapter %d ready, emitting signal", self._chapter_index)
            self.content_ready.emit(content)

        except IndexError:
            # Chapter index out of range
            error_msg = f"Chapter {self._chapter_index + 1} does not exist"
            logger.error("Async loader error: %s", error_msg)
            self.error_occurred.emit("Chapter Not Found", error_msg)

        except CorruptedEPUBError as e:
            # EPUB corruption error
            error_msg = f"Failed to load chapter {self._chapter_index + 1}: {e}"
            logger.error("Async loader error: %s", error_msg)
            self.error_occurred.emit("Chapter Load Error", error_msg)

        except Exception as e:
            # Unexpected errors
            error_msg = f"Unexpected error loading chapter {self._chapter_index + 1}: {e}"
            logger.exception("Async loader error: %s", error_msg)
            self.error_occurred.emit("Error", error_msg)

    def cancel(self) -> None:
        """Request cancellation of the loading operation.

        Sets a flag that the run() method checks at strategic points.
        This is a cooperative cancellation - the thread will finish its
        current operation before checking the flag.

        Note: This does NOT forcefully terminate the thread (unsafe in Qt).
              The thread will complete its current atomic operation and
              then check the flag at the next cancellation point.
        """
        logger.debug("Async loader: cancellation requested for chapter %d", self._chapter_index)
        self._cancelled = True
