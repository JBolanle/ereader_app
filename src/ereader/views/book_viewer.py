"""Book viewer widget for displaying EPUB chapter content.

This module provides the BookViewer class, which uses composition to wrap
QTextBrowser for displaying HTML/XHTML content from EPUB chapters. It implements
the BookRenderer protocol to allow swapping implementations in the future.
"""

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from ereader.models.theme import DEFAULT_THEME, Theme

logger = logging.getLogger(__name__)


class BookViewer(QWidget):
    """Widget for displaying book chapter content.

    This class uses composition to wrap QTextBrowser, providing a clean interface
    for displaying EPUB chapter content. It implements the BookRenderer protocol,
    allowing the rendering implementation to be easily swapped (e.g., to
    QWebEngineView) without changing controller code.

    QTextBrowser supports a subset of HTML 4 and CSS, which is sufficient for
    most EPUB books. It's lightweight and has a simple API.

    Signals:
        scroll_position_changed: Emitted when scroll position changes.
            Args: percentage (float) from 0.0 to 100.0
    """

    # Signals
    scroll_position_changed = pyqtSignal(float)  # percentage 0-100

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the book viewer.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing BookViewer")

        # Create the text browser renderer
        self._renderer = QTextBrowser(self)

        # Configure the text browser
        self._renderer.setReadOnly(True)  # Book content is read-only
        self._renderer.setOpenExternalLinks(False)  # Don't open external links
        self._renderer.setOpenLinks(False)  # Don't follow internal links (for now)

        # Apply default theme (includes font settings via stylesheet)
        self._current_theme = DEFAULT_THEME
        self.apply_theme(DEFAULT_THEME)

        # Setup layout
        layout = QVBoxLayout(self)
        layout.addWidget(self._renderer)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Show welcome message
        self._show_welcome_message()

        # Connect scrollbar changes to emit our signal
        # Note: Connected after initial content load to avoid spurious 0% emission
        # during initialization before any controllers are connected
        self._renderer.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

        logger.debug("BookViewer initialized")

    def apply_theme(self, theme: Theme) -> None:
        """Apply a visual theme to the book viewer.

        This method updates the stylesheet of the text browser to use the
        comprehensive styling defined in the provided theme, including
        typography, colors, and scrollbar styling.

        Args:
            theme: The theme to apply.
        """
        logger.debug("Applying theme: %s", theme.name)

        # Store current theme and apply comprehensive stylesheet
        self._current_theme = theme
        self._renderer.setStyleSheet(theme.get_book_viewer_stylesheet())

        # Refresh welcome message to use new theme colors
        if self._renderer.toPlainText().strip().startswith("Welcome to E-Reader"):
            self._show_welcome_message()

        logger.debug("Theme applied: %s", theme.name)

    def _show_welcome_message(self) -> None:
        """Display a welcome message when no book is loaded."""
        welcome_html = f"""
        <html>
        <body style="text-align: center; padding-top: 100px;
                     font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                                 'Segoe UI', system-ui, sans-serif;">
            <h1 style="color: {self._current_theme.text};
                       font-weight: 300;
                       font-size: 2.5em;
                       margin-bottom: 0.5em;">
                Welcome to E-Reader
            </h1>
            <p style="color: {self._current_theme.text_secondary};
                      font-size: 1.1em;
                      margin: 0.5em 0;">
                Open an EPUB file to start reading
            </p>
            <p style="color: {self._current_theme.text_secondary};
                      font-size: 0.95em;
                      margin-top: 1.5em;">
                File → Open (Ctrl+O)
            </p>
        </body>
        </html>
        """
        self._renderer.setHtml(welcome_html)

    def set_content(self, html: str) -> None:
        """Display HTML content in the viewer.

        This method implements the BookRenderer protocol. It takes HTML
        content (typically from an EPUB chapter) and displays it in the
        text browser widget.

        Args:
            html: HTML content to display (XHTML from EPUB chapter).
        """
        logger.debug("Setting content, length: %d bytes", len(html))
        self._renderer.setHtml(html)
        logger.debug("Content set successfully")

    def clear(self) -> None:
        """Clear all displayed content.

        This method implements the BookRenderer protocol. It removes all
        content from the viewer.
        """
        logger.debug("Clearing viewer content")
        self._renderer.clear()
        logger.debug("Content cleared")

    def set_base_font_size(self, size: int) -> None:
        """Set the base font size for displayed content.

        This method is for future font customization features.

        Args:
            size: Font size in points.
        """
        logger.debug("Setting base font size to %d", size)
        font = self._renderer.font()
        font.setPointSize(size)
        self._renderer.setFont(font)
        logger.debug("Font size updated")

    def scroll_by_pages(self, pages: float) -> None:
        """Scroll by a number of pages (viewport heights).

        Args:
            pages: Number of pages to scroll. Positive = down, negative = up.
                   Examples: 0.5 = half page down, -1.0 = full page up, 1.0 = page down.
        """
        logger.debug("Scrolling by %.1f pages", pages)
        scrollbar = self._renderer.verticalScrollBar()

        # Calculate new position
        page_step = scrollbar.pageStep()
        current_value = scrollbar.value()
        scroll_amount = int(pages * page_step)
        new_value = current_value + scroll_amount

        # Clamp to valid range
        minimum = scrollbar.minimum()
        maximum = scrollbar.maximum()
        clamped_value = max(minimum, min(maximum, new_value))

        logger.debug(
            "Scroll calculation: current=%d, amount=%d, new=%d, clamped=%d (range: %d-%d)",
            current_value,
            scroll_amount,
            new_value,
            clamped_value,
            minimum,
            maximum,
        )

        # Set new value (signal emitted automatically via valueChanged connection)
        scrollbar.setValue(clamped_value)

    def scroll_to_top(self) -> None:
        """Scroll to the top of the chapter."""
        logger.debug("Scrolling to top")
        scrollbar = self._renderer.verticalScrollBar()
        scrollbar.setValue(scrollbar.minimum())

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the chapter."""
        logger.debug("Scrolling to bottom")
        scrollbar = self._renderer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_scroll_percentage(self) -> float:
        """Get current scroll position as a percentage (0-100).

        Returns:
            Float from 0.0 to 100.0 representing scroll position.
            0.0 = at top, 100.0 = at bottom.
            If content is not scrollable (fits in viewport), returns 0.0.
        """
        scrollbar = self._renderer.verticalScrollBar()
        value = scrollbar.value()
        minimum = scrollbar.minimum()
        maximum = scrollbar.maximum()

        # Check if scrollable
        if maximum == minimum:
            logger.debug("Content not scrollable, returning 0.0%%")
            return 0.0

        # Calculate percentage
        percentage = ((value - minimum) / (maximum - minimum)) * 100.0
        logger.debug("Scroll percentage: %.1f%%", percentage)
        return percentage

    def _on_scroll_changed(self) -> None:
        """Handle scroll position changes and emit signal.

        Called when the scrollbar value changes, either from user interaction
        or programmatic scrolling. Emits scroll_position_changed signal with
        the current scroll percentage.
        """
        percentage = self.get_scroll_percentage()
        logger.debug("Scroll changed, emitting signal: %.1f%%", percentage)
        self.scroll_position_changed.emit(percentage)

    # Pagination support methods (Phase 2A)

    def get_content_height(self) -> int:
        """Get total height of rendered content.

        Returns:
            Total height of the document in pixels.
        """
        return int(self._renderer.document().size().height())

    def get_viewport_height(self) -> int:
        """Get height of visible viewport.

        Returns:
            Height of the viewport in pixels.
        """
        return self._renderer.viewport().height()

    def set_scroll_position(self, position: int) -> None:
        """Set scroll position to specific pixel value.

        The scrollbar will automatically clamp the value to valid range.

        Args:
            position: Scroll position in pixels.
        """
        logger.debug("Setting scroll position to %dpx", position)
        scrollbar = self._renderer.verticalScrollBar()
        scrollbar.setValue(position)

    def get_scroll_position(self) -> int:
        """Get current scroll position in pixels.

        Returns:
            Current scroll position in pixels.
        """
        return self._renderer.verticalScrollBar().value()
