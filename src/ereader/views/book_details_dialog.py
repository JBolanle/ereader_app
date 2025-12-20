"""Book details dialog for displaying comprehensive book information.

This module provides the BookDetailsDialog class that shows read-only book
metadata, file information, reading progress, and library information in a
structured layout.
"""

import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

from ereader.models.book_metadata import BookMetadata

logger = logging.getLogger(__name__)


class BookDetailsDialog(QDialog):
    """Modal dialog displaying comprehensive book information.

    Shows read-only book metadata, file information, reading progress,
    and library information in a structured layout.
    """

    def __init__(self, book: BookMetadata, parent=None) -> None:
        """Initialize book details dialog.

        Args:
            book: BookMetadata to display.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing BookDetailsDialog for book: %s", book.title)

        self.setWindowTitle("Book Details")
        self.setMinimumSize(500, 600)

        self._book = book
        self._init_ui()

        logger.debug("BookDetailsDialog initialized")

    def _init_ui(self) -> None:
        """Initialize UI layout."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header section (cover + title/author)
        header_widget = self._create_header()
        layout.addWidget(header_widget)

        # File information section
        file_info_group = self._create_file_info_section()
        layout.addWidget(file_info_group)

        # Reading progress section
        progress_group = self._create_progress_section()
        layout.addWidget(progress_group)

        # Library information section
        library_group = self._create_library_info_section()
        layout.addWidget(library_group)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _create_header(self) -> QLabel:
        """Create header section with title and author.

        Returns:
            QWidget containing header content.
        """
        # For MVP, we'll use a simple text header
        # Phase 3 will add cover image display
        header_label = QLabel(self)

        title = self._book.title
        author = self._book.author if self._book.author else "Unknown Author"

        header_text = f"<h2>{title}</h2><p style='font-size: 14px; color: gray;'>by {author}</p>"
        header_label.setText(header_text)
        header_label.setWordWrap(True)

        return header_label

    def _create_file_info_section(self) -> QGroupBox:
        """Create file information section.

        Returns:
            QGroupBox with file information.
        """
        group = QGroupBox("File Information")
        layout = QVBoxLayout()

        # Location
        file_path = Path(self._book.file_path)
        location_label = QLabel(f"<b>Location:</b> {self._book.file_path}")
        location_label.setWordWrap(True)
        location_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(location_label)

        # Check if file exists
        if not file_path.exists():
            warning_label = QLabel("⚠️ <i>File not found at location</i>")
            warning_label.setStyleSheet("color: #d32f2f;")
            layout.addWidget(warning_label)

        # Size
        size_str = self._format_file_size(self._book.file_size)
        size_label = QLabel(f"<b>Size:</b> {size_str}")
        layout.addWidget(size_label)

        # Format
        format_label = QLabel("<b>Format:</b> EPUB")
        layout.addWidget(format_label)

        group.setLayout(layout)
        return group

    def _create_progress_section(self) -> QGroupBox:
        """Create reading progress section.

        Returns:
            QGroupBox with reading progress.
        """
        group = QGroupBox("Reading Progress")
        layout = QVBoxLayout()

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(int(self._book.reading_progress))
        progress_bar.setFormat(f"{self._book.reading_progress:.1f}% complete")
        layout.addWidget(progress_bar)

        # Current chapter
        chapter_label = QLabel(
            f"<b>Current Chapter:</b> Chapter {self._book.current_chapter_index + 1}"
        )
        layout.addWidget(chapter_label)

        # Status
        status_display = self._get_status_display(self._book.status)
        status_label = QLabel(f"<b>Status:</b> {status_display}")
        layout.addWidget(status_label)

        group.setLayout(layout)
        return group

    def _create_library_info_section(self) -> QGroupBox:
        """Create library information section.

        Returns:
            QGroupBox with library information.
        """
        group = QGroupBox("Library Information")
        layout = QVBoxLayout()

        # Added date
        added_str = self._format_datetime(self._book.added_date)
        added_label = QLabel(f"<b>Added:</b> {added_str}")
        layout.addWidget(added_label)

        # Last opened
        if self._book.last_opened_date:
            opened_str = self._format_datetime(self._book.last_opened_date)
        else:
            opened_str = "Never"
        opened_label = QLabel(f"<b>Last Opened:</b> {opened_str}")
        layout.addWidget(opened_label)

        # Collections (placeholder for Phase 2 collections integration)
        collections_label = QLabel("<b>Collections:</b> None")
        layout.addWidget(collections_label)

        group.setLayout(layout)
        return group

    def _format_file_size(self, size_bytes: int | None) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes.

        Returns:
            Formatted size string (e.g., "2.4 MB", "156 KB", "Unknown").
        """
        if size_bytes is None:
            return "Unknown"

        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            kb = size_bytes / 1024
            return f"{kb:.1f} KB"
        else:
            mb = size_bytes / (1024 * 1024)
            return f"{mb:.1f} MB"

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime in user-friendly format.

        Args:
            dt: Datetime to format.

        Returns:
            Formatted datetime string (e.g., "December 14, 2025 at 3:42 PM").
        """
        return dt.strftime("%B %d, %Y at %-I:%M %p")

    def _get_status_display(self, status: str) -> str:
        """Get display-friendly status text.

        Args:
            status: Status code ("not_started", "reading", "finished").

        Returns:
            Display-friendly status string.
        """
        status_map = {
            "not_started": "Not Started",
            "reading": "Reading",
            "finished": "Finished"
        }
        return status_map.get(status, status.title())
