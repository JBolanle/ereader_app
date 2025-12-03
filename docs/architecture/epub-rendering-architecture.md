# EPUB Rendering Architecture

## Date
2025-12-03

## Context

We need to design the architecture for rendering EPUB book content in a desktop GUI using PyQt6. This is the first user-facing feature that brings together the EPUB parsing layer (already complete) into a functional book reader.

**Requirements:**
- Display EPUB chapter content with HTML/CSS formatting
- Navigate between chapters (next/previous)
- Handle errors gracefully
- Performance: <100ms page renders, <200MB memory usage
- MVC architecture pattern
- Learning goal: Build PyQt6 UI from scratch

**Constraints:**
- Must integrate with existing `EPUBBook` model (src/ereader/models/epub.py)
- Must support HTML content (EPUBs use XHTML for chapters)
- Must remain simple enough for learning PyQt6 fundamentals
- Must be extensible for future features (themes, bookmarks, annotations)

## Architectural Decisions

### Decision 1: HTML Rendering Widget

**Options Considered:**

#### Option A: QTextBrowser (Lightweight)
**Pros:**
- Built into PyQt6 QtWidgets (no additional dependencies)
- Simple API: `setHtml()` to display content
- Supports HTML subset: headings, paragraphs, bold, italic, lists, tables, images
- CSS support for basic styling (fonts, colors, margins, borders)
- Lightweight and fast
- Easier to learn for PyQt6 beginners
- Sufficient for most EPUB books

**Cons:**
- Limited CSS support (no pseudo-classes like `:hover`, `:visited`)
- No JavaScript support
- May not render complex modern EPUBs perfectly
- Float property only works for tables/images
- HTML 4 subset, not full HTML5

#### Option B: QWebEngineView (Full Browser)
**Pros:**
- Full Chromium engine (complete HTML5/CSS3/JavaScript support)
- Renders any EPUB perfectly, including complex layouts
- Future-proof for modern EPUB3 features
- Better for reflowable complex layouts

**Cons:**
- Heavy dependency (requires QtWebEngine package)
- More complex API
- Larger memory footprint
- Harder to learn for beginners
- Overkill for MVP

**Decision: Start with QTextBrowser (Option A)**

**Rationale:**
1. **Learning Goal**: QTextBrowser is simpler, allowing focus on PyQt6 fundamentals (signals/slots, layouts, MVC) without browser engine complexity
2. **Sufficient for MVP**: Most EPUBs use basic HTML/CSS that QTextBrowser handles well
3. **Fast Development**: Simpler API means faster iteration and learning
4. **Extensible Design**: Use Protocol abstraction (see Decision 2) so we can swap to QWebEngineView later if needed
5. **Performance**: Lighter weight helps us meet <100ms render and <200MB memory requirements
6. **Test First**: We can test with real EPUBs and upgrade only if rendering quality is insufficient

**Implementation Notes:**
- Wrap QTextBrowser in a `BookViewer` class to abstract the widget
- Use Protocol interface so switching to QWebEngineView later requires minimal changes
- If future testing shows QTextBrowser is insufficient, we can create a QWebEngineView-based implementation

**References:**
- [Qt Rich Text HTML Subset](https://doc.qt.io/qt-6/richtext-html-subset.html)
- Supported: HTML 4 subset, basic CSS, tables, images, lists
- QTextBrowser docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qtextbrowser.html

---

### Decision 2: Component Structure (MVC Architecture)

**Pattern: Model-View-Controller (MVC)**

Following the project's established MVC pattern, we separate concerns into three layers:

#### Model Layer (Already Exists)
- **EPUBBook** (`src/ereader/models/epub.py`)
  - Responsibilities: Parse EPUB structure, provide metadata, serve chapter content
  - Interface:
    - `get_chapter_count() -> int`
    - `get_chapter_content(index: int) -> str` (returns HTML)
    - Properties: `title`, `authors`, `language`
  - Already implemented and tested ✅

#### View Layer (New - To Implement)

**1. MainWindow** (`src/ereader/views/main_window.py`)
- Top-level application window (QMainWindow)
- Responsibilities:
  - Application lifecycle (show/close window)
  - Menu bar (File > Open, File > Quit)
  - Status bar (book title, chapter info)
  - Layout coordination (compose BookViewer + NavigationBar)
- Signals emitted:
  - `file_open_requested()` - User clicked "Open" in menu
- Signals received:
  - `book_loaded(title: str, author: str)` - From controller
  - `chapter_changed(current: int, total: int)` - From controller

**2. BookViewer** (`src/ereader/views/book_viewer.py`)
- Widget for displaying chapter content
- Responsibilities:
  - Render HTML content (wraps QTextBrowser)
  - Handle scrolling
  - Apply reading styles (font size, margins)
- Interface:
  - `set_content(html: str)` - Display new chapter
  - `clear()` - Clear displayed content
  - `set_base_font_size(size: int)` - For future font customization
- Implementation: Wraps QTextBrowser, configured as read-only

**3. NavigationBar** (`src/ereader/views/navigation_bar.py`)
- Widget with navigation controls (QWidget with layout)
- Responsibilities:
  - Provide Previous/Next buttons
  - Handle keyboard shortcuts (Arrow keys, PgUp/PgDn)
  - Enable/disable buttons based on position (disable Previous at start, Next at end)
- Signals emitted:
  - `next_chapter_requested()` - User wants next chapter
  - `previous_chapter_requested()` - User wants previous chapter
- Signals received:
  - `navigation_state_changed(can_go_back: bool, can_go_forward: bool)` - From controller

#### Controller Layer (New - To Implement)

**ReaderController** (`src/ereader/controllers/reader_controller.py`)
- Coordinates between Model (EPUBBook) and Views
- Responsibilities:
  - Own the EPUBBook instance (or None if no book loaded)
  - Track current chapter index
  - Handle file opening (create EPUBBook, handle errors)
  - Handle navigation requests (load new chapters)
  - Update views with new content and state
  - Error handling and user feedback
- State:
  - `_book: EPUBBook | None` - Currently loaded book
  - `_current_chapter_index: int` - Current position in book
- Key Methods:
  - `open_book(filepath: str)` - Load EPUB, notify views
  - `next_chapter()` - Navigate forward
  - `previous_chapter()` - Navigate backward
  - `_load_chapter(index: int)` - Load and display chapter content
  - `_update_navigation_state()` - Update button enabled/disabled state

**Design Principle: "Dumb Views, Smart Controller"**
- Views just display what they're told and emit signals for user actions
- Views have no knowledge of EPUBBook or business logic
- Controller owns all state and orchestrates the flow

---

### Decision 3: Protocol-Based Abstraction

**Decision: Use Protocol interface for BookRenderer**

To support future extensibility (swapping QTextBrowser for QWebEngineView, adding PDF renderer), define a Protocol interface for content rendering.

**BookRenderer Protocol** (`src/ereader/views/protocols.py`):

```python
from typing import Protocol

class BookRenderer(Protocol):
    """Protocol for widgets that can render book content.

    This protocol defines the interface between the controller and
    rendering widgets, allowing different implementations (QTextBrowser,
    QWebEngineView, etc.) to be swapped without changing controller code.
    """

    def set_content(self, html: str) -> None:
        """Display HTML content in the renderer.

        Args:
            html: HTML content to display (XHTML from EPUB chapter).
        """
        ...

    def clear(self) -> None:
        """Clear all displayed content."""
        ...
```

**Implementation:**
- `BookViewer` implements this protocol (structural subtyping via Protocol)
- Controller depends on `BookRenderer` protocol, not concrete implementation
- Future implementations (e.g., `WebEngineViewer`) just need to implement the protocol

**Benefits:**
- ✅ Easy to swap rendering implementations
- ✅ Testable (can mock BookRenderer in controller tests)
- ✅ Follows project principle: "Protocol-based interfaces for extensibility"
- ✅ Aligns with Python's duck typing and PEP 544

---

### Decision 4: Data Flow and Signals/Slots

PyQt6 uses the **Signals and Slots** pattern for event handling. Here's how data flows through the system:

**Example: User Clicks "Next Chapter"**

```
1. User clicks Next button
   ↓
2. NavigationBar emits next_chapter_requested signal
   ↓
3. ReaderController.next_chapter() slot receives signal
   ↓
4. Controller increments current_chapter_index
   ↓
5. Controller calls book.get_chapter_content(new_index)
   ↓
6. Controller calls viewer.set_content(html)
   ↓
7. BookViewer displays new chapter
   ↓
8. Controller emits chapter_changed(current, total) signal
   ↓
9. MainWindow updates status bar: "Chapter 3 of 12"
   ↓
10. Controller calls _update_navigation_state()
   ↓
11. NavigationBar receives navigation_state_changed signal
   ↓
12. NavigationBar enables/disables buttons appropriately
```

**Signal/Slot Connections:**

```python
# In MainWindow or initialization code:

# File opening
main_window.file_open_requested.connect(controller.open_book)
controller.book_loaded.connect(main_window.update_book_info)

# Navigation
nav_bar.next_chapter_requested.connect(controller.next_chapter)
nav_bar.previous_chapter_requested.connect(controller.previous_chapter)
controller.chapter_changed.connect(main_window.update_chapter_info)
controller.navigation_state_changed.connect(nav_bar.update_buttons)

# Content display
controller.content_ready.connect(viewer.set_content)
```

**Key Principles:**
- **Loose Coupling**: Views don't know about controller, only emit signals
- **One Direction**: Data flows Controller → View, events flow View → Controller
- **Type Safety**: Use PyQt6 type hints in signal definitions
- **Clear Ownership**: Controller owns state, views are stateless displayers

---

### Decision 5: State Management

**Decision: All reading state lives in the Controller**

The Controller (`ReaderController`) owns:
- `_book: EPUBBook | None` - The loaded book instance
- `_current_chapter_index: int` - Current position in book (0-based)

Views are **stateless** - they display what they're told:
- BookViewer doesn't know what chapter it's showing
- NavigationBar doesn't know if it's at the first/last chapter
- MainWindow doesn't track the current book

**Benefits:**
1. **Single Source of Truth**: All state in one place (controller)
2. **Testable**: Easy to test controller logic without UI
3. **Simple Views**: Views are just display widgets, easy to reason about
4. **Persistence Ready**: When we add "remember position" feature, state is already centralized

**Example:**
```python
class ReaderController:
    def __init__(self):
        self._book: EPUBBook | None = None
        self._current_chapter_index: int = 0

    def next_chapter(self) -> None:
        if self._book is None:
            return

        max_index = self._book.get_chapter_count() - 1
        if self._current_chapter_index < max_index:
            self._current_chapter_index += 1
            self._load_chapter(self._current_chapter_index)
```

---

### Decision 6: Async Strategy

**Decision: Synchronous for MVP, async only if performance testing shows it's needed**

**Rationale:**
1. **Measure First**: EPUB operations are likely fast enough (<100ms requirement)
   - Reading from ZIP: typically <10ms for chapter files
   - QTextBrowser.setHtml(): fast for typical chapter sizes

2. **Simplicity for Learning**: Synchronous code is easier to learn and debug for PyQt6 beginners

3. **Easy to Add Later**: If performance testing shows bottlenecks, we can:
   - Use `QThread` for file loading
   - Use Python's `asyncio` with `qasync` library for async operations
   - Pre-fetch next chapter in background

**Performance Testing Plan:**
After MVP implementation, test with:
- Small EPUBs (< 1MB, < 50 chapters)
- Large EPUBs (> 10MB, > 200 chapters)
- Chapters with many images

Measure:
- Time to open book: `EPUBBook.__init__()`
- Time to load chapter: `get_chapter_content()`
- Time to render: `setHtml()` + display

**If any operation > 100ms:** Add async for that operation.

**Implementation Notes:**
- Keep methods designed to be async-compatible (return values, not mutate global state)
- Document places where async might be added (file loading, pre-fetching)

---

### Decision 7: Error Handling Strategy

**Decision: Controller handles all errors, shows user-friendly dialogs**

**Error Categories:**

1. **File Loading Errors**
   - File doesn't exist, not readable, not a valid EPUB
   - Handle in `controller.open_book()`
   - Show QMessageBox with user-friendly message
   - Don't crash, leave previous book open or stay in "no book" state

2. **Chapter Loading Errors**
   - Missing chapter file, corrupted content
   - Handle in `controller._load_chapter()`
   - Show error message: "Unable to load chapter X"
   - Stay on current chapter, don't navigate

3. **Rendering Errors**
   - Malformed HTML (unlikely, but possible)
   - Handle in `BookViewer.set_content()`
   - Display error message in viewer: "Unable to display chapter"
   - Log error for debugging

**Error Handling Pattern:**
```python
def open_book(self, filepath: str) -> None:
    try:
        self._book = EPUBBook(filepath)
        # ... update views ...
    except FileNotFoundError:
        self._show_error("File not found", f"Could not find: {filepath}")
    except InvalidEPUBError as e:
        self._show_error("Invalid EPUB", f"This file is not a valid EPUB: {e}")
    except Exception as e:
        logger.exception("Unexpected error opening book")
        self._show_error("Error", f"Failed to open book: {e}")
```

**Logging:**
- Use Python logging module (already used in EPUBBook)
- Log all errors with context (filepath, chapter index, exception)
- Log at appropriate levels:
  - `logger.error()` for expected errors (bad file format)
  - `logger.exception()` for unexpected errors
  - `logger.warning()` for recoverable issues

---

### Decision 8: Performance Optimizations (Future)

**For MVP: No optimization, measure first**

**After MVP, if performance testing shows bottlenecks:**

1. **Chapter Pre-fetching**
   - Load next chapter in background while user reads current
   - Cache in memory (limit to 3-5 chapters)
   - Clear cache when navigating backward or jumping chapters

2. **Lazy Resource Loading**
   - Images in chapters loaded on-demand
   - Only parse/decode when needed for display

3. **Memory Management**
   - Limit cache size (<200MB requirement)
   - Unload old chapters when cache is full
   - Monitor memory usage with large books

**Current Performance:**
- `EPUBBook.__init__()`: Parses metadata immediately (needed for display)
- `get_chapter_content()`: Reads from ZIP on demand (not cached)
- This meets the performance requirement for typical EPUBs

**Monitoring:**
Add timing logs in controller:
```python
start = time.time()
content = self._book.get_chapter_content(index)
elapsed = (time.time() - start) * 1000
logger.debug(f"Loaded chapter {index} in {elapsed:.1f}ms")
```

---

## Consequences

### What This Enables ✅

1. **Clean MVC Architecture**: Clear separation of concerns, easy to understand and test
2. **Extensible Rendering**: Protocol-based design allows swapping rendering implementations
3. **Simple to Learn**: QTextBrowser approach keeps PyQt6 learning curve manageable
4. **Future Features**: Architecture supports themes, bookmarks, reading progress tracking
5. **Testable**: Controller logic testable without UI, views testable with pytest-qt
6. **Fast Development**: Simple synchronous code for MVP, optimize later if needed

### What This Constrains 📍

1. **HTML Support**: Limited to QTextBrowser's HTML subset (no complex CSS, no JS)
   - *Can upgrade to QWebEngineView if needed*
2. **Synchronous Operations**: File loading blocks UI thread
   - *Will add async if performance testing shows it's needed*
3. **No Pre-fetching**: Each chapter loads on-demand
   - *Can add caching layer later if needed*
4. **EPUB Only**: Architecture focused on EPUB, PDF support needs additional work
   - *Protocol design makes adding PDF renderer straightforward*

### What to Watch Out For ⚠️

1. **QTextBrowser Rendering Quality**: Test with diverse EPUBs to verify quality
   - Monitor for layout issues, unsupported CSS
   - Prepare to upgrade to QWebEngineView if needed

2. **Performance with Large Books**: Test with >200 chapter books
   - Monitor chapter load times
   - Add async/caching if >100ms loads

3. **Memory Usage**: Monitor with image-heavy books
   - QTextBrowser caches images internally
   - May need resource cleanup for large books

4. **State Persistence**: Currently no saving of reading position
   - Future feature will need to serialize controller state
   - Design supports this (state centralized in controller)

5. **Threading Issues**: If we add async later, ensure thread-safe access to EPUBBook
   - Qt requires UI updates on main thread
   - Use QThread or qasync properly

---

## Implementation Guidance

### Phase 1: Minimal Window (Prove PyQt6 Works)
**Goal:** Get a window showing, learn QApplication basics

1. Create `src/ereader/__main__.py` - Entry point
2. Create `src/ereader/views/main_window.py` - Empty QMainWindow
3. Run and see window
4. **Learning Focus:** QApplication, QMainWindow, basic PyQt6 setup

### Phase 2: File Opening (Connect Model to UI)
**Goal:** Open EPUB, display metadata

1. Add File > Open menu to MainWindow
2. Create `src/ereader/controllers/reader_controller.py`
3. Use QFileDialog to select file
4. Load EPUBBook, display title in status bar
5. **Learning Focus:** QFileDialog, signals/slots, error handling

### Phase 3: Content Display (Render First Chapter)
**Goal:** See HTML content rendered

1. Create `src/ereader/views/book_viewer.py` (wraps QTextBrowser)
2. Create protocol: `src/ereader/views/protocols.py`
3. Controller loads first chapter, passes to viewer
4. **Learning Focus:** QTextBrowser, setHtml(), layouts

### Phase 4: Navigation (Chapter Next/Previous)
**Goal:** Full reading experience

1. Create `src/ereader/views/navigation_bar.py`
2. Add Previous/Next buttons, keyboard shortcuts
3. Controller tracks chapter index, loads chapters
4. Update status bar with chapter position
5. **Learning Focus:** QPushButton, keyboard shortcuts, state management

### Phase 5: Polish and Error Handling
**Goal:** Production-ready MVP

1. Error dialogs for all error cases
2. Graceful handling of edge cases
3. Window icon, proper sizing
4. **Learning Focus:** QMessageBox, robustness

### Testing Strategy

**Unit Tests:**
- `tests/test_controllers/test_reader_controller.py`
  - Mock EPUBBook and views
  - Test navigation logic (next/prev, boundaries)
  - Test error handling (bad files, missing chapters)
  - Test state management

**Integration Tests:**
- `tests/test_views/test_main_window.py`
  - Use real EPUB files from `tests/fixtures/`
  - Test with pytest-qt (QTest framework)
  - Verify signals are emitted correctly
  - Test user interactions (button clicks, menu actions)

**Manual Testing:**
- Test with various EPUBs (simple, complex, large, small)
- Test keyboard shortcuts
- Test window resizing
- Verify error messages are user-friendly
- Check performance (timing logs)

### Development Commands

**Learning Phase:**
- `/study PyQt6 basics` - Learn QApplication, signals/slots, layouts
- `/mentor` - Get explanations while building

**Implementation Phase:**
- `/branch feature/epub-rendering-mvp` - Create feature branch
- `/developer` - Implement phase by phase
- `/test` - Run tests frequently during development

**Review Phase:**
- `/code-review` - Self-review before PR
- `/pm` - Check if ready to move on

---

## Component Interface Summary

### EPUBBook (Model - Already Exists)
```python
class EPUBBook:
    filepath: Path
    title: str
    authors: list[str]
    language: str

    def get_chapter_count(self) -> int: ...
    def get_chapter_content(self, chapter_index: int) -> str: ...
```

### BookRenderer (Protocol)
```python
class BookRenderer(Protocol):
    def set_content(self, html: str) -> None: ...
    def clear(self) -> None: ...
```

### BookViewer (View)
```python
class BookViewer(QWidget):  # Implements BookRenderer protocol
    def set_content(self, html: str) -> None: ...
    def clear(self) -> None: ...
    def set_base_font_size(self, size: int) -> None: ...  # Future
```

### NavigationBar (View)
```python
class NavigationBar(QWidget):
    # Signals
    next_chapter_requested: pyqtSignal
    previous_chapter_requested: pyqtSignal

    # Slots
    def update_buttons(self, can_go_back: bool, can_go_forward: bool) -> None: ...
```

### MainWindow (View)
```python
class MainWindow(QMainWindow):
    # Signals
    file_open_requested: pyqtSignal

    # Slots
    def update_book_info(self, title: str, author: str) -> None: ...
    def update_chapter_info(self, current: int, total: int) -> None: ...
```

### ReaderController (Controller)
```python
class ReaderController(QObject):
    # Signals
    book_loaded: pyqtSignal  # (title: str, author: str)
    chapter_changed: pyqtSignal  # (current: int, total: int)
    navigation_state_changed: pyqtSignal  # (can_go_back: bool, can_go_forward: bool)
    content_ready: pyqtSignal  # (html: str)
    error_occurred: pyqtSignal  # (title: str, message: str)

    # Slots (public methods)
    def open_book(self, filepath: str) -> None: ...
    def next_chapter(self) -> None: ...
    def previous_chapter(self) -> None: ...

    # Internal methods
    def _load_chapter(self, index: int) -> None: ...
    def _update_navigation_state(self) -> None: ...
    def _show_error(self, title: str, message: str) -> None: ...
```

---

## References

- **CLAUDE.md**: Project principles, tech stack, performance requirements
- **docs/specs/epub-rendering-mvp.md**: Feature spec with user stories and acceptance criteria
- **src/ereader/models/epub.py**: Existing EPUBBook implementation
- **docs/architecture/project-structure.md**: MVC pattern, exception handling, import patterns
- **PyQt6 Documentation**:
  - https://www.riverbankcomputing.com/static/Docs/PyQt6/
  - QTextBrowser: https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qtextbrowser.html
- **Qt Documentation**:
  - Rich Text HTML Subset: https://doc.qt.io/qt-6/richtext-html-subset.html
  - Signals and Slots: https://doc.qt.io/qt-6/signalsandslots.html
- **Python PEP 544**: Protocols (Structural Subtyping)

---

## Next Steps

1. **Review this architecture** with `/pm` or `/code-review` if needed
2. **Create feature branch**: `/branch feature/epub-rendering-mvp`
3. **Start implementation**: Use `/developer` to implement Phase 1
4. **Iterate through phases**: One phase at a time, test frequently
5. **Come back to `/pm`** when MVP is complete for transition assessment

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-03 | Initial architecture | Issue #17 - Design EPUB rendering architecture |

