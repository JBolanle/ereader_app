"""Book viewer widget for displaying EPUB chapter content.

This module provides the BookViewer class, which wraps QTextBrowser to
display HTML/XHTML content from EPUB chapters. It implements the BookRenderer
protocol to allow swapping implementations in the future.
"""

import logging

from PyQt6.QtWidgets import QTextBrowser, QWidget

logger = logging.getLogger(__name__)


class BookViewer(QTextBrowser):
    """Widget for displaying book chapter content.

    This class wraps QTextBrowser to provide a clean interface for displaying
    EPUB chapter content. It implements the BookRenderer protocol, allowing
    it to be swapped with other rendering implementations (e.g., QWebEngineView)
    without changing controller code.

    QTextBrowser supports a subset of HTML 4 and CSS, which is sufficient for
    most EPUB books. It's lightweight and has a simple API.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the book viewer.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing BookViewer")

        # Configure the text browser
        self.setReadOnly(True)  # Book content is read-only
        self.setOpenExternalLinks(False)  # Don't open external links
        self.setOpenLinks(False)  # Don't follow internal links (for now)

        # Set default styling for readability
        self._setup_default_style()

        logger.debug("BookViewer initialized")

    def _setup_default_style(self) -> None:
        """Configure default styling for better readability."""
        logger.debug("Setting up default style")

        # Set base font size (can be customized later)
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        # Add some padding via stylesheet
        self.setStyleSheet("""
            QTextBrowser {
                padding: 20px;
                background-color: white;
                color: black;
            }
        """)

        logger.debug("Default style applied")

    def set_content(self, html: str) -> None:
        """Display HTML content in the viewer.

        This method implements the BookRenderer protocol. It takes HTML
        content (typically from an EPUB chapter) and displays it in the
        text browser widget.

        Args:
            html: HTML content to display (XHTML from EPUB chapter).
        """
        logger.debug("Setting content, length: %d bytes", len(html))
        self.setHtml(html)
        logger.debug("Content set successfully")

    def clear(self) -> None:
        """Clear all displayed content.

        This method implements the BookRenderer protocol. It removes all
        content from the viewer.
        """
        logger.debug("Clearing viewer content")
        super().clear()
        logger.debug("Content cleared")

    def set_base_font_size(self, size: int) -> None:
        """Set the base font size for displayed content.

        This method is for future font customization features.

        Args:
            size: Font size in points.
        """
        logger.debug("Setting base font size to %d", size)
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        logger.debug("Font size updated")
