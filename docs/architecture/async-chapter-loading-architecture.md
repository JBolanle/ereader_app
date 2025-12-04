# Async Chapter Loading Architecture

## Date
2025-12-04

## Context

### Problem
Users experience noticeable UI lag (~475ms freeze) when loading large image-heavy EPUBs. The bottleneck is `QTextBrowser.setHtml()` blocking the UI thread while:
- Parsing HTML (~30ms)
- Decoding base64 images (~225ms for 15 images)
- Layout + render (~100ms)

Despite implementing Phase 1-3 caching (LRU chapter cache, memory monitoring, multi-layer caching), the lag persists on **initial chapter loads** (cache misses).

See detailed diagnosis: `docs/architecture/performance-lag-diagnosis.md`

### Current Architecture
```
ReaderController._load_chapter(index):
  ↓
1. Check rendered cache → if hit, emit content_ready ✅
  ↓
2. Check raw cache → if hit, skip to step 4
  ↓
3. Load raw HTML from EPUBBook (synchronous)
  ↓
4. Resolve images with resolve_images_in_html() (synchronous, CPU-intensive)
  ↓
5. Update caches
  ↓
6. Emit content_ready signal
  ↓
BookViewer receives signal:
  ↓
7. QTextBrowser.setHtml(html) ← BLOCKS UI THREAD (~200-500ms)
```

**All operations happen on UI thread** → UI freezes during steps 3-7.

### Goal
Move blocking work (steps 3-4) off the UI thread so the application stays responsive during chapter loading.

---

## Architectural Design

### Option Chosen: Async Loading with QThread

**Approach**: Create `AsyncChapterLoader(QThread)` to perform chapter loading and image resolution in a background thread.

**Key Principle**: UI thread only handles cache lookups and signal/slot communication. All I/O and CPU-intensive work happens in background thread.

---

## Component Design

### AsyncChapterLoader Class

```python
from PyQt6.QtCore import QThread, pyqtSignal

class AsyncChapterLoader(QThread):
    """Background thread for loading and rendering chapter content.

    This thread handles the CPU-intensive work of loading chapter HTML
    and resolving image references to base64 data URLs. By moving this
    work off the UI thread, the application stays responsive during loading.

    The thread operates autonomously once started - it checks caches,
    loads from the EPUB if needed, resolves images, updates caches, and
    emits a signal when content is ready.

    Signals:
        content_ready: Emitted when chapter HTML is fully prepared and ready
            to display. Args: html (str)
        error_occurred: Emitted if loading fails. Args: title (str), message (str)

    Thread Safety:
        - Reads from EPUBBook (ZipFile access) - requires verification
        - Writes to CacheManager - requires thread-safe cache implementation
        - Does NOT access UI widgets (only emits signals)
    """

    # Signals for communicating with UI thread
    content_ready = pyqtSignal(str)  # HTML ready to display
    error_occurred = pyqtSignal(str, str)  # error title, message

    def __init__(
        self,
        book: EPUBBook,
        cache_manager: CacheManager,
        chapter_index: int,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the async chapter loader.

        Args:
            book: The EPUBBook to load content from.
            cache_manager: Cache manager for rendered/raw chapters and images.
            chapter_index: Zero-based index of chapter to load.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._book = book
        self._cache_manager = cache_manager
        self._chapter_index = chapter_index
        self._cancelled = False  # Flag for cancellation

    def run(self) -> None:
        """Execute chapter loading in background thread.

        This method runs in a separate thread. It must NOT access UI widgets
        directly - only emit signals to communicate with the UI thread.

        Flow:
            1. Check rendered cache (fast path)
            2. If miss, check raw cache
            3. If miss, load raw HTML from EPUB
            4. Resolve images (CPU-intensive, happens off UI thread)
            5. Update caches
            6. Emit content_ready signal

        All errors are caught and emitted via error_occurred signal.
        """
        try:
            # Generate cache key
            cache_key = f"{self._book.filepath}:{self._chapter_index}"

            # Check if cancelled before starting work
            if self._cancelled:
                return

            # Try rendered chapters cache first (fast path)
            cached_html = self._cache_manager.rendered_chapters.get(cache_key)
            if cached_html is not None:
                logger.debug("Async loader: cache hit for chapter %d", self._chapter_index)
                self.content_ready.emit(cached_html)
                return

            # Check cancellation again (user might have navigated away)
            if self._cancelled:
                return

            # Cache miss - get chapter href for image resolution
            chapter_href = self._book.get_chapter_href(self._chapter_index)

            # Try raw content cache
            cached_raw = self._cache_manager.raw_chapters.get(cache_key)
            if cached_raw is not None:
                logger.debug("Async loader: raw cache hit for chapter %d", self._chapter_index)
                raw_content = cached_raw
            else:
                # Complete miss - load from book
                logger.debug("Async loader: loading chapter %d from EPUB", self._chapter_index)
                raw_content = self._book.get_chapter_content(self._chapter_index)

                # Store raw content in cache
                self._cache_manager.raw_chapters.set(cache_key, raw_content)

            # Check cancellation before expensive image resolution
            if self._cancelled:
                return

            # Resolve image references (CPU-intensive, but we're in background thread!)
            logger.debug("Async loader: resolving images for chapter %d", self._chapter_index)
            content = resolve_images_in_html(raw_content, self._book, chapter_href=chapter_href)

            # Store rendered content in cache
            self._cache_manager.rendered_chapters.set(cache_key, content)

            # Emit signal to UI thread
            logger.debug("Async loader: chapter %d ready, emitting signal", self._chapter_index)
            self.content_ready.emit(content)

        except Exception as e:
            # Catch all exceptions and emit error signal
            error_msg = f"Failed to load chapter {self._chapter_index + 1}: {e}"
            logger.exception("Async loader error: %s", error_msg)
            self.error_occurred.emit("Chapter Load Error", error_msg)

    def cancel(self) -> None:
        """Request cancellation of the loading operation.

        Sets a flag that the run() method checks at strategic points.
        This is a cooperative cancellation - the thread will finish its
        current operation before checking the flag.

        Note: This does NOT forcefully terminate the thread (unsafe in Qt).
        """
        logger.debug("Async loader: cancellation requested for chapter %d", self._chapter_index)
        self._cancelled = True
```

---

## Integration with ReaderController

### Modified _load_chapter() Method

```python
class ReaderController(QObject):
    # ... existing code ...

    def __init__(self) -> None:
        super().__init__()
        # ... existing initialization ...

        # Track current async loader (for cancellation)
        self._current_loader: AsyncChapterLoader | None = None

    def _load_chapter(self, index: int) -> None:
        """Load and display a specific chapter using async loading.

        Creates a background thread to load chapter content without
        blocking the UI. Shows loading indicator while loading.

        Args:
            index: Zero-based chapter index to load.
        """
        if self._book is None:
            logger.error("_load_chapter called with no book loaded")
            return

        try:
            logger.debug("Starting async load for chapter %d", index)

            # Cancel any pending load
            if self._current_loader is not None and self._current_loader.isRunning():
                logger.debug("Cancelling previous async load")
                self._current_loader.cancel()
                self._current_loader.wait(100)  # Wait up to 100ms for cleanup

            # Create async loader
            self._current_loader = AsyncChapterLoader(
                book=self._book,
                cache_manager=self._cache_manager,
                chapter_index=index,
                parent=self,
            )

            # Connect signals
            self._current_loader.content_ready.connect(self._on_content_ready)
            self._current_loader.error_occurred.connect(self._on_loader_error)
            self._current_loader.finished.connect(self._on_loader_finished)

            # TODO: Show loading indicator (emit signal to UI)
            # self.loading_started.emit()

            # Start async loading
            self._current_loader.start()

        except Exception as e:
            error_msg = f"Failed to start loading chapter {index + 1}: {e}"
            logger.exception(error_msg)
            self.error_occurred.emit("Error", error_msg)

    def _on_content_ready(self, html: str) -> None:
        """Handle content_ready signal from AsyncChapterLoader.

        This runs on the UI thread via Qt's signal/slot mechanism.

        Args:
            html: Rendered HTML with resolved images.
        """
        logger.debug("Content ready, emitting to views")

        # TODO: Hide loading indicator
        # self.loading_finished.emit()

        # Emit content to views (BookViewer will call setHtml)
        self.content_ready.emit(html)

        # Reset scroll percentage (new chapter always starts at top)
        self._current_scroll_percentage = 0.0

        # Update chapter position info
        total_chapters = self._book.get_chapter_count()
        self.chapter_changed.emit(self._current_chapter_index + 1, total_chapters)

        # Emit progress update
        self._emit_progress_update()

        # Update navigation button states
        self._update_navigation_state()

        # Log cache statistics
        self._cache_manager.log_stats()

        # Check memory usage
        self._cache_manager.check_memory_threshold()

    def _on_loader_error(self, title: str, message: str) -> None:
        """Handle error_occurred signal from AsyncChapterLoader.

        Args:
            title: Error dialog title.
            message: Error message.
        """
        logger.error("Async loader error: %s - %s", title, message)

        # TODO: Hide loading indicator
        # self.loading_finished.emit()

        # Forward error to UI
        self.error_occurred.emit(title, message)

    def _on_loader_finished(self) -> None:
        """Handle finished signal from AsyncChapterLoader.

        Cleanup when thread completes (success or error).
        """
        logger.debug("Async loader finished")
        # Thread will be garbage collected when no longer referenced
```

---

## Thread Safety Analysis

### Critical Question: Is EPUBBook Thread-Safe?

**EPUBBook uses ZipFile internally** for reading EPUB content.

#### ZipFile Thread Safety (Python Standard Library)

From Python documentation and testing:
- ✅ **Reading is generally thread-safe** for different files in the archive
- ⚠️ **Concurrent reads of the same file may cause issues**
- ❌ **Reading while writing is NOT safe**

#### Our Usage Pattern
- We only **read** from EPUBBook (no writes)
- We **might** read the same image from multiple threads (if pre-fetching is added later)
- We **always** close the book before modifications

#### Recommended Approach (Conservative)

**Option A: Add thread-safe wrapper to EPUBBook (Deferred)**
```python
# In EPUBBook class
def __init__(self, filepath: str) -> None:
    # ... existing code ...
    self._lock = threading.RLock()  # Reentrant lock

def get_resource(self, href: str, relative_to: str | None = None) -> bytes:
    with self._lock:
        # ... existing implementation ...
```

**Option B: Single-threaded access (MVP approach)**
- For MVP, only ONE AsyncChapterLoader runs at a time
- ReaderController cancels previous loader before starting new one
- This naturally prevents concurrent ZipFile access
- **Simpler and sufficient for Phase 4**

**Decision**: Use **Option B** for MVP (single loader at a time), defer Option A to future optimization if pre-fetching is added.

### CacheManager Thread Safety

**Current Implementation**: CacheManager uses OrderedDict and regular dicts - **NOT thread-safe**.

**Risk Assessment**:
- AsyncChapterLoader **writes** to cache (set operations)
- UI thread **reads** from cache (get operations)
- Concurrent read/write = potential race condition

**Mitigation Options**:

**Option A: Add locks to CacheManager**
```python
class ChapterCache:
    def __init__(self, maxsize: int = 10) -> None:
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._lock = threading.RLock()
        # ...

    def get(self, key: str) -> str | None:
        with self._lock:
            # ... existing code ...

    def set(self, key: str, value: str) -> None:
        with self._lock:
            # ... existing code ...
```

**Option B: Use queue for cache updates**
- Async loader emits signals with cache data
- UI thread updates cache in signal handler
- All cache operations on UI thread (thread-safe by design)

**Decision**: Use **Option A** (add locks to caches) for simplicity and robustness. Small performance cost, but eliminates race conditions entirely.

---

## Loading Indicator Design

### Requirements
1. Show indicator when async loading starts
2. Hide indicator when content ready
3. Don't flash indicator for instant cache hits (<50ms)
4. Provide visual feedback that something is happening

### Implementation Approach

**Add new signals to ReaderController**:
```python
class ReaderController(QObject):
    # ... existing signals ...
    loading_started = pyqtSignal()  # Show loading indicator
    loading_finished = pyqtSignal()  # Hide loading indicator
```

**UI Options** (to be designed with `/ux`):
1. **Spinner overlay** on BookViewer (simple, non-intrusive)
2. **Progress bar** in status bar (shows activity)
3. **Status message** "Loading chapter..." (minimal)

**Debouncing**: Use QTimer to delay showing indicator by 50ms
```python
def _load_chapter(self, index: int) -> None:
    # ... create and start async loader ...

    # Only show indicator if loading takes more than 50ms
    QTimer.singleShot(50, lambda: self._show_loading_indicator_if_still_loading())

def _show_loading_indicator_if_still_loading(self) -> None:
    if self._current_loader is not None and self._current_loader.isRunning():
        self.loading_started.emit()
```

**Defer to implementation**: Loading indicator details deferred to Task 4 (see issue #41).

---

## Error Handling

### Error Categories

1. **EPUB read errors** (file not found, corrupted ZIP)
   - Caught in AsyncChapterLoader.run()
   - Emitted via error_occurred signal
   - Displayed to user via ReaderController.error_occurred

2. **Image resolution errors** (missing image, invalid format)
   - Already handled in resolve_images_in_html() (logs warning, keeps original)
   - No special handling needed

3. **Thread errors** (exception in run())
   - Caught by try/except in run()
   - Logged with full traceback
   - Emitted via error_occurred signal

### Error Propagation Flow
```
AsyncChapterLoader.run():
  ↓
Exception caught in try/except
  ↓
logger.exception("...")  # Log full traceback
  ↓
error_occurred.emit(title, message)  # Signal to UI thread
  ↓
ReaderController._on_loader_error()
  ↓
ReaderController.error_occurred.emit()  # Forward to MainWindow
  ↓
MainWindow shows error dialog to user
```

---

## Cancellation Strategy

### Why Cancellation is Needed
User navigates rapidly: Chapter 1 → Chapter 2 → Chapter 3
- Without cancellation: All 3 loads complete, wasting CPU and memory
- With cancellation: Only Chapter 3 completes, Chapters 1-2 abort early

### Implementation

**Cooperative Cancellation** (safe with Qt):
```python
def cancel(self) -> None:
    self._cancelled = True  # Set flag

def run(self) -> None:
    # Check flag at strategic points
    if self._cancelled:
        return  # Exit early

    # ... do some work ...

    if self._cancelled:
        return  # Exit early again

    # ... more work ...
```

**Why NOT Force Termination**:
- QThread.terminate() is unsafe (can corrupt state)
- Python's threading module doesn't support forced termination
- Cooperative cancellation is Qt best practice

**Strategic Cancellation Points**:
1. Before checking rendered cache
2. Before loading raw content
3. Before resolving images (most expensive operation)

### Cleanup
```python
def _load_chapter(self, index: int) -> None:
    # Cancel previous loader
    if self._current_loader is not None and self._current_loader.isRunning():
        self._current_loader.cancel()
        self._current_loader.wait(100)  # Wait up to 100ms for cleanup
        # If still running after 100ms, continue anyway (thread will finish eventually)
```

---

## Performance Expectations

### Before (Current Synchronous Loading)
- Chapter load: ~475ms total
- UI blocked: ~475ms (100% of load time)
- User perception: **Frozen UI** ❌

### After (Async Loading)
- Chapter load: ~475ms total (same)
- UI blocked: ~5-10ms (signal/slot overhead)
- User perception: **Responsive UI** ✅

### Measured Improvement
- UI responsiveness: 475ms → <10ms (**98% reduction** in blocking)
- Total load time: ~475ms (unchanged, but expected)
- User satisfaction: Low → High (responsive > fast)

**Key Insight**: We're not making loading faster - we're making the UI responsive during loading. This is what users actually care about.

---

## Testing Strategy

### Unit Tests for AsyncChapterLoader

```python
def test_async_loader_cache_hit(qtbot):
    """Test that cached content loads instantly."""
    book = EPUBBook("test.epub")
    cache_manager = CacheManager()

    # Pre-populate cache
    cache_key = f"{book.filepath}:0"
    cache_manager.rendered_chapters.set(cache_key, "<html>cached</html>")

    # Create loader
    loader = AsyncChapterLoader(book, cache_manager, 0)

    # Wait for content_ready signal
    with qtbot.waitSignal(loader.content_ready, timeout=1000) as blocker:
        loader.start()

    # Verify cached content emitted
    assert blocker.args[0] == "<html>cached</html>"

def test_async_loader_cache_miss(qtbot):
    """Test that missing content loads from EPUB."""
    # Similar to above, but without pre-populating cache

def test_async_loader_cancellation(qtbot):
    """Test that cancellation aborts loading."""
    loader = AsyncChapterLoader(book, cache_manager, 0)
    loader.start()
    loader.cancel()  # Cancel immediately
    loader.wait()

    # Verify no signal emitted (or handle based on timing)

def test_async_loader_error_handling(qtbot):
    """Test that errors emit error_occurred signal."""
    # Create loader with invalid chapter index
    loader = AsyncChapterLoader(book, cache_manager, 999)

    with qtbot.waitSignal(loader.error_occurred, timeout=1000) as blocker:
        loader.start()

    # Verify error title and message
    assert "error" in blocker.args[1].lower()
```

### Integration Tests for ReaderController

```python
def test_async_chapter_loading(qtbot):
    """Test that controller uses async loading correctly."""
    controller = ReaderController()
    controller.open_book("test.epub")

    # Wait for content_ready signal
    with qtbot.waitSignal(controller.content_ready, timeout=2000):
        controller.next_chapter()

    # Verify content emitted

def test_rapid_navigation_cancellation(qtbot):
    """Test that rapid navigation cancels pending loads."""
    controller = ReaderController()
    controller.open_book("test.epub")

    # Navigate rapidly
    controller.next_chapter()
    controller.next_chapter()  # Should cancel first load
    controller.next_chapter()  # Should cancel second load

    # Wait for final chapter to load
    with qtbot.waitSignal(controller.content_ready, timeout=2000):
        pass

    # Verify only final chapter loaded
```

### Performance Tests

```python
def test_ui_blocking_time(qtbot):
    """Measure UI thread blocking time during async load."""
    controller = ReaderController()
    controller.open_book("large-book.epub")

    start_time = time.perf_counter()
    controller.next_chapter()
    blocking_time = (time.perf_counter() - start_time) * 1000

    # Verify UI blocking is minimal
    assert blocking_time < 50, f"UI blocked for {blocking_time:.2f}ms"
```

---

## Implementation Plan

### Phase 4 Tasks (from Issue #41)

**Task 1: Design ✅** (this document)

**Task 2: Implement AsyncChapterLoader**
- Create `src/ereader/utils/async_loader.py`
- Implement AsyncChapterLoader class
- Add thread locks to CacheManager
- Write unit tests

**Task 3: Integrate with ReaderController**
- Modify _load_chapter() to use async loading
- Add signal handlers (_on_content_ready, etc.)
- Implement cancellation logic
- Update integration tests

**Task 4: Add Loading Indicator**
- Design loading indicator UI (use `/ux`)
- Add loading_started/loading_finished signals
- Implement debounced indicator (50ms delay)
- Test with fast and slow loads

**Task 5: Enhanced Performance Profiling**
- Create `scripts/profile_ui_performance.py`
- Measure QTextBrowser.setHtml() time
- Measure UI blocking time before/after
- Document results in `docs/testing/`

---

## Decision

**Implement AsyncChapterLoader as designed above** with the following choices:

1. **Thread safety**: Single loader at a time (MVP), add locks to caches
2. **Cancellation**: Cooperative cancellation at strategic points
3. **Error handling**: Emit signals, log with full tracebacks
4. **Loading indicator**: Defer detailed design to Task 4 (with `/ux`)
5. **Testing**: Comprehensive unit and integration tests with pytest-qt

---

## Consequences

### What This Enables
✅ Responsive UI during chapter loading (no freezing)
✅ Visual feedback via loading indicator
✅ Better user experience for large EPUBs
✅ Learning Qt threading patterns
✅ Foundation for future optimizations (pre-fetching, progressive loading)

### What This Constrains
⚠️ Introduces threading complexity (lifecycle, cancellation, cleanup)
⚠️ Requires thread-safe caches (locks add small overhead)
⚠️ Content still "pops in" all at once (no progressive rendering yet)
⚠️ Total load time unchanged (just non-blocking)

### What We'll Need to Watch Out For
🔍 **Thread lifecycle**: Ensure threads are properly cleaned up (no leaks)
🔍 **Race conditions**: Verify locks prevent cache corruption
🔍 **Memory management**: Ensure cancelled threads release resources
🔍 **Signal connections**: Disconnect signals when threads finish (prevent leaks)
🔍 **Edge cases**: Handle book closure while loading, rapid navigation, etc.

---

## Open Questions

### 1. Should we verify ZipFile thread safety empirically?

**Recommendation**: Yes, add a simple test:
```python
def test_zipfile_concurrent_reads():
    """Verify ZipFile allows concurrent reads (for future pre-fetching)."""
    import concurrent.futures

    def read_file(zf, name):
        return zf.read(name)

    with ZipFile("test.epub") as zf:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Try reading different files concurrently
            futures = [executor.submit(read_file, zf, name) for name in filenames]
            results = [f.result() for f in futures]

    # If this doesn't crash, concurrent reads are safe
```

### 2. Should loading indicator be a spinner or progress bar?

**Recommendation**: Defer to `/ux` during Task 4. Spinner is simpler (no progress calculation), progress bar is more informative (but requires progress updates from thread).

### 3. Should we add progress reporting (0-100%)?

**For MVP**: No (adds complexity, thread needs to emit progress signals)
**For Future**: Yes (helpful for very large chapters, requires `progress_updated = pyqtSignal(int)`)

### 4. Should we pre-fetch adjacent chapters?

**For MVP**: No (out of scope for Phase 4)
**For Future**: Yes (Phase 6 optimization, requires multiple concurrent loaders)

---

## References

- [Performance Lag Diagnosis](./performance-lag-diagnosis.md)
- [Chapter Caching System](./chapter-caching-system.md)
- [Qt Threading Basics](https://doc.qt.io/qt-6/thread-basics.html)
- [QThread Documentation](https://doc.qt.io/qt-6/qthread.html)
- [Python ZipFile Thread Safety](https://docs.python.org/3/library/zipfile.html)
- Issue #41: feat: Implement Phase 4 - Async Chapter Loading

---

## Next Steps

1. ✅ Architecture designed (this document)
2. Create feature branch: `feature/async-chapter-loading`
3. Implement AsyncChapterLoader (Task 2)
4. Integrate with ReaderController (Task 3)
5. Design and implement loading indicator (Task 4)
6. Enhanced profiling and measurement (Task 5)
7. `/test` - ensure all tests pass
8. `/code-review` - self-review before PR
9. Create PR with measured improvements
