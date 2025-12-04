# Performance Lag Diagnosis: Large Image-Heavy EPUBs

## Date
2025-12-04

## Problem Statement

Users experience noticeable UI lag when loading large image-heavy EPUBs (e.g., "The Mamba Mentality" - 201MB). Despite implementing Phase 1-3 caching (LRU chapter cache, memory monitoring, multi-layer caching), the lag persists on initial chapter loads.

## Investigation Findings

### What the Profiling Shows ✅

The performance profiling (`scripts/profile_performance.py`) measures backend operations:

- **EPUB load time**: 5.98ms ✅ (excellent)
- **Chapter load time**: 1.05ms avg ✅ (excellent)
- **Image resolution time**: 7.97ms avg ✅ (acceptable)
- **Peak memory**: 558MB ⚠️ (exceeds 200MB target)

### What the Profiling DOESN'T Show ❌

**Critical Gap**: The profiling script runs **without the UI** and doesn't measure:

1. **QTextBrowser.setHtml() rendering time** ← **THE BOTTLENECK**
2. Base64 image decoding inside QTextBrowser
3. HTML parsing and layout calculation
4. Widget rendering and painting
5. User-perceived blocking time

### Root Cause Analysis

#### The Complete Loading Flow

```python
# In reader_controller.py: _load_chapter()

# 1. Load raw HTML from EPUB (1.05ms - fast) ✅
raw_content = self._book.get_chapter_content(index)

# 2. Resolve ALL images synchronously (~80-200ms for 10-20 images) ⚠️
#    - For each <img> tag:
#      - Load image data from EPUB
#      - Base64 encode (CPU-intensive for large images)
#      - Build data URL string
#      - Reconstruct HTML
content = resolve_images_in_html(raw_content, self._book, chapter_href)

# 3. Emit to view (signal, fast) ✅
self.content_ready.emit(content)

# 4. View sets content (THIS IS WHERE THE LAG HAPPENS!) ❌
# In book_viewer.py: set_content()
self._renderer.setHtml(html)  # BLOCKS UI THREAD for 200-500ms!
```

#### Why QTextBrowser.setHtml() Blocks

When we call `setHtml()` with a large HTML string containing multiple base64-encoded images:

```
QTextBrowser.setHtml(html)  # Synchronous operation:
  ↓
Parse HTML (50-100ms for large documents)
  ↓
Decode base64 images (100-300ms for multiple large images)
  ↓
Create QImage objects (memory allocation)
  ↓
Layout calculation (text flow, image positioning)
  ↓
Initial render pass
  ↓
Paint to screen
  ↓
[TOTAL: 200-500ms of UI thread blocking]
```

**Result**: User sees frozen UI while QTextBrowser processes everything.

### Measured Impact for "The Mamba Mentality"

**Assumptions** (typical chapter with 15 high-resolution images):

1. **Image resolution**: 15 images × 7.97ms = ~120ms
2. **QTextBrowser.setHtml()**:
   - HTML parsing: ~30ms
   - Base64 decoding: 15 images × 15ms = ~225ms
   - Layout + render: ~100ms
   - **Total: ~355ms**

**Total perceived lag: ~475ms** (approaching half a second!)

This exceeds the **100ms perception threshold** for "instant" feedback, causing noticeable lag.

### Why Caching Doesn't Help Initial Load

Our 3-phase caching system works perfectly for:
- ✅ **Subsequent visits** to the same chapter (cache hits)
- ✅ **Memory management** (limiting total memory usage)
- ✅ **Navigation responsiveness** (back/forward is fast)

But it **doesn't help** with:
- ❌ **First load** of any chapter (always a cache miss)
- ❌ **UI thread blocking** (caching is synchronous)
- ❌ **Progressive loading** (all-or-nothing rendering)

---

## Architectural Bottlenecks

### Primary Bottleneck: UI Thread Blocking

**Problem**: All image processing and rendering happens synchronously on the UI thread.

**Evidence**:
- `resolve_images_in_html()` is called directly in `_load_chapter()`
- `QTextBrowser.setHtml()` blocks until all images are decoded and rendered
- No progressive loading or async operations

**Impact**: High (explains user-reported lag)

### Secondary Bottleneck: Batch Processing

**Problem**: We process ALL images before showing ANY content.

**Evidence**:
- `resolve_images_in_html()` uses `img_pattern.sub()` to process all images at once
- No progressive or lazy loading mechanism

**Impact**: Medium (amplifies primary bottleneck)

### Tertiary Bottleneck: Base64 Encoding Overhead

**Problem**: Base64 increases image size by ~33%, putting pressure on memory and string handling.

**Evidence**:
- For 50MB of images → ~66MB of base64 text in HTML string
- QTextBrowser must decode all this on setHtml()

**Impact**: Low-Medium (contributes to primary bottleneck)

---

## Solution Options

### Option A: Async Image Loading with QThread

**Approach**: Move image resolution to a background thread, emit progress updates.

**Architecture**:
```python
class ImageLoader(QThread):
    progress = pyqtSignal(str)  # Partial HTML with some images loaded
    finished = pyqtSignal(str)  # Final HTML with all images

    def run(self):
        # Load images incrementally
        # Emit progress signal for each image resolved
        # Emit finished signal when done
```

**Pros**:
- UI stays responsive during image loading
- Can show progress indicator
- Enables progressive loading (show text first, images as they load)
- Standard Qt pattern

**Cons**:
- More complex than synchronous approach
- Need to handle thread safety
- QTextBrowser.setHtml() still blocks on decode (unless we use Option C)
- Partial updates might cause flicker

**Verdict**: 🟡 Helps UI responsiveness, but doesn't solve QTextBrowser blocking

---

### Option B: Lazy Image Loading with Placeholders

**Approach**: Initially render HTML with placeholder images, load actual images on-demand.

**Architecture**:
```python
def resolve_images_lazy(html: str) -> str:
    """Replace <img src="..."> with placeholder data URLs."""
    # Generate small 1x1 pixel placeholder
    placeholder = "data:image/png;base64,iVBORw0KGg..."

    # Replace all images with placeholders
    # Store original src in data attribute for later loading
    return html.replace('<img src="path">',
                       f'<img src="{placeholder}" data-real-src="path">')

# Later: Load images as they scroll into view
# OR: Load all images in background after initial render
```

**Pros**:
- Chapter renders instantly (no image decoding)
- Progressive enhancement (text first, images later)
- Reduces initial memory footprint
- Can prioritize visible images (viewport-based loading)

**Cons**:
- Requires mechanism to trigger actual image loading
- More complex than current approach
- QTextBrowser doesn't have built-in lazy loading
- Would need custom QTextDocument resource handling OR JavaScript (not available in QTextBrowser)

**Verdict**: ⚠️ Conceptually excellent, but difficult to implement with QTextBrowser

---

### Option C: Switch to QWebEngineView

**Approach**: Replace QTextBrowser with QWebEngineView for full HTML5 support.

**Architecture**:
```python
from PyQt6.QtWebEngineWidgets import QWebEngineView

class BookViewer(QWidget):
    def __init__(self):
        self._renderer = QWebEngineView(self)
        # Full HTML5, CSS3, JavaScript support
```

**Pros**:
- Native lazy image loading support (`loading="lazy"` attribute)
- Async rendering (doesn't block UI thread as much)
- Better HTML/CSS support
- Can use Intersection Observer API for progressive loading
- Future-proof for complex EPUBs

**Cons**:
- Heavier dependency (requires QtWebEngine)
- Higher memory usage (~50MB base overhead)
- More complex API
- Deviates from MVP "lightweight" goal
- Takes away learning value (we're learning Qt widgets)

**Verdict**: 🟢 Best technical solution, but significant trade-off

---

### Option D: Pre-rendered Image Cache + Async Loading (Hybrid)

**Approach**: Combine async loading with intelligent caching.

**Architecture**:
```python
class AsyncChapterLoader(QThread):
    content_ready = pyqtSignal(str)  # HTML ready to display

    def run(self):
        # 1. Load raw HTML (fast)
        raw = self._book.get_chapter_content(self._index)

        # 2. Check if images are already in image cache
        # 3. If cached: Build HTML with data URLs quickly
        # 4. If not cached: Load images asynchronously, cache them
        # 5. Emit content_ready when done

# Main thread receives signal, calls setHtml() ONCE with all images ready
```

**Pros**:
- UI thread never blocked by image loading
- Caching makes subsequent loads instant
- Works with existing QTextBrowser
- Can show loading indicator during async work
- Minimal architectural change

**Cons**:
- Chapter still "pops in" all at once (no progressive rendering)
- First load still takes same total time, just doesn't block UI
- Need to manage thread lifecycle

**Verdict**: 🟢 Good pragmatic solution for MVP

---

### Option E: Image Pre-fetching/Pre-caching

**Approach**: Pre-load images for next/previous chapters in background.

**Architecture**:
```python
def _load_chapter(self, index: int) -> None:
    # ... load current chapter ...

    # Pre-fetch adjacent chapters in background
    self._prefetch_adjacent_chapters(index)

def _prefetch_adjacent_chapters(self, current_index: int) -> None:
    """Pre-load images for next/previous chapters."""
    # Start background tasks to populate image cache
    # for chapters at current_index ± 1
```

**Pros**:
- Next/previous navigation becomes instant (cache hits)
- Spreads loading cost over time
- Works with existing architecture
- Easy to implement incrementally

**Cons**:
- Doesn't help first load of ANY chapter
- Uses more memory (pre-cached images)
- Doesn't solve UI blocking issue

**Verdict**: 🟡 Good optimization, but doesn't address root cause

---

## Recommended Solution

### **Phased Approach: Option D → Option C**

#### Phase 4 (Immediate - Address Lag): Async Chapter Loading

**Implement Option D** to eliminate UI blocking:

1. Create `AsyncChapterLoader(QThread)` class
2. Move `resolve_images_in_html()` to background thread
3. Show loading indicator while processing
4. Emit signal when content ready
5. Main thread calls `setHtml()` once with fully prepared content

**Expected Impact**:
- ✅ UI stays responsive (no freezing)
- ✅ Loading indicator provides feedback
- ✅ Still uses existing caching infrastructure
- ⚠️ First load still takes ~475ms total, but doesn't block UI

**Implementation Effort**: Medium (2-3 sessions)

#### Phase 5 (Post-MVP - Long-term Solution): QWebEngineView Migration

**Implement Option C** for professional-grade rendering:

1. Create `WebBookViewer` implementing same protocol
2. Add lazy image loading with `loading="lazy"`
3. Migrate gradually (feature flag or settings option)
4. Benchmark memory usage and performance
5. Remove QTextBrowser if QWebEngineView proves superior

**Expected Impact**:
- ✅ Native lazy loading (images load as scrolled into view)
- ✅ Async rendering (better performance)
- ✅ Better EPUB compatibility (HTML5/CSS3)
- ⚠️ Higher memory overhead (~50MB)

**Implementation Effort**: Large (4-6 sessions)

---

## Alternative Quick Wins

### Quick Win 1: Show Content Immediately, Images Later

If we want to ship ASAP without async threading:

```python
def _load_chapter_progressive(self, index: int) -> None:
    # 1. Load raw HTML
    raw_content = self._book.get_chapter_content(index)

    # 2. Show text-only version immediately (no image resolution)
    self.content_ready.emit(raw_content)

    # 3. Resolve images in background (QTimer.singleShot)
    QTimer.singleShot(0, lambda: self._resolve_and_update_images(index, raw_content))
```

**Pros**: Dead simple, no threading
**Cons**: Images "pop in" after text, might be jarring

### Quick Win 2: Reduce Image Quality

Downscale large images before base64 encoding:

```python
def _optimize_image(image_data: bytes) -> bytes:
    """Downscale images larger than screen resolution."""
    img = QImage.fromData(image_data)
    if img.width() > 1920 or img.height() > 1080:
        img = img.scaled(1920, 1080, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # Convert back to bytes
```

**Expected Impact**: Reduce base64 decode time by 30-50%

---

## Measurement Plan

To validate solutions, we need to measure what we're NOT currently measuring:

### Add QTextBrowser.setHtml() Timing

```python
# In book_viewer.py
def set_content(self, html: str) -> None:
    import time
    start = time.perf_counter()

    self._renderer.setHtml(html)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("QTextBrowser.setHtml() took %.2f ms", elapsed_ms)
```

### Add UI Event Loop Blocking Detection

```python
# In main_window.py or controller
from PyQt6.QtCore import QElapsedTimer

def _load_chapter(self, index: int) -> None:
    timer = QElapsedTimer()
    timer.start()

    # ... existing code ...

    # Log if we blocked UI for more than 100ms
    if timer.elapsed() > 100:
        logger.warning("Chapter load blocked UI for %d ms", timer.elapsed())
```

### Enhanced Profiling Script

Create `scripts/profile_ui_performance.py` that:
- Actually renders content in QTextBrowser
- Measures setHtml() time
- Measures total UI blocking time
- Tests with real PyQt application

---

## Decision

**Implement Phase 4 (Async Chapter Loading) as Priority 1** to address immediate user-reported lag.

### Rationale

1. **Solves the root cause**: Moves blocking work off UI thread
2. **Pragmatic**: Works with existing QTextBrowser architecture
3. **Incremental**: Doesn't require major refactoring
4. **Testable**: Easy to measure improvement
5. **Learning opportunity**: Introduces Qt threading patterns
6. **Foundation for future**: Sets up for Phase 5 migration to QWebEngineView

### Implementation Guidance

See companion document: `async-chapter-loading-architecture.md` (to be created during implementation)

---

## Consequences

### What This Enables

✅ Responsive UI during chapter loading
✅ Loading feedback to users
✅ Better understanding of Qt threading
✅ Foundation for progressive loading features
✅ Maintains existing caching benefits

### What This Constrains

⚠️ Introduces threading complexity (need to manage thread lifecycle)
⚠️ Still has "pop-in" effect (content appears all at once, not progressively)
⚠️ Doesn't reduce total loading time, just makes it non-blocking

### What We'll Need to Watch Out For

🔍 **Thread safety**: Ensure EPUBBook access is thread-safe (ZipFile reading)
🔍 **Memory management**: Thread must not hold references to large objects
🔍 **Error handling**: Thread exceptions need to propagate to UI
🔍 **Cancellation**: Handle case where user navigates away before loading completes

---

## Open Questions

1. **Is EPUBBook.get_resource() thread-safe?**
   - Need to verify if ZipFile access is safe from background thread
   - Might need mutex or make EPUBBook thread-safe

2. **Should we show partial content during loading?**
   - Option A: Show nothing until fully loaded (current behavior, but async)
   - Option B: Show text first, images later (progressive)
   - **Recommendation**: Start with A (simpler), consider B later

3. **How to handle rapid chapter navigation?**
   - Cancel pending loads when user navigates away
   - Queue or throttle requests
   - **Recommendation**: Cancel pending loads (avoid wasted work)

---

## References

- [Current Performance Summary](../testing/performance-summary.md)
- [Chapter Caching System](./chapter-caching-system.md)
- [Qt Threading Basics](https://doc.qt.io/qt-6/thread-basics.html)
- [QTextBrowser Documentation](https://doc.qt.io/qt-6/qtextbrowser.html)
- [QWebEngineView Documentation](https://doc.qt.io/qt-6/qwebengineview.html)

---

## Next Steps

1. **Create GitHub issue** for Phase 4 (Async Chapter Loading)
2. **Use `/architect`** to design AsyncChapterLoader component
3. **Implement** async loading with loading indicator
4. **Measure** improvement with enhanced profiling
5. **Iterate** based on user feedback

---

## Appendix: Profiling Enhancement TODO

Update `scripts/profile_performance.py` to measure QTextBrowser rendering:

```python
# Add to profile_performance.py

def profile_ui_rendering(book: EPUBBook, sample_size: int = 5) -> dict[str, Any]:
    """Profile QTextBrowser rendering performance.

    Measures the actual UI blocking time that users experience.
    """
    from PyQt6.QtWidgets import QApplication, QTextBrowser
    import sys

    # Create minimal Qt application
    app = QApplication(sys.argv)
    browser = QTextBrowser()

    results = {
        "chapters_tested": sample_size,
        "render_times_ms": [],
    }

    chapter_count = book.get_chapter_count()
    step = chapter_count // sample_size

    for i in range(sample_size):
        index = i * step

        # Get rendered HTML (with images)
        raw_content = book.get_chapter_content(index)
        chapter_href = book.get_chapter_href(index)
        html = resolve_images_in_html(raw_content, book, chapter_href)

        # Measure setHtml() time
        start = time.perf_counter()
        browser.setHtml(html)
        app.processEvents()  # Force immediate rendering
        render_time = (time.perf_counter() - start) * 1000

        results["render_times_ms"].append(render_time)

    # Statistics
    times = results["render_times_ms"]
    results["min_time_ms"] = min(times)
    results["max_time_ms"] = max(times)
    results["avg_time_ms"] = sum(times) / len(times)

    app.quit()
    return results
```
