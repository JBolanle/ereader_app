# True Page-Based Pagination System Architecture

## Date
2025-12-05

## Context

Issue #31 requests implementing a professional page-based pagination system to replace the current virtual scroll-based navigation (Phase 1 from Issue #21). The goal is to provide stable page numbers, discrete page navigation, and a toggle between scroll and page modes.

**Current State (Phase 1):**
- Viewport-based scrolling with "virtual pages"
- Navigation by scrolling 50% or 100% of viewport
- Progress shown as "Chapter X of Y • Z% through chapter"
- No stable page numbers
- Page count changes with window resize

**User Requirements:**
- Stable page numbers that don't change on window resize
- Display "Page X of Y in Chapter Z"
- Save position as (chapter, page) instead of scroll percentage
- Toggle between continuous scroll and paginated modes
- Professional e-reader experience (Kindle/Kobo quality)

**Constraints:**
- Learning project: Focus on PyQt6 fundamentals, avoid over-complexity
- Current architecture: QTextBrowser-based MVC
- MVP complete: This is a post-MVP enhancement (medium priority)
- Performance: <100ms page calculation, <200MB memory
- Maintain testability and code quality

## Research Findings

### QTextDocument Pagination Capabilities

QTextDocument provides pagination support primarily designed for **printing**:

```python
# Set page size for layout
document.setPageSize(QSizeF(width, height))

# Get calculated page count
page_count = document.pageCount()  # Calls layout.pageCount()

# Print document (auto-paginates)
document.print(printer)
```

**Key Discovery:** QTextDocument can calculate page breaks for printing, but has **no built-in method to display a specific page** interactively. The layout engine (QAbstractTextDocumentLayout) manages pagination internally, but:

- No `renderPage(int pageNum)` method
- No `setVisiblePage(int pageNum)` method
- Can't extract content for a specific page easily
- Designed for print output, not interactive display

**Sources:**
- [QTextDocument pagination methods - Stack Overflow](https://stackoverflow.com/questions/15874129/how-to-access-qtextdocument-pages)
- [QTextDocument Class | Qt GUI | Qt 6.10.1](https://doc.qt.io/qt-6/qtextdocument.html)
- [QAbstractTextDocumentLayout](https://doc.qt.io/qt-6/qabstracttextdocumentlayout.html)

## Options Considered

### Option 1: QTextDocument Page Layout (Hybrid Approach)

**Approach:** Use QTextDocument's pagination to calculate page breaks, then implement custom display logic.

**Possible Implementations:**

**1A. Custom QPainter Rendering:**
```python
# Set page size on document
document.setPageSize(QSizeF(width, height))

# Render specific page using QPainter
def render_page(page_num):
    painter = QPainter(widget)
    # Use QAbstractTextDocumentLayout to draw specific page
    layout.draw(painter, context)  # Complex: need to set clip region
```

**Pros:**
- Uses Qt's built-in layout engine for page break calculation
- Handles complex formatting automatically
- True page boundaries (no mid-paragraph breaks)

**Cons:**
- **Very complex:** Requires implementing custom paint events and QPainter logic
- **No direct API:** Need to work with QAbstractTextDocumentLayout internals
- **Advanced Qt:** Beyond current PyQt6 learning scope
- **Testing difficulty:** Complex rendering logic hard to unit test
- **Overkill:** Using printing APIs for interactive display

**1B. Viewport Clipping:**
```python
# Set page size, calculate page breaks as scroll positions
# Scroll QTextBrowser to show desired page
# Clip viewport to show exactly one page
```

**Pros:**
- Simpler than custom rendering
- Reuses existing QTextBrowser

**Cons:**
- **Not true single-page display:** Full document still rendered
- **Visual artifacts:** Need complex clipping to hide other pages
- **Memory inefficient:** All pages in memory even if only showing one
- **Hacky:** Fighting against QTextBrowser's design

**Recommendation: Not viable** - The complexity and hacky nature outweigh benefits.

---

### Option 2: Manual HTML Chunking

**Approach:** Parse chapter HTML, calculate text fitting in viewport, split into page-sized chunks.

```python
def paginate_html(html: str, viewport_height: int) -> list[str]:
    """Split HTML into page-sized chunks."""
    # Parse HTML into DOM tree
    # Calculate which elements fit on each page
    # Split while preserving tag structure
    # Return list of HTML strings, one per page
```

**Pros:**
- Full control over pagination
- Can display truly one page at a time
- Fits current QTextBrowser architecture
- Clear separation: one HTML string = one page

**Cons:**
- **Extremely complex:** HTML/CSS parsing and splitting is non-trivial
- **Tag structure preservation:** Must ensure all tags properly closed
- **Image handling:** Complex to split images across pages
- **CSS context:** Need to maintain styles across page boundaries
- **Re-calculation:** Must re-chunk on every resize or font change
- **Error-prone:** Easy to break formatting with incorrect splits
- **Maintenance burden:** Complex code to maintain and debug

**Example Complexity:**
```html
<!-- Original HTML -->
<div class="chapter">
  <p>This is a long paragraph that spans multiple pages...</p>
  <img src="image.jpg" />
</div>

<!-- Must split to: -->
<!-- Page 1 -->
<div class="chapter">
  <p>This is a long paragraph that...</p>
</div>

<!-- Page 2 -->
<div class="chapter">
  <p>...spans multiple pages...</p>
  <img src="image.jpg" />
</div>
```

Handling partial elements, nested tags, CSS inheritance, images—all very complex.

**Recommendation: Avoid** - Complexity far exceeds benefit for a learning project.

---

### Option 3: QWebEngineView with CSS Paged Media

**Approach:** Switch from QTextBrowser to QWebEngineView (full Chromium engine), use CSS paged media and JavaScript for pagination.

```python
# Use QWebEngineView instead of QTextBrowser
viewer = QWebEngineView()

# Apply CSS for paged media
css = """
@media print {
  @page { size: A4; margin: 2cm; }
}
body { column-width: 600px; column-gap: 0; }
"""

# JavaScript to navigate pages
viewer.page().runJavaScript("jumpToPage(3);")
```

**Pros:**
- **Web standards:** CSS paged media designed for this
- **Proven approach:** Used by Readium.js, Epub.js
- **Future-proof:** Supports EPUB3, complex CSS, JavaScript
- **Professional quality:** Can match Kindle/Kobo pagination

**Cons:**
- **Major architectural change:** Complete rewrite of rendering layer
- **Heavy dependency:** QtWebEngine adds ~100MB to app size
- **Resource intensive:** Chromium engine uses more memory/CPU
- **Learning scope:** Shifts focus from PyQt to web technologies
- **Overkill for MVP+1:** We already have working QTextBrowser rendering
- **Defeats learning goal:** We chose QTextBrowser to learn Qt fundamentals

**When this makes sense:**
- If QTextBrowser rendering quality becomes insufficient
- If we need complex EPUB3 features (JavaScript, advanced CSS)
- If we decide to make this a production e-reader app

**Recommendation: Defer** - Keep as future option (Phase 3+), not for Phase 2.

---

### Option 4: Enhanced Virtual Pagination (Recommended)

**Approach:** Calculate stable page boundaries based on content height and fixed viewport dimensions. Navigate by discrete pages rather than smooth scrolling.

**Core Concept:**
- Calculate page breaks as array of scroll positions: `[0, 800, 1600, 2400, ...]`
- In **Page Mode:** Navigate by jumping to page_breaks[page_num]
- In **Scroll Mode:** Current Phase 1 behavior (continuous scrolling)
- Store position as (chapter, page_number) with scroll offset for precision

**Implementation Overview:**
```python
class PaginationEngine:
    def calculate_page_breaks(
        self,
        content_height: int,
        viewport_height: int
    ) -> list[int]:
        """Calculate scroll positions for page boundaries."""
        page_breaks = [0]
        current_pos = 0

        while current_pos < content_height:
            current_pos += viewport_height
            page_breaks.append(min(current_pos, content_height))

        return page_breaks

    def get_page_number(self, scroll_position: int) -> int:
        """Get page number from scroll position."""
        for i, break_pos in enumerate(self.page_breaks):
            if scroll_position < break_pos:
                return i
        return len(self.page_breaks) - 1

    def navigate_to_page(self, page_num: int) -> int:
        """Get scroll position for a specific page."""
        return self.page_breaks[page_num]
```

**Pros:**
- ✅ **Builds on Phase 1:** Reuses existing scroll infrastructure
- ✅ **Stable page numbers:** Within a session and viewport size
- ✅ **Simpler implementation:** No HTML parsing or custom rendering
- ✅ **Fits current architecture:** No changes to QTextBrowser or MVC
- ✅ **Mode toggle:** Easy to switch between page/scroll modes
- ✅ **Testable:** Pure logic, easy to unit test
- ✅ **Achievable:** Can implement in estimated time budget (3-5 days)
- ✅ **Learning-focused:** Teaches state management, not rendering complexity

**Cons:**
- ⚠️ **Not "true" pages:** Still continuous content, just discrete navigation
- ⚠️ **Page breaks mid-paragraph:** May break reading flow
- ⚠️ **Resize recalculation:** Page numbers change on window resize
  - *Mitigation:* Recalculate and restore relative position
- ⚠️ **Not as polished:** Not Kindle-quality, but "good enough" for learning project

**Differences from Phase 1:**
| Aspect | Phase 1 (Current) | Phase 2 (Enhanced Virtual) |
|--------|-------------------|----------------------------|
| Navigation | Smooth scroll by viewport % | Discrete jumps to page boundaries |
| Display | "X% through chapter" | "Page X of Y in Chapter Z" |
| Position | Scroll percentage (0-100%) | Page number + offset |
| Stability | Changes continuously | Stable within session |
| Resize | Percentage preserved | Recalculate pages, restore position |

**Why This is "Good Enough":**
1. **Learning project goals:** Focus on architecture and state management, not rendering engines
2. **Pragmatic:** 80% of user value for 20% of the effort
3. **Extensible:** Can upgrade to Option 3 (QWebEngineView) later if needed
4. **Professional standard:** Similar to many web-based e-readers before CSS paged media
5. **MVP+1 appropriate:** Significant improvement over Phase 1 without overengineering

---

## Decision: Enhanced Virtual Pagination (Option 4)

**Chosen Approach:** Implement enhanced virtual pagination with stable page numbers and mode toggle.

**Rationale:**

1. **Appropriate for Learning Project:**
   - Teaches state management, caching, and user preferences
   - Doesn't require deep rendering engine knowledge
   - Stays within PyQt6 fundamentals scope

2. **Pragmatic Engineering:**
   - Option 1 (QTextDocument) requires advanced Qt rendering (out of scope)
   - Option 2 (HTML chunking) is extremely complex for marginal benefit
   - Option 3 (QWebEngineView) is architectural overkill for a post-MVP enhancement
   - Option 4 delivers core user needs with reasonable complexity

3. **Fits Current Architecture:**
   - Builds naturally on Phase 1 implementation
   - No changes to rendering layer (BookViewer, QTextBrowser)
   - Adds new controller logic (PaginationEngine)
   - Maintains MVC separation

4. **Future Extensibility:**
   - If we later need true pagination, we can:
     - Upgrade to QWebEngineView (Option 3)
     - Replace PaginationEngine internals
     - Keep same external API (controller signals/slots)
   - User-facing features (position saving, mode toggle) remain the same

5. **Time-Boxed Implementation:**
   - Estimated 3-5 days matches issue estimate
   - Can be tested and refined incrementally
   - Low risk of scope creep

**Trade-offs Accepted:**
- Page breaks may occur mid-paragraph (not perfect typography)
- Page numbers change on window resize (recalculate and restore position)
- Not matching Kindle/Kobo polish (acceptable for learning project)

---

## Architecture Design

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                        MainWindow                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              BookViewer (View)                       │   │
│  │  - QTextBrowser wrapper                              │   │
│  │  - Renders HTML content                              │   │
│  │  - Emits scroll_position_changed(int)                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           NavigationBar (View)                       │   │
│  │  - Previous/Next buttons                             │   │
│  │  - Page/Scroll mode toggle button                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  - Status Bar: "Page 12 of 45 in Chapter 3" or              │
│                "Chapter 3 of 15 • 45% through chapter"       │
└─────────────────────────────────────────────────────────────┘
                          ↕ Signals/Slots
┌─────────────────────────────────────────────────────────────┐
│              ReaderController (Controller)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         PaginationEngine (NEW)                       │   │
│  │  - calculate_page_breaks()                           │   │
│  │  - get_page_number(scroll_pos)                       │   │
│  │  - navigate_to_page(page_num) -> scroll_pos          │   │
│  │  - recalculate_on_resize()                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │       ReadingPosition (NEW Model)                    │   │
│  │  - chapter_index: int                                │   │
│  │  - page_number: int (page mode)                      │   │
│  │  - scroll_offset: int (precise position)             │   │
│  └──────────────────────────────────────────────────────┘   │
│  - Current mode: PageMode | ScrollMode                      │
│  - Navigation mode logic                                    │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│                   EPUBBook (Model)                           │
│  - Existing, no changes needed                               │
└─────────────────────────────────────────────────────────────┘
```

### New Components

#### 1. PaginationEngine Class

**Location:** `src/ereader/utils/pagination_engine.py`

**Responsibility:** Calculate and manage page boundaries for a chapter.

```python
from dataclasses import dataclass

@dataclass
class PageBreaks:
    """Page break information for a chapter."""
    viewport_height: int
    content_height: int
    page_breaks: list[int]  # Scroll positions for each page start

    @property
    def page_count(self) -> int:
        """Number of pages in this chapter."""
        return len(self.page_breaks)

class PaginationEngine:
    """Engine for calculating page boundaries within chapters.

    This class manages the calculation of page breaks based on viewport
    height and content height. It provides methods to convert between
    scroll positions and page numbers.
    """

    def __init__(self) -> None:
        self._page_breaks: PageBreaks | None = None

    def calculate_page_breaks(
        self,
        content_height: int,
        viewport_height: int
    ) -> PageBreaks:
        """Calculate page break positions for given dimensions.

        Args:
            content_height: Total height of the chapter content in pixels.
            viewport_height: Height of the visible viewport in pixels.

        Returns:
            PageBreaks object with calculated break positions.
        """
        page_breaks = [0]  # First page always starts at 0
        current_pos = 0

        while current_pos + viewport_height < content_height:
            current_pos += viewport_height
            page_breaks.append(current_pos)

        # Last page break at content height
        if page_breaks[-1] != content_height:
            page_breaks.append(content_height)

        self._page_breaks = PageBreaks(
            viewport_height=viewport_height,
            content_height=content_height,
            page_breaks=page_breaks
        )

        logger.debug(
            "Calculated %d pages (viewport: %dpx, content: %dpx)",
            len(page_breaks),
            viewport_height,
            content_height
        )

        return self._page_breaks

    def get_page_number(self, scroll_position: int) -> int:
        """Get page number from scroll position (0-indexed).

        Args:
            scroll_position: Current scroll position in pixels.

        Returns:
            Page number (0-indexed).
        """
        if self._page_breaks is None:
            return 0

        # Find the page this scroll position belongs to
        for i in range(len(self._page_breaks.page_breaks) - 1):
            if scroll_position < self._page_breaks.page_breaks[i + 1]:
                return i

        # Last page
        return len(self._page_breaks.page_breaks) - 2

    def get_scroll_position_for_page(self, page_number: int) -> int:
        """Get scroll position for a specific page number.

        Args:
            page_number: Page number (0-indexed).

        Returns:
            Scroll position in pixels.
        """
        if self._page_breaks is None:
            return 0

        if page_number < 0 or page_number >= len(self._page_breaks.page_breaks) - 1:
            logger.warning("Invalid page number: %d", page_number)
            return 0

        return self._page_breaks.page_breaks[page_number]

    def get_page_count(self) -> int:
        """Get total number of pages."""
        if self._page_breaks is None:
            return 0
        return self._page_breaks.page_count - 1  # -1 because last break is end marker

    def needs_recalculation(self, viewport_height: int) -> bool:
        """Check if page breaks need recalculation due to resize.

        Args:
            viewport_height: Current viewport height.

        Returns:
            True if recalculation needed.
        """
        if self._page_breaks is None:
            return True
        return self._page_breaks.viewport_height != viewport_height
```

#### 2. ReadingPosition Model

**Location:** `src/ereader/models/reading_position.py`

**Responsibility:** Store and manage reading position within a book.

```python
from dataclasses import dataclass
from enum import Enum

class NavigationMode(Enum):
    """Navigation modes for the reader."""
    SCROLL = "scroll"  # Continuous scrolling (Phase 1 behavior)
    PAGE = "page"      # Discrete page navigation (Phase 2)

@dataclass
class ReadingPosition:
    """Represents a position within a book.

    Attributes:
        chapter_index: Zero-based chapter index.
        page_number: Zero-based page number within chapter (for page mode).
        scroll_offset: Exact scroll position in pixels (for precision).
        mode: Current navigation mode.
    """
    chapter_index: int
    page_number: int = 0
    scroll_offset: int = 0
    mode: NavigationMode = NavigationMode.SCROLL

    def __str__(self) -> str:
        """Human-readable position string."""
        if self.mode == NavigationMode.PAGE:
            return f"Chapter {self.chapter_index + 1}, Page {self.page_number + 1}"
        else:
            return f"Chapter {self.chapter_index + 1}, {self.scroll_offset}px"
```

#### 3. Position Persistence

**Location:** Extend `src/ereader/utils/settings.py` (new file)

**Responsibility:** Save/load reading positions and user preferences.

```python
from PyQt6.QtCore import QSettings
from ereader.models.reading_position import ReadingPosition, NavigationMode

class ReaderSettings:
    """Manages persistent settings for the e-reader."""

    def __init__(self) -> None:
        self._settings = QSettings("EReader", "EReaderApp")

    def save_reading_position(
        self,
        book_path: str,
        position: ReadingPosition
    ) -> None:
        """Save reading position for a book.

        Args:
            book_path: Path to the EPUB file (used as key).
            position: Reading position to save.
        """
        key = f"positions/{book_path}"
        self._settings.setValue(f"{key}/chapter", position.chapter_index)
        self._settings.setValue(f"{key}/page", position.page_number)
        self._settings.setValue(f"{key}/offset", position.scroll_offset)
        self._settings.setValue(f"{key}/mode", position.mode.value)
        self._settings.sync()

    def load_reading_position(self, book_path: str) -> ReadingPosition | None:
        """Load saved reading position for a book.

        Args:
            book_path: Path to the EPUB file.

        Returns:
            ReadingPosition if found, None otherwise.
        """
        key = f"positions/{book_path}"

        if not self._settings.contains(f"{key}/chapter"):
            return None

        chapter = self._settings.value(f"{key}/chapter", 0, type=int)
        page = self._settings.value(f"{key}/page", 0, type=int)
        offset = self._settings.value(f"{key}/offset", 0, type=int)
        mode_str = self._settings.value(f"{key}/mode", "scroll", type=str)
        mode = NavigationMode(mode_str)

        return ReadingPosition(
            chapter_index=chapter,
            page_number=page,
            scroll_offset=offset,
            mode=mode
        )

    def get_default_navigation_mode(self) -> NavigationMode:
        """Get user's preferred default navigation mode."""
        mode_str = self._settings.value("preferences/navigation_mode", "scroll", type=str)
        return NavigationMode(mode_str)

    def set_default_navigation_mode(self, mode: NavigationMode) -> None:
        """Set user's preferred default navigation mode."""
        self._settings.setValue("preferences/navigation_mode", mode.value)
        self._settings.sync()
```

### Modified Components

#### ReaderController Enhancements

**New State:**
```python
class ReaderController(QObject):
    def __init__(self) -> None:
        # ... existing state ...

        # Pagination state (NEW)
        self._pagination_engine = PaginationEngine()
        self._current_mode: NavigationMode = NavigationMode.SCROLL
        self._current_position: ReadingPosition = ReadingPosition(0)
        self._settings = ReaderSettings()
```

**New Signals:**
```python
# New signals for pagination
pagination_changed = pyqtSignal(int, int)  # current_page, total_pages
mode_changed = pyqtSignal(NavigationMode)  # navigation mode changed
```

**New Methods:**
```python
def toggle_navigation_mode(self) -> None:
    """Toggle between scroll and page modes."""
    if self._current_mode == NavigationMode.SCROLL:
        self._switch_to_page_mode()
    else:
        self._switch_to_scroll_mode()

def _switch_to_page_mode(self) -> None:
    """Switch to discrete page navigation."""
    self._current_mode = NavigationMode.PAGE

    # Calculate pages for current chapter
    self._recalculate_pages()

    # Update UI
    self.mode_changed.emit(NavigationMode.PAGE)
    self._emit_progress_update()

def _switch_to_scroll_mode(self) -> None:
    """Switch to continuous scroll navigation."""
    self._current_mode = NavigationMode.SCROLL

    # Update UI
    self.mode_changed.emit(NavigationMode.SCROLL)
    self._emit_progress_update()

def _recalculate_pages(self) -> None:
    """Recalculate page breaks for current chapter."""
    # Get content and viewport dimensions from BookViewer
    # Call pagination_engine.calculate_page_breaks()
    # Emit pagination_changed signal

def next_page(self) -> None:
    """Navigate to next page (page mode only)."""
    if self._current_mode != NavigationMode.PAGE:
        return

    # Get current page number
    # Increment and navigate

def previous_page(self) -> None:
    """Navigate to previous page (page mode only)."""
    # Similar to next_page

def on_viewport_resized(self, width: int, height: int) -> None:
    """Handle viewport resize - recalculate pages if needed."""
    if self._current_mode == NavigationMode.PAGE:
        # Store current position
        # Recalculate pages
        # Restore relative position
```

#### BookViewer Enhancements

**New Methods:**
```python
def get_content_height(self) -> int:
    """Get total height of rendered content."""
    return self._renderer.document().size().height()

def get_viewport_height(self) -> int:
    """Get height of visible viewport."""
    return self._renderer.viewport().height()

def set_scroll_position(self, position: int) -> None:
    """Set scroll position to specific pixel value."""
    scrollbar = self._renderer.verticalScrollBar()
    scrollbar.setValue(position)

def get_scroll_position(self) -> int:
    """Get current scroll position in pixels."""
    return self._renderer.verticalScrollBar().value()
```

#### NavigationBar Enhancements

**New UI Elements:**
```python
# Add mode toggle button
self._mode_toggle_button = QPushButton("Page Mode", self)
self._mode_toggle_button.clicked.connect(self.mode_toggle_requested.emit)

# Update button text based on mode
def update_mode_button(self, mode: NavigationMode) -> None:
    if mode == NavigationMode.PAGE:
        self._mode_toggle_button.setText("Scroll Mode")
    else:
        self._mode_toggle_button.setText("Page Mode")
```

#### MainWindow Enhancements

**Status Bar Updates:**
```python
def _on_progress_changed(self, progress: str) -> None:
    """Update status bar with mode-appropriate progress string."""
    # In scroll mode: "Chapter 3 of 15 • 45% through chapter"
    # In page mode:   "Page 12 of 45 in Chapter 3"

def _on_pagination_changed(self, current_page: int, total_pages: int) -> None:
    """Update status bar with page information (page mode)."""
    # Format and display page progress
```

**Keyboard Shortcuts:**
```python
# Add mode toggle shortcut
mode_toggle = QShortcut(QKeySequence("Ctrl+M"), self)
mode_toggle.activated.connect(self._controller.toggle_navigation_mode)

# Update arrow key behavior based on mode
# Page mode: Jump to next/previous page
# Scroll mode: Scroll by percentage (current behavior)
```

---

## Data Flow

### Page Mode Navigation Flow

```
User presses Right arrow (in Page mode)
    ↓
MainWindow shortcut detects key
    ↓
Controller.next_page() called
    ↓
Controller gets current page from pagination_engine.get_page_number(scroll_pos)
    ↓
Controller increments page number
    ↓
Controller gets scroll position: pagination_engine.get_scroll_position_for_page(new_page)
    ↓
Controller calls BookViewer.set_scroll_position(scroll_pos)
    ↓
BookViewer scrollbar changes, emits valueChanged
    ↓
BookViewer._on_scroll_changed() calculates new page number
    ↓
BookViewer emits scroll_position_changed(scroll_pos)
    ↓
Controller updates current_position
    ↓
Controller emits pagination_changed(current_page, total_pages)
    ↓
MainWindow updates status bar: "Page 12 of 45 in Chapter 3"
```

### Mode Toggle Flow

```
User presses Ctrl+M (or clicks Mode button)
    ↓
Controller.toggle_navigation_mode() called
    ↓
Controller checks current mode
    ↓
If switching to PAGE mode:
    ├─ Call _switch_to_page_mode()
    ├─ Get current scroll position from BookViewer
    ├─ Get content height and viewport height
    ├─ Call pagination_engine.calculate_page_breaks()
    ├─ Convert scroll position to page number
    ├─ Emit mode_changed(PAGE)
    └─ Emit pagination_changed(page, total_pages)
    ↓
If switching to SCROLL mode:
    ├─ Call _switch_to_scroll_mode()
    ├─ Emit mode_changed(SCROLL)
    └─ Emit reading_progress_changed(percentage_string)
    ↓
Views update based on new mode
    ├─ NavigationBar updates button text
    ├─ MainWindow updates status bar format
    └─ Keyboard shortcuts adjust behavior
```

### Window Resize in Page Mode

```
User resizes window
    ↓
BookViewer detects resize event
    ↓
Controller.on_viewport_resized(new_width, new_height) called
    ↓
If in PAGE mode:
    ├─ Get current scroll position (for restoration)
    ├─ Get current page number via pagination_engine
    ├─ Calculate new page breaks with new viewport height
    ├─ Calculate new scroll position that maintains relative position
    │  (e.g., if on page 3 of 10, stay on page 3 of new page count)
    ├─ Set new scroll position
    └─ Emit pagination_changed with new page count
```

---

## Implementation Plan

### Phase 2A: Basic Pagination Engine (Days 1-2)

**Goal:** Calculate page breaks and display page numbers.

**Tasks:**
1. Create `PaginationEngine` class
   - Implement `calculate_page_breaks()`
   - Implement `get_page_number()` and `get_scroll_position_for_page()`
   - Unit tests for all methods
2. Create `ReadingPosition` model
   - Dataclass with chapter, page, offset
   - Unit tests
3. Enhance `BookViewer`
   - Add `get_content_height()`, `get_viewport_height()`
   - Add `set_scroll_position()`, `get_scroll_position()`
4. Enhance `ReaderController`
   - Add `PaginationEngine` instance
   - Implement `_recalculate_pages()` on chapter load
   - Add `pagination_changed` signal
   - Update `_emit_progress_update()` to use page numbers when in page mode
5. Update `MainWindow`
   - Connect pagination signals
   - Update status bar to show page numbers
6. **Testing:**
   - Unit tests for `PaginationEngine`
   - Integration tests for page calculation
   - Manual testing with various chapter lengths

### Phase 2B: Page Navigation (Days 2-3)

**Goal:** Implement discrete page navigation.

**Tasks:**
1. Enhance `ReaderController`
   - Implement `next_page()` and `previous_page()` methods
   - Update keyboard shortcut routing based on mode
   - Handle boundary conditions (first/last page)
2. Update `MainWindow`
   - Modify arrow key shortcuts to use page navigation in page mode
   - Update navigation button connections
3. Enhance `NavigationBar`
   - Update button enabled/disabled logic for pages
4. **Testing:**
   - Unit tests for navigation logic
   - Integration tests for keyboard navigation
   - Manual testing: navigate through chapters in page mode

### Phase 2C: Mode Toggle (Day 3)

**Goal:** Allow user to switch between scroll and page modes.

**Tasks:**
1. Create `NavigationMode` enum
2. Enhance `ReaderController`
   - Add `_current_mode` state
   - Implement `toggle_navigation_mode()`
   - Implement `_switch_to_page_mode()` and `_switch_to_scroll_mode()`
   - Add `mode_changed` signal
3. Enhance `NavigationBar`
   - Add mode toggle button
   - Connect to controller
   - Update button text based on mode
4. Update `MainWindow`
   - Add Ctrl+M keyboard shortcut for mode toggle
   - Update navigation routing based on mode
5. **Testing:**
   - Unit tests for mode switching
   - Integration tests for UI updates on mode change
   - Manual testing: toggle modes while reading

### Phase 2D: Position Persistence (Day 4)

**Goal:** Save and restore reading positions.

**Tasks:**
1. Create `ReaderSettings` class
   - Implement `save_reading_position()` and `load_reading_position()`
   - Use QSettings for storage
2. Enhance `ReaderController`
   - Load position when opening book
   - Save position periodically and on close
   - Restore exact position (chapter, page, offset)
3. **Testing:**
   - Unit tests for settings persistence
   - Integration tests for position restoration
   - Manual testing: close/reopen book, verify position preserved

### Phase 2E: Window Resize Handling (Day 4-5)

**Goal:** Handle viewport resize gracefully in page mode.

**Tasks:**
1. Enhance `BookViewer`
   - Emit resize event signal
2. Enhance `ReaderController`
   - Implement `on_viewport_resized()`
   - Recalculate pages on resize
   - Maintain relative position (page number, not scroll pixels)
3. **Testing:**
   - Unit tests for resize logic
   - Integration tests for position preservation on resize
   - Manual testing: resize window, verify pages recalculate correctly

### Phase 2F: Polish and Edge Cases (Day 5)

**Goal:** Handle edge cases and improve UX.

**Tasks:**
1. Handle short chapters (< 1 viewport)
   - Display "Page 1 of 1" correctly
2. Handle very long chapters
   - Ensure page calculation doesn't hang (performance test)
3. Improve page break calculation
   - Optionally add small overlap (e.g., 50px) to prevent orphaned words
4. Add loading indicator for page calculation (if needed)
5. Documentation
   - Update user-facing documentation
   - Add code comments for complex logic
6. **Testing:**
   - Edge case testing (short chapters, long chapters)
   - Performance testing (large books)
   - Accessibility review
   - Final manual testing with diverse EPUBs

---

## Testing Strategy

### Unit Tests

**`tests/test_utils/test_pagination_engine.py`:**
```python
def test_calculate_page_breaks_single_page():
    """Test pagination when content fits in single viewport."""
    engine = PaginationEngine()
    breaks = engine.calculate_page_breaks(
        content_height=500,
        viewport_height=800
    )
    assert breaks.page_count == 1
    assert breaks.page_breaks == [0, 500]

def test_calculate_page_breaks_multiple_pages():
    """Test pagination with multiple pages."""
    engine = PaginationEngine()
    breaks = engine.calculate_page_breaks(
        content_height=2500,
        viewport_height=800
    )
    assert breaks.page_count == 4
    assert breaks.page_breaks == [0, 800, 1600, 2400, 2500]

def test_get_page_number_from_scroll():
    """Test converting scroll position to page number."""
    engine = PaginationEngine()
    engine.calculate_page_breaks(2500, 800)

    assert engine.get_page_number(0) == 0      # First page
    assert engine.get_page_number(400) == 0    # Middle of first page
    assert engine.get_page_number(800) == 1    # Second page
    assert engine.get_page_number(2400) == 3   # Last page

def test_get_scroll_position_for_page():
    """Test converting page number to scroll position."""
    engine = PaginationEngine()
    engine.calculate_page_breaks(2500, 800)

    assert engine.get_scroll_position_for_page(0) == 0
    assert engine.get_scroll_position_for_page(1) == 800
    assert engine.get_scroll_position_for_page(3) == 2400

def test_needs_recalculation():
    """Test detection of viewport resize."""
    engine = PaginationEngine()
    engine.calculate_page_breaks(2500, 800)

    assert not engine.needs_recalculation(800)  # Same height
    assert engine.needs_recalculation(900)      # Different height
```

**`tests/test_models/test_reading_position.py`:**
```python
def test_reading_position_creation():
    """Test creating a reading position."""
    pos = ReadingPosition(
        chapter_index=2,
        page_number=5,
        scroll_offset=1200,
        mode=NavigationMode.PAGE
    )
    assert pos.chapter_index == 2
    assert pos.page_number == 5

def test_reading_position_string_page_mode():
    """Test string representation in page mode."""
    pos = ReadingPosition(2, 5, mode=NavigationMode.PAGE)
    assert str(pos) == "Chapter 3, Page 6"

def test_reading_position_string_scroll_mode():
    """Test string representation in scroll mode."""
    pos = ReadingPosition(2, 0, 1200, NavigationMode.SCROLL)
    assert str(pos) == "Chapter 3, 1200px"
```

**`tests/test_utils/test_settings.py`:**
```python
def test_save_and_load_position():
    """Test saving and loading reading position."""
    settings = ReaderSettings()
    pos = ReadingPosition(2, 5, 1200, NavigationMode.PAGE)

    settings.save_reading_position("/path/to/book.epub", pos)
    loaded = settings.load_reading_position("/path/to/book.epub")

    assert loaded is not None
    assert loaded.chapter_index == 2
    assert loaded.page_number == 5
    assert loaded.scroll_offset == 1200
    assert loaded.mode == NavigationMode.PAGE
```

### Integration Tests

**`tests/test_integration/test_pagination_flow.py`:**
```python
def test_page_mode_navigation(qtbot):
    """Test navigating pages in page mode."""
    # Setup: Load book, switch to page mode
    # Action: Press Right arrow key
    # Assert: Page number increments, scroll position changes

def test_mode_toggle_preserves_position(qtbot):
    """Test that toggling modes preserves reading position."""
    # Setup: Navigate to middle of chapter
    # Action: Toggle scroll → page → scroll
    # Assert: Position roughly preserved

def test_window_resize_recalculates_pages(qtbot):
    """Test page recalculation on resize."""
    # Setup: Page mode, known page count
    # Action: Resize window
    # Assert: Page count changes, relative position preserved
```

### Manual Testing

**Scenarios:**
1. Navigate through entire book in page mode
2. Toggle between modes frequently
3. Resize window in page mode, verify position
4. Test with short chapters (< 1 page)
5. Test with very long chapters (100+ pages)
6. Save position, close, reopen, verify restoration
7. Test all keyboard shortcuts
8. Verify status bar updates correctly

---

## Performance Considerations

**Page Break Calculation:**
- Time complexity: O(n) where n = content_height / viewport_height
- Typical case: 5000px content / 800px viewport = ~6 pages = negligible (<1ms)
- Worst case: Very long chapter (50000px / 800px = 62 pages) = still <5ms
- **Acceptable:** Well under 100ms requirement

**Memory:**
- Page breaks array: ~8 bytes per int × 100 pages max = 800 bytes per chapter
- Current chapter only (not cached for all chapters)
- **Negligible impact:** << 1MB

**Resize Handling:**
- Recalculate on resize event (debounce with QTimer if too frequent)
- Target: <50ms for smooth UX

**Position Saving:**
- Save on chapter change and app close (not every scroll)
- QSettings writes to disk asynchronously
- No performance impact

---

## Consequences

### What This Enables ✅

1. **Stable Page Numbers:** Users can reference specific pages
2. **Discrete Navigation:** Arrow keys jump pages, not smooth scroll
3. **Position Persistence:** Save and restore exact reading position
4. **Mode Flexibility:** Users choose scroll vs. page based on preference
5. **Professional UX:** Closer to traditional e-reader experience
6. **Foundation for Future:** Architecture supports upgrading to true pagination later

### What This Constrains 📍

1. **Page Breaks:** May occur mid-paragraph (not perfect typography)
2. **Resize Behavior:** Page numbers change on window resize
   - Mitigated by recalculation and position restoration
3. **Not Kindle-Quality:** Doesn't match commercial e-readers exactly
4. **Viewport-Dependent:** Pages tied to window size, not universal
5. **EPUB-Only:** Pagination logic assumes HTML content

### What to Watch Out For ⚠️

1. **Performance with Very Long Chapters:**
   - Monitor page calculation time for 100+ page chapters
   - Add debouncing for resize events if needed

2. **Position Restoration Edge Cases:**
   - Window size changed since last session
   - Chapter content changed (book updated)
   - Handle gracefully with fallback to chapter start

3. **User Expectations:**
   - Users may expect "true" pages like Kindle
   - Document limitations clearly in UI/help

4. **Font Size Changes:**
   - If we add font customization later, must recalculate pages
   - Same logic as resize handling

5. **State Complexity:**
   - More controller state to manage (mode, pagination engine, position)
   - Keep tests comprehensive to catch state bugs

---

## Future Enhancements (Phase 3+)

**If we need true pagination later:**

1. **Upgrade to QWebEngineView (Option 3):**
   - Replace QTextBrowser with QWebEngineView
   - Use CSS paged media or JavaScript pagination libraries
   - PaginationEngine interface can stay the same
   - Controller logic mostly unchanged

2. **Smart Page Breaks:**
   - Avoid breaking mid-paragraph
   - Use heuristics (look for paragraph boundaries near page breaks)
   - More complex but better UX

3. **Pre-calculation and Caching:**
   - Calculate pages for all chapters on book open (background thread)
   - Cache page breaks per chapter
   - Faster navigation, no recalculation

4. **Reading Statistics:**
   - Track pages read per session
   - Estimate time remaining based on reading speed
   - "5 pages left in chapter" display

5. **Minimap / Page Thumbnails:**
   - Visual representation of pages
   - Quick jump to specific page

---

## Learning Value

**What you'll learn implementing this:**

1. **State Management:**
   - Managing multiple navigation modes
   - Coordinating state across controller and views
   - Handling state transitions cleanly

2. **QSettings for Persistence:**
   - Saving application state
   - Loading and restoring user data
   - Platform-independent settings storage

3. **Algorithm Design:**
   - Page break calculation
   - Scroll position ↔ page number conversion
   - Position preservation across recalculation

4. **Event Handling:**
   - Window resize events
   - Mode switching
   - Keyboard shortcut routing based on state

5. **User Preferences:**
   - Persisting user choices
   - Mode toggle patterns
   - Preference UI design

6. **Architecture Evolution:**
   - Extending existing MVC architecture
   - Adding features without breaking existing functionality
   - Maintaining backward compatibility (scroll mode still works)

This is an excellent learning feature: substantial enough to teach complex concepts, scoped enough to complete in reasonable time, and provides real user value.

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-05 | Initial architecture | Issue #31 - Design true pagination system |

---

## References

- **Issue #31:** True page-based pagination system
- **Issue #21:** Keyboard navigation (Phase 1 - Virtual pagination)
- **docs/architecture/keyboard-navigation-architecture.md:** Phase 1 design
- **docs/architecture/epub-rendering-architecture.md:** Current rendering architecture
- **Qt Documentation:**
  - [QTextDocument Pagination](https://doc.qt.io/qt-6/qtextdocument.html)
  - [QAbstractTextDocumentLayout](https://doc.qt.io/qt-6/qabstracttextdocumentlayout.html)
  - [QSettings Class](https://doc.qt.io/qt-6/qsettings.html)
- **Research Sources:**
  - [QTextDocument pages - Stack Overflow](https://stackoverflow.com/questions/15874129/how-to-access-qtextdocument-pages)
  - [Rich Text Layouts - Qt](https://doc.qt.io/qt-6/richtext-layouts.html)
