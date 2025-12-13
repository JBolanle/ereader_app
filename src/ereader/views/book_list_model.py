"""Qt model for book list in library view.

This module provides the BookListModel class that implements Qt's model/view
architecture for displaying books in the library grid.
"""

import logging

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt

from ereader.models.book_metadata import BookMetadata

logger = logging.getLogger(__name__)


class BookListModel(QAbstractListModel):
    """Qt model for list of books.

    This model implements QAbstractListModel to provide book data to
    QListView for grid display. It follows Qt's model/view architecture
    for efficient rendering and updates.

    The model stores BookMetadata objects and provides them to the view
    via the data() method using the UserRole.
    """

    def __init__(self, books: list[BookMetadata] | None = None, parent=None) -> None:
        """Initialize the book list model.

        Args:
            books: Initial list of books (defaults to empty list).
            parent: Parent QObject (optional).
        """
        super().__init__(parent)
        self._books = books if books is not None else []
        logger.debug("BookListModel initialized with %d books", len(self._books))

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows in the model.

        Args:
            parent: Parent index (unused for list models).

        Returns:
            Number of books in the model.
        """
        # List models should return 0 when parent is valid
        if parent.isValid():
            return 0
        return len(self._books)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Return data for the given index and role.

        Args:
            index: Model index.
            role: Data role.

        Returns:
            BookMetadata for UserRole, title for DisplayRole, None otherwise.
        """
        if not index.isValid():
            return None

        if index.row() >= len(self._books):
            return None

        book = self._books[index.row()]

        if role == Qt.ItemDataRole.UserRole:
            # Return full BookMetadata for delegate to render
            return book
        elif role == Qt.ItemDataRole.DisplayRole:
            # Return title for accessibility/search
            return book.title
        elif role == Qt.ItemDataRole.ToolTipRole:
            # Return tooltip with full title and author
            return str(book)  # Uses BookMetadata.__str__()

        return None

    def set_books(self, books: list[BookMetadata]) -> None:
        """Update the book list.

        This method triggers a model reset, causing the view to refresh.
        Use this when the book list changes (e.g., after import, filter).

        Args:
            books: New list of books to display.
        """
        logger.debug("Updating book list: %d books", len(books))

        # Notify view that model is about to be reset
        self.beginResetModel()

        # Update internal data
        self._books = books

        # Notify view that model has been reset
        self.endResetModel()

        logger.debug("Book list updated successfully")

    def get_book(self, index: QModelIndex) -> BookMetadata | None:
        """Get book at the given index.

        Args:
            index: Model index.

        Returns:
            BookMetadata if index is valid, None otherwise.
        """
        if not index.isValid() or index.row() >= len(self._books):
            return None
        return self._books[index.row()]
