# Enhanced Keyboard Navigation Architecture (Phase 1)

## Date
2025-12-03

## Context

We need to implement enhanced keyboard navigation to improve the reading experience:
- Left/Right arrows to navigate between chapters
- Up/Down/PageUp/PageDown to scroll within chapters
- Home/End to jump to chapter top/bottom
- Progress indicator showing position within chapter

**UX Requirements:**
- Arrow keys scroll by ~50% viewport (preserves reading context)
- Page Up/Down scroll by 100% viewport (traditional page flip)
- Home/End scroll instantly (standard desktop behavior)
- Progress display: "Chapter X of Y • Z% through chapter"
- Smooth experience with no jarring jumps

**Current Architecture:**
- MVC pattern with Protocol-based interfaces
- ReaderController owns all reading state (book, chapter position)
- BookViewer wraps QTextBrowser for HTML rendering
- MainWindow coordinates views and connects signals
- NavigationBar provides button-based navigation

## Design Decisions

### 1. Where Should Scroll Methods Live?

**Decision:** BookViewer

**Rationale:**
- BookViewer wraps QTextBrowser and owns the scrollbar
- Controller should not know about view implementation details
- Follows single responsibility principle (view handles display, controller handles state)
- Allows future swap to different rendering widget without changing controller

### 2. How Should Progress Tracking Work?

**Decision:** Signal-based communication from BookViewer → Controller → MainWindow

**Rationale:**
- Follows existing signal/slot pattern in codebase
- Controller formats the progress string (owns chapter state)
- MainWindow just displays formatted string (stateless view)
- BookViewer emits low-level scroll percentage
- Controller combines chapter info + scroll percentage into user-facing string

**Flow:**
```
User scrolls
    ↓
BookViewer detects scroll (valueChanged signal)
    ↓
BookViewer.scroll_position_changed(percentage) emitted
    ↓
ReaderController._on_scroll_changed(percentage) slot
    ↓
ReaderController.reading_progress_changed(formatted_string) emitted
    ↓
MainWindow updates status bar
```

### 3. Where Should Keyboard Shortcuts Be Defined?

**Decision:** MainWindow

**Rationale:**
- MainWindow already defines menu shortcuts (Ctrl+O, Ctrl+Q)
- Consistent location for all keyboard bindings
- MainWindow owns both controller and views, can route to appropriate target
- Chapter navigation → Controller methods
- Scroll navigation → BookViewer methods

### 4. Should We Implement Smooth Scrolling Animations?

**Decision:** No, not in Phase 1 (defer to future enhancement)

**Rationale:**
- Instant scrolling with 50% overlap provides "smooth experience" via context preservation
- Animation requires QPropertyAnimation complexity
- YAGNI - ship MVP faster, measure if users request smooth animation
- UX design's "smooth scrolling" primarily refers to no jarring jumps (achieved by 50% scroll)
- Can add animations later without breaking API

### 5. Should Scroll Position Be Persisted Per Chapter?

**Decision:** No, not in Phase 1

**Rationale:**
- UX design mentioned it but marked as "optional"
- Adds complexity (controller stores scroll state per chapter)
- Not critical for MVP reading experience
- Always starting at top is acceptable behavior for Phase 1
- Can add in Phase 2 with true pagination

## Component Design

### BookViewer Enhancements

**New Signal:**
```python
from PyQt6.QtCore import pyqtSignal

class BookViewer(QWidget):
    # Signals
    scroll_position_changed = pyqtSignal(float)  # percentage 0-100
```

**New Methods:**
```python
def scroll_by_pages(self, pages: float) -> None:
    """Scroll by a number of pages (viewport heights).

    Args:
        pages: Number of pages to scroll. Positive = down, negative = up.
               Examples: 0.5 = half page down, -1.0 = full page up, 1.0 = page down.

    Implementation:
        - Get scrollbar and pageStep (viewport height)
        - Calculate new position: current + (pages * pageStep)
        - Clamp to valid range [minimum, maximum]
        - Set new value
        - Signal emitted automatically via valueChanged connection
    """

def scroll_to_top(self) -> None:
    """Scroll to the top of the chapter.

    Implementation:
        - Set scrollbar value to minimum() (usually 0)
    """

def scroll_to_bottom(self) -> None:
    """Scroll to the bottom of the chapter.

    Implementation:
        - Set scrollbar value to maximum()
    """

def get_scroll_percentage(self) -> float:
    """Get current scroll position as a percentage (0-100).

    Returns:
        Float from 0.0 to 100.0 representing scroll position.
        0.0 = at top, 100.0 = at bottom.
        If content is not scrollable (fits in viewport), returns 0.0.

    Implementation:
        scrollbar = self._renderer.verticalScrollBar()
        value = scrollbar.value()
        minimum = scrollbar.minimum()
        maximum = scrollbar.maximum()

        if maximum == minimum:  # Not scrollable
            return 0.0

        percentage = ((value - minimum) / (maximum - minimum)) * 100.0
        return percentage
    """
```

**Connection Setup (in `__init__`):**
```python
def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)
    # ... existing setup ...

    # Connect scrollbar changes to emit our signal
    self._renderer.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

def _on_scroll_changed(self) -> None:
    """Handle scroll position changes and emit signal."""
    percentage = self.get_scroll_percentage()
    self.scroll_position_changed.emit(percentage)
```

**Important Notes:**
- QTextBrowser content changes (set_content) also trigger valueChanged
- Emit signal on content changes too (scroll resets to top = 0%)
- Signal emitted for both programmatic and user-initiated scrolling

### ReaderController Enhancements

**New Signal:**
```python
reading_progress_changed = pyqtSignal(str)  # formatted progress string
```

**New State Variable:**
```python
def __init__(self) -> None:
    super().__init__()
    # ... existing state ...
    self._current_scroll_percentage: float = 0.0
```

**New Methods:**
```python
def _on_scroll_changed(self, percentage: float) -> None:
    """Handle scroll position changes from BookViewer.

    Args:
        percentage: Scroll position from 0-100.
    """
    logger.debug("Scroll position changed: %.1f%%", percentage)
    self._current_scroll_percentage = percentage
    self._emit_progress_update()

def _emit_progress_update(self) -> None:
    """Emit formatted reading progress string."""
    if self._book is None:
        return

    current = self._current_chapter_index + 1  # 1-based for display
    total = self._book.get_chapter_count()
    scroll_pct = self._current_scroll_percentage

    progress = f"Chapter {current} of {total} • {scroll_pct:.0f}% through chapter"
    logger.debug("Emitting progress update: %s", progress)
    self.reading_progress_changed.emit(progress)
```

**Modified Methods:**
```python
def _load_chapter(self, index: int) -> None:
    # ... existing chapter loading logic ...

    # After successful load:
    # Reset scroll percentage (new chapter always starts at top)
    self._current_scroll_percentage = 0.0

    # Emit progress update (replaces old chapter_changed for status bar)
    self._emit_progress_update()

    # Still emit chapter_changed for other potential listeners
    total_chapters = self._book.get_chapter_count()
    self.chapter_changed.emit(index + 1, total_chapters)
```

**Note:** We keep `chapter_changed` signal for backward compatibility and potential future use, but status bar will use `reading_progress_changed` instead.

### MainWindow Enhancements

**New Method:**
```python
def _setup_keyboard_shortcuts(self) -> None:
    """Create and configure keyboard shortcuts for navigation."""
    logger.debug("Setting up keyboard shortcuts")

    # Chapter navigation (Left/Right arrows)
    left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
    left_shortcut.activated.connect(self._controller.previous_chapter)

    right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
    right_shortcut.activated.connect(self._controller.next_chapter)

    # Within-chapter scrolling (Up/Down arrows - 50% viewport)
    up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
    up_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(-0.5))

    down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
    down_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(0.5))

    # Page scrolling (PageUp/PageDown - 100% viewport)
    page_up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
    page_up_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(-1.0))

    page_down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
    page_down_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(1.0))

    # Jump to top/bottom (Home/End)
    home_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Home), self)
    home_shortcut.activated.connect(self._book_viewer.scroll_to_top)

    end_shortcut = QShortcut(QKeySequence(Qt.Key.Key_End), self)
    end_shortcut.activated.connect(self._book_viewer.scroll_to_bottom)

    logger.debug("Keyboard shortcuts configured")
```

**Modified/New Connection Setup:**
```python
def _setup_controller_connections(self) -> None:
    """Connect controller signals to view slots."""
    logger.debug("Setting up controller signal connections")

    # ... existing connections ...

    # Connect book viewer scroll events to controller
    self._book_viewer.scroll_position_changed.connect(self._controller._on_scroll_changed)

    # Connect controller progress updates to status bar
    self._controller.reading_progress_changed.connect(self._on_progress_changed)

    logger.debug("Controller connections established")
```

**New Slot:**
```python
def _on_progress_changed(self, progress: str) -> None:
    """Handle reading_progress_changed signal from controller.

    Updates the status bar with formatted progress string.

    Args:
        progress: Formatted progress string (e.g., "Chapter 3 of 15 • 45% through chapter").
    """
    logger.debug("Progress changed: %s", progress)

    status_bar = self.statusBar()
    if status_bar is not None:
        status_bar.showMessage(progress)
```

**Modified `__init__`:**
```python
def __init__(self) -> None:
    super().__init__()
    # ... existing setup ...

    self._setup_controller_connections()
    self._setup_menu_bar()
    self._setup_status_bar()
    self._setup_keyboard_shortcuts()  # NEW

    logger.debug("MainWindow initialized successfully")
```

**Note:** Can remove or keep `_on_chapter_changed()` method. If kept, it will still be called but status bar update will be redundant (progress signal updates it already). Recommend keeping for now (doesn't hurt) and potentially removing later.

## Data Flow Diagrams

### Chapter Navigation Flow (Left/Right Arrow)

```
User presses Left arrow
    ↓
MainWindow QShortcut detects key
    ↓
MainWindow calls controller.previous_chapter()
    ↓
Controller updates _current_chapter_index
    ↓
Controller calls _load_chapter()
    ↓
Controller emits content_ready signal
    ↓
BookViewer.set_content() called
    ↓
QTextBrowser content changes, scroll resets to top
    ↓
QScrollBar.valueChanged signal fires
    ↓
BookViewer._on_scroll_changed() called
    ↓
BookViewer emits scroll_position_changed(0.0)
    ↓
Controller._on_scroll_changed(0.0) called
    ↓
Controller sets _current_scroll_percentage = 0.0
    ↓
Controller calls _emit_progress_update()
    ↓
Controller emits reading_progress_changed("Chapter 2 of 15 • 0% through chapter")
    ↓
MainWindow._on_progress_changed() called
    ↓
Status bar updated
```

### Scroll Navigation Flow (Down Arrow)

```
User presses Down arrow
    ↓
MainWindow QShortcut detects key
    ↓
MainWindow calls book_viewer.scroll_by_pages(0.5)
    ↓
BookViewer calculates new scroll position
    ↓
BookViewer sets scrollbar value
    ↓
QScrollBar.valueChanged signal fires
    ↓
BookViewer._on_scroll_changed() called
    ↓
BookViewer calculates percentage with get_scroll_percentage()
    ↓
BookViewer emits scroll_position_changed(e.g., 23.5)
    ↓
Controller._on_scroll_changed(23.5) called
    ↓
Controller sets _current_scroll_percentage = 23.5
    ↓
Controller calls _emit_progress_update()
    ↓
Controller emits reading_progress_changed("Chapter 3 of 15 • 24% through chapter")
    ↓
MainWindow._on_progress_changed() called
    ↓
Status bar updated
```

### Manual Scroll Flow (Mouse Wheel / Scrollbar Drag)

```
User scrolls with mouse wheel
    ↓
QTextBrowser handles scroll event
    ↓
QScrollBar value changes
    ↓
QScrollBar.valueChanged signal fires
    ↓
[Same flow as Scroll Navigation above from this point]
```

## Edge Cases and Boundary Handling

### At Chapter Boundaries

**First chapter + Left arrow:**
- Controller checks `_current_chapter_index > 0` before decrementing
- No action taken (silent failure)
- No error message (follows physical book analogy)

**Last chapter + Right arrow:**
- Controller checks `_current_chapter_index < max` before incrementing
- No action taken (silent failure)
- No error message

**Already implemented in existing code** - no changes needed.

### At Scroll Boundaries

**At top + Up arrow / Page Up:**
- BookViewer calculates: `new_value = current + (-0.5 * pageStep)`
- new_value is clamped to `scrollbar.minimum()` (0)
- Setting value to current value triggers no signal if unchanged
- No visible effect, no error

**At bottom + Down arrow / Page Down:**
- BookViewer calculates: `new_value = current + (0.5 * pageStep)`
- new_value is clamped to `scrollbar.maximum()`
- Same clamping behavior

**Implementation detail:** Use Python's `max()` and `min()` to clamp:
```python
new_value = max(minimum, min(maximum, calculated_value))
```

### Content Shorter Than Viewport

**Short chapter (no scrolling needed):**
- `scrollbar.maximum()` == `scrollbar.minimum()`
- `get_scroll_percentage()` returns 0.0 (check for zero division)
- Scroll methods do nothing (value unchanged)
- Progress shows "0% through chapter" (technically correct)

### Percentage Rounding

**Display precision:**
- Format with `{percentage:.0f}%` (no decimal places)
- Example: 23.7% displays as "24%"
- Acceptable for user-facing progress indicator

## Testing Strategy

### Unit Tests

**BookViewer Tests** (`tests/test_views/test_book_viewer.py`):
```python
def test_scroll_by_pages_down():
    """Test scrolling down by pages."""
    # Setup: viewer with scrollable content
    # Action: scroll_by_pages(0.5)
    # Assert: scrollbar value increased by ~50% of pageStep

def test_scroll_by_pages_up():
    """Test scrolling up by pages."""
    # Similar to above, negative value

def test_scroll_to_top():
    """Test jump to top."""
    # Setup: scroll to middle
    # Action: scroll_to_top()
    # Assert: scrollbar.value() == scrollbar.minimum()

def test_scroll_to_bottom():
    """Test jump to bottom."""
    # Setup: scroll to middle
    # Action: scroll_to_bottom()
    # Assert: scrollbar.value() == scrollbar.maximum()

def test_get_scroll_percentage_at_top():
    """Test percentage calculation at top."""
    # Assert: get_scroll_percentage() == 0.0

def test_get_scroll_percentage_at_bottom():
    """Test percentage calculation at bottom."""
    # Assert: get_scroll_percentage() == 100.0

def test_get_scroll_percentage_no_scroll():
    """Test percentage when content fits viewport."""
    # Setup: short content
    # Assert: get_scroll_percentage() == 0.0

def test_scroll_position_changed_signal_emitted():
    """Test signal emission on scroll."""
    # Setup: spy on signal
    # Action: scroll_by_pages(0.5)
    # Assert: signal emitted with correct percentage

def test_scroll_boundary_clamp_top():
    """Test scrolling past top is clamped."""
    # Setup: at top
    # Action: scroll_by_pages(-1.0)
    # Assert: still at top, no error

def test_scroll_boundary_clamp_bottom():
    """Test scrolling past bottom is clamped."""
    # Setup: at bottom
    # Action: scroll_by_pages(1.0)
    # Assert: still at bottom, no error
```

**ReaderController Tests** (`tests/test_controllers/test_reader_controller.py`):
```python
def test_on_scroll_changed_updates_percentage():
    """Test scroll change updates internal state."""
    # Action: controller._on_scroll_changed(45.5)
    # Assert: controller._current_scroll_percentage == 45.5

def test_on_scroll_changed_emits_progress_signal():
    """Test scroll change emits formatted progress."""
    # Setup: book loaded, chapter 3 of 10
    # Action: controller._on_scroll_changed(45.5)
    # Assert: reading_progress_changed signal emitted with "Chapter 3 of 10 • 46% through chapter"

def test_emit_progress_update_formats_correctly():
    """Test progress string formatting."""
    # Setup: chapter 1 of 5, scroll 0%
    # Action: controller._emit_progress_update()
    # Assert: "Chapter 1 of 5 • 0% through chapter"

def test_load_chapter_resets_scroll_percentage():
    """Test chapter load resets scroll to 0%."""
    # Setup: scroll at 50%
    # Action: controller.next_chapter()
    # Assert: _current_scroll_percentage == 0.0

def test_progress_update_on_chapter_load():
    """Test progress emitted when chapter loads."""
    # Setup: spy on reading_progress_changed signal
    # Action: load chapter
    # Assert: signal emitted with 0% scroll
```

### Integration Tests

**Keyboard Shortcuts Tests** (potentially `tests/test_integration/test_keyboard_navigation.py`):
```python
def test_left_arrow_changes_chapter():
    """Test Left arrow navigates to previous chapter."""
    # Setup: QTest.keyPress() on main window
    # Assert: chapter changed in controller

def test_right_arrow_changes_chapter():
    """Test Right arrow navigates to next chapter."""

def test_down_arrow_scrolls_viewer():
    """Test Down arrow scrolls book viewer."""
    # Setup: get initial scroll position
    # Action: QTest.keyPress(Qt.Key.Key_Down)
    # Assert: scroll position increased

def test_page_down_scrolls_full_page():
    """Test PageDown scrolls by full viewport."""

def test_home_jumps_to_top():
    """Test Home key jumps to chapter top."""

def test_end_jumps_to_bottom():
    """Test End key jumps to chapter bottom."""
```

**Signal Flow Tests:**
```python
def test_scroll_updates_status_bar():
    """Test scrolling updates status bar via signal chain."""
    # Setup: load book, spy on status bar
    # Action: trigger scroll
    # Assert: status bar text includes percentage
```

### Manual Testing Checklist

See UX design document for comprehensive manual testing checklist. Key scenarios:
- All keyboard shortcuts work as expected
- Boundary conditions don't cause errors
- Progress indicator updates in real-time
- Works with short, medium, and long chapters
- Window resize doesn't break scroll percentage

## Performance Considerations

**Signal Emission Frequency:**
- `scroll_position_changed` emits on every scroll value change
- Could emit frequently during mouse wheel scrolling
- Impact: Negligible (just updating a status bar label)
- If performance issues arise: Debounce with QTimer

**Scroll Percentage Calculation:**
- Called on every scroll event
- Simple arithmetic: `(value - min) / (max - min) * 100`
- Impact: Negligible

**Chapter Cache:**
- Existing LRU cache (10 chapters) handles performance
- Scroll state not cached in Phase 1 (always start at top)

## Future Enhancements (Phase 2)

**True Pagination:**
- Calculate actual pages based on viewport size and content
- Display "Page X of Y" instead of percentage
- Store page boundaries, not just scroll positions
- See Issue #31 for details

**Scroll Position Persistence:**
- Store scroll percentage per chapter in controller
- Return to saved position when navigating back
- Clear on book close

**Smooth Scroll Animations:**
- Use QPropertyAnimation on scrollbar value
- Animate from current to target position over 200-300ms
- Easing curve for natural feel

**Configurable Scroll Amounts:**
- User setting for arrow key scroll amount
- Options: 25%, 50%, 75%, or line-based scrolling

## Consequences

**What this enables:**
- Complete keyboard-only reading experience
- Better accessibility for keyboard users
- More precise reading position feedback
- Foundation for future pagination system

**What this constrains:**
- Status bar format is now "Chapter X of Y • Z% through chapter"
- BookViewer must emit scroll signals (coupling to MainWindow via Controller)
- Arrow keys reserved for navigation (can't be used for other features)

**What to watch out for:**
- Signal performance if scroll events are too frequent
- Scroll percentage accuracy with different font sizes / content types
- Potential conflicts if adding other keyboard shortcuts later
- Ensuring tests don't become brittle with percentage assertions (use ranges)

## Implementation Order

**Recommended sequence:**

1. **BookViewer scroll methods** (independent, testable)
   - Add signal
   - Implement `scroll_by_pages()`, `scroll_to_top()`, `scroll_to_bottom()`
   - Implement `get_scroll_percentage()`
   - Connect scrollbar signal
   - Write unit tests

2. **ReaderController progress tracking** (independent, testable)
   - Add signal and state variable
   - Implement `_on_scroll_changed()` and `_emit_progress_update()`
   - Modify `_load_chapter()` to reset and emit
   - Write unit tests

3. **MainWindow integration** (wires everything together)
   - Add `_setup_keyboard_shortcuts()`
   - Add `_on_progress_changed()` slot
   - Modify `_setup_controller_connections()`
   - Call setup in `__init__`
   - Write integration tests

4. **Manual testing and iteration**
   - Test all keyboard shortcuts
   - Test boundary conditions
   - Test various chapter lengths
   - Adjust scroll amounts if needed

**Estimated effort:** 4-6 hours (matches issue estimate)
- Step 1: 2 hours
- Step 2: 1 hour
- Step 3: 1 hour
- Step 4: 1-2 hours

## Learning Value

**What you'll learn implementing this:**

1. **Qt Signals and Slots:**
   - Creating custom signals
   - Connecting signal chains across components
   - Understanding signal emission timing

2. **QScrollBar API:**
   - Getting/setting scroll position
   - Understanding min/max/value/pageStep
   - valueChanged signal behavior

3. **QShortcut System:**
   - Creating keyboard shortcuts without menu items
   - QKeySequence and Qt.Key enums
   - Connecting shortcuts to lambda functions

4. **MVC Signal Flow:**
   - How views communicate with controller
   - How controller owns business logic (formatting)
   - How MainWindow stays stateless

5. **Testing Qt Widgets:**
   - Mocking scrollbar behavior
   - Using QSignalSpy for signal testing
   - Simulating keyboard input with QTest

6. **Progressive Enhancement:**
   - Shipping Phase 1 quickly (scroll-based)
   - Planning Phase 2 (pagination)
   - Balancing perfect vs. good enough

This is a great learning feature: non-trivial but well-scoped, touches multiple layers, teaches Qt fundamentals.
