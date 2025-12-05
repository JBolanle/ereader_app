# Image Optimization Architecture

## Date
2025-12-05

## Context

Performance profiling revealed that image-heavy EPUBs (e.g., "The Mamba Mentality" - 201MB) cause excessive memory usage, reaching 559MB peak during reading. While the multi-layer caching system (Phase 3, completed) caps overall memory growth, individual images remain unoptimized:

- Large images (8000×6000 pixels) are base64-encoded without downscaling
- Base64 encoding adds ~33% memory overhead
- All images in a chapter load immediately (no lazy loading)
- ImageCache infrastructure exists but is not yet utilized

**Goal:** Reduce per-image memory footprint by 60-70% through intelligent downscaling while maintaining visual quality for reading.

---

## Problem Statement

### Current Flow
```
AsyncChapterLoader (background thread)
  ↓
resolve_images_in_html()
  ↓
Load raw image bytes from EPUB
  ↓
Base64 encode (no processing)
  ↓
Embed in HTML: <img src="data:image/jpeg;base64,...">
  ↓
Store entire HTML in rendered_chapters cache
```

### Issues
1. **No image optimization**: Large images (>1920×1080) consume excessive memory
2. **ImageCache unused**: Infrastructure exists but no code utilizes it
3. **Dual storage potential**: Risk of storing same image data twice (in ImageCache + rendered HTML)
4. **No processing pipeline**: Pillow logic would be mixed into HTML parsing function (SRP violation)

---

## Options Considered

### Option A: Modify resolve_images_in_html() Directly

Add Pillow processing inline to the existing `replace_image()` inner function:

```python
def replace_image(match):
    raw_bytes = epub_book.get_resource(src_value)

    # Add Pillow processing here
    img = Image.open(BytesIO(raw_bytes))
    if img.width > 1920 or img.height > 1080:
        # downscale logic...

    base64_data = base64.b64encode(processed_bytes)
    return f'<img src="data:...;base64,{base64_data}">'
```

**Pros:**
- Minimal file changes
- All logic in one place

**Cons:**
- ❌ Violates Single Responsibility Principle (HTML parsing + image processing)
- ❌ Hard to test Pillow logic in isolation
- ❌ No clear cache integration point
- ❌ 100+ line function becomes 150+ lines

**Verdict:** ❌ Rejected - Poor separation of concerns

---

### Option B: Extract image_processor Module + Integrate ImageCache

Create separate `image_processor.py` for Pillow logic and integrate with existing ImageCache:

```python
# image_processor.py
def process_image(image_data: bytes, max_w: int, max_h: int) -> bytes:
    """Downscale if needed, return processed bytes."""

# html_resources.py
def resolve_images_in_html(html, book, chapter_href, image_cache):
    def replace_image(match):
        cache_key = f"{book.filepath}:{src_value}"

        # Try cache first
        processed_bytes = image_cache.get(cache_key)
        if processed_bytes is None:
            raw_bytes = epub_book.get_resource(src_value)
            processed_bytes = process_image(raw_bytes, 1920, 1080)
            image_cache.set(cache_key, processed_bytes)

        # Base64 encode and embed
        base64_data = base64.b64encode(processed_bytes)
        return f'<img src="data:...;base64,{base64_data}">'
```

**Pros:**
- ✅ Clear separation: image_processor handles Pillow, html_resources handles HTML
- ✅ ImageCache stores processed bytes (single storage, no duplication)
- ✅ Easy to unit test image_processor independently
- ✅ Explicit cache dependency (good for testing)
- ✅ Thread-safe (ImageCache has RLock)

**Cons:**
- Additional file to maintain
- Extra parameter to resolve_images_in_html()

**Verdict:** ✅ **Recommended** - Clean architecture, testable, efficient

---

### Option C: Global ImageCache Singleton

Use global ImageCache instance instead of passing as parameter:

```python
# globals.py
IMAGE_CACHE = ImageCache(max_memory_mb=50)

# html_resources.py
from ereader.globals import IMAGE_CACHE

def resolve_images_in_html(html, book, chapter_href):
    # Use IMAGE_CACHE directly
```

**Pros:**
- No parameter passing needed
- Simpler function signatures

**Cons:**
- ❌ Global state (harder to test, implicit dependency)
- ❌ Can't mock cache in tests without monkey-patching
- ❌ Not thread-safe if multiple instances created
- ❌ Goes against MVC principles (explicit dependencies preferred)

**Verdict:** ❌ Rejected - Global state anti-pattern

---

## Decision

**Implement Option B: Extract image_processor + Integrate ImageCache**

### Rationale

1. **Separation of Concerns**: Pillow logic isolated in `image_processor.py`, HTML parsing stays in `html_resources.py`
2. **Single Storage**: ImageCache stores processed bytes once, rendered HTML contains base64 of those bytes
3. **Testability**: Can unit test image processing without HTML parsing
4. **Explicit Dependencies**: Cache passed as parameter (easy to mock, clear contract)
5. **Thread-Safety**: ImageCache already has RLock for concurrent AsyncChapterLoader access
6. **Future-Proof**: Clean foundation for Phase 2 (lazy loading) and Phase 3 (format optimization)

---

## Detailed Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ ReaderController                                             │
│  └─ CacheManager                                             │
│      ├─ rendered_chapters: ChapterCache                      │
│      ├─ raw_chapters: ChapterCache                           │
│      └─ images: ImageCache  ← NOW UTILIZED!                  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ AsyncChapterLoader (QThread)                                 │
│  └─ run() method executes in background thread               │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ resolve_images_in_html(html, book, chapter_href, image_cache│
│  └─ replace_image(match) - for each <img> tag                │
│      ├─ Generate cache key: f"{book.filepath}:{image_path}"  │
│      ├─ Check ImageCache for processed bytes                 │
│      ├─ On MISS: Load raw → process_image() → cache          │
│      └─ Base64 encode → embed in HTML                        │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ image_processor.py (NEW)                                     │
│  ├─ process_image(bytes, max_w, max_h) -> bytes              │
│  │   └─ Pillow: Open → Check size → Resize if needed → Save │
│  ├─ should_skip_processing(mime_type) -> bool                │
│  │   └─ Returns True for SVG (vector-based)                  │
│  └─ ImageProcessingError (custom exception)                  │
└─────────────────────────────────────────────────────────────┘
```

---

### image_processor.py API

**Purpose:** Isolated module for image processing using Pillow. Handles downscaling, format detection, and error handling.

```python
"""Image processing utilities for optimizing EPUB images.

This module provides functions to process and optimize images from EPUBs,
primarily focused on downscaling oversized images to reduce memory usage.
"""

from io import BytesIO
from PIL import Image
import logging

from ereader.exceptions import ImageProcessingError

logger = logging.getLogger(__name__)

# Maximum dimensions for downscaling (1920x1080 is common screen resolution)
DEFAULT_MAX_WIDTH = 1920
DEFAULT_MAX_HEIGHT = 1080

# Aggressive downscaling for extremely large images (>10MB)
AGGRESSIVE_MAX_WIDTH = 1280
AGGRESSIVE_MAX_HEIGHT = 720


def process_image(
    image_data: bytes,
    max_width: int = DEFAULT_MAX_WIDTH,
    max_height: int = DEFAULT_MAX_HEIGHT,
) -> bytes:
    """Process and optionally downscale an image.

    Opens the image with Pillow, checks dimensions, and downscales if the
    image exceeds the maximum width or height. Maintains aspect ratio and
    uses high-quality LANCZOS resampling.

    Args:
        image_data: Raw image bytes from EPUB.
        max_width: Maximum allowed width in pixels.
        max_height: Maximum allowed height in pixels.

    Returns:
        Processed image bytes. Original format is preserved (JPEG stays JPEG,
        PNG stays PNG). If image is within limits, returns original bytes
        unchanged.

    Raises:
        ImageProcessingError: If image cannot be opened or processed.
            Common causes: corrupted data, unsupported format, truncated file.

    Example:
        >>> raw_bytes = epub.get_resource("images/photo.jpg")
        >>> processed = process_image(raw_bytes, max_width=1920, max_height=1080)
        >>> # If photo was 4000x3000, it's now 1920x1440 (aspect preserved)
    """
    try:
        # Open image with Pillow
        img = Image.open(BytesIO(image_data))

        logger.debug(
            "Processing image: %dx%d, format=%s, mode=%s",
            img.width,
            img.height,
            img.format,
            img.mode,
        )

        # Skip if already within limits
        if img.width <= max_width and img.height <= max_height:
            logger.debug(
                "Image within limits (%dx%d <= %dx%d), skipping downscale",
                img.width,
                img.height,
                max_width,
                max_height,
            )
            return image_data

        # Calculate new size maintaining aspect ratio
        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))

        logger.info(
            "Downscaling image: %dx%d -> %dx%d (%.1f%% of original)",
            img.width,
            img.height,
            new_size[0],
            new_size[1],
            ratio * 100,
        )

        # Downscale using high-quality LANCZOS resampling
        # LANCZOS provides excellent quality for downscaling
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save to bytes, preserving original format
        output = BytesIO()
        save_format = img.format or "JPEG"  # Default to JPEG if format unknown

        # For JPEG, we could add quality parameter here (Phase 3)
        img_resized.save(output, format=save_format)

        processed_bytes = output.getvalue()

        logger.debug(
            "Image processed: %d bytes -> %d bytes (%.1f%% reduction)",
            len(image_data),
            len(processed_bytes),
            (1 - len(processed_bytes) / len(image_data)) * 100,
        )

        return processed_bytes

    except Image.UnidentifiedImageError as e:
        # Pillow couldn't identify the image format
        logger.error("Failed to identify image format: %s", e)
        raise ImageProcessingError(f"Unrecognized image format: {e}") from e

    except OSError as e:
        # File I/O errors (truncated, corrupted, etc.)
        logger.error("Failed to process image: %s", e)
        raise ImageProcessingError(f"Image processing failed: {e}") from e

    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception("Unexpected error processing image: %s", e)
        raise ImageProcessingError(f"Unexpected error: {e}") from e


def should_skip_processing(mime_type: str) -> bool:
    """Determine if an image should skip processing based on MIME type.

    Some image types should not be processed:
    - SVG: Vector graphics scale perfectly, no need to downscale
    - (Future: animated GIFs might need special handling)

    Args:
        mime_type: MIME type string (e.g., "image/jpeg", "image/svg+xml")

    Returns:
        True if image should skip processing and be used as-is.

    Example:
        >>> should_skip_processing("image/svg+xml")
        True
        >>> should_skip_processing("image/jpeg")
        False
    """
    # SVG is vector-based, scales perfectly without processing
    if mime_type == "image/svg+xml":
        logger.debug("Skipping processing for SVG (vector format)")
        return True

    # Future: might skip animated GIFs, or WebP, etc.

    return False


def get_aggressive_limits(image_size_bytes: int) -> tuple[int, int]:
    """Get more aggressive downscaling limits for very large images.

    Extremely large images (>10MB) get more aggressive downscaling to
    prevent memory spikes during processing.

    Args:
        image_size_bytes: Size of raw image data in bytes.

    Returns:
        Tuple of (max_width, max_height) to use for downscaling.

    Example:
        >>> get_aggressive_limits(5 * 1024 * 1024)  # 5MB
        (1920, 1080)  # Normal limits
        >>> get_aggressive_limits(15 * 1024 * 1024)  # 15MB
        (1280, 720)  # Aggressive limits
    """
    # Threshold: 10MB
    if image_size_bytes > 10 * 1024 * 1024:
        logger.info(
            "Large image detected (%.1f MB), using aggressive downscaling",
            image_size_bytes / (1024 * 1024),
        )
        return (AGGRESSIVE_MAX_WIDTH, AGGRESSIVE_MAX_HEIGHT)

    return (DEFAULT_MAX_WIDTH, DEFAULT_MAX_HEIGHT)
```

---

### Modified: html_resources.py

**Changes:**
1. Add `image_cache` parameter (optional, backwards compatible)
2. Update `replace_image()` to check cache before processing
3. Integrate with `image_processor.process_image()`
4. Store processed bytes in ImageCache
5. Add error handling for `ImageProcessingError`

```python
"""HTML resource resolution utilities for EPUB content.

This module provides functions to resolve and embed resources (images, CSS, etc.)
referenced in EPUB HTML content.
"""

import base64
import logging
import re
from typing import TYPE_CHECKING

from ereader.exceptions import CorruptedEPUBError, ImageProcessingError
from ereader.utils.image_processor import (
    process_image,
    should_skip_processing,
    get_aggressive_limits,
)

if TYPE_CHECKING:
    from ereader.models.epub import EPUBBook
    from ereader.utils.image_cache import ImageCache

logger = logging.getLogger(__name__)

# ... (MIME_TYPES and RESPONSIVE_IMAGE_STYLE unchanged)


def resolve_images_in_html(
    html: str,
    epub_book: "EPUBBook",
    chapter_href: str | None = None,
    image_cache: "ImageCache | None" = None,
) -> str:
    """Resolve image references in HTML by embedding them as base64 data URLs.

    Finds all <img> tags in the HTML content and replaces relative src attributes
    with base64-encoded data URLs, loading the image data from the EPUB file.

    Images are optimized before encoding:
    - Oversized images are downscaled to screen resolution (1920x1080)
    - Processed images are cached to avoid re-processing
    - SVG images are not processed (vector-based, scale perfectly)

    Args:
        html: The HTML content containing image references.
        epub_book: The EPUBBook instance to load image resources from.
        chapter_href: Optional href of the chapter HTML file (e.g., "text/chapter1.html").
                     If provided, image paths are resolved relative to this file.
                     If None, paths are resolved relative to the OPF file.
        image_cache: Optional ImageCache for storing processed images.
                     If None, images are processed but not cached.

    Returns:
        Modified HTML with images embedded as data URLs.

    Example:
        >>> html = '<img src="images/cover.jpg" />'
        >>> cache = ImageCache(max_memory_mb=50)
        >>> resolved_html = resolve_images_in_html(html, book, image_cache=cache)
        >>> # Large image downscaled, processed version cached
    """
    # Pattern to match <img> tags and capture the src attribute
    img_pattern = re.compile(
        r'<img\s+([^>]*?)src=(["\'])([^"\']+?)\2([^>]*?)>', re.IGNORECASE
    )

    def replace_image(match: re.Match[str]) -> str:
        """Replace a single image src with a data URL."""
        before_src = match.group(1)  # Attributes before src
        src_value = match.group(3)  # The actual src value
        after_src = match.group(4)  # Attributes after src

        # Skip if already a data URL or absolute URL
        if src_value.startswith(("data:", "http://", "https://")):
            logger.debug("Skipping absolute/data URL: %s", src_value)
            return match.group(0)  # Return original

        logger.debug("Resolving image: %s", src_value)

        try:
            # Generate cache key: book filepath + image resource path
            cache_key = f"{epub_book.filepath}:{src_value}"

            # Try ImageCache first (stores processed bytes)
            processed_bytes = None
            if image_cache is not None:
                processed_bytes = image_cache.get(cache_key)

            if processed_bytes is not None:
                logger.debug("Image cache HIT: %s", src_value)
            else:
                logger.debug("Image cache MISS: %s", src_value)

                # Load raw image data from EPUB
                raw_bytes = epub_book.get_resource(src_value, relative_to=chapter_href)

                # Determine MIME type
                mime_type = _get_mime_type(src_value)

                # Process image (downscale if needed)
                if should_skip_processing(mime_type):
                    # SVG or other vector format - use as-is
                    processed_bytes = raw_bytes
                    logger.debug("Skipping processing for %s (MIME: %s)", src_value, mime_type)
                else:
                    # Determine downscaling limits (aggressive for large images)
                    max_width, max_height = get_aggressive_limits(len(raw_bytes))

                    try:
                        # Process with Pillow
                        processed_bytes = process_image(
                            raw_bytes, max_width=max_width, max_height=max_height
                        )
                    except ImageProcessingError as e:
                        # Processing failed - fall back to original bytes
                        logger.warning(
                            "Image processing failed for %s: %s (using original)", src_value, e
                        )
                        processed_bytes = raw_bytes

                # Store processed bytes in cache
                if image_cache is not None:
                    image_cache.set(cache_key, processed_bytes)
                    logger.debug("Cached processed image: %s", cache_key)

            # Base64 encode the processed bytes
            base64_data = base64.b64encode(processed_bytes).decode("ascii")

            # Determine MIME type (needed for data URL)
            mime_type = _get_mime_type(src_value)

            # Build data URL
            data_url = f"data:{mime_type};base64,{base64_data}"

            logger.debug(
                "Resolved image %s (%d bytes processed, %d bytes base64)",
                src_value,
                len(processed_bytes),
                len(base64_data),
            )

            # Reconstruct the img tag with data URL and responsive styling
            return f'<img {before_src}src="{data_url}" style="{RESPONSIVE_IMAGE_STYLE}"{after_src}>'

        except CorruptedEPUBError:
            # Image not found in EPUB
            logger.warning("Image not found in EPUB: %s", src_value)
            return match.group(0)  # Return original tag

        except Exception as e:
            # Unexpected error - log and keep original
            logger.error("Unexpected error resolving image %s: %s", src_value, e)
            return match.group(0)

    # Replace all image tags
    resolved_html = img_pattern.sub(replace_image, html)

    return resolved_html


# ... (_get_mime_type unchanged)
```

---

### Modified: async_loader.py

**Changes:** Pass ImageCache from CacheManager to `resolve_images_in_html()`

```python
# In AsyncChapterLoader.run() method, line ~143:

# OLD:
content = resolve_images_in_html(raw_content, self._book, chapter_href=chapter_href)

# NEW:
content = resolve_images_in_html(
    raw_content,
    self._book,
    chapter_href=chapter_href,
    image_cache=self._cache_manager.images,  # Pass ImageCache
)
```

---

### New Exception: ImageProcessingError

Add to `src/ereader/exceptions.py`:

```python
class ImageProcessingError(EReaderError):
    """Raised when image processing fails.

    This can occur due to:
    - Corrupted image data
    - Unsupported image format
    - Pillow processing errors (resize, save, etc.)
    - Truncated or incomplete image files

    The error is caught and handled gracefully by using the original
    image bytes as a fallback.
    """
    pass
```

---

### Cache Key Strategy

**Format:** `{book_filepath}:{image_resource_path}`

**Examples:**
```python
# Book: /Users/me/books/mamba.epub, Image: images/photo1.jpg
cache_key = "/Users/me/books/mamba.epub:images/photo1.jpg"

# Book: /Users/me/books/1984.epub, Image: ../images/cover.png
cache_key = "/Users/me/books/1984.epub:../images/cover.png"
```

**Collision Handling:**
- Different books, same image path: Different cache keys (book filepath differs) ✅
- Same book, different image paths: Different cache keys (image path differs) ✅
- Same book moved/renamed: Cache miss, re-process images (acceptable for MVP) ⚠️

**Future Enhancement (Phase 3):** Generate stable book ID hash to survive file moves:
```python
book_id = hashlib.md5(book_metadata_string).hexdigest()[:12]
cache_key = f"{book_id}:{image_resource_path}"
```

---

### Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ User navigates to chapter                                     │
└───────────────┬──────────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────────────┐
│ ReaderController._load_chapter(index)                         │
│  - Cancel previous AsyncChapterLoader if running             │
│  - Create new AsyncChapterLoader                             │
│  - Start background thread                                   │
└───────────────┬──────────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────────────┐
│ AsyncChapterLoader.run() [BACKGROUND THREAD]                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 1. Check rendered_chapters cache                     │    │
│  │    ├─ HIT: emit content_ready → DONE                 │    │
│  │    └─ MISS: continue                                 │    │
│  │                                                       │    │
│  │ 2. Check raw_chapters cache                          │    │
│  │    ├─ HIT: raw_content = cached                      │    │
│  │    └─ MISS: raw_content = book.get_chapter_content() │    │
│  │                                                       │    │
│  │ 3. resolve_images_in_html()                          │    │
│  │    └─ For each <img> tag:                            │    │
│  │        ├─ Generate cache_key                         │    │
│  │        ├─ Check ImageCache                           │    │
│  │        │   ├─ HIT: processed_bytes = cached          │    │
│  │        │   └─ MISS:                                  │    │
│  │        │       ├─ Load raw_bytes from EPUB           │    │
│  │        │       ├─ Check if should skip (SVG)         │    │
│  │        │       ├─ process_image(raw_bytes)           │    │
│  │        │       │   └─ Pillow: open → check → resize  │    │
│  │        │       └─ ImageCache.set(key, processed)     │    │
│  │        └─ Base64 encode → embed in HTML              │    │
│  │                                                       │    │
│  │ 4. Store in caches                                   │    │
│  │    ├─ rendered_chapters.set(key, final_html)         │    │
│  │    └─ raw_chapters.set(key, raw_content)             │    │
│  │                                                       │    │
│  │ 5. emit content_ready(final_html)                    │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────┬──────────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────────────┐
│ ReaderController._on_content_ready(html) [UI THREAD]         │
│  - Update current chapter index                             │
│  - Emit content_ready signal to BookViewer                   │
│  - BookViewer displays HTML                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Consequences

### What This Enables ✅

1. **Significant Memory Reduction**
   - Expected: 559MB → ~160-210MB (60-70% reduction)
   - Exceeds spec target of 30-50%

2. **ImageCache Utilization**
   - Infrastructure finally used for its intended purpose
   - Processed images cached, avoiding re-processing on re-read

3. **Clean Architecture**
   - image_processor isolated and testable
   - Clear separation of concerns (HTML parsing vs image processing)
   - Explicit dependencies (easy to mock in tests)

4. **Thread-Safe Processing**
   - ImageCache already has RLock for concurrent access
   - AsyncChapterLoader continues to work unchanged

5. **Future-Proof Foundation**
   - Clean integration point for Phase 2 (lazy loading)
   - Ready for Phase 3 (format optimization, quality adjustment)

---

### What This Constrains ⚠️

1. **Cache Key Dependency on File Path**
   - If book file is moved/renamed, cache misses occur
   - Acceptable for MVP, can add book ID hash in Phase 3

2. **Fixed Downscaling Limits**
   - Hardcoded 1920×1080 (normal) and 1280×720 (aggressive)
   - No runtime configuration in Phase 1
   - Can add ImageConfig in Phase 3

3. **Format Preservation**
   - JPEG stays JPEG, PNG stays PNG
   - No format optimization (PNG→JPEG conversion) in Phase 1
   - Deferred to Phase 3

4. **No Lazy Loading Yet**
   - All images still load immediately (processed, but not lazy)
   - Phase 2 will address this (separate concern)

---

### What We'll Need to Watch Out For 🔍

1. **Pillow Processing Time**
   - Large images (8000×6000) may take 50-100ms to downscale
   - Acceptable in background thread, but monitor performance
   - **Mitigation:** Already runs in AsyncChapterLoader (non-blocking)

2. **Memory Spike During Processing**
   - Pillow loads full image into memory before resizing
   - Very large images (>10MB) might cause temporary spike
   - **Mitigation:** Aggressive limits (1280×720) for >10MB images

3. **Cache Invalidation**
   - No automatic invalidation if image content changes in EPUB
   - Not relevant for MVP (EPUBs are immutable files)
   - **Mitigation:** Document assumption, add invalidation if needed

4. **SVG Handling**
   - Assumption: QTextBrowser renders SVG correctly
   - Need to verify with test EPUB containing SVG images
   - **Mitigation:** Test with various SVG types

5. **ImageCache Memory Limit**
   - Set to 50MB, might fill up quickly with large books
   - LRU eviction should handle it, but monitor cache_stats
   - **Mitigation:** Log cache stats, consider increasing limit if needed

6. **Format Detection Edge Cases**
   - Some images might not have file extensions
   - MIME type detection defaults to "image/jpeg"
   - **Mitigation:** Pillow detects format from bytes, not filename

---

## Implementation Notes

### Testing Strategy

**Unit Tests (image_processor):**
- `test_process_image_no_downscale()` - Image within limits
- `test_process_image_downscale_width()` - Exceeds width only
- `test_process_image_downscale_height()` - Exceeds height only
- `test_process_image_downscale_both()` - Exceeds both dimensions
- `test_process_image_aspect_ratio()` - Aspect ratio preserved
- `test_process_image_formats()` - JPEG, PNG, GIF
- `test_process_image_corrupted()` - Raises ImageProcessingError
- `test_should_skip_processing_svg()` - SVG returns True
- `test_should_skip_processing_jpeg()` - JPEG returns False
- `test_get_aggressive_limits_normal()` - <10MB → 1920×1080
- `test_get_aggressive_limits_large()` - >10MB → 1280×720

**Integration Tests (html_resources):**
- `test_resolve_images_with_cache()` - Cache hit/miss behavior
- `test_resolve_images_without_cache()` - Works with cache=None
- `test_resolve_images_downscale()` - Large image gets downscaled
- `test_resolve_images_svg_skip()` - SVG not processed
- `test_resolve_images_processing_error()` - Falls back to original
- `test_cache_key_format()` - Correct key generation

**Performance Tests:**
- Run `scripts/profile_performance.py` with Mamba Mentality
- Measure: memory before/after, cache hit rates, processing time
- Target: <200MB peak memory (currently 559MB)

### Configuration (Phase 1)

**Hardcoded Constants:**
```python
# image_processor.py
DEFAULT_MAX_WIDTH = 1920
DEFAULT_MAX_HEIGHT = 1080
AGGRESSIVE_MAX_WIDTH = 1280
AGGRESSIVE_MAX_HEIGHT = 720
AGGRESSIVE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB
```

**Future Configuration (Phase 3):**
```python
@dataclass
class ImageConfig:
    max_image_width: int = 1920
    max_image_height: int = 1080
    aggressive_threshold_mb: int = 10
    aggressive_max_width: int = 1280
    aggressive_max_height: int = 720
    jpeg_quality: int = 85  # Phase 3: compression quality
```

### Logging Strategy

**DEBUG:**
- Every cache hit/miss for images
- Image dimensions before/after processing
- Processing time and byte size reduction

**INFO:**
- Downscaling operations (log every downscale)
- Aggressive downscaling triggered

**WARNING:**
- Image processing failures (fall back to original)
- Unusually large images (>20MB)

**ERROR:**
- ImageProcessingError exceptions
- Unexpected errors in image processing

### Performance Monitoring

**Metrics to Track:**
```python
# In AsyncChapterLoader after resolve_images_in_html():
cache_stats = self._cache_manager.images.stats()
logger.debug(
    "ImageCache stats: %d images, %.1f MB, %.1f%% hit rate",
    cache_stats["size"],
    cache_stats["memory_mb"],
    cache_stats["hit_rate"],
)
```

**Performance Test Baseline (Mamba Mentality - 201MB EPUB):**
- Before: 559MB peak memory
- After (expected): 160-210MB peak memory
- ImageCache hit rate: Expect >60% on re-reading chapters
- Processing overhead: +10-50ms per image (first load only)

---

## Phase 2 Considerations (Lazy Loading)

### QTextBrowser Limitations 🚨

After architectural review, identified **critical constraint**:

**QTextBrowser does NOT support:**
- JavaScript execution
- HTML5 `loading="lazy"` attribute
- Dynamic DOM updates (setHtml() replaces entire document)

**This means:**
- ❌ Spec's Option A (HTML5 lazy loading): **Won't work**
- ❌ Spec's Option B (Scroll detection + img replacement): **Won't work**
- ⚠️ Spec's Option C (Progressive loading): Possible but loads all images

### Path Forward for Phase 2

**Option 1: Upgrade to QWebEngineView** (recommended if true lazy loading needed)
- Full Chromium engine, supports modern HTML/JS/CSS
- Can dynamically update DOM via JavaScript
- True lazy loading possible (load on scroll)
- **Trade-off:** Heavier dependency (~100MB), more complex integration

**Option 2: Progressive Loading with QTextBrowser** (keep current widget)
- Load text immediately, re-render HTML as each image processes
- Still loads all images, but shows them progressively
- Better UX (text appears fast), but no memory savings
- **Trade-off:** Multiple setHtml() calls might flicker

**Option 3: Defer Phase 2** (recommended for MVP)
- Phase 1 downscaling already achieves 60-70% memory reduction
- True page-based pagination (#31) might change rendering approach
- Reassess lazy loading after pagination implementation
- **Trade-off:** No progressive loading UX in MVP

**Recommendation:** Implement Phase 1, measure results, then decide:
- If memory <200MB with downscaling alone → Skip Phase 2
- If memory still high → Evaluate QWebEngineView migration
- If pagination changes rendering → Defer until pagination complete

---

## Open Questions (Resolved)

### 1. Cache Key for Images ✅
**Q:** Use `filepath:image_path` or generate stable book ID?
**A:** Use filepath for Phase 1 (simpler). Add book ID hash in Phase 3 if file moves become an issue.

### 2. Error Handling Policy ✅
**Q:** If image processing fails, show placeholder or keep original?
**A:** Keep original bytes (fall back), log warning. Better than broken images.

### 3. Configuration Location ✅
**Q:** Hardcode 1920×1080 or make configurable?
**A:** Hardcode for Phase 1, add ImageConfig in Phase 3 when we have UI for settings.

### 4. Aggressive Downscaling Threshold ✅
**Q:** What dimensions for >10MB images?
**A:** 1280×720 (720p resolution). Still good quality, ~half the pixels of 1080p.

### 5. Format Preservation ✅
**Q:** Always preserve format, or convert PNG→JPEG for large images?
**A:** Phase 1 preserves format. Phase 3 adds intelligent conversion.

---

## References

### Internal Documents
- [Performance Summary](../testing/performance-summary.md) - Profiling data
- [Chapter Caching System](./chapter-caching-system.md) - Multi-layer cache architecture
- [EPUB Rendering Architecture](./epub-rendering-architecture.md) - Current rendering flow
- [Image Optimization Spec](../specs/image-optimization.md) - Feature specification

### External Resources
- [Pillow Documentation](https://pillow.readthedocs.io/) - Image processing library
- [Pillow Resize Performance](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters) - Resampling algorithms
- [QTextBrowser Limitations](https://doc.qt.io/qt-6/qtextbrowser.html) - Widget capabilities
- [QWebEngineView](https://doc.qt.io/qt-6/qwebengineview.html) - Alternative rendering widget

---

## Related Work

**Issues:**
- #43: Image Optimization Phase 1: Downscaling (this implementation)
- #44: Image Optimization Phase 2: Lazy Loading (reassess after Phase 1)
- #45: Image Optimization Phase 3: Format Optimization (optional)
- #31: True Page-Based Pagination (may affect Phase 2 approach)

**Completed:**
- #28: Phase 2 Memory Monitor (monitoring infrastructure in place)
- #29: Phase 3 Multi-Layer Caching (ImageCache ready to use)

---

**Last Updated:** 2025-12-05
**Status:** Ready for Implementation
**Next Steps:**
1. Add Pillow dependency: `uv add pillow`
2. Create `image_processor.py` with unit tests
3. Modify `html_resources.py` to integrate processing
4. Wire up `async_loader.py` to pass ImageCache
5. Run performance tests (Mamba Mentality comparison)
6. Update performance-summary.md with results
