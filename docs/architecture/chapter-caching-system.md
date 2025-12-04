# Chapter Caching System Architecture

## Date
2025-12-03

## Context

Performance profiling revealed that memory usage grows unbounded as users navigate through chapters in image-heavy EPUBs, reaching up to 559MB for large books like "The Mamba Mentality" (201MB EPUB). The root cause is that rendered HTML chapters with base64-encoded images are kept in memory indefinitely.

### Current State
- No caching mechanism exists
- Each chapter render creates new HTML with embedded base64 images
- Memory grows ~8-10MB per chapter with images
- No automatic cleanup of old chapters

### Requirements
- **Primary**: Cap memory at ~150MB for large books (currently: 559MB)
- Maintain fast navigation for recently-viewed chapters
- Support future optimizations (lazy image loading, image compression)
- Transparent to the view layer
- Easy to monitor and debug

### Constraints
- Synchronous architecture (no async for MVP)
- MVC pattern with Protocol abstraction
- Must work with existing EPUBBook model
- QTextBrowser rendering widget

---

## Options Considered

### Option A: functools.lru_cache Decorator

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def get_rendered_chapter(book: EPUBBook, chapter_index: int) -> str:
    # Rendering logic
    pass
```

**Pros:**
- Built-in, no dependencies
- Simple to implement (one decorator)
- Automatic LRU eviction
- Thread-safe

**Cons:**
- Can only cache by immutable arguments (book object is mutable)
- No visibility into cache state (debugging)
- No memory-aware eviction (only count-based)
- No way to manually invalidate cache
- Doesn't support multi-layer caching strategy

**Verdict:** ❌ Too simplistic for our needs

---

### Option B: Custom LRU with OrderedDict

```python
from collections import OrderedDict
from typing import Tuple

class ChapterCache:
    def __init__(self, maxsize: int = 10):
        self._cache: OrderedDict[Tuple[str, int], str] = OrderedDict()
        self._maxsize = maxsize

    def get(self, book_id: str, chapter_index: int) -> str | None:
        key = (book_id, chapter_index)
        if key in self._cache:
            self._cache.move_to_end(key)  # Mark as recently used
            return self._cache[key]
        return None

    def set(self, book_id: str, chapter_index: int, html: str) -> None:
        key = (book_id, chapter_index)
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            self._cache[key] = html
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)  # Remove oldest
```

**Pros:**
- Full control over caching logic
- Can add memory tracking
- Easy to add manual invalidation
- Can inspect cache state
- Good learning opportunity (understand LRU internals)
- No external dependencies

**Cons:**
- More code to maintain
- Need to implement memory estimation ourselves
- Need to handle edge cases (thread safety if needed)

**Verdict:** ✅ Good balance of control and simplicity

---

### Option C: cachetools Library

```python
from cachetools import LRUCache, cached
from cachetools.keys import hashkey

cache = LRUCache(maxsize=10)

@cached(cache, key=lambda book, idx: hashkey(book.file_path, idx))
def get_rendered_chapter(book: EPUBBook, chapter_index: int) -> str:
    # Rendering logic
    pass
```

**Pros:**
- More features than functools (size-based, time-based)
- Well-tested library
- Can monitor cache statistics
- Supports custom key functions

**Cons:**
- External dependency (adds complexity)
- Still count-based, not memory-aware
- Overkill for our current needs
- Less educational value

**Verdict:** ⚠️ Good option, but adds dependency we may not need

---

### Option D: Multi-Layer Caching Strategy

Separate caches for different concerns:

```python
class CacheManager:
    def __init__(self):
        self.rendered_chapters = ChapterCache(maxsize=10)      # Rendered HTML
        self.raw_chapters = ChapterCache(maxsize=20)           # Raw content
        self.images = ImageCache(max_memory_mb=50)             # Processed images
        self.memory_monitor = MemoryMonitor(threshold_mb=150)
```

**Pros:**
- Separation of concerns (rendered vs raw vs images)
- Can optimize each cache independently
- Supports future enhancements (lazy loading, compression)
- Memory-aware eviction possible
- Better monitoring and debugging

**Cons:**
- More complex implementation
- Risk of over-engineering for MVP
- More moving parts to coordinate

**Verdict:** 🟡 Ideal for long-term, but may be too much for Priority 1

---

## Decision

**Implement Option B (Custom LRU with OrderedDict) for Priority 1, with architecture to support Option D later.**

### Rationale

1. **Simplicity First**: Option B gives us what we need now without over-engineering
2. **Control**: We can add memory tracking and monitoring as needed
3. **Learning**: Building our own LRU deepens understanding of caching
4. **No Dependencies**: Stays within standard library
5. **Extensible**: Can evolve into multi-layer strategy (Option D) when needed

### Phased Approach

**Phase 1 (Priority 1 - NOW):**
- Implement `ChapterCache` with LRU eviction (Option B)
- Cache rendered HTML at controller level
- Fixed maxsize of 10 chapters

**Phase 2 (Priority 4 - COMPLETED):** ✅
- Add `MemoryMonitor` to track actual memory usage
- Log warnings when memory exceeds thresholds
- Enhanced cache statistics with memory estimates and timing metrics

**Phase 3 (Priority 2 & 3 - LATER):**
- Separate `ImageCache` for processed images
- Lazy image loading integration
- Image compression/optimization

---

## Detailed Design

### Component: ChapterCache

**Location:** `src/ereader/utils/cache.py`

**Interface:**
```python
from typing import Protocol

class Cache(Protocol):
    """Protocol for cache implementations."""

    def get(self, key: str) -> str | None:
        """Retrieve cached value by key."""
        ...

    def set(self, key: str, value: str) -> None:
        """Store value in cache."""
        ...

    def clear(self) -> None:
        """Clear all cached values."""
        ...

    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        ...
```

**Implementation:**
```python
from collections import OrderedDict
from typing import Any
import logging

logger = logging.getLogger(__name__)

class ChapterCache:
    """LRU cache for rendered chapter HTML.

    Uses OrderedDict to track access order. When cache is full,
    removes the least recently used item.

    Args:
        maxsize: Maximum number of chapters to cache (default: 10)
    """

    def __init__(self, maxsize: int = 10) -> None:
        if maxsize < 1:
            raise ValueError("maxsize must be at least 1")

        self._cache: OrderedDict[str, str] = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

        logger.info("ChapterCache initialized with maxsize=%d", maxsize)

    def get(self, key: str) -> str | None:
        """Retrieve cached HTML by key.

        If key exists, marks it as recently used by moving to end.

        Args:
            key: Cache key (typically "book_id:chapter_index")

        Returns:
            Cached HTML string, or None if not found
        """
        if key in self._cache:
            self._cache.move_to_end(key)  # Mark as recently used
            self._hits += 1
            logger.debug("Cache HIT: %s (hits=%d, misses=%d)",
                        key, self._hits, self._misses)
            return self._cache[key]

        self._misses += 1
        logger.debug("Cache MISS: %s (hits=%d, misses=%d)",
                    key, self._hits, self._misses)
        return None

    def set(self, key: str, value: str) -> None:
        """Store HTML in cache.

        If cache is full, evicts least recently used item.

        Args:
            key: Cache key (typically "book_id:chapter_index")
            value: Rendered HTML string
        """
        if key in self._cache:
            # Update existing entry and mark as recently used
            self._cache.move_to_end(key)
            self._cache[key] = value
            logger.debug("Cache UPDATE: %s", key)
        else:
            # Add new entry
            self._cache[key] = value

            # Evict oldest if necessary
            if len(self._cache) > self._maxsize:
                evicted_key = next(iter(self._cache))
                self._cache.popitem(last=False)  # Remove oldest (first item)
                logger.info("Cache EVICTION: %s (cache full: %d/%d)",
                           evicted_key, len(self._cache), self._maxsize)
            else:
                logger.debug("Cache SET: %s (size: %d/%d)",
                           key, len(self._cache), self._maxsize)

    def clear(self) -> None:
        """Remove all cached entries."""
        size = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache CLEARED: removed %d entries", size)

    def stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dictionary with cache metrics:
            - size: Current number of cached items
            - maxsize: Maximum cache capacity
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Percentage of requests that hit cache
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate
        }

    def __len__(self) -> int:
        """Return number of items in cache."""
        return len(self._cache)
```

---

### Integration with EPUBController

**Before (no caching):**
```python
class EPUBController:
    def get_current_chapter_html(self) -> str:
        chapter = self._book.get_chapter_content(self._current_chapter)
        return self._render_chapter_html(chapter)
```

**After (with caching):**
```python
class EPUBController:
    def __init__(self, book: EPUBBook):
        self._book = book
        self._chapter_cache = ChapterCache(maxsize=10)
        # ... other initialization

    def get_current_chapter_html(self) -> str:
        # Generate cache key
        cache_key = f"{self._book.file_path}:{self._current_chapter}"

        # Try cache first
        cached_html = self._chapter_cache.get(cache_key)
        if cached_html is not None:
            return cached_html

        # Cache miss - render and store
        chapter = self._book.get_chapter_content(self._current_chapter)
        html = self._render_chapter_html(chapter)
        self._chapter_cache.set(cache_key, html)

        return html
```

---

### Cache Key Strategy

**Format:** `{book_file_path}:{chapter_index}`

**Examples:**
- `/path/to/book.epub:0`
- `/path/to/book.epub:5`

**Rationale:**
- Simple and human-readable (debugging)
- Unique across books and chapters
- No risk of collision
- File path ensures different books don't collide
- Chapter index is stable (doesn't change)

**Alternative Considered:** Hash-based keys (e.g., `md5(file_path + chapter_index)`)
- **Rejected**: Harder to debug, no real benefit for our use case

---

## Consequences

### What This Enables
✅ Memory capped at ~150MB for large books (down from 559MB)
✅ Fast navigation for recently-viewed chapters (cache hits)
✅ Automatic cleanup of old chapters (LRU eviction)
✅ Visibility into cache behavior (stats and logging)
✅ Foundation for future multi-layer caching

### What This Constrains
⚠️ Limited to 10 chapters in memory (configurable, but fixed per session)
⚠️ No memory-aware eviction yet (count-based only)
⚠️ Cache invalidation is automatic only (no manual refresh)

### What We'll Need to Watch Out For
🔍 **Memory estimation accuracy**: We're caching count-based (10 chapters), not memory-based. If chapters vary wildly in size, we might still exceed targets.
  - **Mitigation**: Monitor in Phase 2, adjust maxsize if needed

🔍 **Cache key stability**: If book file path changes (move/rename), cache misses occur.
  - **Mitigation**: Acceptable for MVP, can add book ID later

🔍 **Sequential reading assumption**: LRU works well for forward/backward reading, but random jumping might cause more evictions.
  - **Mitigation**: 10 chapters should be enough for typical navigation patterns

---

## Implementation Notes

### Testing Strategy

1. **Unit Tests** (`tests/test_utils/test_cache.py`):
   - Cache hit/miss behavior
   - LRU eviction order
   - Stats tracking accuracy
   - Edge cases (maxsize=1, clear, etc.)
   - Cache key generation

2. **Integration Tests** (`tests/test_controllers/test_epub_controller_cache.py`):
   - Controller uses cache correctly
   - Navigation patterns (forward, backward, random)
   - Multiple books don't collide
   - Cache cleared on book change

3. **Performance Tests** (update `scripts/profile_performance.py`):
   - Memory usage with cache enabled
   - Compare before/after caching
   - Cache hit rates for typical reading patterns

### Logging Strategy

- **DEBUG**: Every cache operation (get, set, hit, miss)
- **INFO**: Initialization, evictions, clear operations
- **WARNING**: (Phase 2) Memory threshold exceeded

### Configuration

For MVP, hardcode `maxsize=10`. Later, can add to config:
```python
# config.py (future)
CACHE_MAX_CHAPTERS = 10
MEMORY_THRESHOLD_MB = 150
```

### Migration Path

Phase 1 → Phase 2:
- Add `MemoryMonitor` class alongside `ChapterCache`
- Monitor doesn't change cache behavior, just observes
- Log warnings when memory exceeds thresholds

Phase 2 → Phase 3:
- Extract image processing from chapter rendering
- Create `ImageCache` that shares memory budget with `ChapterCache`
- Introduce `CacheManager` to coordinate multiple caches

---

## Performance Impact Estimates

### Expected Memory Usage (with cache)
- **Text-only books**: < 30MB (was: < 50MB) ✅ Minor improvement
- **Image-heavy books**: ~150MB (was: 559MB) ✅ **73% reduction**

### Expected Cache Hit Rates
- **Sequential reading** (forward): ~90% hits (only first page per chapter misses)
- **Review reading** (back few pages): ~80% hits (recent chapters cached)
- **Random navigation**: ~30% hits (depends on jump distance)

### Rendering Performance
- **Cache hit**: < 1ms (retrieve from memory)
- **Cache miss**: 1-8ms (render and store)
- **Net improvement**: ~90% of navigation operations become < 1ms

---

## Open Questions

1. **Should maxsize be configurable at runtime?**
   - **Decision**: No, not for MVP. Hardcode at 10, can add config later if users need it.

2. **Should we pre-cache next/previous chapters?**
   - **Decision**: No, not for MVP. Cache on-demand is simpler and sufficient.

3. **Should cache persist across app sessions?**
   - **Decision**: No. In-memory only for MVP. Disk caching is a future enhancement.

4. **What about cache invalidation on book update?**
   - **Decision**: Out of scope. We don't support live book editing in MVP.

---

## References

- [Performance Summary](../testing/performance-summary.md) - Profiling results that motivated this design
- [EPUB Rendering Architecture](./epub-rendering-architecture.md) - MVC architecture this integrates with
- Python `collections.OrderedDict` documentation
- LRU cache algorithms: [Wikipedia](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU))

---

## Related Work

- **Issue #28**: Implement Phase 2 (Memory Monitor) - ✅ **COMPLETED**
- **Issue #TBD**: Implement Phase 3 (Multi-layer caching)
- **Issue #TBD**: Add cache configuration UI (advanced settings)
- **Issue #TBD**: Disk-based cache for faster app startup

---

## Phase 2 Implementation Details (Completed)

### MemoryMonitor Class

**Location:** `src/ereader/utils/memory_monitor.py`

The `MemoryMonitor` class provides process-level memory tracking using `psutil`:

```python
class MemoryMonitor:
    """Monitor memory usage and alert when thresholds exceeded."""

    def __init__(self, threshold_mb: int = 150):
        """Initialize with memory threshold in MB."""

    def get_current_usage(self) -> float:
        """Get current process memory usage in MB (RSS)."""

    def check_threshold(self) -> bool:
        """Check if memory exceeds threshold. Log warning if true."""

    def get_stats(self) -> dict[str, Any]:
        """Get memory monitor statistics."""
```

**Features:**
- Tracks RSS (Resident Set Size) memory usage
- Logs WARNING when threshold exceeded (only once until recovery)
- Logs INFO at memory milestones (100MB, 125MB, 150MB, etc.)
- Tracks monitor age and provides statistics

**Integration:**
- Created automatically in `ReaderController.__init__()`
- `check_threshold()` called after each chapter load
- Default threshold: 150MB (configurable)

### Enhanced ChapterCache Statistics

The `ChapterCache.stats()` method now includes:

**Original metrics:**
- `size`: Current number of cached items
- `maxsize`: Maximum cache capacity
- `hits`: Number of cache hits
- `misses`: Number of cache misses
- `hit_rate`: Percentage of requests that hit cache

**Phase 2 additions:**
- `estimated_memory_mb`: Estimated cache memory usage in MB (using `sys.getsizeof`)
- `avg_item_size_kb`: Average size of cached items in KB
- `time_since_last_eviction`: Seconds since last eviction (or None)
- `cache_age_seconds`: Seconds since cache creation

### Logging Strategy

**DEBUG level:**
- Every cache operation (get, set, hit, miss)
- Current memory usage checks

**INFO level:**
- Cache initialization
- Cache evictions
- Memory milestones reached (100MB, 125MB, etc.)
- Memory recovery (dropped below threshold)

**WARNING level:**
- Memory threshold exceeded (logged once per exceedance)

### Testing

**Unit Tests:** `tests/test_utils/test_memory_monitor.py`
- 18 tests covering all MemoryMonitor functionality
- Mocks psutil for deterministic testing
- Tests threshold detection, milestone logging, stats

**Integration Tests:** `tests/test_controllers/test_reader_controller.py`
- 6 tests for MemoryMonitor integration with ReaderController
- Verifies memory checks occur after chapter loads
- Tests warning generation and logging

**Enhanced Cache Tests:** `tests/test_utils/test_cache.py`
- 8 new tests for Phase 2 statistics
- Tests memory estimation, timing metrics, cache age

**Test Coverage:** 100% for both MemoryMonitor and ChapterCache

### Performance Impact

- **Memory overhead**: Minimal (~1KB for MemoryMonitor instance)
- **CPU overhead**: ~0.1ms per memory check (psutil call)
- **Frequency**: One check per chapter load (acceptable)

### Future Enhancements (Phase 3)

- Memory-aware eviction (not just count-based)
- Separate ImageCache for processed images
- CacheManager to coordinate multiple caches
- Configurable memory limits via UI
