"""Collection sidebar widget for library navigation.

This module provides the CollectionSidebarWidget that displays smart collections
and user-created collections in a hierarchical tree structure.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ereader.models.library_database import LibraryRepository

logger = logging.getLogger(__name__)


class CollectionSidebarWidget(QWidget):
    """Sidebar widget for collection navigation.

    Displays two sections in a tree structure:
    1. Smart Collections (Recent Reads, Favorites, etc.) - always visible
    2. My Collections (user-created) - from database

    Signals:
        collection_selected: Emitted when user selects a collection.
            Args: collection_type (str), collection_id (int | str | None)
                  - For "All Books": ("all", None)
                  - For smart collections: ("smart", name like "recent_reads")
                  - For user collections: ("user", collection_id)
        add_collection_requested: Emitted when user clicks add collection button.
    """

    # Signals
    collection_selected = pyqtSignal(str, object)  # (type, id_or_name)
    add_collection_requested = pyqtSignal()

    def __init__(self, repository: LibraryRepository, parent=None) -> None:
        """Initialize the collection sidebar.

        Args:
            repository: Library repository for loading collections.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing CollectionSidebarWidget")

        self._repository = repository

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("Library")
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 20px; "
            "background: transparent;"
        )
        layout.addWidget(header)

        # Collection tree
        self._tree = QTreeWidget(self)
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(15)
        self._tree.setRootIsDecorated(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.setStyleSheet(
            """
            QTreeWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QTreeWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background: rgba(0, 0, 0, 0.05);
            }
            QTreeWidget::item:selected {
                background: rgba(0, 0, 0, 0.1);
            }
            """
        )
        layout.addWidget(self._tree)

        # Actions toolbar (bottom)
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 10, 10, 10)

        self._add_collection_btn = QPushButton("+")
        self._add_collection_btn.setToolTip("Create new collection")
        self._add_collection_btn.setFixedSize(32, 32)
        self._add_collection_btn.clicked.connect(self._on_add_collection)
        self._add_collection_btn.setStyleSheet(
            """
            QPushButton {
                font-size: 18px;
                border-radius: 16px;
                background: rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.15);
            }
            """
        )
        toolbar.addWidget(self._add_collection_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Populate tree
        self._populate_tree()

        logger.debug("CollectionSidebarWidget initialized")

    def _populate_tree(self) -> None:
        """Build the collection tree structure."""
        logger.debug("Populating collection tree")

        self._tree.clear()

        # === LIBRARY SECTION (Smart Collections) ===
        library_section = QTreeWidgetItem(self._tree)
        library_section.setText(0, "📚 Library")
        library_section.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Section header, not selectable
        library_section.setExpanded(True)

        # All Books (default view)
        all_item = QTreeWidgetItem(library_section)
        all_item.setText(0, "   All Books")
        all_item.setData(0, Qt.ItemDataRole.UserRole, ("all", None))

        # Recent Reads
        recent_item = QTreeWidgetItem(library_section)
        recent_item.setText(0, "   📖 Recent Reads")
        recent_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "recent_reads"))

        # Favorites
        favorites_item = QTreeWidgetItem(library_section)
        favorites_item.setText(0, "   ⭐ Favorites")
        favorites_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "favorites"))

        # Currently Reading
        reading_item = QTreeWidgetItem(library_section)
        reading_item.setText(0, "   📗 Currently Reading")
        reading_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "currently_reading"))

        # To Read
        to_read_item = QTreeWidgetItem(library_section)
        to_read_item.setText(0, "   📙 To Read")
        to_read_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "to_read"))

        # === MY COLLECTIONS SECTION (User Collections) ===
        user_section = QTreeWidgetItem(self._tree)
        user_section.setText(0, "📂 My Collections")
        user_section.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Section header, not selectable
        user_section.setExpanded(True)

        # Load user collections from database
        try:
            collections = self._repository.get_all_collections()
            logger.debug("Loaded %d user collections", len(collections))

            if not collections:
                # Show hint when no collections
                empty_item = QTreeWidgetItem(user_section)
                empty_item.setText(0, "   (no collections yet)")
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable or enabled
                empty_item.setForeground(0, Qt.GlobalColor.gray)
            else:
                for collection in collections:
                    coll_item = QTreeWidgetItem(user_section)
                    coll_item.setText(0, f"   📁 {collection.name} ({collection.book_count})")
                    coll_item.setData(0, Qt.ItemDataRole.UserRole, ("user", collection.id))

        except Exception as e:
            logger.error("Failed to load user collections: %s", e)
            error_item = QTreeWidgetItem(user_section)
            error_item.setText(0, "   (error loading collections)")
            error_item.setFlags(Qt.ItemFlag.NoItemFlags)
            error_item.setForeground(0, Qt.GlobalColor.red)

        logger.debug("Collection tree populated")

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle collection item click.

        Args:
            item: Clicked tree item.
            column: Column index (unused).
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            # Clicked on section header or empty item
            logger.debug("Clicked on non-selectable item")
            return

        collection_type, collection_id = data
        logger.debug("Collection selected: type=%s, id=%s", collection_type, collection_id)

        self.collection_selected.emit(collection_type, collection_id)

    def _on_add_collection(self) -> None:
        """Handle add collection button click."""
        logger.debug("Add collection button clicked")
        self.add_collection_requested.emit()

    def refresh_collections(self) -> None:
        """Refresh the collection list from database.

        Call this after creating, renaming, or deleting collections.
        """
        logger.debug("Refreshing collection tree")
        self._populate_tree()
