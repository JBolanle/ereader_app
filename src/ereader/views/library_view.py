"""Library view widget - main library interface container.

This module provides the LibraryView class that serves as the main container
for the library interface, including sidebar navigation, search/sort controls,
and the book grid.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ereader.models.book_metadata import BookMetadata
from ereader.models.library_database import LibraryRepository
from ereader.models.library_filter import LibraryFilter
from ereader.views.book_grid_widget import BookGridWidget
from ereader.views.collection_sidebar_widget import CollectionSidebarWidget
from ereader.views.empty_library_widget import EmptyLibraryWidget

logger = logging.getLogger(__name__)


class LibraryView(QWidget):
    """Main library view container with sidebar and search/sort.

    This widget provides the complete library interface:
    - Left sidebar: Collection navigation (smart + user collections)
    - Right panel: Search box, sort dropdown, book grid, status label

    The view switches between empty state and full library based on book count.

    Signals:
        book_open_requested: Emitted when user wants to open a book.
            Args: book_id (int)
        import_requested: Emitted when user wants to import books.
        collection_filter_changed: Emitted when collection selection changes.
            Args: collection_type (str), collection_id (int | str | None)
    """

    # Signals
    book_open_requested = pyqtSignal(int)  # book_id
    import_requested = pyqtSignal()
    collection_filter_changed = pyqtSignal(str, object)  # (type, id_or_name)

    def __init__(self, repository: LibraryRepository, parent=None) -> None:
        """Initialize the library view.

        Args:
            repository: Library repository for loading collections and books.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing LibraryView")

        self._repository = repository
        self._current_filter = LibraryFilter()
        self._all_books: list[BookMetadata] = []

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create stacked widget for empty state / library with sidebar
        self._stacked_widget = QStackedWidget(self)

        # Page 0: Empty state
        self._empty_widget = EmptyLibraryWidget(self)
        self._empty_widget.import_requested.connect(self._on_import_requested)
        self._stacked_widget.addWidget(self._empty_widget)

        # Page 1: Library with sidebar (QSplitter)
        library_widget = QWidget(self)
        library_layout = QHBoxLayout(library_widget)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, library_widget)

        # LEFT: Sidebar
        self._sidebar = CollectionSidebarWidget(repository, self)
        self._sidebar.collection_selected.connect(self._on_collection_selected)
        self._sidebar.add_collection_requested.connect(self._on_add_collection_requested)
        self._splitter.addWidget(self._sidebar)

        # RIGHT: Main panel (search + grid + status)
        main_panel = QWidget(self)
        main_panel_layout = QVBoxLayout(main_panel)
        main_panel_layout.setContentsMargins(20, 20, 20, 20)
        main_panel_layout.setSpacing(15)

        # Header (search + sort)
        header_layout = QHBoxLayout()

        # Search box
        self._search_box = QLineEdit(self)
        self._search_box.setPlaceholderText("Search books...")
        self._search_box.textChanged.connect(self._on_search_changed)
        self._search_box.setClearButtonEnabled(True)
        self._search_box.setStyleSheet(
            """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #999;
            }
            """
        )
        header_layout.addWidget(self._search_box, stretch=1)

        header_layout.addSpacing(10)

        # Sort dropdown
        sort_label = QLabel("Sort:")
        header_layout.addWidget(sort_label)

        self._sort_combo = QComboBox(self)
        self._sort_combo.addItems([
            "Recent",
            "Title A-Z",
            "Author A-Z",
            "Progress"
        ])
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self._sort_combo.setStyleSheet(
            """
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 120px;
            }
            """
        )
        header_layout.addWidget(self._sort_combo)

        main_panel_layout.addLayout(header_layout)

        # Book grid
        self._grid_widget = BookGridWidget(self)
        self._grid_widget.book_selected.connect(self._on_book_selected)
        self._grid_widget.book_activated.connect(self._on_book_activated)
        main_panel_layout.addWidget(self._grid_widget)

        # Status label
        self._status_label = QLabel("", self)
        self._status_label.setStyleSheet("color: gray; font-size: 12px;")
        main_panel_layout.addWidget(self._status_label)

        self._splitter.addWidget(main_panel)

        # Set initial splitter sizes (sidebar 250px, main panel takes rest)
        self._splitter.setSizes([250, 750])

        # TODO: Load/save splitter state from QSettings

        library_layout.addWidget(self._splitter)
        self._stacked_widget.addWidget(library_widget)

        # Add stacked widget to main layout
        main_layout.addWidget(self._stacked_widget)

        # Start with empty state
        self._stacked_widget.setCurrentIndex(0)

        logger.debug("LibraryView initialized")

    def set_books(self, books: list[BookMetadata]) -> None:
        """Update the library with books.

        If books is empty, shows the empty state. Otherwise, shows the library
        with sidebar and grid.

        Args:
            books: List of all books in the library.
        """
        logger.debug("Setting %d books in library view", len(books))

        self._all_books = books

        if not books:
            # Show empty state
            self._stacked_widget.setCurrentIndex(0)
            logger.debug("Showing empty state (no books)")
        else:
            # Show library with sidebar
            self._stacked_widget.setCurrentIndex(1)
            # Apply current filter
            self._refresh_grid()
            logger.debug("Showing library with %d books", len(books))

    def show_empty_state(self) -> None:
        """Explicitly show the empty state.

        This can be called to show the empty state even if there are books
        (e.g., during error conditions).
        """
        logger.debug("Explicitly showing empty state")
        self._stacked_widget.setCurrentIndex(0)

    def refresh_sidebar(self) -> None:
        """Refresh the sidebar collection list.

        Call this after creating, renaming, or deleting collections.
        """
        logger.debug("Refreshing sidebar collections")
        self._sidebar.refresh_collections()

    def _on_search_changed(self, text: str) -> None:
        """Handle search box text change (real-time filtering).

        Args:
            text: Current search text.
        """
        logger.debug("Search text changed: '%s'", text)
        self._current_filter.search_query = text
        self._refresh_grid()

    def _on_sort_changed(self, index: int) -> None:
        """Handle sort selection change.

        Args:
            index: Selected combo box index.
        """
        sort_map = {
            0: "recent",
            1: "title",
            2: "author",
            3: "progress"
        }
        sort_by = sort_map.get(index, "recent")
        logger.debug("Sort changed to: %s", sort_by)
        self._current_filter.sort_by = sort_by
        self._refresh_grid()

    def _on_collection_selected(self, collection_type: str, collection_id) -> None:
        """Handle collection selection from sidebar.

        Args:
            collection_type: Type of collection ("all", "smart", or "user").
            collection_id: Collection identifier (None, str, or int).
        """
        logger.debug("Collection selected: type=%s, id=%s", collection_type, collection_id)

        # Update filter based on collection type
        if collection_type == "all":
            # All Books - clear all filters except search/sort
            search = self._current_filter.search_query
            sort = self._current_filter.sort_by
            self._current_filter = LibraryFilter(
                search_query=search,
                sort_by=sort
            )

        elif collection_type == "smart":
            # Smart collection - apply specific filter
            search = self._current_filter.search_query
            sort = self._current_filter.sort_by

            if collection_id == "recent_reads":
                self._current_filter = LibraryFilter(
                    search_query=search,
                    days_since_opened=30,
                    sort_by="recent"
                )
            elif collection_id == "currently_reading":
                self._current_filter = LibraryFilter(
                    search_query=search,
                    status="reading",
                    sort_by="recent"
                )
            elif collection_id == "to_read":
                self._current_filter = LibraryFilter(
                    search_query=search,
                    status="not_started",
                    sort_by="added_date_desc"
                )
            elif collection_id == "favorites":
                # TODO: Implement favorites when column added
                self._current_filter = LibraryFilter(
                    search_query=search,
                    sort_by=sort
                )

        elif collection_type == "user":
            # User collection - filter by collection_id
            search = self._current_filter.search_query
            sort = self._current_filter.sort_by
            self._current_filter = LibraryFilter(
                search_query=search,
                collection_id=collection_id,
                sort_by=sort
            )

        self._refresh_grid()
        self.collection_filter_changed.emit(collection_type, collection_id)

    def _on_add_collection_requested(self) -> None:
        """Handle add collection request from sidebar.

        NOTE: For now, this is a placeholder. The actual collection creation
        dialog will be implemented when we add controller integration.
        """
        logger.debug("Add collection requested (not yet implemented)")
        # TODO: Emit signal to controller to show collection creation dialog

    def _refresh_grid(self) -> None:
        """Refresh grid with current filter."""
        logger.debug("Refreshing grid with filter: %s", self._current_filter)

        # Query books with filter
        try:
            books = self._repository.filter_books(self._current_filter)
            logger.debug("Filter returned %d books", len(books))

            # Update grid
            self._grid_widget.set_books(books)

            # Update status label
            total_books = len(self._all_books)
            if len(books) == total_books:
                self._status_label.setText(f"{total_books} books")
            else:
                self._status_label.setText(f"Showing {len(books)} of {total_books} books")

        except Exception as e:
            logger.error("Failed to refresh grid: %s", e)
            self._status_label.setText("Error loading books")

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
