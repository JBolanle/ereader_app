"""Library database repository for book management.

This module provides the LibraryRepository class that encapsulates all database
operations for the library system. It uses the Repository pattern to isolate
database concerns from business logic.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from ereader.exceptions import EReaderError
from ereader.models.book_metadata import BookMetadata
from ereader.models.collection import Collection
from ereader.models.library_filter import LibraryFilter

logger = logging.getLogger(__name__)


class DatabaseError(EReaderError):
    """Raised when a database operation fails."""

    pass


class LibraryRepository:
    """Repository for library database operations.

    This class manages the SQLite database for book library management,
    providing CRUD operations for books and collections. It owns the
    database schema and handles migrations.

    The repository uses the Repository pattern to separate database
    concerns from business logic. Controllers interact with this class
    rather than executing raw SQL.

    Attributes:
        CURRENT_SCHEMA_VERSION: Current database schema version (for migrations).
    """

    CURRENT_SCHEMA_VERSION = 2

    def __init__(self, db_path: Path | str) -> None:
        """Initialize repository with database file path.

        Creates the database and schema if they don't exist. Runs migrations
        if the database schema is outdated.

        Args:
            db_path: Path to SQLite database file (can be ":memory:" for testing).

        Raises:
            DatabaseError: If database cannot be opened or initialized.
        """
        logger.debug("Initializing LibraryRepository with db_path: %s", db_path)

        self._db_path = Path(db_path) if db_path != ":memory:" else ":memory:"

        try:
            # Open database connection
            self._conn = sqlite3.connect(str(db_path))
            self._conn.row_factory = sqlite3.Row  # Access columns by name

            # Enable foreign key constraints (required for CASCADE)
            self._conn.execute("PRAGMA foreign_keys = ON")

            logger.debug("Database connection established")

            # Ensure schema exists and is up-to-date
            self._ensure_schema()

            logger.debug("LibraryRepository initialized successfully")

        except sqlite3.Error as e:
            error_msg = f"Failed to initialize database: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def close(self) -> None:
        """Close the database connection.

        Should be called when the repository is no longer needed,
        typically when the application closes.
        """
        logger.debug("Closing database connection")
        if self._conn:
            self._conn.close()
            logger.debug("Database connection closed")

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist, run migrations if needed.

        Checks the current schema version and runs migrations to bring
        the database up to CURRENT_SCHEMA_VERSION.

        Raises:
            DatabaseError: If schema creation or migration fails.
        """
        logger.debug("Ensuring database schema is current")

        try:
            cursor = self._conn.cursor()

            # Check current version
            try:
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                current_version = result[0] if result[0] is not None else 0
                logger.debug("Current schema version: %d", current_version)
            except sqlite3.OperationalError:
                # schema_version table doesn't exist, this is first run
                current_version = 0
                logger.debug("No schema_version table found, assuming version 0")

            # Run migrations if needed
            if current_version < self.CURRENT_SCHEMA_VERSION:
                logger.info(
                    "Running migrations from version %d to %d",
                    current_version,
                    self.CURRENT_SCHEMA_VERSION,
                )
                self._run_migrations(current_version)

            logger.debug("Database schema is current (version %d)", self.CURRENT_SCHEMA_VERSION)

        except sqlite3.Error as e:
            error_msg = f"Failed to ensure schema: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _run_migrations(self, from_version: int) -> None:
        """Run migrations from from_version to CURRENT_SCHEMA_VERSION.

        Args:
            from_version: Starting schema version (0 for initial creation).

        Raises:
            DatabaseError: If migration fails.
        """
        logger.debug("Running migrations from version %d", from_version)

        try:
            if from_version < 1:
                self._create_initial_schema()

            if from_version < 2:
                self._migrate_v1_to_v2()

            self._conn.commit()
            logger.info("Migrations completed successfully")

        except sqlite3.Error as e:
            self._conn.rollback()
            error_msg = f"Migration failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _create_initial_schema(self) -> None:
        """Create initial database schema (version 1).

        Creates the books table and indexes for common queries.

        Raises:
            DatabaseError: If schema creation fails.
        """
        logger.debug("Creating initial schema (version 1)")

        cursor = self._conn.cursor()

        # Create books table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                file_path TEXT UNIQUE NOT NULL,
                cover_path TEXT,
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_opened_date DATETIME,
                reading_progress REAL DEFAULT 0.0,
                current_chapter_index INTEGER DEFAULT 0,
                scroll_position INTEGER DEFAULT 0,
                status TEXT DEFAULT 'not_started',
                file_size INTEGER,
                CHECK (status IN ('not_started', 'reading', 'finished'))
            )
            """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_books_last_opened
            ON books(last_opened_date DESC)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_books_title
            ON books(title COLLATE NOCASE)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_books_author
            ON books(author COLLATE NOCASE)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_books_status
            ON books(status)
            """
        )

        # Create schema_version table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Record schema version
        cursor.execute(
            """
            INSERT OR REPLACE INTO schema_version (version)
            VALUES (?)
            """,
            (1,),
        )

        logger.debug("Initial schema created successfully")

    def _migrate_v1_to_v2(self) -> None:
        """Migrate database from v1 to v2 (add collections support).

        Adds the collections and book_collections tables to support
        user-created collections and collection-based filtering.

        Raises:
            DatabaseError: If migration fails.
        """
        logger.info("Migrating database from v1 to v2 (collections support)")

        cursor = self._conn.cursor()

        # Create collections table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                color TEXT,
                sort_order INTEGER DEFAULT 0
            )
            """
        )

        # Create book_collections junction table (many-to-many)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS book_collections (
                book_id INTEGER NOT NULL,
                collection_id INTEGER NOT NULL,
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (book_id, collection_id),
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
            )
            """
        )

        # Create indexes for performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collections_name
            ON collections(name COLLATE NOCASE)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_collections_sort_order
            ON collections(sort_order)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_book_collections_book
            ON book_collections(book_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_book_collections_collection
            ON book_collections(collection_id)
            """
        )

        # Update schema version
        cursor.execute(
            """
            INSERT OR REPLACE INTO schema_version (version)
            VALUES (?)
            """,
            (2,),
        )

        logger.info("Migration to v2 complete (collections support added)")

    def add_book(self, metadata: BookMetadata) -> int:
        """Add a new book to the library.

        Args:
            metadata: Book metadata to add. The id field is ignored.

        Returns:
            Database ID of the newly added book.

        Raises:
            DatabaseError: If book already exists or database operation fails.
        """
        logger.debug("Adding book: %s", metadata.title)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO books (
                    title, author, file_path, cover_path, added_date,
                    last_opened_date, reading_progress, current_chapter_index,
                    scroll_position, status, file_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.title,
                    metadata.author,
                    metadata.file_path,
                    metadata.cover_path,
                    metadata.added_date,
                    metadata.last_opened_date,
                    metadata.reading_progress,
                    metadata.current_chapter_index,
                    metadata.scroll_position,
                    metadata.status,
                    metadata.file_size,
                ),
            )

            self._conn.commit()
            book_id = cursor.lastrowid

            logger.info("Book added successfully with ID %d: %s", book_id, metadata.title)
            return book_id

        except sqlite3.IntegrityError as e:
            # Likely duplicate file_path (UNIQUE constraint)
            error_msg = f"Book already exists in library: {metadata.file_path}"
            logger.warning(error_msg)
            raise DatabaseError(error_msg) from e

        except sqlite3.Error as e:
            error_msg = f"Failed to add book: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_book(self, book_id: int) -> BookMetadata | None:
        """Get a book by its database ID.

        Args:
            book_id: Database ID of the book.

        Returns:
            BookMetadata if found, None otherwise.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Getting book with ID: %d", book_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM books WHERE id = ?
                """,
                (book_id,),
            )

            row = cursor.fetchone()
            if row is None:
                logger.debug("Book not found: %d", book_id)
                return None

            metadata = self._row_to_metadata(row)
            logger.debug("Book found: %s", metadata.title)
            return metadata

        except sqlite3.Error as e:
            error_msg = f"Failed to get book: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_all_books(self) -> list[BookMetadata]:
        """Get all books in the library.

        Returns:
            List of all books, sorted by last_opened_date (most recent first).
            Returns empty list if no books in library.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Getting all books")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM books
                ORDER BY last_opened_date DESC NULLS LAST, added_date DESC
                """
            )

            rows = cursor.fetchall()
            books = [self._row_to_metadata(row) for row in rows]

            logger.debug("Retrieved %d books", len(books))
            return books

        except sqlite3.Error as e:
            error_msg = f"Failed to get all books: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_book(self, book_id: int, **kwargs) -> None:
        """Update book fields.

        Args:
            book_id: Database ID of the book to update.
            **kwargs: Fields to update (e.g., title="New Title", status="reading").

        Raises:
            DatabaseError: If book doesn't exist, invalid column name, or database operation fails.
        """
        if not kwargs:
            logger.debug("No fields to update for book %d", book_id)
            return

        # Whitelist of allowed columns to prevent SQL injection
        allowed_columns = {
            "title",
            "author",
            "file_path",
            "cover_path",
            "last_opened_date",
            "reading_progress",
            "current_chapter_index",
            "scroll_position",
            "status",
            "file_size",
        }

        # Validate all column names
        invalid_columns = set(kwargs.keys()) - allowed_columns
        if invalid_columns:
            error_msg = f"Invalid column names: {invalid_columns}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

        logger.debug("Updating book %d with fields: %s", book_id, list(kwargs.keys()))

        try:
            # Build UPDATE query dynamically (column names validated above)
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [book_id]

            cursor = self._conn.cursor()
            cursor.execute(
                f"""
                UPDATE books SET {set_clause} WHERE id = ?
                """,
                values,
            )

            self._conn.commit()

            if cursor.rowcount == 0:
                error_msg = f"Book not found: {book_id}"
                logger.warning(error_msg)
                raise DatabaseError(error_msg)

            logger.debug("Book %d updated successfully", book_id)

        except sqlite3.Error as e:
            error_msg = f"Failed to update book: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_book(self, book_id: int) -> None:
        """Delete a book from the library.

        Args:
            book_id: Database ID of the book to delete.

        Raises:
            DatabaseError: If book doesn't exist or database operation fails.
        """
        logger.debug("Deleting book with ID: %d", book_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                DELETE FROM books WHERE id = ?
                """,
                (book_id,),
            )

            self._conn.commit()

            if cursor.rowcount == 0:
                error_msg = f"Book not found: {book_id}"
                logger.warning(error_msg)
                raise DatabaseError(error_msg)

            logger.info("Book %d deleted successfully", book_id)

        except sqlite3.Error as e:
            error_msg = f"Failed to delete book: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def search_books(self, query: str) -> list[BookMetadata]:
        """Search books by title or author.

        Args:
            query: Search query (case-insensitive).

        Returns:
            List of books matching the query, sorted by last_opened_date.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Searching books for query: %s", query)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM books
                WHERE title LIKE ? OR author LIKE ?
                ORDER BY last_opened_date DESC NULLS LAST, added_date DESC
                """,
                (f"%{query}%", f"%{query}%"),
            )

            rows = cursor.fetchall()
            books = [self._row_to_metadata(row) for row in rows]

            logger.debug("Search found %d books", len(books))
            return books

        except sqlite3.Error as e:
            error_msg = f"Failed to search books: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def filter_books(self, filter_obj: LibraryFilter) -> list[BookMetadata]:
        """Filter and sort books based on filter criteria.

        Args:
            filter_obj: Filter and sort criteria.

        Returns:
            List of books matching the filter, sorted according to sort_by.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Filtering books with: %s", filter_obj)

        try:
            query = "SELECT * FROM books WHERE 1=1"
            params: list = []

            # Apply filters
            if filter_obj.search_query:
                query += " AND (title LIKE ? OR author LIKE ?)"
                params.extend([f"%{filter_obj.search_query}%", f"%{filter_obj.search_query}%"])

            if filter_obj.status:
                query += " AND status = ?"
                params.append(filter_obj.status)

            if filter_obj.author:
                query += " AND author = ?"
                params.append(filter_obj.author)

            # Collection filter
            if filter_obj.collection_id:
                query += """
                    AND id IN (
                        SELECT book_id FROM book_collections
                        WHERE collection_id = ?
                    )
                """
                params.append(filter_obj.collection_id)

            # Days since opened filter (for "Recent Reads" smart collection)
            if filter_obj.days_since_opened:
                query += " AND last_opened_date >= datetime('now', '-' || ? || ' days')"
                params.append(filter_obj.days_since_opened)

            # Apply sorting
            if filter_obj.sort_by == "recent":
                query += " ORDER BY last_opened_date DESC NULLS LAST, added_date DESC"
            elif filter_obj.sort_by == "title":
                query += " ORDER BY title COLLATE NOCASE"
            elif filter_obj.sort_by == "author":
                query += " ORDER BY author COLLATE NOCASE, title COLLATE NOCASE"
            elif filter_obj.sort_by == "progress":
                query += " ORDER BY reading_progress DESC"
            elif filter_obj.sort_by == "added_date_desc":
                query += " ORDER BY added_date DESC"
            else:
                # Default to recent if unknown sort_by
                query += " ORDER BY last_opened_date DESC NULLS LAST, added_date DESC"

            cursor = self._conn.cursor()
            cursor.execute(query, params)

            rows = cursor.fetchall()
            books = [self._row_to_metadata(row) for row in rows]

            logger.debug("Filter found %d books", len(books))
            return books

        except sqlite3.Error as e:
            error_msg = f"Failed to filter books: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_reading_position(
        self, book_id: int, chapter_index: int, scroll_position: int, progress: float
    ) -> None:
        """Update reading position for a book.

        Args:
            book_id: Database ID of the book.
            chapter_index: Current chapter index (0-based).
            scroll_position: Scroll position within chapter (pixels).
            progress: Overall reading progress (0.0 to 100.0).

        Raises:
            DatabaseError: If book doesn't exist or database operation fails.
        """
        logger.debug("Updating reading position for book %d", book_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                UPDATE books
                SET current_chapter_index = ?,
                    scroll_position = ?,
                    reading_progress = ?,
                    last_opened_date = ?,
                    status = CASE
                        WHEN status = 'not_started' THEN 'reading'
                        ELSE status
                    END
                WHERE id = ?
                """,
                (chapter_index, scroll_position, progress, datetime.now(), book_id),
            )

            self._conn.commit()

            if cursor.rowcount == 0:
                error_msg = f"Book not found: {book_id}"
                logger.warning(error_msg)
                raise DatabaseError(error_msg)

            logger.debug("Reading position updated for book %d", book_id)

        except sqlite3.Error as e:
            error_msg = f"Failed to update reading position: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _row_to_metadata(self, row: sqlite3.Row) -> BookMetadata:
        """Convert database row to BookMetadata object.

        Args:
            row: Database row from books table.

        Returns:
            BookMetadata object.
        """
        return BookMetadata(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            file_path=row["file_path"],
            cover_path=row["cover_path"],
            added_date=datetime.fromisoformat(row["added_date"]),
            last_opened_date=(
                datetime.fromisoformat(row["last_opened_date"])
                if row["last_opened_date"]
                else None
            ),
            reading_progress=row["reading_progress"],
            current_chapter_index=row["current_chapter_index"],
            scroll_position=row["scroll_position"],
            status=row["status"],
            file_size=row["file_size"],
        )

    # === Collection CRUD Methods ===

    def create_collection(self, name: str, color: str | None = None) -> int:
        """Create a new user collection.

        Args:
            name: Collection name (must be unique).
            color: Optional hex color for UI display (e.g., "#FF5733").

        Returns:
            Database ID of the newly created collection.

        Raises:
            DatabaseError: If collection name already exists or database operation fails.
        """
        logger.debug("Creating collection: %s", name)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO collections (name, color)
                VALUES (?, ?)
                """,
                (name, color),
            )
            self._conn.commit()

            collection_id = cursor.lastrowid
            logger.info("Created collection '%s' with ID %d", name, collection_id)
            return collection_id

        except sqlite3.IntegrityError as e:
            error_msg = f"Collection '{name}' already exists"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except sqlite3.Error as e:
            error_msg = f"Failed to create collection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_all_collections(self) -> list[Collection]:
        """Get all user collections with book counts.

        Returns:
            List of collections, sorted by sort_order then name.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Fetching all collections with book counts")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.id, c.name, c.created_date, c.color, c.sort_order,
                    COUNT(bc.book_id) as book_count
                FROM collections c
                LEFT JOIN book_collections bc ON c.id = bc.collection_id
                GROUP BY c.id
                ORDER BY c.sort_order, c.name COLLATE NOCASE
                """
            )

            collections = []
            for row in cursor.fetchall():
                collections.append(
                    Collection(
                        id=row["id"],
                        name=row["name"],
                        created_date=datetime.fromisoformat(row["created_date"]),
                        color=row["color"],
                        sort_order=row["sort_order"],
                        book_count=row["book_count"],
                    )
                )

            logger.debug("Found %d collections", len(collections))
            return collections

        except sqlite3.Error as e:
            error_msg = f"Failed to get collections: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_collection(self, collection_id: int) -> Collection | None:
        """Get a specific collection by ID.

        Args:
            collection_id: Collection database ID.

        Returns:
            Collection object if found, None otherwise.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Fetching collection %d", collection_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT
                    c.id, c.name, c.created_date, c.color, c.sort_order,
                    COUNT(bc.book_id) as book_count
                FROM collections c
                LEFT JOIN book_collections bc ON c.id = bc.collection_id
                WHERE c.id = ?
                GROUP BY c.id
                """,
                (collection_id,),
            )

            row = cursor.fetchone()
            if row is None:
                logger.debug("Collection %d not found", collection_id)
                return None

            collection = Collection(
                id=row["id"],
                name=row["name"],
                created_date=datetime.fromisoformat(row["created_date"]),
                color=row["color"],
                sort_order=row["sort_order"],
                book_count=row["book_count"],
            )

            logger.debug("Found collection: %s", collection.name)
            return collection

        except sqlite3.Error as e:
            error_msg = f"Failed to get collection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def add_book_to_collection(self, book_id: int, collection_id: int) -> None:
        """Add a book to a collection.

        Args:
            book_id: Book database ID.
            collection_id: Collection database ID.

        Raises:
            DatabaseError: If book or collection doesn't exist, or link already exists.
        """
        logger.debug("Adding book %d to collection %d", book_id, collection_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO book_collections (book_id, collection_id)
                VALUES (?, ?)
                """,
                (book_id, collection_id),
            )
            self._conn.commit()

            logger.info("Added book %d to collection %d", book_id, collection_id)

        except sqlite3.IntegrityError as e:
            error_msg = "Book already in collection or invalid book/collection ID"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except sqlite3.Error as e:
            error_msg = f"Failed to add book to collection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def remove_book_from_collection(self, book_id: int, collection_id: int) -> None:
        """Remove a book from a collection.

        Args:
            book_id: Book database ID.
            collection_id: Collection database ID.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Removing book %d from collection %d", book_id, collection_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                DELETE FROM book_collections
                WHERE book_id = ? AND collection_id = ?
                """,
                (book_id, collection_id),
            )
            self._conn.commit()

            if cursor.rowcount == 0:
                logger.warning("Book %d was not in collection %d", book_id, collection_id)
            else:
                logger.info("Removed book %d from collection %d", book_id, collection_id)

        except sqlite3.Error as e:
            error_msg = f"Failed to remove book from collection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_collection(self, collection_id: int) -> None:
        """Delete a user collection.

        Book-collection links are automatically deleted (ON DELETE CASCADE).

        Args:
            collection_id: Collection database ID.

        Raises:
            DatabaseError: If database operation fails.
        """
        logger.debug("Deleting collection %d", collection_id)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                DELETE FROM collections
                WHERE id = ?
                """,
                (collection_id,),
            )
            self._conn.commit()

            if cursor.rowcount == 0:
                logger.warning("Collection %d not found", collection_id)
            else:
                logger.info("Deleted collection %d", collection_id)

        except sqlite3.Error as e:
            error_msg = f"Failed to delete collection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def rename_collection(self, collection_id: int, new_name: str) -> None:
        """Rename a collection.

        Args:
            collection_id: Collection database ID.
            new_name: New collection name (must be unique).

        Raises:
            DatabaseError: If collection doesn't exist, name already taken, or database operation fails.
        """
        logger.debug("Renaming collection %d to '%s'", collection_id, new_name)

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                UPDATE collections
                SET name = ?
                WHERE id = ?
                """,
                (new_name, collection_id),
            )
            self._conn.commit()

            if cursor.rowcount == 0:
                error_msg = f"Collection {collection_id} not found"
                logger.error(error_msg)
                raise DatabaseError(error_msg)

            logger.info("Renamed collection %d to '%s'", collection_id, new_name)

        except sqlite3.IntegrityError as e:
            error_msg = f"Collection name '{new_name}' already exists"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except sqlite3.Error as e:
            error_msg = f"Failed to rename collection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
