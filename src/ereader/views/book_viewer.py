"""Book viewer widget for displaying EPUB chapter content.

This module provides the BookViewer class, which uses composition to wrap
QTextBrowser for displaying HTML/XHTML content from EPUB chapters. It implements
the BookRenderer protocol to allow swapping implementations in the future.
"""

import logging

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class BookViewer(QWidget):
    """Widget for displaying book chapter content.

    This class uses composition to wrap QTextBrowser, providing a clean interface
    for displaying EPUB chapter content. It implements the BookRenderer protocol,
    allowing the rendering implementation to be easily swapped (e.g., to
    QWebEngineView) without changing controller code.

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

        # Create the text browser renderer
        self._renderer = QTextBrowser(self)

        # Configure the text browser
        self._renderer.setReadOnly(True)  # Book content is read-only
        self._renderer.setOpenExternalLinks(False)  # Don't open external links
        self._renderer.setOpenLinks(False)  # Don't follow internal links (for now)

        # Set default styling for readability
        self._setup_default_style()

        # Setup layout
        layout = QVBoxLayout(self)
        layout.addWidget(self._renderer)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Show welcome message
        self._show_welcome_message()

        logger.debug("BookViewer initialized")

    def _setup_default_style(self) -> None:
        """Configure default styling for better readability."""
        logger.debug("Setting up default style")

        # Set base font size (can be customized later)
        font = self._renderer.font()
        font.setPointSize(12)
        self._renderer.setFont(font)

        # Add some padding via stylesheet
        self._renderer.setStyleSheet("""
            QTextBrowser {
                padding: 20px;
                background-color: white;
                color: black;
            }
        """)

        logger.debug("Default style applied")

    def _show_welcome_message(self) -> None:
        """Display a welcome message when no book is loaded."""
        welcome_html = """
        <html>
        <body style="text-align: center; padding-top: 100px; font-family: sans-serif;">
            <h1>Welcome to E-Reader</h1>
            <p style="color: gray;">Open an EPUB file to start reading</p>
            <p style="color: gray; font-size: 0.9em;">File → Open (Ctrl+O)</p>
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
