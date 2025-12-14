"""Library view widget - main library interface container.

This module provides the LibraryView class that serves as the main container
for the library interface, including the book grid and empty state.
"""

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ereader.models.book_metadata import BookMetadata
from ereader.views.book_grid_widget import BookGridWidget
from ereader.views.empty_library_widget import EmptyLibraryWidget

logger = logging.getLogger(__name__)


class LibraryView(QWidget):
    """Main library view container.

    This widget serves as the container for the library interface. It switches
    between the empty state (EmptyLibraryWidget) and the book grid (BookGridWidget)
    based on whether the library has books.

    The view uses a QStackedWidget to switch between:
    - Index 0: EmptyLibraryWidget (shown when no books)
    - Index 1: BookGridWidget (shown when books exist)

    Signals:
        book_open_requested: Emitted when user wants to open a book.
            Args: book_id (int)
        import_requested: Emitted when user wants to import books.
    """

    # Signals
    book_open_requested = pyqtSignal(int)  # book_id
    import_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """Initialize the library view.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing LibraryView")

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create stacked widget for empty state / grid view
        self._stacked_widget = QStackedWidget(self)

        # Page 0: Empty state
        self._empty_widget = EmptyLibraryWidget(self)
        self._empty_widget.import_requested.connect(self._on_import_requested)
        self._stacked_widget.addWidget(self._empty_widget)

        # Page 1: Book grid
        self._grid_widget = BookGridWidget(self)
        self._grid_widget.book_selected.connect(self._on_book_selected)
        self._grid_widget.book_activated.connect(self._on_book_activated)
        self._stacked_widget.addWidget(self._grid_widget)

        # Add stacked widget to layout
        layout.addWidget(self._stacked_widget)

        # Start with empty state
        self._stacked_widget.setCurrentIndex(0)

        logger.debug("LibraryView initialized")

    def set_books(self, books: list[BookMetadata]) -> None:
        """Update the library with books.

        If books is empty, shows the empty state. Otherwise, shows the grid.

        Args:
            books: List of books to display.
        """
        logger.debug("Setting %d books in library view", len(books))

        if not books:
            # Show empty state
            self._stacked_widget.setCurrentIndex(0)
            logger.debug("Showing empty state (no books)")
        else:
            # Show grid
            self._grid_widget.set_books(books)
            self._stacked_widget.setCurrentIndex(1)
            logger.debug("Showing grid with %d books", len(books))

    def show_empty_state(self) -> None:
        """Explicitly show the empty state.

        This can be called to show the empty state even if there are books
        (e.g., during error conditions).
        """
        logger.debug("Explicitly showing empty state")
        self._stacked_widget.setCurrentIndex(0)

    def _on_book_selected(self, book_id: int) -> None:
        """Handle book selection (single click).

        Args:
            book_id: Database ID of selected book.
        """
        logger.debug("Book selected: %d", book_id)
        # Currently no action on single click (just selection highlight)
        # Could be used for showing book details in Phase 3

    def _on_book_activated(self, book_id: int) -> None:
        """Handle book activation (double-click or Enter).

        Args:
            book_id: Database ID of activated book.
        """
        logger.debug("Book activated: %d", book_id)
        self.book_open_requested.emit(book_id)

    def _on_import_requested(self) -> None:
        """Handle import request from empty state."""
        logger.debug("Import requested from empty state")
        self.import_requested.emit()
