"""Empty state widget for library view.

This module provides the EmptyLibraryWidget that displays when the library
has no books, prompting the user to import their first book.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class EmptyLibraryWidget(QWidget):
    """Empty state display for library with no books.

    This widget shows a friendly message and an "Import Books" button
    when the library is empty.

    Signals:
        import_requested: Emitted when user clicks "Import Books" button.
    """

    # Signal
    import_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """Initialize the empty library widget.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing EmptyLibraryWidget")

        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Icon/Emoji
        icon_label = QLabel("📚", self)
        icon_font = QFont("Arial", 64)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel("Your Library is Empty", self)
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Import EPUB files to get started", self)
        subtitle_font = QFont("Arial", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #757575;")  # Gray text
        layout.addWidget(subtitle_label)

        # Import button
        import_button = QPushButton("Import Books", self)
        import_button.setMinimumSize(150, 40)
        import_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            """
        )
        import_button.clicked.connect(self._on_import_clicked)
        layout.addWidget(import_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Keyboard shortcut hint
        shortcut_label = QLabel("(Ctrl+I)", self)
        shortcut_font = QFont("Arial", 10)
        shortcut_label.setFont(shortcut_font)
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_label.setStyleSheet("color: #9E9E9E;")  # Light gray
        layout.addWidget(shortcut_label)

        # Add stretch to center content vertically
        layout.addStretch()

        logger.debug("EmptyLibraryWidget initialized")

    def _on_import_clicked(self) -> None:
        """Handle import button click."""
        logger.debug("Import button clicked")
        self.import_requested.emit()
