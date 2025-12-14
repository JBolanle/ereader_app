# Library Management System - Specification

**Status:** Approved Design (Awaiting Implementation)
**Priority:** HIGH - Top Post-MVP Feature
**Created:** 2025-12-13
**UX Design:** Approved 2025-12-13

---

## Overview

Transform the e-reader from a single-book viewer into a personal reading library with collection management, search, and organization features. This is the #1 priority post-MVP enhancement.

**User Problem:** Currently, users must navigate the filesystem and use File → Open for every book. There's no way to build a reading collection, see reading history, or organize books.

**Solution:** Add a library management system with grid/list views, collections, search, reading status tracking, and automatic position persistence.

---

## User Goals

**Primary:**
- Build and manage a personal reading collection
- Quick access to any book without filesystem browsing
- See reading progress across all books at a glance

**Secondary:**
- Organize books by collections, author, genre, reading status
- Find specific books via search/filter
- Import new books easily
- Resume reading from where they left off

---

## Design Decisions

### 1. Grid-First Approach ✅
- **Decision:** Start with grid view (like Kindle/Kobo), add list view in Phase 3
- **Rationale:** Grid view with covers is more engaging for visual browsing, matches user expectations from other e-readers
- **Fallback:** List view for users who prefer compact information-dense layout

### 2. Collections (Not Tags) ✅
- **Decision:** Simple collections system where one book can belong to multiple collections
- **Rationale:** Simpler mental model than tags, sufficient for most users, matches Kindle's approach
- **Examples:** "Science Fiction", "Technical", "To Read", "Favorites"

### 3. Cover Extraction ✅
- **Phase 1:** Use placeholder icons (book emoji or colored rectangles)
- **Phase 2:** Extract cover images from EPUB metadata
- **Rationale:** Phase 1 focus on functionality, Phase 2 adds polish

### 4. Phased Implementation ✅
Breaking into 3 phases to ship value incrementally:
- **Phase 1:** Basic library (import, grid, open, persistence)
- **Phase 2:** Organization (collections, filters, sort, search, status)
- **Phase 3:** Polish (Continue Reading, covers, list view, context menus, details)

---

## User Flows

### Flow 1: First-Time User (Empty Library)

1. User launches app
2. System shows **empty library state** with "Import Books" prompt
3. User clicks **"Import Books"** button or uses menu **File → Import**
4. System opens file dialog (multi-select enabled for EPUB files)
5. User selects one or more EPUB files
6. System imports books with **progress indicator** (shows count, current file)
7. System shows **library grid** with newly imported books
8. User **double-clicks** a book to start reading
9. System switches to reading view, opens book at beginning

**Success:** User has books in library and is reading

### Flow 2: Returning User (Existing Library)

1. User launches app
2. System shows **library grid** with all books (default: sorted by recent)
3. User sees **"Continue Reading"** section at top (3-5 recently opened books)
4. User clicks a book from "Continue Reading" or browses main library grid
5. System opens book at **last read position** (chapter + scroll position)

**Success:** User resumes reading immediately with minimal friction

### Flow 3: Organizing Books into Collections

1. User has library open with multiple books
2. User clicks **menu View → Manage Collections** (or dedicated button in Phase 3)
3. System shows **collection manager** (sidebar or dialog)
4. User creates new collection by clicking **"+ New Collection"**
5. User enters collection name (e.g., "Science Fiction")
6. User selects books and right-clicks → **"Add to Collection"** → selects collection
7. System updates book's collection membership in database
8. User can now **filter by collection** using Filter dropdown

**Success:** Books are organized, library is filterable by collection

### Flow 4: Finding a Book (Search)

1. User has library with many books (10+)
2. User clicks **search box** at top (or presses Ctrl+F)
3. User types query (e.g., "Martian")
4. System **filters library in real-time** as user types
5. User sees matching books (searched by title, author)
6. User clicks book to open or presses **Escape** to clear search

**Success:** User found book quickly without scrolling

### Flow 5: Importing Additional Books

1. User has existing library
2. User clicks **File → Import** (or Import button)
3. System opens file dialog
4. User selects 5 EPUB files
5. System shows **progress toast**: "Importing books... 3 of 5"
6. System encounters 1 corrupted file
7. System imports 4 valid files, shows **error toast** for the failed one:
   - "⚠️ Failed to import 1 file"
   - "corrupted.epub - Not a valid EPUB"
   - [View Details] button
8. Library grid updates to show 4 new books
9. Status bar shows: "17 books • Last import: just now"

**Success:** User added books to library, aware of any failures

---

## Interface Design

### Main Window Layout

```
┌─────────────────────────────────────────────────────┐
│ E-Reader                                   [- □ ×]  │
├─────────────────────────────────────────────────────┤
│ File   View   Help                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📚 My Library                    [🔍 Search...]    │
│                                                     │
│  ┌─ Continue Reading ────────────────────────────┐ │
│  │ [Book 1]  [Book 2]  [Book 3]                  │ │
│  │ 45%       12%       87%                        │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  ┌─ All Books (12) ─────────────────────────────┐  │
│  │ [Filter ▼] [Sort: Recent ▼] [Grid/List]      │  │
│  ├────────────────────────────────────────────────┤ │
│  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐             │  │
│  │ │ 📕  │ │ 📗  │ │ 📘  │ │ 📙  │  ...        │  │
│  │ │Book │ │Book │ │Book │ │Book │             │  │
│  │ │Title│ │Title│ │Title│ │Title│             │  │
│  │ │Auth │ │Auth │ │Auth │ │Auth │             │  │
│  │ │[===]│ │[= ]│ │[===]│ │[   ]│             │  │
│  │ │ 75% │ │ 15% │ │100% │ │ 0% │             │  │
│  │ └─────┘ └─────┘ └─────┘ └─────┘             │  │
│  │                                               │  │
│  │ (Grid continues with more books...)          │  │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│ 12 books • Last import: 2 hours ago                │
└─────────────────────────────────────────────────────┘
```

### UI Components

#### 1. Library Header
- **📚 My Library** title (left)
- **Search box** (right): Real-time filtering
  - Placeholder: "Search books..."
  - Icon: Magnifying glass
  - Shortcut: Ctrl+F focuses search

#### 2. Continue Reading Section (Phase 3)
- **Horizontal scroll** of 3-5 recently opened books
- **Each card shows:**
  - Cover thumbnail (smaller than main grid)
  - Book title (truncated)
  - Progress percentage
- **Interaction:** Click to open book at last position
- **Show when:** User has opened at least 1 book

#### 3. Filter & Sort Bar
- **Filter dropdown:**
  - All Books (default)
  - By Collection (Fiction, Technical, To Read, etc.)
  - By Status (Reading, Finished, Not Started)
  - By Author (Phase 3)
- **Sort dropdown:**
  - Recent (last opened first)
  - Title A-Z
  - Author A-Z
  - Progress % (Phase 3)
- **View toggle:** Grid (default) / List (Phase 3)

#### 4. Book Grid View
- **Card dimensions:** 180px wide × 260px tall
- **Card contents:**
  - Cover area: 150px × 200px (placeholder icon or extracted cover)
  - Title: Max 2 lines, truncated with ellipsis
  - Author: 1 line, truncated
  - Progress bar: Visual indicator (0-100%)
  - Progress text: "75%"
- **Grid spacing:** 20px between cards
- **Responsive:** Auto-adjusts columns based on window width
  - Window 900px: 4 columns
  - Window 1100px: 5 columns
  - Window 1300px: 6 columns
- **Interactions:**
  - **Hover:** Card elevates (subtle shadow), tooltip shows full title/author
  - **Click:** Selects card (highlight border)
  - **Double-click:** Opens book for reading
  - **Right-click:** Context menu (Phase 3)

#### 5. Book List View (Phase 3)
- **Row layout:**
  - Thumbnail (50×70px) | Title | Author | Progress bar | Progress % | Last opened
- **Sortable columns:** Click header to sort
- **More compact:** Shows 2-3× more books than grid view

#### 6. Status Bar
- **Left side:** Book count, last import timestamp
  - Example: "12 books • Last import: 2 hours ago"
- **Right side:** Active filter info (if any)
  - Example: "Filtered by: Science Fiction (4 books)"

#### 7. Context Menu (Right-click, Phase 3)
- Open
- Open in New Window (future)
- Book Details
- Add to Collection
- Mark as Finished / Reading / Not Started
- Remove from Library
- Delete File (with confirmation)

---

## States to Design

### Empty State (No Books)
```
┌─────────────────────────────────────────┐
│                                         │
│         📚 Your Library is Empty        │
│                                         │
│     Import EPUB files to get started   │
│                                         │
│      [Import Books] (Ctrl+I)           │
│                                         │
│         or drag files here              │
│                                         │
└─────────────────────────────────────────┘
```
- **Goal:** Make it obvious how to add books
- **Primary action:** Large "Import Books" button
- **Secondary action:** Drag-and-drop hint (Phase 2+)

### Loading State (During Import)
- **Toast notification** (non-blocking):
  ```
  📥 Importing books... 3 of 5
  Processing: "The Martian.epub"
  [Cancel]
  ```
- **Cancelable:** User can abort import
- **Progress:** Shows current file and count
- **Duration:** Remains visible until complete or canceled

### Error State (Import Failures)
- **Toast notification** (dismissible):
  ```
  ⚠️ Failed to import 2 files
  • corrupted.epub - Not a valid EPUB
  • missing.epub - File not found
  [View Details] [Dismiss]
  ```
- **Partial success:** Valid files are imported, invalid ones reported
- **Details:** Expandable error log (Phase 3)
- **Recovery:** User can retry importing failed files

### Success State (Books Imported)
- **Toast notification** (auto-dismiss after 3s):
  ```
  ✅ Imported 5 books successfully
  ```
- **Visual feedback:** New books appear in grid with subtle highlight
- **Status bar:** Updates book count

### Reading State (Book Opened)
- **Transition:** Smooth switch from library view to reader view
- **Library state preserved:** Filters, sort order, scroll position
- **Return path:**
  - Menu: Library → View Library (Ctrl+L)
  - Or: Back button in navigation bar (Phase 3)

---

## Data Model

### Database Schema (SQLite)

#### Table: `books`
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    file_path TEXT UNIQUE NOT NULL,  -- Absolute path to EPUB
    cover_path TEXT,                  -- Path to extracted cover (NULL for placeholder)
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_opened_date DATETIME,
    reading_progress REAL DEFAULT 0.0,  -- 0.0 to 100.0
    current_chapter_index INTEGER DEFAULT 0,
    scroll_position INTEGER DEFAULT 0,  -- Pixel position in chapter
    status TEXT DEFAULT 'not_started', -- not_started, reading, finished
    file_size INTEGER,                 -- For display/stats
    page_count INTEGER                 -- Estimated (Phase 3)
);

CREATE INDEX idx_last_opened ON books(last_opened_date DESC);
CREATE INDEX idx_title ON books(title);
CREATE INDEX idx_author ON books(author);
CREATE INDEX idx_status ON books(status);
```

#### Table: `collections` (Phase 2)
```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0  -- For custom ordering
);
```

#### Table: `book_collections` (Phase 2, many-to-many)
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

### Python Data Models

#### `BookMetadata` (dataclass)
```python
@dataclass
class BookMetadata:
    """Lightweight book metadata for library display."""
    id: int
    title: str
    author: str | None
    file_path: str
    cover_path: str | None
    added_date: datetime
    last_opened_date: datetime | None
    reading_progress: float  # 0.0 to 100.0
    current_chapter_index: int
    scroll_position: int
    status: str  # "not_started" | "reading" | "finished"
    file_size: int | None
```

#### `LibraryFilter` (dataclass)
```python
@dataclass
class LibraryFilter:
    """Active filter and sort state for library view."""
    search_query: str = ""
    collection_id: int | None = None  # None = All Books
    status: str | None = None         # None = All statuses
    author: str | None = None         # None = All authors
    sort_by: str = "recent"           # recent, title, author, progress
    view_mode: str = "grid"           # grid or list
```

---

## Architecture Components

### New Classes to Create

#### Models (src/ereader/models/)
- `library_database.py` - SQLite database operations (CRUD for books, collections)
- `book_metadata.py` - BookMetadata dataclass
- `library_filter.py` - LibraryFilter dataclass

#### Controllers (src/ereader/controllers/)
- `library_controller.py` - Library state management, import, filtering, persistence

#### Views (src/ereader/views/)
- `library_view.py` - Main library container widget
- `book_card_widget.py` - Single book card for grid view
- `book_grid_widget.py` - Grid of book cards (QListView with custom delegate)
- `continue_reading_widget.py` - Horizontal scroll of recent books (Phase 3)
- `empty_library_widget.py` - Empty state display

#### Utilities (src/ereader/utils/)
- `cover_extractor.py` - Extract cover images from EPUB metadata (Phase 2)
- `import_worker.py` - Background import with progress (Phase 2)

### Modified Classes

#### `main_window.py`
- Add `QStackedWidget` to switch between Library and Reader views
- Add menu items: File → Import, Library → View Library
- Add keyboard shortcuts: Ctrl+I (Import), Ctrl+L (Library)
- Handle view switching

#### `reader_controller.py`
- Save reading position to database (not just QSettings)
- Emit signals when position changes for library to update

---

## PyQt6 Widget Hierarchy

```
QMainWindow (MainWindow)
├── QMenuBar
│   ├── File
│   │   ├── Open (legacy, keep for single-file)
│   │   ├── Import (NEW)
│   │   └── Quit
│   ├── Library (NEW)
│   │   ├── View Library (Ctrl+L)
│   │   └── Manage Collections (Phase 2)
│   ├── View
│   │   └── (existing theme options)
│   └── Help
│
├── QStackedWidget (central widget)
│   ├── [0] LibraryView (NEW)
│   │   └── QVBoxLayout
│   │       ├── QHBoxLayout (header)
│   │       │   ├── QLabel ("📚 My Library")
│   │       │   └── QLineEdit (search box)
│   │       │
│   │       ├── ContinueReadingWidget (Phase 3)
│   │       │   └── QScrollArea (horizontal)
│   │       │       └── (3-5 BookCardWidgets)
│   │       │
│   │       ├── QHBoxLayout (filter bar)
│   │       │   ├── QComboBox (filter)
│   │       │   ├── QComboBox (sort)
│   │       │   └── QToolButton (grid/list toggle)
│   │       │
│   │       └── QListView (book grid)
│   │           └── BookDelegate (custom card rendering)
│   │
│   └── [1] QWidget (existing reader layout)
│       └── QVBoxLayout
│           ├── BookViewer
│           └── NavigationBar
│
└── QStatusBar
```

---

## Keyboard Shortcuts

### New Shortcuts
- **Ctrl+I** - Import books
- **Ctrl+L** - Show library (when in reading view)
- **Ctrl+F** - Focus search box (when in library)
- **Escape** - Clear search
- **Delete** - Remove selected book from library (with confirmation, Phase 3)
- **Ctrl+N** - New collection (when collection manager open, Phase 2)

### Existing Shortcuts (Still Work in Reader)
- Ctrl+O - Open file (single book)
- Ctrl+Q - Quit
- Left/Right - Navigate chapters/pages
- Ctrl+M - Toggle navigation mode
- F1 - Keyboard shortcuts help

---

## Interaction Patterns

### Pattern: Card-Based Grid
- **Hover:** Card elevates slightly (box-shadow), shows tooltip with full title/author
- **Click:** Selects card (2px border highlight)
- **Double-click:** Opens book for reading
- **Right-click:** Context menu (Phase 3)
- **Keyboard:** Arrow keys navigate, Enter opens, Space selects

### Pattern: Real-Time Search
- **Typing:** Library filters immediately, no search button
- **Matching:** Searches title and author fields (case-insensitive)
- **Feedback:** Status bar shows "Showing 3 of 12 books"
- **Clear:** Escape key or clicking X in search box

### Pattern: View Switching
- **Library → Reader:** Double-click book or press Enter on selected book
- **Reader → Library:** Ctrl+L or menu Library → View Library
- **State preservation:** Library remembers filter, sort, scroll position

### Pattern: Import Workflow
- **Trigger:** File → Import or Ctrl+I
- **Dialog:** Multi-select file dialog (EPUB only)
- **Progress:** Toast notification shows progress (non-blocking)
- **Result:** Success toast or error toast with details
- **Update:** Library grid refreshes with new books

---

## Phased Implementation Plan

### Phase 1: Basic Library (MVP) - PRIORITY
**Goal:** Users can import books, see them in a grid, and open them to read.

**Features:**
- SQLite database with `books` table
- Import single or multiple EPUB files
- Grid view with placeholder book cards (no real covers yet)
- Book card shows: placeholder icon, title, author, progress %
- Double-click to open book
- QStackedWidget to switch between library and reader
- Reading position persists per book (chapter + scroll)
- Basic menu items: File → Import, Library → View Library

**Deliverables:**
- Database schema and CRUD operations
- LibraryController and LibraryView
- BookCardWidget and BookGridWidget
- Import workflow with basic error handling
- Tests for all new models and controllers
- Update MainWindow to use QStackedWidget

**Estimated Complexity:** Medium-High
**Estimated Time:** 2-3 implementation sessions

---

### Phase 2: Organization
**Goal:** Users can organize books with collections, filter, sort, and search.

**Features:**
- Collections system (create, rename, delete collections)
- Assign books to collections (one book can have multiple)
- Filter by collection
- Filter by reading status (not started, reading, finished)
- Sort by: Recent, Title A-Z, Author A-Z
- Real-time search by title/author
- Status bar shows filter/search info

**Deliverables:**
- `collections` and `book_collections` tables
- Collection manager UI (sidebar or dialog)
- Filter and sort dropdowns functional
- Search box with real-time filtering
- Mark book status (context menu or button)

**Estimated Complexity:** Medium
**Estimated Time:** 1-2 implementation sessions

---

### Phase 3: Polish & Advanced
**Goal:** Professional-grade library experience with visual polish.

**Features:**
- Continue Reading section (horizontal scroll of recent books)
- Cover image extraction from EPUBs
- List view option (compact alternative to grid)
- Context menus (right-click on books)
- Book details view (metadata, file info, stats)
- Drag-and-drop to import books
- Remove/delete books from library
- Better empty state with drag-and-drop hint

**Deliverables:**
- ContinueReadingWidget
- Cover extraction utility
- List view with QTableView
- Context menu actions
- Book details dialog
- Drag-and-drop import handler

**Estimated Complexity:** Medium
**Estimated Time:** 1-2 implementation sessions

---

## Accessibility Considerations

### Keyboard Navigation
- **Tab order:** Search box → Filter dropdown → Sort dropdown → Book grid → Status bar
- **Arrow keys:** Navigate book grid
- **Enter:** Open selected book
- **Escape:** Clear search, close dialogs
- **All actions accessible via keyboard**

### Visual Feedback
- **Hover states:** Card elevation, background color change
- **Focus indicators:** 2px border around selected card, focus ring on inputs
- **Active states:** Slightly darker on click
- **Loading indicators:** Progress bar or spinner with text label

### Screen Reader Support
- **Book cards:** `aria-label="Title by Author, 45% complete, last opened today"`
- **Search box:** `aria-label="Search library by title or author"`
- **Buttons:** Clear text labels, not icon-only
- **Status updates:** Announce filter/search results count

### Touch Targets (Desktop)
- **Book cards:** 180×260px (well above 44×44 minimum)
- **Buttons:** Minimum 44×44px
- **Clickable areas:** No smaller than 32×32px

---

## Error Handling

### Import Errors
- **File not found:** "Could not import {filename} - File not found"
- **Not an EPUB:** "Could not import {filename} - Not a valid EPUB file"
- **Corrupted EPUB:** "Could not import {filename} - File is corrupted or incomplete"
- **Already imported:** "Skipped {filename} - Already in library"
- **Permission denied:** "Could not import {filename} - Permission denied"

### Database Errors
- **Database locked:** Retry with exponential backoff, show error after 3 retries
- **Disk full:** "Cannot import books - Disk space full"
- **Database corrupted:** Show error, offer to rebuild database (Phase 3)

### Reading Position Errors
- **Book file moved/deleted:** "Could not open {title} - File not found at {path}. Remove from library?"
- **EPUB changed:** "Could not open {title} - File has been modified. Re-import?"

---

## Performance Considerations

### Lazy Loading
- **Grid view:** Only render visible cards + buffer (virtualization)
- **Metadata:** Load book metadata from database, not full EPUB parsing
- **Covers:** Load cover images on-demand, cache in memory (LRU)

### Database Optimization
- **Indexes:** On last_opened_date, title, author, status
- **Prepared statements:** Reuse for common queries
- **Transactions:** Batch imports in single transaction

### Expected Performance
- **Import 10 books:** < 5 seconds (without cover extraction)
- **Load library with 100 books:** < 500ms
- **Search filtering:** < 100ms (real-time, no lag)
- **Open book from library:** < 500ms

---

## Testing Strategy

### Unit Tests
- Database CRUD operations (add, update, delete books)
- LibraryController state management
- Filter logic (search, collection, status)
- Sort logic (recent, title, author)
- Import validation (valid/invalid EPUBs)

### Integration Tests
- End-to-end import workflow
- Switch between library and reader
- Reading position persistence
- Collection assignment and filtering

### UI Tests (pytest-qt)
- Library view renders correctly
- Book cards clickable
- Search filters in real-time
- View switching works
- Keyboard shortcuts functional

### Manual Testing
- Import various EPUB files (valid, corrupted, large)
- Test with 0, 1, 10, 100 books
- Verify responsive grid (resize window)
- Check all keyboard shortcuts
- Test filter/sort combinations

---

## Migration Considerations

### Existing User Data
- **Current:** Reading position stored in QSettings per file path
- **New:** Migrate to database on first library load
- **Migration script:** Read QSettings, create database entries for previously opened books
- **Fallback:** If EPUB file not in library, prompt to import

### Backward Compatibility
- **File → Open still works:** Opens book directly (legacy mode)
- **No library required:** App can still function as single-book reader
- **Graceful degradation:** If database unavailable, fall back to single-book mode

---

## Future Enhancements (Post-Phase 3)

### Advanced Features
- **Book details editing:** Manually edit title, author, cover
- **Reading statistics:** Pages read per day, time spent, books completed
- **Smart collections:** Auto-collections based on author, genre, tags
- **Export library:** Backup database and metadata
- **Import library:** Restore from backup
- **Cloud sync:** Sync reading positions across devices (far future)
- **Multiple libraries:** Switch between different book collections
- **Advanced search:** Filter by date added, file size, word count

### Integration Features
- **Goodreads integration:** Import reading list, sync status
- **Calibre import:** Import existing Calibre library metadata
- **File watching:** Auto-import new EPUBs from watched folder

---

## E-Reader UX Convention Alignment

This design follows established e-reader patterns:

| Feature | Kindle | Kobo | Apple Books | Our Design |
|---------|--------|------|-------------|------------|
| Library grid view | ✅ | ✅ | ✅ | ✅ Phase 1 |
| Continue Reading | ✅ | ✅ | ✅ | ✅ Phase 3 |
| Collections | ✅ | ✅ (Shelves) | ✅ | ✅ Phase 2 |
| Search | ✅ | ✅ | ✅ | ✅ Phase 2 |
| Reading status | ✅ | ✅ | ✅ | ✅ Phase 2 |
| List view | ✅ | ✅ | ✅ | ✅ Phase 3 |
| Book covers | ✅ | ✅ | ✅ | ✅ Phase 3 |
| Sort options | ✅ | ✅ | ✅ | ✅ Phase 2 |

**Verdict:** Strong alignment with industry standards while maintaining simplicity for MVP.

---

## Success Metrics

### Phase 1 Success
- [ ] User can import books into library
- [ ] User can see all books in grid view
- [ ] User can open any book by double-clicking
- [ ] Reading position persists per book
- [ ] User can switch between library and reader

### Phase 2 Success
- [ ] User can create and manage collections
- [ ] User can filter by collection or status
- [ ] User can search books by title/author
- [ ] User can sort library by different criteria

### Phase 3 Success
- [ ] User sees recently opened books at top
- [ ] Book covers display instead of placeholders
- [ ] User can choose grid or list view
- [ ] Context menus provide quick actions

### Overall Success
- [ ] 90%+ test coverage on library code
- [ ] Library loads with 100 books in < 500ms
- [ ] No user-reported bugs in import workflow
- [ ] Users report library as "essential feature"

---

## Documentation Updates Needed

### User-Facing
- Update README with library features
- Add screenshots of library grid
- Document keyboard shortcuts (Ctrl+I, Ctrl+L)

### Developer-Facing
- Document database schema and migrations
- Document LibraryController API
- Add architecture diagram for library components
- Update CLAUDE.md with library feature status

---

## Open Questions

None - all design decisions approved.

---

## References

- **UX Design:** This document (approved 2025-12-13)
- **Original UX Evaluation:** Session 2025-12-13 (prioritized library as #1)
- **E-Reader Conventions Research:** Kindle, Kobo, Apple Books, Calibre
- **Related Issues:** TBD (create GitHub issue for tracking)

---

**Next Steps:**
1. Invoke `/architect` to design technical architecture
2. Create GitHub issue to track implementation
3. Begin Phase 1 implementation with `/developer`
