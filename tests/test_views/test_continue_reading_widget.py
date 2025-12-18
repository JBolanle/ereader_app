"""Tests for Continue Reading widget."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from ereader.models.book_metadata import BookMetadata
from ereader.views.continue_reading_widget import (
    BookCardWidget,
    ContinueReadingWidget,
)


@pytest.fixture
def sample_books() -> list[BookMetadata]:
    """Create sample books for testing.

    Returns:
        List of BookMetadata with varying last_opened_date values.
    """
    now = datetime.now()

    return [
        # Recently opened books (should appear)
        BookMetadata(
            id=1,
            title="Recently Read Book 1",
            author="Author 1",
            file_path="/path/book1.epub",
            cover_path=None,
            added_date=now - timedelta(days=10),
            last_opened_date=now - timedelta(hours=1),  # Most recent
            reading_progress=45.0,
            current_chapter_index=5,
            scroll_position=100,
            status="reading",
            file_size=1000000,
        ),
        BookMetadata(
            id=2,
            title="Recently Read Book 2",
            author="Author 2",
            file_path="/path/book2.epub",
            cover_path=None,
            added_date=now - timedelta(days=9),
            last_opened_date=now - timedelta(days=1),  # Second most recent
            reading_progress=12.0,
            current_chapter_index=2,
            scroll_position=50,
            status="reading",
            file_size=800000,
        ),
        BookMetadata(
            id=3,
            title="Recently Read Book 3",
            author="Author 3",
            file_path="/path/book3.epub",
            cover_path=None,
            added_date=now - timedelta(days=8),
            last_opened_date=now - timedelta(days=2),
            reading_progress=87.0,
            current_chapter_index=15,
            scroll_position=200,
            status="reading",
            file_size=1200000,
        ),
        # Not opened yet (should not appear)
        BookMetadata(
            id=4,
            title="Never Opened Book",
            author="Author 4",
            file_path="/path/book4.epub",
            cover_path=None,
            added_date=now - timedelta(days=7),
            last_opened_date=None,  # Never opened
            reading_progress=0.0,
            current_chapter_index=0,
            scroll_position=0,
            status="not_started",
            file_size=900000,
        ),
    ]


@pytest.fixture
def many_opened_books() -> list[BookMetadata]:
    """Create many opened books to test the 5-book limit.

    Returns:
        List of 7 opened books.
    """
    now = datetime.now()
    books = []

    for i in range(7):
        books.append(
            BookMetadata(
                id=i + 1,
                title=f"Book {i + 1}",
                author=f"Author {i + 1}",
                file_path=f"/path/book{i+1}.epub",
                cover_path=None,
                added_date=now - timedelta(days=10 - i),
                last_opened_date=now - timedelta(days=i),  # i=0 is most recent
                reading_progress=float(i * 10),
                current_chapter_index=i,
                scroll_position=i * 100,
                status="reading",
                file_size=1000000,
            )
        )

    return books


class TestBookCardWidget:
    """Tests for individual book card widget."""

    def test_book_card_initialization(
        self, qtbot: QtBot, sample_books: list[BookMetadata]
    ) -> None:
        """Test that book card initializes correctly.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data.
        """
        book = sample_books[0]
        card = BookCardWidget(book)
        qtbot.addWidget(card)

        # Check size
        assert card.width() == BookCardWidget.CARD_WIDTH
        assert card.height() == BookCardWidget.CARD_HEIGHT

        # Check tooltip contains book info
        assert book.title in card.toolTip()
        assert book.author in card.toolTip()
        assert "45%" in card.toolTip()

    def test_book_card_click_emits_signal(
        self, qtbot: QtBot, sample_books: list[BookMetadata]
    ) -> None:
        """Test that clicking card emits clicked signal.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data.
        """
        book = sample_books[0]
        card = BookCardWidget(book)
        qtbot.addWidget(card)

        # Connect signal and click
        with qtbot.waitSignal(card.clicked, timeout=1000) as blocker:
            qtbot.mouseClick(card, Qt.MouseButton.LeftButton)

        # Verify signal emitted with correct book ID
        assert blocker.args == [book.id]

    def test_book_card_with_cover(
        self, qtbot: QtBot, sample_books: list[BookMetadata], tmp_path: Path
    ) -> None:
        """Test book card with actual cover image.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data.
            tmp_path: Temporary directory for cover image.
        """
        # Create a dummy cover file
        cover_path = tmp_path / "cover.jpg"
        cover_path.touch()

        book = sample_books[0]
        book.cover_path = str(cover_path)

        card = BookCardWidget(book)
        qtbot.addWidget(card)

        # Card should initialize without error
        assert card is not None


class TestContinueReadingWidget:
    """Tests for Continue Reading widget."""

    def test_widget_initialization(self, qtbot: QtBot) -> None:
        """Test that widget initializes correctly.

        Args:
            qtbot: Qt test fixture.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        assert widget is not None
        # Widget should be hidden initially (no books set)
        assert not widget.isVisible()

    def test_set_books_filters_unopened_books(
        self, qtbot: QtBot, sample_books: list[BookMetadata]
    ) -> None:
        """Test that set_books only shows opened books.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data (includes unopened book).
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        widget.set_books(sample_books)

        # Should show 3 opened books (book 4 is not opened)
        assert len(widget._book_cards) == 3
        assert widget.isVisible()

        # Verify it's the opened books
        card_ids = [card._book.id for card in widget._book_cards]
        assert 1 in card_ids
        assert 2 in card_ids
        assert 3 in card_ids
        assert 4 not in card_ids  # Not opened

    def test_set_books_sorts_by_most_recent(
        self, qtbot: QtBot, sample_books: list[BookMetadata]
    ) -> None:
        """Test that books are sorted by most recent first.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        widget.set_books(sample_books)

        # Verify order: most recent first
        card_ids = [card._book.id for card in widget._book_cards]
        assert card_ids == [1, 2, 3]  # Book 1 opened 1 hour ago, 2 opened 1 day ago, etc.

    def test_set_books_limits_to_five(
        self, qtbot: QtBot, many_opened_books: list[BookMetadata]
    ) -> None:
        """Test that widget limits to 5 books maximum.

        Args:
            qtbot: Qt test fixture.
            many_opened_books: 7 opened books.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        widget.set_books(many_opened_books)

        # Should show only 5 books
        assert len(widget._book_cards) == 5

        # Should be the 5 most recent (IDs 1-5)
        card_ids = [card._book.id for card in widget._book_cards]
        assert len(card_ids) == 5
        assert all(book_id in range(1, 6) for book_id in card_ids)

    def test_set_books_hides_when_no_opened_books(self, qtbot: QtBot) -> None:
        """Test that widget hides when no books have been opened.

        Args:
            qtbot: Qt test fixture.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        # Create books that have never been opened
        books = [
            BookMetadata(
                id=1,
                title="Never Opened",
                author="Author",
                file_path="/path/book.epub",
                cover_path=None,
                added_date=datetime.now(),
                last_opened_date=None,
                reading_progress=0.0,
                current_chapter_index=0,
                scroll_position=0,
                status="not_started",
                file_size=1000000,
            )
        ]

        widget.set_books(books)

        # Widget should be hidden
        assert not widget.isVisible()
        assert len(widget._book_cards) == 0

    def test_book_activated_signal(
        self, qtbot: QtBot, sample_books: list[BookMetadata]
    ) -> None:
        """Test that clicking a book card emits book_activated signal.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        widget.set_books(sample_books)

        # Get first card
        first_card = widget._book_cards[0]

        # Connect signal and click card
        with qtbot.waitSignal(widget.book_activated, timeout=1000) as blocker:
            qtbot.mouseClick(first_card, Qt.MouseButton.LeftButton)

        # Verify signal emitted with correct book ID
        assert blocker.args == [first_card._book.id]

    def test_set_books_updates_existing_cards(
        self, qtbot: QtBot, sample_books: list[BookMetadata]
    ) -> None:
        """Test that calling set_books multiple times updates cards.

        Args:
            qtbot: Qt test fixture.
            sample_books: Sample book data.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        # Set books first time
        widget.set_books(sample_books)
        assert len(widget._book_cards) == 3

        # Update books (remove one)
        updated_books = sample_books[:2]  # Only first 2 books
        widget.set_books(updated_books)

        # Should now show 2 opened books
        assert len(widget._book_cards) == 2

    def test_empty_books_list(self, qtbot: QtBot) -> None:
        """Test widget behavior with empty book list.

        Args:
            qtbot: Qt test fixture.
        """
        widget = ContinueReadingWidget()
        qtbot.addWidget(widget)

        widget.set_books([])

        # Widget should be hidden
        assert not widget.isVisible()
        assert len(widget._book_cards) == 0
