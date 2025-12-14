# Library Management System Architecture

## Date
2025-12-13

## Context

**Problem:** Transform the e-reader from a single-book viewer into a personal library manager with collection organization, search, and reading persistence across multiple books.

**Current State:**
- Application has MVC architecture for single-book reading (EPUBBook → ReaderController → MainWindow/BookViewer)
- MainWindow uses single central widget (BookViewer + NavigationBar)
- Reading position stored in QSettings per file path
- No database, no book collection, no metadata persistence

**Requirements from UX Spec:**
- Multi-book library with grid/list views
- Import multiple EPUB files
- Collections system for organization
- Search and filter functionality
- Reading status tracking (not started, reading, finished)
- Reading position persistence per book
- Performance: Load 100 books < 500ms, search < 100ms

**Constraints:**
- Must integrate with existing ReaderController and book reading flow
- Must maintain existing MVC pattern
- Database must be local (SQLite, no server)
- Must support phased implementation (Phase 1 → Phase 2 → Phase 3)

---

## Architectural Decisions

### Decision 1: Database Layer Design

**think hard about database architecture**

#### Options Considered

**Option A: Direct SQL in Controller**
- Controllers execute raw SQL queries
- No abstraction layer

**Pros:**
- Simple, no extra layer
- Fast development
- Direct control over queries

**Cons:**
- SQL scattered across codebase
- Hard to test (need database for every test)
- Hard to change schema (find all queries)
- Violates separation of concerns
- SQL injection risk if not careful

---

**Option B: Repository Pattern**
- Create `LibraryRepository` class that encapsulates all database operations
- Controllers call repository methods, not raw SQL
- Repository owns database connection and schema

**Pros:**
- ✅ **Single responsibility**: All database logic in one place
- ✅ **Testable**: Easy to mock repository in controller tests
- ✅ **Schema isolation**: Schema changes only affect repository
- ✅ **Type safety**: Repository methods have clear type signatures
- ✅ **Transaction management**: Repository controls transaction boundaries
- ✅ **Migration friendly**: Schema version can be managed in repository

**Cons:**
- Extra abstraction layer
- More classes to maintain

---

**Option C: ORM (SQLAlchemy, Peewee)**
- Use full ORM for object-relational mapping
- Models defined as classes with relationships

**Pros:**
- Powerful query API
- Automatic relationship handling
- Migration tools

**Cons:**
- Heavy dependency for simple needs
- Learning curve (another framework to learn)
- Overkill for straightforward schema
- Potential performance overhead
- Harder to optimize queries

---

**Decision: Option B - Repository Pattern**

**Rationale:**
1. **Learning Value**: Teaches database design without ORM complexity
2. **Testability**: Repository easy to mock, controllers stay testable
3. **Flexibility**: Can write optimized SQL where needed
4. **Simplicity**: Straightforward pattern, easy to understand
5. **Right-sized**: Matches our scale (3 tables, simple queries)

**Implementation:**
```python
# src/ereader/models/library_database.py

class LibraryRepository:
    """Repository for library database operations (books, collections)."""

    def __init__(self, db_path: str | Path):
        """Initialize repository with database file path."""

    # Book CRUD
    def add_book(self, metadata: BookMetadata) -> int: ...
    def get_book(self, book_id: int) -> BookMetadata | None: ...
    def get_all_books(self) -> list[BookMetadata]: ...
    def update_book(self, book_id: int, **kwargs) -> None: ...
    def delete_book(self, book_id: int) -> None: ...

    # Search & Filter
    def search_books(self, query: str) -> list[BookMetadata]: ...
    def filter_books(self, filter: LibraryFilter) -> list[BookMetadata]: ...

    # Collections (Phase 2)
    def create_collection(self, name: str) -> int: ...
    def get_collections(self) -> list[Collection]: ...
    def add_book_to_collection(self, book_id: int, collection_id: int) -> None: ...

    # Position tracking
    def update_reading_position(self, book_id: int, position: ReadingPosition) -> None: ...
```

---

### Decision 2: View Switching Architecture

**think hard about how to transition between library and reader views**

#### Options Considered

**Option A: Two Separate Windows**
- Library window and reader window
- Open reader in new window when book selected

**Pros:**
- Simple window management
- Can have multiple books open simultaneously

**Cons:**
- Awkward UX (multiple windows to manage)
- Not how other e-readers work
- State management complex (which window is active?)

---

**Option B: QStackedWidget (Single Window, Multiple Views)**
- MainWindow contains QStackedWidget with two pages:
  - Index 0: LibraryView
  - Index 1: ReaderView (existing BookViewer + NavigationBar)
- Switch between views by changing QStackedWidget index

**Pros:**
- ✅ **Single window**: Matches user expectations from Kindle/Kobo
- ✅ **Clean transitions**: Qt handles view switching
- ✅ **State preservation**: Each view maintains its state when not visible
- ✅ **Simple architecture**: One window, two views
- ✅ **PyQt6 best practice**: Standard pattern for multi-view apps

**Cons:**
- Can only view one thing at a time (library OR reader, not both)

---

**Option C: Tab Widget**
- Library and reader as tabs in QTabWidget

**Pros:**
- Easy to switch views
- Can see both tabs available

**Cons:**
- Tabs don't make sense for this UX (not documents)
- Not how e-readers work
- Tab bar takes space

---

**Decision: Option B - QStackedWidget**

**Rationale:**
1. **UX Convention**: Kindle, Kobo, Apple Books all use single-window switching
2. **State Preservation**: QStackedWidget keeps both views in memory, fast switching
3. **Clean API**: `stack.setCurrentIndex(0)` for library, `stack.setCurrentIndex(1)` for reader
4. **Minimal Changes**: Existing reader layout becomes one page of stack

**Implementation:**
```python
# Modified MainWindow structure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create stacked widget
        self._stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self._stacked_widget)

        # Page 0: Library View
        self._library_view = LibraryView(self)
        self._stacked_widget.addWidget(self._library_view)  # Index 0

        # Page 1: Reader View (existing components)
        reader_container = QWidget(self)
        reader_layout = QVBoxLayout(reader_container)
        reader_layout.addWidget(self._book_viewer)
        reader_layout.addWidget(self._navigation_bar)
        self._stacked_widget.addWidget(reader_container)  # Index 1

        # Start on library view
        self._stacked_widget.setCurrentIndex(0)

    def show_library(self) -> None:
        self._stacked_widget.setCurrentIndex(0)

    def show_reader(self) -> None:
        self._stacked_widget.setCurrentIndex(1)
```

---

### Decision 3: MVC Structure for Library

**Maintain MVC pattern with dedicated library components**

#### Architecture Overview

```
┌─────────────────────────────────────────┐
│           MainWindow (View)             │
│  ┌───────────────────────────────────┐  │
│  │     QStackedWidget                │  │
│  │  ┌────────────┐  ┌─────────────┐ │  │
│  │  │ Library    │  │ Reader      │ │  │
│  │  │ View       │  │ View        │ │  │
│  │  │ (Index 0)  │  │ (Index 1)   │ │  │
│  │  └────────────┘  └─────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │ Library │          │ Reader  │
    │Controller│          │Controller│
    └────┬────┘          └────┬────┘
         │                    │
    ┌────▼────┐          ┌────▼────┐
    │Library  │          │ EPUB    │
    │Database │          │ Book    │
    │(Model)  │          │ (Model) │
    └─────────┘          └─────────┘
```

#### Component Responsibilities

**Models (Data Layer)**
- `LibraryRepository` - Database operations (books, collections, positions)
- `BookMetadata` - Lightweight book data for library display
- `EPUBBook` - Full book parser (existing, used when reading)

**Controllers (Business Logic)**
- `LibraryController` - Manages library state, import, search/filter
- `ReaderController` - Manages reading state (existing, slight modifications)

**Views (UI Layer)**
- `LibraryView` - Main library UI container
- `BookGridWidget` - Grid of book cards
- `BookCardWidget` - Single book card display
- `EmptyLibraryWidget` - Empty state display
- `MainWindow` - Coordinates view switching

---

### Decision 4: Data Model Design

**Separate BookMetadata (lightweight) from EPUBBook (heavyweight)**

#### Problem
- EPUBBook parses entire EPUB file (expensive)
- Library needs to display 100+ books quickly
- Solution: Two-tier data model

#### Data Models

**BookMetadata (dataclass)**
```python
@dataclass
class BookMetadata:
    """Lightweight book data for library display.

    Loaded from database, not from EPUB file.
    Used for library grid rendering.
    """
    id: int                              # Database primary key
    title: str
    author: str | None
    file_path: str                        # Absolute path to EPUB
    cover_path: str | None                # Path to cover image (Phase 2)
    added_date: datetime
    last_opened_date: datetime | None
    reading_progress: float               # 0.0 to 100.0
    current_chapter_index: int
    scroll_position: int
    status: str                           # "not_started" | "reading" | "finished"
    file_size: int | None
```

**EPUBBook (existing class)**
- Full EPUB parser
- Only loaded when user opens book for reading
- Expensive operation (parses ZIP, XML)

**Separation Benefits:**
1. **Fast library loading**: Display 100 books without parsing 100 EPUBs
2. **Memory efficient**: Metadata is ~1KB/book, EPUBBook is ~500KB+
3. **Clear separation**: Database data vs file data

---

### Decision 5: Import Workflow Design

**Synchronous import with progress feedback for Phase 1, async for Phase 2**

#### Phase 1: Synchronous Import (MVP)

**Rationale:**
- Simpler to implement and test
- Importing 5-10 books is fast enough (~1-2s)
- Blocking UI during import is acceptable for MVP
- Can show progress toast (non-blocking visual feedback)

**Implementation:**
```python
class LibraryController(QObject):
    # Signals
    import_started = pyqtSignal(int)  # total_files
    import_progress = pyqtSignal(int, int, str)  # current, total, filename
    import_completed = pyqtSignal(int, int)  # succeeded, failed
    import_error = pyqtSignal(str, str)  # filename, error_message

    def import_books(self, filepaths: list[str]) -> None:
        """Import books into library (synchronous for Phase 1)."""
        total = len(filepaths)
        succeeded = 0
        failed = 0

        self.import_started.emit(total)

        for i, filepath in enumerate(filepaths, 1):
            self.import_progress.emit(i, total, Path(filepath).name)

            try:
                # Parse EPUB to get metadata
                book = EPUBBook(filepath)

                # Create metadata record
                metadata = BookMetadata(
                    id=0,  # Will be set by database
                    title=book.title,
                    author=", ".join(book.authors) if book.authors else "Unknown",
                    file_path=str(Path(filepath).absolute()),
                    cover_path=None,  # Phase 2
                    added_date=datetime.now(),
                    last_opened_date=None,
                    reading_progress=0.0,
                    current_chapter_index=0,
                    scroll_position=0,
                    status="not_started",
                    file_size=Path(filepath).stat().st_size
                )

                # Add to database
                self._repository.add_book(metadata)
                succeeded += 1

            except Exception as e:
                logger.exception(f"Failed to import {filepath}")
                self.import_error.emit(Path(filepath).name, str(e))
                failed += 1

        self.import_completed.emit(succeeded, failed)
```

#### Phase 2: Async Import (Future Enhancement)

**When to add:**
- User requests importing many books (50+)
- Feedback shows UI blocking is annoying

**Implementation:**
- Use QThread for background import
- Emit progress signals from thread
- Update UI on main thread via signals

---

### Decision 6: Integration with Existing Reader

**Minimal modifications to ReaderController, extend for library support**

#### Changes to ReaderController

**Add database persistence:**
```python
class ReaderController(QObject):
    def __init__(self, repository: LibraryRepository | None = None):
        # ... existing init ...
        self._repository = repository  # Optional for backward compatibility
        self._current_book_id: int | None = None  # Track book ID in library

    def open_book_from_library(self, book_id: int) -> None:
        """Open book from library (new method for library integration)."""
        # Get metadata from database
        metadata = self._repository.get_book(book_id)
        if metadata is None:
            self.error_occurred.emit("Book Not Found", "This book is no longer in the library.")
            return

        # Open the EPUB file
        self._current_book_id = book_id
        self.open_book(metadata.file_path)

        # Restore saved position
        self._restore_position(metadata)

    def _restore_position(self, metadata: BookMetadata) -> None:
        """Restore reading position from metadata."""
        if metadata.current_chapter_index > 0:
            self._current_chapter_index = metadata.current_chapter_index
            self._load_chapter(metadata.current_chapter_index)
            # Restore scroll position (requires viewer reference)
            if self._book_viewer:
                self._book_viewer.set_scroll_position(metadata.scroll_position)

    def save_current_position(self) -> None:
        """Save reading position to database (called on chapter change, app close)."""
        if self._repository and self._current_book_id and self._book:
            position = ReadingPosition(
                chapter_index=self._current_chapter_index,
                scroll_position=self._book_viewer.get_scroll_position() if self._book_viewer else 0,
                progress_percentage=self._calculate_progress()
            )
            self._repository.update_reading_position(self._current_book_id, position)
```

**Backward Compatibility:**
- `open_book(filepath)` still works (direct file opening, legacy mode)
- `open_book_from_library(book_id)` new method for library integration
- Repository is optional parameter (existing tests don't need it)

---

### Decision 7: Search and Filter Implementation

**In-memory filtering for Phase 1, indexed search for Phase 2 if needed**

#### Phase 1: Simple SQL LIKE Queries

**Rationale:**
- SQLite full-text search (FTS) is complex
- LIKE queries sufficient for < 1000 books
- Meets < 100ms search requirement

**Implementation:**
```python
class LibraryRepository:
    def search_books(self, query: str) -> list[BookMetadata]:
        """Search books by title or author (case-insensitive)."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY last_opened_date DESC
        """, (f"%{query}%", f"%{query}%"))
        return [self._row_to_metadata(row) for row in cursor.fetchall()]

    def filter_books(self, filter: LibraryFilter) -> list[BookMetadata]:
        """Filter and sort books based on filter criteria."""
        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if filter.collection_id:
            query += " AND id IN (SELECT book_id FROM book_collections WHERE collection_id = ?)"
            params.append(filter.collection_id)

        if filter.status:
            query += " AND status = ?"
            params.append(filter.status)

        if filter.search_query:
            query += " AND (title LIKE ? OR author LIKE ?)"
            params.extend([f"%{filter.search_query}%", f"%{filter.search_query}%"])

        # Sort
        if filter.sort_by == "recent":
            query += " ORDER BY last_opened_date DESC NULLS LAST, added_date DESC"
        elif filter.sort_by == "title":
            query += " ORDER BY title COLLATE NOCASE"
        elif filter.sort_by == "author":
            query += " ORDER BY author COLLATE NOCASE"

        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return [self._row_to_metadata(row) for row in cursor.fetchall()]
```

#### Phase 2: Optimize if Needed
- Add SQLite FTS5 virtual table
- Add indexes on frequently queried columns
- Measure performance with 1000+ book library

---

### Decision 8: Database Schema and Migrations

**Simple schema versioning with manual migrations**

#### Schema Version Tracking

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Migration Strategy

**Phase 1: Create tables on first launch**
```python
class LibraryRepository:
    CURRENT_SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist, run migrations if needed."""
        # Check current version
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version")
            current_version = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # schema_version table doesn't exist, this is first run
            current_version = 0

        if current_version < self.CURRENT_SCHEMA_VERSION:
            self._run_migrations(current_version)

    def _run_migrations(self, from_version: int) -> None:
        """Run migrations from from_version to CURRENT_SCHEMA_VERSION."""
        if from_version < 1:
            self._create_initial_schema()
        # Future: if from_version < 2: self._migrate_v1_to_v2()
```

#### Initial Schema (Phase 1)

```sql
-- Books table
CREATE TABLE books (
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
);

-- Indexes for common queries
CREATE INDEX idx_books_last_opened ON books(last_opened_date DESC);
CREATE INDEX idx_books_title ON books(title COLLATE NOCASE);
CREATE INDEX idx_books_author ON books(author COLLATE NOCASE);
CREATE INDEX idx_books_status ON books(status);

-- Schema version tracking
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version) VALUES (1);
```

#### Collections Schema (Phase 2)

```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE book_collections (
    book_id INTEGER NOT NULL,
    collection_id INTEGER NOT NULL,
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (book_id, collection_id),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
);

CREATE INDEX idx_book_collections_book ON book_collections(book_id);
CREATE INDEX idx_book_collections_collection ON book_collections(collection_id);
```

---

### Decision 9: UI Component Architecture

**Custom QListView with delegate for book cards**

#### Options Considered

**Option A: QScrollArea with Manual Grid Layout**
- Manually position QWidget cards in grid
- Handle resize events manually

**Pros:**
- Full control over rendering

**Cons:**
- Reinventing the wheel
- No built-in selection, keyboard nav
- Hard to make performant with many items

---

**Option B: QListView with QStyledItemDelegate**
- Use PyQt6's model/view architecture
- Custom delegate paints book cards
- QListView handles scrolling, selection, keyboard

**Pros:**
- ✅ **PyQt6 best practice**: Designed for this use case
- ✅ **Performance**: Built-in virtualization (only renders visible items)
- ✅ **Selection**: Free selection, multi-select, keyboard nav
- ✅ **Scrolling**: Smooth scrolling, keyboard support
- ✅ **Learning value**: Teaches Qt model/view pattern

**Cons:**
- More complex setup (model + delegate)
- Steeper learning curve

---

**Option C: QTableView**
- Table with custom rendering

**Pros:**
- Good for list view (columns)

**Cons:**
- Wrong mental model for grid view
- Columns don't map to grid cards naturally

---

**Decision: Option B - QListView with Custom Delegate**

**Rationale:**
1. **Performance**: Virtualization handles 1000+ books efficiently
2. **Learning Value**: Teaches Qt model/view architecture
3. **Features**: Selection, keyboard nav, scrolling all free
4. **Standard Pattern**: How Qt apps should handle lists/grids

#### Implementation Structure

```python
# src/ereader/views/book_grid_widget.py

class BookGridWidget(QListView):
    """Grid view of book cards using Qt model/view architecture."""

    book_selected = pyqtSignal(int)  # book_id
    book_activated = pyqtSignal(int)  # book_id (double-click/enter)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configure list view for grid display
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setSpacing(20)
        self.setUniformItemSizes(True)  # Performance hint

        # Set custom delegate for card rendering
        self._delegate = BookCardDelegate(self)
        self.setItemDelegate(self._delegate)

        # Set model
        self._model = BookListModel([], self)
        self.setModel(self._model)

        # Connect signals
        self.clicked.connect(self._on_clicked)
        self.activated.connect(self._on_activated)

    def set_books(self, books: list[BookMetadata]) -> void:
        """Update the list of books to display."""
        self._model.set_books(books)


# src/ereader/views/book_card_delegate.py

class BookCardDelegate(QStyledItemDelegate):
    """Custom delegate for rendering book cards in grid."""

    CARD_WIDTH = 180
    CARD_HEIGHT = 260

    def paint(self, painter, option, index):
        """Paint a book card."""
        book = index.data(Qt.ItemDataRole.UserRole)  # BookMetadata

        # Draw card background
        # Draw cover (or placeholder)
        # Draw title (truncated)
        # Draw author
        # Draw progress bar
        # Draw progress percentage
        # ... custom painting logic ...

    def sizeHint(self, option, index):
        """Return size of book card."""
        return QSize(self.CARD_WIDTH, self.CARD_HEIGHT)


# src/ereader/views/book_list_model.py

class BookListModel(QAbstractListModel):
    """Model for list of books (Qt model/view architecture)."""

    def __init__(self, books: list[BookMetadata], parent=None):
        super().__init__(parent)
        self._books = books

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._books)

    def data(self, index, role):
        if not index.isValid():
            return None

        book = self._books[index.row()]

        if role == Qt.ItemDataRole.UserRole:
            return book  # Return full BookMetadata
        elif role == Qt.ItemDataRole.DisplayRole:
            return book.title

        return None

    def set_books(self, books: list[BookMetadata]) -> None:
        """Update book list (triggers view refresh)."""
        self.beginResetModel()
        self._books = books
        self.endResetModel()
```

---

## Component Interface Summary

### New Data Models

**BookMetadata (dataclass)**
```python
@dataclass
class BookMetadata:
    id: int
    title: str
    author: str | None
    file_path: str
    cover_path: str | None
    added_date: datetime
    last_opened_date: datetime | None
    reading_progress: float
    current_chapter_index: int
    scroll_position: int
    status: str
    file_size: int | None
```

**LibraryFilter (dataclass)**
```python
@dataclass
class LibraryFilter:
    search_query: str = ""
    collection_id: int | None = None
    status: str | None = None
    sort_by: str = "recent"  # recent | title | author
```

**Collection (dataclass, Phase 2)**
```python
@dataclass
class Collection:
    id: int
    name: str
    created_date: datetime
    book_count: int
```

### New Repository

**LibraryRepository**
```python
class LibraryRepository:
    def __init__(self, db_path: Path): ...

    # Book operations
    def add_book(self, metadata: BookMetadata) -> int: ...
    def get_book(self, book_id: int) -> BookMetadata | None: ...
    def get_all_books(self) -> list[BookMetadata]: ...
    def update_book(self, book_id: int, **kwargs) -> None: ...
    def delete_book(self, book_id: int) -> None: ...

    # Search & filter
    def search_books(self, query: str) -> list[BookMetadata]: ...
    def filter_books(self, filter: LibraryFilter) -> list[BookMetadata]: ...

    # Position tracking
    def update_reading_position(self, book_id: int, position: ReadingPosition) -> None: ...

    # Collections (Phase 2)
    def create_collection(self, name: str) -> int: ...
    def get_collections(self) -> list[Collection]: ...
    def add_book_to_collection(self, book_id: int, collection_id: int) -> None: ...
    def remove_book_from_collection(self, book_id: int, collection_id: int) -> None: ...
```

### New Controller

**LibraryController**
```python
class LibraryController(QObject):
    # Signals
    library_loaded = pyqtSignal(list)  # list[BookMetadata]
    import_started = pyqtSignal(int)  # total_files
    import_progress = pyqtSignal(int, int, str)  # current, total, filename
    import_completed = pyqtSignal(int, int)  # succeeded, failed
    import_error = pyqtSignal(str, str)  # filename, error_message
    filter_changed = pyqtSignal(list)  # filtered list[BookMetadata]

    def __init__(self, repository: LibraryRepository): ...

    # Library management
    def load_library(self) -> None: ...
    def import_books(self, filepaths: list[str]) -> None: ...
    def delete_book(self, book_id: int) -> None: ...

    # Search & filter
    def set_filter(self, filter: LibraryFilter) -> None: ...
    def search(self, query: str) -> None: ...

    # Collections (Phase 2)
    def create_collection(self, name: str) -> None: ...
    def add_to_collection(self, book_id: int, collection_id: int) -> None: ...
```

### New Views

**LibraryView**
```python
class LibraryView(QWidget):
    book_open_requested = pyqtSignal(int)  # book_id
    import_requested = pyqtSignal()

    def __init__(self, parent=None): ...
    def set_books(self, books: list[BookMetadata]) -> None: ...
    def show_empty_state(self) -> None: ...
```

**BookGridWidget**
```python
class BookGridWidget(QListView):
    book_selected = pyqtSignal(int)  # book_id
    book_activated = pyqtSignal(int)  # book_id (double-click)

    def set_books(self, books: list[BookMetadata]) -> None: ...
```

**EmptyLibraryWidget**
```python
class EmptyLibraryWidget(QWidget):
    import_requested = pyqtSignal()

    def __init__(self, parent=None): ...
```

### Modified Classes

**MainWindow**
```python
class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing init ...

        # Replace single central widget with stacked widget
        self._stacked_widget = QStackedWidget(self)
        self._library_view = LibraryView(self)  # Index 0
        self._reader_view = # existing BookViewer+Nav  # Index 1

        # Create both controllers
        self._library_controller = LibraryController(repository)
        self._reader_controller = ReaderController(repository)

        # Connect library → reader transition
        self._library_view.book_open_requested.connect(self._open_book_from_library)

    def _open_book_from_library(self, book_id: int) -> None:
        self._reader_controller.open_book_from_library(book_id)
        self._stacked_widget.setCurrentIndex(1)  # Switch to reader

    def show_library(self) -> None:
        self._stacked_widget.setCurrentIndex(0)

    def show_reader(self) -> None:
        self._stacked_widget.setCurrentIndex(1)
```

**ReaderController**
```python
class ReaderController(QObject):
    def __init__(self, repository: LibraryRepository | None = None):
        # ... existing init ...
        self._repository = repository
        self._current_book_id: int | None = None

    def open_book_from_library(self, book_id: int) -> None: ...
    def save_current_position(self) -> None: ...
```

---

## Database Location and Initialization

**Database Path:**
```python
# Platform-specific user data directory
from pathlib import Path
import sys

def get_library_db_path() -> Path:
    """Get platform-appropriate path for library database."""
    if sys.platform == "darwin":  # macOS
        data_dir = Path.home() / "Library" / "Application Support" / "EReader"
    elif sys.platform == "win32":  # Windows
        data_dir = Path(os.getenv("APPDATA", Path.home())) / "EReader"
    else:  # Linux
        data_dir = Path.home() / ".local" / "share" / "ereader"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "library.db"
```

**Initialization in main():**
```python
# src/ereader/__main__.py

def main():
    app = QApplication(sys.argv)

    # Initialize database
    db_path = get_library_db_path()
    repository = LibraryRepository(db_path)

    # Create main window with repository
    window = MainWindow(repository)
    window.show()

    sys.exit(app.exec())
```

---

## Phased Implementation Plan

### Phase 1: Basic Library (MVP)

**Files to Create:**
- `src/ereader/models/library_database.py` - LibraryRepository
- `src/ereader/models/book_metadata.py` - BookMetadata dataclass
- `src/ereader/controllers/library_controller.py` - LibraryController
- `src/ereader/views/library_view.py` - Main library container
- `src/ereader/views/book_grid_widget.py` - Grid display
- `src/ereader/views/book_list_model.py` - Qt model
- `src/ereader/views/book_card_delegate.py` - Card rendering
- `src/ereader/views/empty_library_widget.py` - Empty state
- `src/ereader/utils/database_utils.py` - Database path helpers

**Files to Modify:**
- `src/ereader/views/main_window.py` - Add QStackedWidget
- `src/ereader/controllers/reader_controller.py` - Add library integration
- `src/ereader/__main__.py` - Initialize repository

**Features:**
✅ SQLite database with books table
✅ Import EPUB files (sync, single or multi-select)
✅ Grid view with placeholder book cards
✅ Double-click to open book
✅ QStackedWidget view switching
✅ Reading position persistence per book
✅ Empty library state

**Tests:**
- Unit tests for LibraryRepository (CRUD, search)
- Unit tests for LibraryController (import, filter)
- Integration test: Import → view → open → read → switch back
- UI tests with pytest-qt

---

### Phase 2: Organization

**Files to Create:**
- `src/ereader/models/collection.py` - Collection dataclass
- `src/ereader/views/collection_manager.py` - Collection UI (dialog/sidebar)

**Files to Modify:**
- `src/ereader/models/library_database.py` - Add collection methods
- `src/ereader/controllers/library_controller.py` - Add collection logic
- `src/ereader/views/library_view.py` - Add filter/sort UI

**Features:**
✅ Collections table and many-to-many relationships
✅ Create, rename, delete collections
✅ Assign books to collections
✅ Filter by collection
✅ Filter by reading status
✅ Sort by title, author, recent
✅ Real-time search

---

### Phase 3: Polish

**Files to Create:**
- `src/ereader/views/continue_reading_widget.py` - Recent books section
- `src/ereader/utils/cover_extractor.py` - Extract EPUB covers
- `src/ereader/views/book_details_dialog.py` - Book info dialog

**Files to Modify:**
- `src/ereader/views/book_card_delegate.py` - Render real covers
- `src/ereader/views/library_view.py` - Add continue reading section
- `src/ereader/views/book_grid_widget.py` - Add context menu

**Features:**
✅ Continue Reading section (3-5 recent books)
✅ Cover image extraction
✅ List view alternative
✅ Context menus (right-click actions)
✅ Book details view
✅ Drag-and-drop import

---

## Performance Considerations

### Load Time Targets
- **Library load (100 books):** < 500ms
  - Database query: ~10ms (indexed)
  - Model setup: ~50ms
  - Initial render: ~100ms (virtualization)
  - Total budget: 160ms ✅ well under target

- **Search:** < 100ms
  - SQL LIKE query: ~20ms
  - Model update: ~20ms
  - Re-render: ~50ms
  - Total: ~90ms ✅

- **Import (10 books):** < 5s
  - EPUB parse: ~200ms/book = 2s
  - Database insert: ~10ms/book = 100ms
  - Total: ~2.1s ✅

### Memory Usage
- **BookMetadata:** ~1KB/book
- **100 books in memory:** ~100KB (negligible)
- **Qt model/view:** Only visible cards rendered (~20 cards × 50KB = 1MB)
- **Total library overhead:** < 5MB ✅ well under 200MB budget

### Optimization Strategies
1. **Lazy loading:** Only parse EPUB when opening, not when importing (Phase 1)
2. **Virtualization:** QListView only renders visible cards
3. **Indexing:** Database indexes on commonly queried columns
4. **Prepared statements:** Reuse SQL statements
5. **Connection pooling:** Single database connection per app instance

---

## Error Handling Strategy

### Import Errors
```python
try:
    book = EPUBBook(filepath)
except FileNotFoundError:
    # File was deleted between selection and import
    error_msg = f"{filename} - File not found"
except EPUBParseError as e:
    # Not a valid EPUB
    error_msg = f"{filename} - Not a valid EPUB: {e}"
except PermissionError:
    # No read permission
    error_msg = f"{filename} - Permission denied"
except Exception as e:
    # Unexpected error
    logger.exception(f"Unexpected error importing {filepath}")
    error_msg = f"{filename} - Unexpected error: {e}"

# Emit error signal
self.import_error.emit(filename, error_msg)
```

### Database Errors
```python
try:
    self._repository.add_book(metadata)
except sqlite3.IntegrityError:
    # Book already in library (duplicate file_path)
    self.import_error.emit(filename, "Already in library")
except sqlite3.OperationalError as e:
    # Database locked, disk full, etc.
    logger.error(f"Database error: {e}")
    self.import_error.emit(filename, "Database error")
```

### File Path Errors (Book Moved/Deleted)
```python
def open_book_from_library(self, book_id: int) -> None:
    metadata = self._repository.get_book(book_id)
    if not Path(metadata.file_path).exists():
        self.error_occurred.emit(
            "Book Not Found",
            f"The file for '{metadata.title}' could not be found at:\n"
            f"{metadata.file_path}\n\n"
            f"It may have been moved or deleted. Remove from library?"
        )
        return

    self.open_book(metadata.file_path)
```

---

## Migration from QSettings to Database

**Backward Compatibility Strategy:**

On first library load, migrate existing reading positions from QSettings:

```python
class LibraryRepository:
    def migrate_from_qsettings(self) -> None:
        """Migrate reading positions from QSettings to database (one-time)."""
        from PyQt6.QtCore import QSettings

        settings = QSettings("EReader", "EReader")
        settings.beginGroup("reading_positions")

        for filepath in settings.allKeys():
            # Check if book is in library
            book = self.get_book_by_path(filepath)
            if book is None:
                continue  # Book not in library, skip

            # Migrate position
            position_data = settings.value(filepath)
            if position_data:
                self.update_reading_position(book.id, position_data)

        settings.endGroup()

        # Mark migration complete
        settings.setValue("library_migration_complete", True)
```

---

## Testing Strategy

### Unit Tests

**LibraryRepository:**
- Test database creation and schema version
- Test CRUD operations (add, get, update, delete books)
- Test search and filter queries
- Test collection operations (Phase 2)
- Test edge cases (duplicate file_path, missing books)
- Use in-memory database (`:memory:`) for fast tests

**LibraryController:**
- Mock LibraryRepository
- Test import workflow (success, failures, partial success)
- Test filter logic
- Test signal emissions

**BookListModel:**
- Test rowCount, data, setBooks
- Test model updates trigger view refresh

### Integration Tests

**Import Workflow:**
- Import real EPUB files
- Verify database entries created
- Verify metadata extracted correctly
- Test multi-file import

**View Switching:**
- Open library → select book → verify reader opens
- Read book → switch to library → verify library state preserved

### UI Tests (pytest-qt)

**LibraryView:**
- Test book grid renders
- Test empty state displays when no books
- Test search filtering
- Test double-click opens book

**BookGridWidget:**
- Test selection with mouse and keyboard
- Test scrolling
- Test card rendering (via delegate)

### Performance Tests

**Load 100 books:**
- Measure database query time
- Measure model setup time
- Measure initial render time
- Assert total < 500ms

**Search:**
- Measure search query time
- Assert < 100ms

---

## Consequences

### What This Enables ✅

1. **Multi-book library**: Users can manage large collections
2. **Persistent reading positions**: Resume any book where you left off
3. **Organization**: Collections, search, filters
4. **Fast access**: Grid view with quick search
5. **Foundation for features**: Bookmarks, annotations, stats all need database
6. **Learning value**: SQLite, Qt model/view, repository pattern

### What This Constrains 📍

1. **Database dependency**: App now requires SQLite (built into Python, OK)
2. **View switching**: Can only view library OR reader, not both simultaneously
3. **Single library**: One database per user (could add multi-library later)
4. **File paths**: Books must remain at saved paths (could add file watching later)

### What to Watch Out For ⚠️

1. **Database corruption**: Need backup/recovery strategy (Phase 3)
2. **File path changes**: If user moves EPUB files, library breaks
   - Mitigation: Show error, offer to remove from library
3. **Large libraries**: Test with 1000+ books to verify performance
4. **Concurrent access**: Don't allow multiple app instances (file lock)
5. **Platform differences**: Test database path logic on macOS, Windows, Linux

---

## Implementation Guidance

### Development Order (Phase 1)

1. **Database foundation:**
   - Create LibraryRepository with schema
   - Write unit tests for CRUD operations
   - Test with in-memory database

2. **Data models:**
   - Create BookMetadata dataclass
   - Create LibraryFilter dataclass
   - Document data flow

3. **Controller logic:**
   - Create LibraryController
   - Implement import_books()
   - Write controller unit tests

4. **Qt model/view:**
   - Create BookListModel
   - Create BookCardDelegate
   - Create BookGridWidget
   - Test with mock data

5. **Library view:**
   - Create LibraryView container
   - Create EmptyLibraryWidget
   - Wire up signals

6. **Integration:**
   - Modify MainWindow for QStackedWidget
   - Modify ReaderController for library support
   - Test full workflow

7. **Polish:**
   - Add keyboard shortcuts
   - Add menu items
   - Add error handling
   - Manual testing with real EPUBs

### Testing Workflow

```bash
# Run tests frequently
/test

# Test specific module
uv run pytest tests/test_models/test_library_database.py -v

# Test with coverage
uv run pytest --cov=src/ereader/models/library_database.py
```

### Development Commands

```bash
# Create feature branch
/branch feature/library-management-phase1

# Implement with guidance
/developer

# Review before committing
/code-review

# Create PR
/pr
```

---

## References

- **UX Spec:** docs/specs/library-management-system.md
- **Existing MVC:** docs/architecture/epub-rendering-architecture.md
- **Project Principles:** CLAUDE.md
- **SQLite Docs:** https://docs.python.org/3/library/sqlite3.html
- **Qt Model/View:** https://doc.qt.io/qt-6/model-view-programming.html
- **Repository Pattern:** https://martinfowler.com/eaaCatalog/repository.html

---

## Next Steps

1. **Review this architecture** - User approves design
2. **Create GitHub issue** - Track Phase 1 implementation
3. **Invoke `/developer`** - Begin Phase 1 implementation
4. **Iterate through phases** - Ship incrementally

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-13 | Initial architecture | Library management system design |
