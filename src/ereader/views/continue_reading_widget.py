"""Continue Reading widget for library view.

This module provides the ContinueReadingWidget class that displays a horizontal
scroll of recently opened books, allowing quick access to resume reading.
"""

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ereader.models.book_metadata import BookMetadata

logger = logging.getLogger(__name__)


class BookCardWidget(QWidget):
    """Individual book card for Continue Reading section.

    This widget represents a single book card with cover, title, and progress.
    It's smaller than the main grid cards (120×180px vs 180×260px).

    Signals:
        clicked: Emitted when the card is clicked.
            Args: book_id (int)
    """

    # Card dimensions (smaller than main grid)
    CARD_WIDTH = 120
    CARD_HEIGHT = 180

    # Layout constants
    COVER_WIDTH = 100
    COVER_HEIGHT = 133
    PADDING = 10

    clicked = pyqtSignal(int)  # book_id

    def __init__(self, book: BookMetadata, parent=None) -> None:
        """Initialize the book card widget.

        Args:
            book: Book metadata to display.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        self._book = book

        # Set fixed size
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)

        # Enable hover and click
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        # Track hover state for visual feedback
        self._is_hovered = False

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Cover image (or placeholder)
        self._cover_label = QLabel(self)
        self._cover_label.setFixedSize(self.COVER_WIDTH, self.COVER_HEIGHT)
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_label.setStyleSheet(
            """
            QLabel {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            """
        )

        # Load cover or show placeholder
        if book.cover_path and Path(book.cover_path).exists():
            pixmap = QPixmap(book.cover_path)
            if not pixmap.isNull():
                # Scale to fit cover area while maintaining aspect ratio
                scaled = pixmap.scaled(
                    self.COVER_WIDTH,
                    self.COVER_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._cover_label.setPixmap(scaled)
            else:
                self._cover_label.setText("📖")
                self._cover_label.setStyleSheet(
                    self._cover_label.styleSheet() + "font-size: 48px;"
                )
        else:
            self._cover_label.setText("📖")
            self._cover_label.setStyleSheet(
                self._cover_label.styleSheet() + "font-size: 48px;"
            )

        layout.addWidget(self._cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title (1 line, truncated)
        title_label = QLabel(self)
        title_label.setText(book.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(False)
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #333;
            }
            """
        )
        # Truncate with ellipsis
        font_metrics = QFontMetrics(title_label.font())
        elided_text = font_metrics.elidedText(
            book.title, Qt.TextElideMode.ElideRight, self.CARD_WIDTH - 10
        )
        title_label.setText(elided_text)
        layout.addWidget(title_label)

        # Progress percentage
        progress_label = QLabel(f"{int(book.reading_progress)}%", self)
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_label.setStyleSheet(
            """
            QLabel {
                font-size: 10px;
                color: #666;
            }
            """
        )
        layout.addWidget(progress_label)

        # Set tooltip with full title and author
        tooltip = f"{book.title}\n{book.author if book.author else 'Unknown Author'}\n{int(book.reading_progress)}% complete"
        self.setToolTip(tooltip)

        logger.debug("BookCardWidget created for book ID %d", book.id)

    def enterEvent(self, event) -> None:
        """Handle mouse enter event for hover effect.

        Args:
            event: Enter event.
        """
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave event for hover effect.

        Args:
            event: Leave event.
        """
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press event to emit clicked signal.

        Args:
            event: Mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            logger.debug("Book card clicked: book ID %d", self._book.id)
            self.clicked.emit(self._book.id)
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        """Paint the widget with hover effect.

        Args:
            event: Paint event.
        """
        super().paintEvent(event)

        # Draw hover effect
        if self._is_hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Semi-transparent overlay
            painter.fillRect(self.rect(), QColor(0, 0, 0, 20))


class ContinueReadingWidget(QWidget):
    """Horizontal scroll widget showing recently opened books.

    This widget displays 3-5 most recently opened books in a horizontal
    scrollable layout, providing quick access to resume reading.

    Signals:
        book_activated: Emitted when a book card is clicked.
            Args: book_id (int)
    """

    book_activated = pyqtSignal(int)  # book_id

    def __init__(self, parent=None) -> None:
        """Initialize the Continue Reading widget.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing ContinueReadingWidget")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(8)

        # Title label
        title_label = QLabel("Continue Reading", self)
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding-left: 5px;
            }
            """
        )
        main_layout.addWidget(title_label)

        # Scroll area (horizontal)
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setStyleSheet(
            """
            QScrollArea {
                background-color: transparent;
            }
            """
        )

        # Container widget for book cards
        self._container = QWidget(self)
        self._container_layout = QHBoxLayout(self._container)
        self._container_layout.setContentsMargins(5, 5, 5, 5)
        self._container_layout.setSpacing(15)
        self._container_layout.addStretch()  # Push cards to the left

        self._scroll_area.setWidget(self._container)
        main_layout.addWidget(self._scroll_area)

        # Store book cards
        self._book_cards: list[BookCardWidget] = []

        logger.debug("ContinueReadingWidget initialized")

    def set_books(self, books: list[BookMetadata]) -> None:
        """Update the widget with recently opened books.

        Filters books to show only those that have been opened (last_opened_date
        is not None), sorts by most recent first, and limits to 5 books.

        Args:
            books: List of all books in the library.
        """
        logger.debug("Setting books for Continue Reading widget: %d total", len(books))

        # Clear existing cards
        self._clear_cards()

        # Filter to books that have been opened
        opened_books = [b for b in books if b.last_opened_date is not None]

        if not opened_books:
            logger.debug("No books have been opened yet")
            self.hide()
            return

        # Sort by last_opened_date descending (most recent first)
        opened_books.sort(key=lambda b: b.last_opened_date, reverse=True)

        # Limit to 5 books
        recent_books = opened_books[:5]
        logger.debug("Showing %d recently opened books", len(recent_books))

        # Create card for each book
        for book in recent_books:
            card = BookCardWidget(book, self)
            card.clicked.connect(self._on_book_clicked)
            self._container_layout.insertWidget(
                self._container_layout.count() - 1, card
            )
            self._book_cards.append(card)

        # Show widget
        self.show()

    def _clear_cards(self) -> None:
        """Remove all book cards from the layout."""
        for card in self._book_cards:
            card.clicked.disconnect()
            self._container_layout.removeWidget(card)
            card.deleteLater()

        self._book_cards.clear()
        logger.debug("Cleared all book cards")

    def _on_book_clicked(self, book_id: int) -> None:
        """Handle book card click.

        Args:
            book_id: ID of the clicked book.
        """
        logger.debug("Book card clicked in Continue Reading: book ID %d", book_id)
        self.book_activated.emit(book_id)
