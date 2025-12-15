"""Tests for Phase 2 library collections functionality.

Tests the collection CRUD operations and enhanced filtering added in Phase 2.
"""

from datetime import datetime

import pytest

from ereader.models.book_metadata import BookMetadata
from ereader.models.library_database import DatabaseError, LibraryRepository
from ereader.models.library_filter import LibraryFilter


class TestDatabaseMigration:
    """Test database schema migration from v1 to v2."""

    def test_fresh_database_creates_v2_schema(self):
        """Fresh database should be created with v2 schema."""
        repo = LibraryRepository(":memory:")

        # Check schema version
        cursor = repo._conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        version = cursor.fetchone()[0]

        assert version == 2, "Fresh database should be v2"

    def test_v2_schema_has_collections_table(self):
        """V2 schema should have collections table."""
        repo = LibraryRepository(":memory:")

        cursor = repo._conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='collections'"
        )
        result = cursor.fetchone()

        assert result is not None, "collections table should exist"

    def test_v2_schema_has_book_collections_table(self):
        """V2 schema should have book_collections junction table."""
        repo = LibraryRepository(":memory:")

        cursor = repo._conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='book_collections'"
        )
        result = cursor.fetchone()

        assert result is not None, "book_collections table should exist"


class TestCollectionCRUD:
    """Test collection create, read, update, delete operations."""

    @pytest.fixture
    def repo(self):
        """Create in-memory repository for testing."""
        return LibraryRepository(":memory:")

    def test_create_collection(self, repo):
        """Should create a new collection."""
        collection_id = repo.create_collection("Science Fiction")

        assert collection_id > 0, "Should return valid ID"

        # Verify collection exists
        collection = repo.get_collection(collection_id)
        assert collection is not None
        assert collection.name == "Science Fiction"
        assert collection.book_count == 0

    def test_create_collection_with_color(self, repo):
        """Should create collection with optional color."""
        collection_id = repo.create_collection("Fantasy", color="#FF5733")

        collection = repo.get_collection(collection_id)
        assert collection.color == "#FF5733"

    def test_create_duplicate_collection_raises_error(self, repo):
        """Creating duplicate collection name should raise error."""
        repo.create_collection("Favorites")

        with pytest.raises(DatabaseError, match="already exists"):
            repo.create_collection("Favorites")

    def test_get_all_collections_empty(self, repo):
        """Getting collections from empty database should return empty list."""
        collections = repo.get_all_collections()
        assert collections == []

    def test_get_all_collections(self, repo):
        """Should return all collections sorted by name."""
        repo.create_collection("Science Fiction")
        repo.create_collection("Fantasy")
        repo.create_collection("Biography")

        collections = repo.get_all_collections()

        assert len(collections) == 3
        # Should be sorted by name
        assert collections[0].name == "Biography"
        assert collections[1].name == "Fantasy"
        assert collections[2].name == "Science Fiction"

    def test_get_collection_not_found(self, repo):
        """Getting non-existent collection should return None."""
        collection = repo.get_collection(999)
        assert collection is None

    def test_rename_collection(self, repo):
        """Should rename a collection."""
        collection_id = repo.create_collection("Old Name")

        repo.rename_collection(collection_id, "New Name")

        collection = repo.get_collection(collection_id)
        assert collection.name == "New Name"

    def test_rename_collection_to_existing_name_raises_error(self, repo):
        """Renaming to existing name should raise error."""
        repo.create_collection("Collection A")
        collection_id = repo.create_collection("Collection B")

        with pytest.raises(DatabaseError, match="already exists"):
            repo.rename_collection(collection_id, "Collection A")

    def test_rename_nonexistent_collection_raises_error(self, repo):
        """Renaming non-existent collection should raise error."""
        with pytest.raises(DatabaseError, match="not found"):
            repo.rename_collection(999, "New Name")

    def test_delete_collection(self, repo):
        """Should delete a collection."""
        collection_id = repo.create_collection("To Delete")

        repo.delete_collection(collection_id)

        collection = repo.get_collection(collection_id)
        assert collection is None

    def test_delete_nonexistent_collection_does_not_raise(self, repo):
        """Deleting non-existent collection should not raise error."""
        # Should not raise
        repo.delete_collection(999)


class TestBookCollectionLinks:
    """Test adding/removing books from collections."""

    @pytest.fixture
    def repo_with_books(self):
        """Create repository with sample books."""
        repo = LibraryRepository(":memory:")

        # Add sample books
        book1 = BookMetadata(
            id=0,
            title="Book One",
            author="Author A",
            file_path="/path/to/book1.epub",
            cover_path=None,
            added_date=datetime.now(),
            last_opened_date=None,
            reading_progress=0.0,
            current_chapter_index=0,
            scroll_position=0,
            status="not_started",
            file_size=1000,
        )
        book2 = BookMetadata(
            id=0,
            title="Book Two",
            author="Author B",
            file_path="/path/to/book2.epub",
            cover_path=None,
            added_date=datetime.now(),
            last_opened_date=None,
            reading_progress=50.0,
            current_chapter_index=5,
            scroll_position=100,
            status="reading",
            file_size=2000,
        )

        repo.add_book(book1)
        repo.add_book(book2)

        return repo

    def test_add_book_to_collection(self, repo_with_books):
        """Should add a book to a collection."""
        repo = repo_with_books
        collection_id = repo.create_collection("My Collection")

        repo.add_book_to_collection(1, collection_id)

        # Verify book count
        collection = repo.get_collection(collection_id)
        assert collection.book_count == 1

    def test_add_multiple_books_to_collection(self, repo_with_books):
        """Should add multiple books to a collection."""
        repo = repo_with_books
        collection_id = repo.create_collection("My Collection")

        repo.add_book_to_collection(1, collection_id)
        repo.add_book_to_collection(2, collection_id)

        collection = repo.get_collection(collection_id)
        assert collection.book_count == 2

    def test_add_book_to_collection_duplicate_raises_error(self, repo_with_books):
        """Adding same book twice should raise error."""
        repo = repo_with_books
        collection_id = repo.create_collection("My Collection")

        repo.add_book_to_collection(1, collection_id)

        with pytest.raises(DatabaseError, match="already in collection"):
            repo.add_book_to_collection(1, collection_id)

    def test_remove_book_from_collection(self, repo_with_books):
        """Should remove a book from a collection."""
        repo = repo_with_books
        collection_id = repo.create_collection("My Collection")

        repo.add_book_to_collection(1, collection_id)
        repo.remove_book_from_collection(1, collection_id)

        collection = repo.get_collection(collection_id)
        assert collection.book_count == 0

    def test_delete_collection_cascades_to_links(self, repo_with_books):
        """Deleting collection should delete book-collection links."""
        repo = repo_with_books
        collection_id = repo.create_collection("My Collection")

        repo.add_book_to_collection(1, collection_id)
        repo.add_book_to_collection(2, collection_id)

        # Delete collection
        repo.delete_collection(collection_id)

        # Verify links are deleted (books should still exist)
        cursor = repo._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM book_collections WHERE collection_id = ?", (collection_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "Book-collection links should be deleted"


class TestEnhancedFiltering:
    """Test enhanced filter_books() with Phase 2 criteria."""

    @pytest.fixture
    def repo_with_data(self):
        """Create repository with diverse books for filtering tests."""
        repo = LibraryRepository(":memory:")

        # Add books with different statuses and dates
        books = [
            BookMetadata(
                id=0,
                title="Recent Book",
                author="Author A",
                file_path="/path/recent.epub",
                cover_path=None,
                added_date=datetime.now(),
                last_opened_date=datetime.now(),  # Opened recently
                reading_progress=25.0,
                current_chapter_index=2,
                scroll_position=50,
                status="reading",
                file_size=1000,
            ),
            BookMetadata(
                id=0,
                title="Old Book",
                author="Author B",
                file_path="/path/old.epub",
                cover_path=None,
                added_date=datetime(2020, 1, 1),
                last_opened_date=datetime(2020, 1, 1),  # Opened long ago
                reading_progress=100.0,
                current_chapter_index=10,
                scroll_position=0,
                status="finished",
                file_size=2000,
            ),
            BookMetadata(
                id=0,
                title="Not Started",
                author="Author C",
                file_path="/path/notstarted.epub",
                cover_path=None,
                added_date=datetime.now(),
                last_opened_date=None,
                reading_progress=0.0,
                current_chapter_index=0,
                scroll_position=0,
                status="not_started",
                file_size=1500,
            ),
        ]

        for book in books:
            repo.add_book(book)

        return repo

    def test_filter_by_status_reading(self, repo_with_data):
        """Should filter books by reading status."""
        filter_obj = LibraryFilter(status="reading")

        books = repo_with_data.filter_books(filter_obj)

        assert len(books) == 1
        assert books[0].title == "Recent Book"

    def test_filter_by_status_not_started(self, repo_with_data):
        """Should filter books by not_started status."""
        filter_obj = LibraryFilter(status="not_started")

        books = repo_with_data.filter_books(filter_obj)

        assert len(books) == 1
        assert books[0].title == "Not Started"

    def test_filter_by_days_since_opened(self, repo_with_data):
        """Should filter books opened in last N days."""
        # Filter for books opened in last 30 days
        filter_obj = LibraryFilter(days_since_opened=30)

        books = repo_with_data.filter_books(filter_obj)

        # Only "Recent Book" was opened recently
        assert len(books) == 1
        assert books[0].title == "Recent Book"

    def test_filter_by_collection(self, repo_with_data):
        """Should filter books by collection."""
        repo = repo_with_data
        collection_id = repo.create_collection("My Collection")

        # Add one book to collection
        repo.add_book_to_collection(1, collection_id)

        filter_obj = LibraryFilter(collection_id=collection_id)
        books = repo.filter_books(filter_obj)

        assert len(books) == 1

    def test_sort_by_progress(self, repo_with_data):
        """Should sort books by reading progress."""
        filter_obj = LibraryFilter(sort_by="progress")

        books = repo_with_data.filter_books(filter_obj)

        # Should be sorted descending by progress
        assert books[0].reading_progress == 100.0  # Old Book (finished)
        assert books[1].reading_progress == 25.0   # Recent Book
        assert books[2].reading_progress == 0.0    # Not Started

    def test_sort_by_added_date_desc(self, repo_with_data):
        """Should sort books by added date (newest first)."""
        filter_obj = LibraryFilter(sort_by="added_date_desc")

        books = repo_with_data.filter_books(filter_obj)

        # Newest books first
        assert books[0].title in ["Recent Book", "Not Started"]
        assert books[-1].title == "Old Book"

    def test_combined_filter_status_and_search(self, repo_with_data):
        """Should combine status filter with search."""
        filter_obj = LibraryFilter(status="reading", search_query="Recent")

        books = repo_with_data.filter_books(filter_obj)

        assert len(books) == 1
        assert books[0].title == "Recent Book"


class TestUpdateBookSecurity:
    """Test security features of update_book() method."""

    @pytest.fixture
    def repo_with_book(self):
        """Create repository with a single book."""
        repo = LibraryRepository(":memory:")

        book = BookMetadata(
            id=0,
            title="Test Book",
            author="Test Author",
            file_path="/path/to/book.epub",
            cover_path=None,
            added_date=datetime.now(),
            last_opened_date=None,
            reading_progress=0.0,
            current_chapter_index=0,
            scroll_position=0,
            status="not_started",
            file_size=1000,
        )
        repo.add_book(book)

        return repo

    def test_update_book_with_valid_columns(self, repo_with_book):
        """Should update book with whitelisted column names."""
        repo = repo_with_book

        # All these columns should be allowed
        repo.update_book(1, title="New Title")
        repo.update_book(1, author="New Author")
        repo.update_book(1, status="reading")
        repo.update_book(1, reading_progress=50.0)

        book = repo.get_book(1)
        assert book.title == "New Title"
        assert book.author == "New Author"
        assert book.status == "reading"
        assert book.reading_progress == 50.0

    def test_update_book_with_invalid_column_raises_error(self, repo_with_book):
        """Should reject invalid column names to prevent SQL injection."""
        repo = repo_with_book

        # Try to update with an invalid column name
        with pytest.raises(DatabaseError, match="Invalid column names"):
            repo.update_book(1, malicious_column="DROP TABLE books")

    def test_update_book_with_mixed_columns_raises_error(self, repo_with_book):
        """Should reject update if any column is invalid."""
        repo = repo_with_book

        # Mix of valid and invalid columns should fail
        with pytest.raises(DatabaseError, match="Invalid column names"):
            repo.update_book(1, title="New Title", invalid_col="value")
