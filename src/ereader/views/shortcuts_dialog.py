"""Keyboard shortcuts help dialog.

This module provides a modal dialog that displays all available keyboard
shortcuts organized by category for user reference and discoverability.
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

# Shortcuts data organized by category
SHORTCUTS_DATA = {
    "Navigation": [
        ("Left/Right Arrow", "Navigate (scroll/page based on mode)"),
        ("Page Up/Down", "Full page navigation"),
        ("Home/End", "Jump to chapter beginning/end"),
        ("Ctrl+G", "Go to specific page"),
    ],
    "Chapters": [
        ("Ctrl+Left/Right", "Previous/Next chapter"),
        ("Ctrl+Home/End", "First/Last chapter"),
    ],
    "View": [
        ("Ctrl+M", "Toggle scroll/page mode"),
        ("Ctrl+Shift+H", "Toggle auto-hide navigation"),
        ("Ctrl+T", "Toggle theme (Light/Dark)"),
    ],
    "File": [
        ("Ctrl+O", "Open book"),
        ("Ctrl+Q", "Quit"),
    ],
    "Help": [
        ("F1", "Show keyboard shortcuts"),
    ],
}


class ShortcutsDialog(QDialog):
    """Modal dialog displaying keyboard shortcuts organized by category.

    This dialog provides a comprehensive reference for all available keyboard
    shortcuts in the application, organized by functional category for easy
    discovery.

    Categories:
    - Navigation: Arrow keys, page navigation, chapter navigation
    - Chapters: Chapter-specific shortcuts
    - View: Theme, mode, and UI toggles
    - File: File operations
    - Help: Help-related shortcuts
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the keyboard shortcuts dialog.

        Args:
            parent: Parent widget (typically MainWindow).
        """
        super().__init__(parent)
        logger.debug("Initializing ShortcutsDialog")

        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.resize(550, 650)

        self._setup_ui()

        logger.debug("ShortcutsDialog initialized")

    def _setup_ui(self) -> None:
        """Create dialog layout with shortcuts organized by category."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title label
        title_label = QLabel("Keyboard Shortcuts")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Add category sections
        for category in ["Navigation", "Chapters", "View", "File", "Help"]:
            section = self._create_category_section(category)
            layout.addWidget(section)

        # Add stretch to push close button to bottom
        layout.addStretch()

        # Close button (centered)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.setMinimumWidth(100)
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)  # Make it default (Enter key closes)
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _create_category_section(self, category: str) -> QWidget:
        """Create a section with category heading and shortcuts table.

        Args:
            category: The category name (must exist in SHORTCUTS_DATA).

        Returns:
            QGroupBox containing the shortcuts table for this category.
        """
        group_box = QGroupBox(category)
        layout = QVBoxLayout(group_box)

        # Create table for shortcuts
        shortcuts = SHORTCUTS_DATA.get(category, [])
        table = QTableWidget(len(shortcuts), 2)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])

        # Populate table
        for row, (shortcut, action) in enumerate(shortcuts):
            # Shortcut cell (bold, monospace)
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_font = shortcut_item.font()
            shortcut_font.setBold(True)
            shortcut_font.setFamily("monospace")
            shortcut_item.setFont(shortcut_font)
            shortcut_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Read-only
            table.setItem(row, 0, shortcut_item)

            # Action cell
            action_item = QTableWidgetItem(action)
            action_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Read-only
            table.setItem(row, 1, action_item)

        # Table styling
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        # Adjust column widths
        table.setColumnWidth(0, 180)  # Shortcut column

        # Set fixed height based on content
        row_height = table.rowHeight(0) if shortcuts else 30
        header_height = table.horizontalHeader().height()
        table_height = header_height + (row_height * len(shortcuts)) + 4
        table.setFixedHeight(table_height)

        layout.addWidget(table)
        return group_box

    def keyPressEvent(self, event) -> None:
        """Handle key press events.

        Escape key closes the dialog in addition to the Close button.

        Args:
            event: The key press event.
        """
        if event.key() == Qt.Key.Key_Escape:
            logger.debug("Escape key pressed, closing shortcuts dialog")
            self.reject()
        else:
            super().keyPressEvent(event)
