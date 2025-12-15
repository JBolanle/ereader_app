"""Remove book confirmation dialog.

This module provides the RemoveBookDialog class that confirms book removal
with an option to also delete the file from disk.
"""

import logging
from enum import Enum

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ereader.models.book_metadata import BookMetadata

logger = logging.getLogger(__name__)


class RemoveBookResult(Enum):
    """Result of remove book dialog."""
    CANCEL = 0
    REMOVE_ONLY = 1
    REMOVE_AND_DELETE = 2


class RemoveBookDialog(QDialog):
    """Confirmation dialog for removing books from library.

    Provides two options:
    1. Remove from library only (safe - keeps file on disk)
    2. Remove from library AND delete file (destructive)

    Uses double confirmation for file deletion.
    """

    def __init__(self, book: BookMetadata, parent=None) -> None:
        """Initialize remove book dialog.

        Args:
            book: BookMetadata of book to remove.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing RemoveBookDialog for book: %s", book.title)

        self.setWindowTitle("Remove Book from Library?")
        self.setMinimumWidth(500)

        self._book = book
        self._result = RemoveBookResult.CANCEL
        self._init_ui()

        logger.debug("RemoveBookDialog initialized")

    def _init_ui(self) -> None:
        """Initialize UI layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title and author
        author = self._book.author if self._book.author else "Unknown Author"
        title_label = QLabel(f'<h3>"{self._book.title}"</h3><p>by {author}</p>')
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Explanation
        explanation = QLabel(
            "This will remove the book from your library.<br>"
            "The file will <b>NOT</b> be deleted from your disk."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        # Checkbox for file deletion
        self._delete_checkbox = QCheckBox("Also delete file from disk (permanent)")
        self._delete_checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self._delete_checkbox)

        # File path
        file_label = QLabel(f"<small><i>File: {self._book.file_path}</i></small>")
        file_label.setWordWrap(True)
        file_label.setStyleSheet("color: gray;")
        layout.addWidget(file_label)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Buttons (custom instead of QDialogButtonBox for styling)
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        # Remove/Delete button
        self._remove_button = QPushButton("Remove from Library")
        self._remove_button.clicked.connect(self._on_remove_clicked)
        self._remove_button.setDefault(True)  # Default button
        buttons_layout.addWidget(self._remove_button)

        layout.addLayout(buttons_layout)

    def _on_checkbox_changed(self, state: int) -> None:
        """Handle checkbox state change - update button text/style.

        Args:
            state: Qt.CheckState value.
        """
        if state == Qt.CheckState.Checked.value:
            logger.debug("File deletion checkbox checked")
            self._remove_button.setText("Delete Book and File")
            self._remove_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
                """
            )
        else:
            logger.debug("File deletion checkbox unchecked")
            self._remove_button.setText("Remove from Library")
            self._remove_button.setStyleSheet("")

    def _on_remove_clicked(self) -> None:
        """Handle remove/delete button click."""
        if self._delete_checkbox.isChecked():
            logger.debug("User requested file deletion - showing double confirmation")
            # Show second confirmation for destructive action
            reply = QMessageBox.warning(
                self,
                "⚠️ Delete Book and File?",
                f"This will PERMANENTLY DELETE the file:\n\n{self._book.file_path}\n\n"
                "This action cannot be undone.\n"
                "The book will be removed from your library and the file will be deleted from your disk.",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Ok:
                logger.debug("User confirmed file deletion")
                self._result = RemoveBookResult.REMOVE_AND_DELETE
                self.accept()
            else:
                logger.debug("User cancelled file deletion")
        else:
            logger.debug("User chose to remove from library only")
            self._result = RemoveBookResult.REMOVE_ONLY
            self.accept()

    def get_result(self) -> RemoveBookResult:
        """Get dialog result after exec().

        Returns:
            RemoveBookResult indicating user's choice.
        """
        return self._result
