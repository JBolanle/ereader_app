# Library Phase 2: Organization Architecture

## Date
2025-12-14

## Context

**Current State (Phase 1 Complete):**
- SQLite database with `books` table
- LibraryRepository with CRUD operations
- BookGridWidget with grid display
- Import workflow (synchronous, multiple files)
- Reading position persistence per book
- Basic LibraryView (empty state + grid)

**Phase 2 Goal:**
Transform library from simple grid display into organized collection system with:
- Sidebar-based collection navigation (from UI mockup)
- Smart collections (Recent Reads, Favorites, Currently Reading, To Read)
- User-created collections
- Filter, sort, and real-time search
- Enhanced reading status tracking

**UI Design Source:**
- Mockup: `docs/ux/ui-references/mockup1.png`
- Spec: `docs/specs/library-management-system.md`

**Key UX Insight from Mockup:**
The mockup shows a **sidebar-based collection browser** (like Apple Books/Music), NOT dropdown filters. This is a significant UX improvement over the original spec's filter dropdown approach.

**Constraints:**
- Must integrate with existing Phase 1 code (LibraryRepository, BookGridWidget)
- Database migration from schema v1 to v2
- Maintain < 100ms search performance
- Support 100+ books in library

---

## Architectural Decisions

### Decision 1: Sidebar Layout Architecture

**Think about the best UI structure for sidebar + main content.**

#### Options Considered

**Option A: QSplitter (Sidebar | Main Content)**
- Left panel: Collection sidebar (tree/list)
- Right panel: Book grid + header

**Pros:**
- ✅ Native PyQt6 widget with built-in resize handle
- ✅ User can adjust sidebar width
- ✅ State preservation (splitter position saved)
- ✅ Standard desktop pattern (Finder, iTunes, Apple Books)

**Cons:**
- Need to manage splitter state in settings

---

**Option B: Fixed Layout (QHBoxLayout)**
- Fixed-width sidebar (no resize)
- Main content takes remaining space

**Pros:**
- Simpler implementation
- Predictable layout

**Cons:**
- ❌ No user control over sidebar width
- ❌ Feels rigid on different screen sizes
- ❌ Not standard for desktop apps

---

**Option C: Collapsible Sidebar (Custom Widget)**
- Sidebar can be toggled hidden/visible
- Animated transition

**Pros:**
- Maximizes space when sidebar hidden
- Good for small screens

**Cons:**
- More complex implementation
- Not in original mockup
- Can implement later if needed

---

**Decision: Option A - QSplitter**

**Rationale:**
1. **UX Convention**: Matches Finder, iTunes, Apple Books, Kindle
2. **User Control**: Users can adjust sidebar width to preference
3. **PyQt6 Standard**: Built-in widget, well-tested
4. **Responsive**: Works on different screen sizes

**Implementation:**
```python
class LibraryView(QWidget):
    def __init__(self):
        # Replace current single-widget layout with splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Collection sidebar
        self._sidebar = CollectionSidebarWidget(self)
        self._splitter.addWidget(self._sidebar)

        # Right panel: Main content (header + grid)
        self._main_panel = QWidget(self)
        # ... (existing grid widget goes here)
        self._splitter.addWidget(self._main_panel)

        # Set initial sizes (sidebar 250px, main gets rest)
        self._splitter.setSizes([250, 750])

        # Save/restore splitter state
        settings = QSettings("EReader", "EReader")
        if settings.contains("library_splitter_state"):
            self._splitter.restoreState(settings.value("library_splitter_state"))
```

---

### Decision 2: Smart Collections vs User Collections

**Think hard about how to distinguish smart collections from user-created ones.**

#### Options Considered

**Option A: Database Flag (is_smart BOOLEAN)**
- Add `is_smart` column to collections table
- Smart collections have `is_smart = 1`
- Cannot be deleted or renamed if `is_smart = 1`

**Pros:**
- Simple to implement
- All collections in same table

**Cons:**
- Smart collections computed dynamically (not stored)
- Mixing stored data with computed data in same table
- Confusing data model

---

**Option B: Separate Smart Collections (Code-Only)**
- Smart collections defined in code, not database
- User collections stored in database
- Smart collections query books with specific criteria

**Pros:**
- ✅ **Clear separation**: Smart = computed, User = stored
- ✅ **No database overhead**: Smart collections don't need rows
- ✅ **Easier to add new smart collections**: Just add to code
- ✅ **Better performance**: No need to query collections table for smart ones

**Cons:**
- Two different data sources (code vs database)
- Need abstraction to handle both uniformly in UI

---

**Option C: Hybrid (Store All in Database)**
- Store smart collections in database like user collections
- Mark with `is_smart = 1`
- Update counts via triggers or periodic refresh

**Pros:**
- Uniform storage

**Cons:**
- ❌ Complex triggers needed
- ❌ Redundant data (counts stored but derived)
- ❌ Harder to maintain consistency

---

**Decision: Option B - Separate Smart Collections (Code-Only)**

**Rationale:**
1. **Conceptual Clarity**: Smart collections are queries, not stored entities
2. **Performance**: No database lookups for smart collection definitions
3. **Maintainability**: Add new smart collections by editing code
4. **Standard Pattern**: Kindle, Apple Books use same approach

**Implementation:**

```python
# Smart collections defined as queries
class SmartCollections:
    """Definitions for built-in smart collections."""

    @staticmethod
    def recent_reads(repository: LibraryRepository) -> list[BookMetadata]:
        """Books opened in last 30 days, sorted by last opened."""
        return repository.filter_books(LibraryFilter(
            days_since_opened=30,
            sort_by="recent"
        ))

    @staticmethod
    def currently_reading(repository: LibraryRepository) -> list[BookMetadata]:
        """Books with status='reading', sorted by last opened."""
        return repository.filter_books(LibraryFilter(
            status="reading",
            sort_by="recent"
        ))

    @staticmethod
    def to_read(repository: LibraryRepository) -> list[BookMetadata]:
        """Books with status='not_started', sorted by added date."""
        return repository.filter_books(LibraryFilter(
            status="not_started",
            sort_by="added_date_desc"
        ))

    @staticmethod
    def favorites(repository: LibraryRepository) -> list[BookMetadata]:
        """Books marked as favorites (future: add is_favorite column)."""
        # For now, return empty list (implement when favorites added)
        return []

# Sidebar knows about both smart and user collections
class CollectionSidebarWidget(QWidget):
    def _populate_collections(self):
        # Add smart collections (hardcoded)
        self._add_smart_collection("Recent Reads", SmartCollections.recent_reads)
        self._add_smart_collection("Favorites", SmartCollections.favorites)

        # Add separator
        self._add_separator()

        # Add user collections (from database)
        user_collections = self._repository.get_all_collections()
        for collection in user_collections:
            self._add_user_collection(collection)
```

---

### Decision 3: Database Schema for Collections

**Schema version will increment to v2 with collections support.**

#### New Tables

**collections table:**
```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    color TEXT,  -- Optional: hex color for UI (e.g., "#FF5733")
    sort_order INTEGER DEFAULT 0  -- For custom ordering in sidebar
);

CREATE INDEX idx_collections_name ON collections(name COLLATE NOCASE);
CREATE INDEX idx_collections_sort_order ON collections(sort_order);
```

**book_collections table (many-to-many junction):**
```sql
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

**Migration Strategy:**
```python
class LibraryRepository:
    CURRENT_SCHEMA_VERSION = 2  # Increment from 1

    def _run_migrations(self, from_version: int) -> None:
        """Run migrations from from_version to CURRENT_SCHEMA_VERSION."""
        if from_version < 1:
            self._create_initial_schema()  # Create books table

        if from_version < 2:
            self._migrate_v1_to_v2()  # Add collections tables

    def _migrate_v1_to_v2(self) -> None:
        """Migrate from v1 to v2: Add collections support."""
        logger.info("Migrating database from v1 to v2 (collections)")

        cursor = self._conn.cursor()

        # Create collections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                color TEXT,
                sort_order INTEGER DEFAULT 0
            )
        """)

        # Create book_collections junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_collections (
                book_id INTEGER NOT NULL,
                collection_id INTEGER NOT NULL,
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (book_id, collection_id),
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name COLLATE NOCASE)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_sort_order ON collections(sort_order)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_collections_book ON book_collections(book_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_collections_collection ON book_collections(collection_id)")

        # Update schema version
        cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (2)")

        self._conn.commit()
        logger.info("Migration to v2 complete")
```

---

### Decision 4: Collection Data Model

**New dataclass for collections:**

```python
@dataclass
class Collection:
    """User-created collection of books.

    Represents a user-defined grouping of books (e.g., "Science Fiction", "To Read").
    Smart collections (Recent Reads, Currently Reading) are NOT stored as Collection
    objects - they are computed queries defined in SmartCollections.

    Attributes:
        id: Database primary key (0 for new collections)
        name: Collection name (must be unique)
        created_date: When collection was created
        color: Optional hex color for UI display (e.g., "#FF5733")
        sort_order: Custom order for sidebar display (lower = higher in list)
        book_count: Number of books in collection (computed, not stored)
    """
    id: int
    name: str
    created_date: datetime
    color: str | None = None
    sort_order: int = 0
    book_count: int = 0  # Computed from book_collections table
```

---

### Decision 5: Sidebar Widget Architecture

**Think about how to structure the sidebar UI.**

#### Sidebar Components

The sidebar needs to display:
1. **Smart Collections** (hardcoded list, always visible)
   - Recent Reads
   - Favorites
   - Currently Reading
   - To Read

2. **User Collections** (from database, dynamic)
   - User-created collections
   - Can add/rename/delete
   - Expandable/collapsible section

3. **Actions** (bottom toolbar)
   - Settings
   - Add collection (+)

#### Widget Structure

**Option A: QListWidget (Simple List)**
- All collections in flat list
- Section headers as disabled items

**Pros:**
- Simple to implement
- Fast rendering

**Cons:**
- ❌ No hierarchy (can't collapse sections)
- ❌ Harder to style section headers
- ❌ Limited to list paradigm

---

**Option B: QTreeWidget (Hierarchical Tree)**
- Top-level items: Section headers ("Smart Collections", "My Collections")
- Child items: Individual collections
- Can expand/collapse sections

**Pros:**
- ✅ **Hierarchical**: Matches mockup structure
- ✅ **Collapsible sections**: Users can hide user collections if desired
- ✅ **Standard pattern**: Finder sidebar uses tree
- ✅ **Visual hierarchy**: Clear separation between sections

**Cons:**
- Slightly more complex than flat list

---

**Option C: Custom Widget with Sections**
- Manually layout sections with headers
- Each section has its own list

**Pros:**
- Full control over styling

**Cons:**
- ❌ Reinventing the wheel
- ❌ More code to maintain
- ❌ Harder to make keyboard navigable

---

**Decision: Option B - QTreeWidget**

**Rationale:**
1. **Matches Mockup**: Hierarchical structure with sections
2. **Collapsible**: Users can hide sections they don't use
3. **PyQt6 Standard**: Well-tested widget with keyboard support
4. **Scalable**: Can add more sections later (e.g., "Authors", "Tags")

**Implementation:**

```python
class CollectionSidebarWidget(QWidget):
    """Sidebar widget for collection navigation.

    Displays two sections:
    1. Smart Collections (Recent Reads, Favorites, etc.) - always visible
    2. My Collections (user-created) - from database

    Signals:
        collection_selected: Emitted when user selects a collection.
            Args: collection_type (str), collection_id (int | None)
                  - For smart collections: ("smart", None) with collection_type as name
                  - For user collections: ("user", collection_id)
        all_books_selected: Emitted when "All Books" selected.
    """

    # Signals
    collection_selected = pyqtSignal(str, object)  # (type, id_or_name)
    all_books_selected = pyqtSignal()

    def __init__(self, repository: LibraryRepository, parent=None):
        super().__init__(parent)
        self._repository = repository

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("Library")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 20px;")
        layout.addWidget(header)

        # Collection tree
        self._tree = QTreeWidget(self)
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(20)
        self._tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._tree)

        # Actions toolbar (bottom)
        toolbar = QHBoxLayout()
        self._add_collection_btn = QPushButton("+")
        self._add_collection_btn.setToolTip("Create new collection")
        self._add_collection_btn.clicked.connect(self._on_add_collection)
        toolbar.addWidget(self._add_collection_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Populate tree
        self._populate_tree()

    def _populate_tree(self):
        """Build the collection tree structure."""
        self._tree.clear()

        # === SMART COLLECTIONS SECTION ===
        smart_section = QTreeWidgetItem(self._tree)
        smart_section.setText(0, "Library")
        smart_section.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not selectable

        # All Books (default view)
        all_item = QTreeWidgetItem(smart_section)
        all_item.setText(0, "📚 All Books")
        all_item.setData(0, Qt.ItemDataRole.UserRole, ("all", None))

        # Recent Reads
        recent_item = QTreeWidgetItem(smart_section)
        recent_item.setText(0, "📖 Recent Reads")
        recent_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "recent_reads"))

        # Favorites
        favorites_item = QTreeWidgetItem(smart_section)
        favorites_item.setText(0, "⭐ Favorites")
        favorites_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "favorites"))

        # Currently Reading
        reading_item = QTreeWidgetItem(smart_section)
        reading_item.setText(0, "📗 Currently Reading")
        reading_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "currently_reading"))

        # To Read
        to_read_item = QTreeWidgetItem(smart_section)
        to_read_item.setText(0, "📙 To Read")
        to_read_item.setData(0, Qt.ItemDataRole.UserRole, ("smart", "to_read"))

        smart_section.setExpanded(True)

        # === USER COLLECTIONS SECTION ===
        user_section = QTreeWidgetItem(self._tree)
        user_section.setText(0, "My Collections")
        user_section.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not selectable

        # Load user collections from database
        collections = self._repository.get_all_collections()
        for collection in collections:
            coll_item = QTreeWidgetItem(user_section)
            coll_item.setText(0, f"📁 {collection.name} ({collection.book_count})")
            coll_item.setData(0, Qt.ItemDataRole.UserRole, ("user", collection.id))

        user_section.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle collection item click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return  # Clicked on section header

        collection_type, collection_id = data

        if collection_type == "all":
            self.all_books_selected.emit()
        elif collection_type == "smart":
            self.collection_selected.emit("smart", collection_id)
        elif collection_type == "user":
            self.collection_selected.emit("user", collection_id)
```

---

### Decision 6: Filter and Sort Implementation

**Extend LibraryFilter to support new filtering criteria.**

#### Enhanced LibraryFilter

```python
@dataclass
class LibraryFilter:
    """Filter and sort criteria for library views.

    Attributes:
        search_query: Text to search in title/author (empty = no search)
        collection_id: User collection to filter by (None = all books)
        status: Reading status filter (None = all statuses)
        author: Filter by specific author (None = all authors)
        sort_by: Sort order (recent, title, author, progress, added_date_desc)
        days_since_opened: Only books opened in last N days (None = all)
    """
    search_query: str = ""
    collection_id: int | None = None  # User collection ID
    status: str | None = None  # "not_started" | "reading" | "finished"
    author: str | None = None
    sort_by: str = "recent"  # recent | title | author | progress | added_date_desc
    days_since_opened: int | None = None  # For "Recent Reads" smart collection
```

#### Repository Methods

```python
class LibraryRepository:
    # ... existing methods ...

    def filter_books(self, filter: LibraryFilter) -> list[BookMetadata]:
        """Filter and sort books based on criteria.

        Args:
            filter: Filter criteria.

        Returns:
            List of books matching filter, sorted by filter.sort_by.
        """
        query = "SELECT * FROM books WHERE 1=1"
        params = []

        # Collection filter
        if filter.collection_id:
            query += """
                AND id IN (
                    SELECT book_id FROM book_collections
                    WHERE collection_id = ?
                )
            """
            params.append(filter.collection_id)

        # Status filter
        if filter.status:
            query += " AND status = ?"
            params.append(filter.status)

        # Search query (title or author)
        if filter.search_query:
            query += " AND (title LIKE ? OR author LIKE ?)"
            search_pattern = f"%{filter.search_query}%"
            params.extend([search_pattern, search_pattern])

        # Author filter
        if filter.author:
            query += " AND author = ?"
            params.append(filter.author)

        # Days since opened (for Recent Reads)
        if filter.days_since_opened:
            query += " AND last_opened_date >= datetime('now', '-{} days')".format(
                filter.days_since_opened
            )

        # Sort
        if filter.sort_by == "recent":
            query += " ORDER BY last_opened_date DESC NULLS LAST, added_date DESC"
        elif filter.sort_by == "title":
            query += " ORDER BY title COLLATE NOCASE"
        elif filter.sort_by == "author":
            query += " ORDER BY author COLLATE NOCASE, title COLLATE NOCASE"
        elif filter.sort_by == "progress":
            query += " ORDER BY reading_progress DESC"
        elif filter.sort_by == "added_date_desc":
            query += " ORDER BY added_date DESC"

        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return [self._row_to_metadata(row) for row in cursor.fetchall()]

    # === Collection CRUD ===

    def create_collection(self, name: str, color: str | None = None) -> int:
        """Create a new user collection.

        Args:
            name: Collection name (must be unique).
            color: Optional hex color (e.g., "#FF5733").

        Returns:
            Database ID of the new collection.

        Raises:
            DatabaseError: If collection name already exists.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO collections (name, color) VALUES (?, ?)",
                (name, color)
            )
            self._conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DatabaseError(f"Collection '{name}' already exists") from e

    def get_all_collections(self) -> list[Collection]:
        """Get all user collections with book counts.

        Returns:
            List of collections, sorted by sort_order.
        """
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT
                c.id, c.name, c.created_date, c.color, c.sort_order,
                COUNT(bc.book_id) as book_count
            FROM collections c
            LEFT JOIN book_collections bc ON c.id = bc.collection_id
            GROUP BY c.id
            ORDER BY c.sort_order, c.name COLLATE NOCASE
        """)

        collections = []
        for row in cursor.fetchall():
            collections.append(Collection(
                id=row["id"],
                name=row["name"],
                created_date=datetime.fromisoformat(row["created_date"]),
                color=row["color"],
                sort_order=row["sort_order"],
                book_count=row["book_count"]
            ))
        return collections

    def add_book_to_collection(self, book_id: int, collection_id: int) -> None:
        """Add a book to a collection.

        Args:
            book_id: Book database ID.
            collection_id: Collection database ID.

        Raises:
            DatabaseError: If book or collection doesn't exist, or already linked.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO book_collections (book_id, collection_id) VALUES (?, ?)",
                (book_id, collection_id)
            )
            self._conn.commit()
        except sqlite3.IntegrityError as e:
            raise DatabaseError(f"Book already in collection or invalid IDs") from e

    def remove_book_from_collection(self, book_id: int, collection_id: int) -> None:
        """Remove a book from a collection.

        Args:
            book_id: Book database ID.
            collection_id: Collection database ID.
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM book_collections WHERE book_id = ? AND collection_id = ?",
            (book_id, collection_id)
        )
        self._conn.commit()

    def delete_collection(self, collection_id: int) -> None:
        """Delete a user collection.

        Book-collection links are automatically deleted (ON DELETE CASCADE).

        Args:
            collection_id: Collection database ID.
        """
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        self._conn.commit()
```

---

### Decision 7: Real-Time Search Implementation

**Search should filter the grid as user types.**

#### Search Widget Integration

```python
class LibraryView(QWidget):
    """Enhanced library view with sidebar, search, and grid."""

    def __init__(self, repository: LibraryRepository, parent=None):
        super().__init__(parent)
        self._repository = repository

        # Create main splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # LEFT: Sidebar
        self._sidebar = CollectionSidebarWidget(repository, self)
        self._sidebar.collection_selected.connect(self._on_collection_selected)
        self._sidebar.all_books_selected.connect(self._on_all_books_selected)
        self._splitter.addWidget(self._sidebar)

        # RIGHT: Main panel (header + grid)
        main_panel = QWidget(self)
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header (search + actions)
        header = QHBoxLayout()

        # Search box
        self._search_box = QLineEdit(self)
        self._search_box.setPlaceholderText("Search books...")
        self._search_box.textChanged.connect(self._on_search_changed)
        self._search_box.setClearButtonEnabled(True)
        header.addWidget(self._search_box, stretch=1)

        # Sort dropdown
        self._sort_combo = QComboBox(self)
        self._sort_combo.addItems([
            "Recent",
            "Title A-Z",
            "Author A-Z",
            "Progress"
        ])
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        header.addWidget(self._sort_combo)

        main_layout.addLayout(header)

        # Book grid (existing Phase 1 widget)
        self._grid = BookGridWidget(self)
        self._grid.book_activated.connect(self._on_book_activated)
        main_layout.addWidget(self._grid)

        # Status label
        self._status_label = QLabel("", self)
        self._status_label.setStyleSheet("color: gray; font-size: 12px;")
        main_layout.addWidget(self._status_label)

        self._splitter.addWidget(main_panel)
        self._splitter.setSizes([250, 750])

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._splitter)

        # State
        self._current_filter = LibraryFilter()
        self._all_books = []

    def _on_search_changed(self, text: str):
        """Handle search box text change (real-time filtering)."""
        self._current_filter.search_query = text
        self._refresh_grid()

    def _on_sort_changed(self, index: int):
        """Handle sort selection change."""
        sort_map = {
            0: "recent",
            1: "title",
            2: "author",
            3: "progress"
        }
        self._current_filter.sort_by = sort_map[index]
        self._refresh_grid()

    def _on_collection_selected(self, collection_type: str, collection_id):
        """Handle collection selection from sidebar."""
        # Update filter based on collection type
        if collection_type == "smart":
            # Map smart collection name to filter
            if collection_id == "recent_reads":
                self._current_filter = LibraryFilter(
                    days_since_opened=30,
                    sort_by="recent"
                )
            elif collection_id == "currently_reading":
                self._current_filter = LibraryFilter(
                    status="reading",
                    sort_by="recent"
                )
            elif collection_id == "to_read":
                self._current_filter = LibraryFilter(
                    status="not_started",
                    sort_by="added_date_desc"
                )
            elif collection_id == "favorites":
                # TODO: Implement favorites when column added
                self._current_filter = LibraryFilter()

        elif collection_type == "user":
            # User collection filter
            self._current_filter = LibraryFilter(
                collection_id=collection_id,
                sort_by="recent"
            )

        self._refresh_grid()

    def _on_all_books_selected(self):
        """Handle "All Books" selection."""
        self._current_filter = LibraryFilter(sort_by="recent")
        self._refresh_grid()

    def _refresh_grid(self):
        """Refresh grid with current filter."""
        # Query books with filter
        books = self._repository.filter_books(self._current_filter)

        # Update grid
        self._grid.set_books(books)

        # Update status label
        total_books = len(self._repository.get_all_books())
        if len(books) == total_books:
            self._status_label.setText(f"{total_books} books")
        else:
            self._status_label.setText(f"Showing {len(books)} of {total_books} books")
```

---

### Decision 8: Controller Integration

**LibraryController needs minimal changes for Phase 2.**

The controller already handles import and loading. For Phase 2, add:

```python
class LibraryController(QObject):
    # Existing signals
    library_loaded = pyqtSignal(list)
    # ... other existing signals ...

    # New signals for Phase 2
    collection_created = pyqtSignal(int, str)  # (collection_id, name)
    collection_deleted = pyqtSignal(int)  # collection_id
    book_added_to_collection = pyqtSignal(int, int)  # (book_id, collection_id)

    def __init__(self, repository: LibraryRepository):
        super().__init__()
        self._repository = repository

    # === New Collection Methods ===

    def create_collection(self, name: str) -> None:
        """Create a new user collection.

        Args:
            name: Collection name.

        Emits:
            collection_created: (collection_id, name) on success
            error_occurred: (title, message) on failure
        """
        try:
            collection_id = self._repository.create_collection(name)
            self.collection_created.emit(collection_id, name)
            logger.info("Created collection '%s' with ID %d", name, collection_id)
        except DatabaseError as e:
            self.error_occurred.emit("Cannot Create Collection", str(e))
            logger.error("Failed to create collection: %s", e)

    def add_book_to_collection(self, book_id: int, collection_id: int) -> None:
        """Add a book to a collection."""
        try:
            self._repository.add_book_to_collection(book_id, collection_id)
            self.book_added_to_collection.emit(book_id, collection_id)
        except DatabaseError as e:
            self.error_occurred.emit("Cannot Add to Collection", str(e))
```

---

## Component Interface Summary

### New Data Models

**Collection (dataclass)**
```python
@dataclass
class Collection:
    id: int
    name: str
    created_date: datetime
    color: str | None = None
    sort_order: int = 0
    book_count: int = 0  # Computed
```

**Enhanced LibraryFilter**
```python
@dataclass
class LibraryFilter:
    search_query: str = ""
    collection_id: int | None = None
    status: str | None = None
    author: str | None = None
    sort_by: str = "recent"
    days_since_opened: int | None = None  # NEW for Recent Reads
```

### New Views

**CollectionSidebarWidget**
```python
class CollectionSidebarWidget(QWidget):
    collection_selected = pyqtSignal(str, object)  # (type, id_or_name)
    all_books_selected = pyqtSignal()

    def __init__(self, repository: LibraryRepository, parent=None): ...
    def refresh_collections(self) -> None: ...  # Reload from database
```

### Modified Components

**LibraryView (Phase 1 → Phase 2)**
- **Before**: Simple widget with grid or empty state
- **After**: QSplitter with sidebar + main panel
- **New features**: Search box, sort dropdown, status label
- **Signals**: Same (book_open_requested, import_requested)

**LibraryRepository**
- **New methods**:
  - `create_collection()`, `get_all_collections()`, `delete_collection()`
  - `add_book_to_collection()`, `remove_book_from_collection()`
  - Enhanced `filter_books()` with new criteria
- **Schema**: Migrated to v2 (adds collections, book_collections tables)

---

## Integration Plan

### Step 1: Database Migration
1. Increment `CURRENT_SCHEMA_VERSION` to 2
2. Implement `_migrate_v1_to_v2()` method
3. Test migration with existing Phase 1 databases
4. Verify backward compatibility (fresh install vs migration)

### Step 2: Data Models
1. Create `Collection` dataclass in `src/ereader/models/collection.py`
2. Enhance `LibraryFilter` with new fields
3. Update repository methods for collections

### Step 3: Repository Methods
1. Implement collection CRUD methods
2. Enhance `filter_books()` for new criteria
3. Write unit tests for all new methods

### Step 4: Smart Collections
1. Create `SmartCollections` helper class
2. Define queries for each smart collection
3. Test with sample data

### Step 5: Sidebar Widget
1. Create `CollectionSidebarWidget` using QTreeWidget
2. Implement tree population logic
3. Wire up signals for selection
4. Test keyboard navigation

### Step 6: LibraryView Refactor
1. Replace single-widget layout with QSplitter
2. Add search box and sort dropdown
3. Connect sidebar signals to grid refresh
4. Test splitter state persistence

### Step 7: Controller Updates
1. Add collection management methods to `LibraryController`
2. Emit appropriate signals
3. Update error handling

### Step 8: Integration Testing
1. Test end-to-end: Create collection → Add books → Filter → Search
2. Test smart collections (Recent Reads, Currently Reading, etc.)
3. Test migration from Phase 1 database
4. Performance test with 100+ books

---

## Performance Considerations

### Database Query Performance
- **Filter with collection**: Uses indexed book_collections lookup (< 10ms)
- **Search**: LIKE queries on indexed title/author columns (< 20ms)
- **Collection counts**: Computed via JOIN in single query (< 5ms)
- **Total filter + sort**: < 50ms for 100 books ✅ (target: < 100ms)

### UI Responsiveness
- **Sidebar refresh**: Only when collections change, not on every book filter
- **Grid refresh**: Reuses existing BookGridWidget (virtualized, fast)
- **Search debouncing**: Not needed initially (< 50ms is imperceptible)

### Memory Usage
- **Collection objects**: ~200 bytes each × 20 collections = 4KB (negligible)
- **Sidebar tree items**: ~500 bytes each × 30 items = 15KB (negligible)
- **Total overhead**: < 50KB ✅

---

## Migration from Phase 1

### Existing Users
1. On first launch with Phase 2 code:
   - Database auto-migrates from v1 to v2
   - Books preserved with all metadata
   - No user collections initially
   - Library view starts in "All Books" (default)

2. User can immediately:
   - Use smart collections (Recent Reads, etc.)
   - Create first user collection
   - Search and sort books

### Backward Compatibility
- **Phase 1 code on Phase 2 database**: ❌ Won't work (unknown tables)
- **Phase 2 code on Phase 1 database**: ✅ Works (auto-migrates)
- **Solution**: Version Phase 2 as major release (no downgrade support)

---

## UI/UX Considerations

### Keyboard Shortcuts (Phase 2)
- **Ctrl+F**: Focus search box
- **Escape**: Clear search
- **Ctrl+N**: New collection (when sidebar focused)
- **Delete**: Remove book from collection (Phase 3)
- **Up/Down**: Navigate sidebar collections

### Visual Hierarchy
- **Sidebar**: Muted background, smaller font
- **Main panel**: White background, prominent
- **Search box**: Large, obvious
- **Grid**: Existing Phase 1 styling

### Empty States
- **No books in collection**: "No books in this collection. Add books by right-clicking a book in All Books." (Phase 3)
- **No search results**: "No books match '{query}'. Try different keywords."
- **No collections**: User section shows "(no collections yet)" hint

---

## Testing Strategy

### Unit Tests

**LibraryRepository (Collections):**
- `test_create_collection()` - Create, verify in database
- `test_create_duplicate_collection()` - Should raise DatabaseError
- `test_get_all_collections()` - Verify sorting and book counts
- `test_add_book_to_collection()` - Many-to-many link creation
- `test_remove_book_from_collection()` - Link deletion
- `test_delete_collection()` - Cascade deletes book links
- `test_filter_by_collection()` - Filter books by collection ID
- `test_smart_collection_queries()` - Recent Reads, Currently Reading, etc.

**CollectionSidebarWidget:**
- `test_populate_smart_collections()` - Verify hardcoded items
- `test_populate_user_collections()` - Load from database
- `test_collection_selection()` - Emit correct signals
- `test_add_collection_action()` - Dialog and creation flow

**LibraryView (Phase 2):**
- `test_search_filtering()` - Real-time search updates grid
- `test_sort_changes()` - Sort dropdown updates grid
- `test_collection_selection()` - Sidebar selection filters grid
- `test_splitter_state()` - State saved/restored

### Integration Tests

**End-to-End Collection Workflow:**
1. Create collection "Science Fiction"
2. Add 3 books to collection
3. Select collection in sidebar
4. Verify grid shows only those 3 books
5. Search within collection
6. Remove book from collection
7. Delete collection

**Smart Collections:**
1. Open 3 books (sets last_opened_date)
2. Select "Recent Reads"
3. Verify those 3 books shown
4. Mark 1 book as "reading"
5. Select "Currently Reading"
6. Verify 1 book shown

**Migration:**
1. Create Phase 1 database with 10 books
2. Launch with Phase 2 code
3. Verify migration to v2
4. Verify books preserved
5. Create collection
6. Verify collection persists after restart

### UI Tests (pytest-qt)

**Sidebar Interaction:**
- Click smart collection → Verify signal emitted
- Click user collection → Verify signal emitted
- Add collection button → Verify dialog opens

**Search:**
- Type in search box → Verify grid updates
- Clear search → Verify grid shows all books

**Sort:**
- Change sort dropdown → Verify grid reorders

---

## Consequences

### What This Enables ✅

1. **Organized Library**: Users can group books into collections
2. **Smart Filtering**: Built-in smart collections (Recent Reads, etc.)
3. **Quick Access**: Sidebar navigation faster than search for collections
4. **Search + Filter**: Combine search with collection filtering
5. **Foundation for Phase 3**: Favorites, Continue Reading section, etc.

### What This Constrains 📍

1. **Fixed Smart Collections**: Adding new smart collections requires code change
2. **No Nested Collections**: Collections are flat (no hierarchies)
3. **No Book Duplication**: Books can be in multiple collections, but editing metadata affects all instances

### What to Watch Out For ⚠️

1. **Migration Safety**: Test v1→v2 migration thoroughly
2. **Collection Names**: Enforce unique names to avoid user confusion
3. **Search Performance**: Monitor with 500+ books (may need FTS5)
4. **Sidebar Width**: Save/restore splitter state properly
5. **Empty Collections**: Handle empty collection state gracefully

---

## Future Enhancements (Phase 3 and Beyond)

### Phase 3 Candidates
- **Favorites**: Add `is_favorite` column to books, add to Favorites smart collection
- **Continue Reading**: Horizontal widget at top showing recent books with progress
- **Context Menus**: Right-click on book → Add to Collection
- **Collection Colors**: Use `color` column for visual coding
- **Drag and Drop**: Drag books to collections in sidebar

### Long-Term Possibilities
- **Nested Collections**: Collections within collections
- **Smart Collection Editor**: User-defined smart collections with custom rules
- **Collection Sharing**: Export/import collection definitions
- **Advanced Search**: Filter by date added, file size, page count
- **Auto-Collections**: Automatically group by author, genre, etc.

---

## References

- **UI Mockup**: `docs/ux/ui-references/mockup1.png`
- **Feature Spec**: `docs/specs/library-management-system.md`
- **Phase 1 Architecture**: `docs/architecture/library-management-architecture.md`
- **Project Guidelines**: `CLAUDE.md`
- **Qt Model/View**: https://doc.qt.io/qt-6/model-view-programming.html
- **SQLite Foreign Keys**: https://www.sqlite.org/foreignkeys.html

---

## Implementation Guidance

### Development Order

1. **Database Layer** (1-2 hours)
   - Implement migration v1→v2
   - Add collection CRUD methods to repository
   - Write unit tests for new methods

2. **Data Models** (30 mins)
   - Create `Collection` dataclass
   - Enhance `LibraryFilter`
   - Create `SmartCollections` helper

3. **Sidebar Widget** (2-3 hours)
   - Create `CollectionSidebarWidget` with QTreeWidget
   - Implement tree population
   - Wire up signals
   - Test keyboard navigation

4. **LibraryView Refactor** (2-3 hours)
   - Replace layout with QSplitter
   - Add search box and sort dropdown
   - Connect sidebar to grid filtering
   - Test splitter persistence

5. **Controller Updates** (1 hour)
   - Add collection methods
   - Wire up signals
   - Test error handling

6. **Integration & Testing** (2-3 hours)
   - End-to-end collection workflow test
   - Smart collection tests
   - Migration test with Phase 1 database
   - Performance test with 100+ books

**Total Estimated Time**: 8-12 hours of focused development

### Testing Workflow

```bash
# Run tests frequently
uv run pytest tests/test_models/test_library_database.py -v

# Test migration specifically
uv run pytest tests/test_models/test_library_database.py::test_migration_v1_to_v2 -v

# Test sidebar widget
uv run pytest tests/test_views/test_collection_sidebar.py -v

# Run all library tests
uv run pytest tests/ -k library -v
```

### Manual Testing Checklist

- [ ] Create Phase 1 database, verify migration to v2
- [ ] Create collection "Science Fiction"
- [ ] Add 3 books to collection
- [ ] Select collection in sidebar, verify filtered grid
- [ ] Search within collection
- [ ] Test "Recent Reads" smart collection
- [ ] Test "Currently Reading" smart collection
- [ ] Test "To Read" smart collection
- [ ] Delete collection, verify books remain
- [ ] Resize sidebar, quit, restart, verify width saved
- [ ] Test with 100+ books, verify < 100ms search

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-14 | Initial Phase 2 architecture | Design collections, sidebar, filter/sort/search |

---

**Status**: ✅ **Ready for Implementation**

This architecture is approved and ready for development. Proceed with `/developer` to implement Phase 2.
