"""Custom delegate for rendering book cards in library grid.

This module provides the BookCardDelegate class that paints book cards
with cover placeholders, titles, authors, and progress indicators.
"""

import logging
from pathlib import Path

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from ereader.models.book_metadata import BookMetadata

logger = logging.getLogger(__name__)


class BookCardDelegate(QStyledItemDelegate):
    """Custom delegate for rendering book cards in grid.

    This delegate paints each book as a card with:
    - Cover area (placeholder rectangle with book icon)
    - Title (max 2 lines, truncated with ellipsis)
    - Author (1 line, truncated)
    - Progress bar (visual 0-100%)
    - Progress text (percentage)

    Card dimensions: 180px wide × 260px tall
    """

    # Card dimensions
    CARD_WIDTH = 180
    CARD_HEIGHT = 260

    # Layout constants
    COVER_WIDTH = 150
    COVER_HEIGHT = 200
    COVER_MARGIN_TOP = 10
    TITLE_MARGIN_TOP = 5
    AUTHOR_MARGIN_TOP = 3
    PROGRESS_BAR_HEIGHT = 8
    PROGRESS_BAR_MARGIN_TOP = 5
    PADDING = 10

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index
    ) -> None:
        """Paint a book card.

        Args:
            painter: QPainter to draw with.
            option: Style options for the item.
            index: Model index of the item.
        """
        # Get book data from model
        book = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(book, BookMetadata):
            # Fallback to default painting if data is invalid
            super().paint(painter, option, index)
            return

        painter.save()

        # Draw selection/hover background
        if option.state & QStyle.StateFlag.State_Selected:
            # Selected state: light blue background
            painter.fillRect(option.rect, QColor("#E3F2FD"))
            # Draw selection border
            painter.setPen(QPen(QColor("#2196F3"), 2))
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            # Hover state: very light gray background
            painter.fillRect(option.rect, QColor("#F5F5F5"))

        # Calculate layout
        card_rect = option.rect
        center_x = card_rect.center().x()

        # 1. Draw cover (centered)
        cover_x = center_x - self.COVER_WIDTH // 2
        cover_y = card_rect.top() + self.COVER_MARGIN_TOP
        cover_rect = QRect(cover_x, cover_y, self.COVER_WIDTH, self.COVER_HEIGHT)

        # Try to load actual cover if available
        if book.cover_path and Path(book.cover_path).exists():
            # Load cover image
            pixmap = QPixmap(book.cover_path)
            if not pixmap.isNull():
                # Scale to fit cover_rect while preserving aspect ratio
                scaled = pixmap.scaled(
                    cover_rect.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                # Center in cover_rect
                x = cover_rect.x() + (cover_rect.width() - scaled.width()) // 2
                y = cover_rect.y() + (cover_rect.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            else:
                # Pixmap failed to load, use placeholder
                self._draw_placeholder_cover(painter, cover_rect)
        else:
            # No cover or file missing, use placeholder
            self._draw_placeholder_cover(painter, cover_rect)

        # 2. Draw title (max 2 lines, centered)
        title_y = cover_y + self.COVER_HEIGHT + self.TITLE_MARGIN_TOP
        title_rect = QRect(
            card_rect.left() + self.PADDING,
            title_y,
            card_rect.width() - 2 * self.PADDING,
            30,  # Approx 2 lines
        )

        title_font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#212121"))

        # Truncate title if too long (max 2 lines)
        fm = QFontMetrics(title_font)
        title = book.title
        elided_title = fm.elidedText(title, Qt.TextElideMode.ElideRight, title_rect.width() * 2)
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
            elided_title,
        )

        # 3. Draw author (1 line, centered)
        author_y = title_y + 32
        author_rect = QRect(
            card_rect.left() + self.PADDING,
            author_y,
            card_rect.width() - 2 * self.PADDING,
            15,
        )

        author_font = QFont("Arial", 8)
        painter.setFont(author_font)
        painter.setPen(QColor("#757575"))

        author = book.author if book.author else "Unknown Author"
        fm_author = QFontMetrics(author_font)
        elided_author = fm_author.elidedText(
            author, Qt.TextElideMode.ElideRight, author_rect.width()
        )
        painter.drawText(author_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, elided_author)

        # 4. Draw progress bar
        progress_y = author_y + 18
        progress_bar_width = card_rect.width() - 2 * self.PADDING
        progress_bar_rect = QRect(
            card_rect.left() + self.PADDING,
            progress_y,
            progress_bar_width,
            self.PROGRESS_BAR_HEIGHT,
        )

        # Background (gray)
        painter.fillRect(progress_bar_rect, QColor("#E0E0E0"))

        # Progress fill (blue)
        progress_width = int(progress_bar_width * (book.reading_progress / 100.0))
        if progress_width > 0:
            progress_fill_rect = QRect(
                progress_bar_rect.left(),
                progress_bar_rect.top(),
                progress_width,
                self.PROGRESS_BAR_HEIGHT,
            )
            painter.fillRect(progress_fill_rect, QColor("#4CAF50"))  # Green for progress

        # Progress border
        painter.setPen(QPen(QColor("#BDBDBD"), 1))
        painter.drawRect(progress_bar_rect)

        # 5. Draw progress percentage
        progress_text_y = progress_y + self.PROGRESS_BAR_HEIGHT + 3
        progress_text_rect = QRect(
            card_rect.left() + self.PADDING,
            progress_text_y,
            card_rect.width() - 2 * self.PADDING,
            12,
        )

        progress_font = QFont("Arial", 8)
        painter.setFont(progress_font)
        painter.setPen(QColor("#757575"))
        progress_text = f"{book.reading_progress:.0f}%"
        painter.drawText(
            progress_text_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, progress_text
        )

        painter.restore()

    def sizeHint(
        self, option: QStyleOptionViewItem, index
    ) -> QSize:
        """Return size hint for book card.

        Args:
            option: Style options for the item.
            index: Model index of the item.

        Returns:
            QSize with card dimensions.
        """
        return QSize(self.CARD_WIDTH, self.CARD_HEIGHT)

    def _draw_placeholder_cover(self, painter: QPainter, cover_rect: QRect) -> None:
        """Draw placeholder cover (gray box with book icon).

        Used when no cover is available or cover loading fails.

        Args:
            painter: QPainter to draw with.
            cover_rect: Rectangle to draw placeholder in.
        """
        # Draw cover background (light gray rectangle)
        painter.fillRect(cover_rect, QColor("#E0E0E0"))
        painter.setPen(QPen(QColor("#BDBDBD"), 1))
        painter.drawRect(cover_rect)

        # Draw book icon (📕 emoji or simple representation)
        painter.setPen(QColor("#757575"))
        icon_font = QFont("Arial", 48)
        painter.setFont(icon_font)
        painter.drawText(cover_rect, Qt.AlignmentFlag.AlignCenter, "📕")
