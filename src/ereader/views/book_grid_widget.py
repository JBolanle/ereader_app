"""Grid view widget for displaying books in library.

This module provides the BookGridWidget class that displays books in a
responsive grid layout using Qt's model/view architecture.
"""

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QListView

from ereader.models.book_metadata import BookMetadata
from ereader.views.book_card_delegate import BookCardDelegate
from ereader.views.book_list_model import BookListModel

logger = logging.getLogger(__name__)


class BookGridWidget(QListView):
    """Grid view of book cards using Qt model/view architecture.

    This widget displays books in a responsive grid layout. It uses:
    - BookListModel for data management
    - BookCardDelegate for custom card rendering
    - QListView in IconMode for grid layout

    The grid automatically adjusts the number of columns based on
    the available width, with 20px spacing between cards.

    Signals:
        book_selected: Emitted when a book is clicked.
            Args: book_id (int)
        book_activated: Emitted when a book is double-clicked or Enter pressed.
            Args: book_id (int)
    """

    # Signals
    book_selected = pyqtSignal(int)  # book_id
    book_activated = pyqtSignal(int)  # book_id

    def __init__(self, parent=None) -> None:
        """Initialize the book grid widget.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing BookGridWidget")

        # Configure list view for grid display
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setSpacing(20)  # 20px between cards
        self.setUniformItemSizes(True)  # Performance hint

        # Enable selection
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)

        # Set custom delegate for card rendering
        self._delegate = BookCardDelegate(self)
        self.setItemDelegate(self._delegate)

        # Set model
        self._model = BookListModel([], self)
        self.setModel(self._model)

        # Connect signals
        self.clicked.connect(self._on_clicked)
        self.activated.connect(self._on_activated)  # Double-click or Enter

        logger.debug("BookGridWidget initialized")

    def set_books(self, books: list[BookMetadata]) -> None:
        """Update the list of books to display.

        Args:
            books: List of books to display in the grid.
        """
        logger.debug("Setting %d books in grid", len(books))
        self._model.set_books(books)

    def _on_clicked(self, index) -> None:
        """Handle book click (single click).

        Args:
            index: Model index of clicked item.
        """
        book = self._model.get_book(index)
        if book:
            logger.debug("Book clicked: %s (ID: %d)", book.title, book.id)
            self.book_selected.emit(book.id)

    def _on_activated(self, index) -> None:
        """Handle book activation (double-click or Enter).

        Args:
            index: Model index of activated item.
        """
        book = self._model.get_book(index)
        if book:
            logger.debug("Book activated: %s (ID: %d)", book.title, book.id)
            self.book_activated.emit(book.id)
