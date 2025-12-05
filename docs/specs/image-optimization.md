# Feature: Image Optimization

## Overview

Optimize image handling in the e-reader to reduce memory usage, improve rendering performance, and enhance user experience when reading image-heavy EPUBs. This feature builds on the existing multi-layer caching architecture (Phases 1-3) to add intelligent image processing and optimization.

**Context:** Performance profiling revealed that large, high-resolution images in EPUBs contribute significantly to memory usage. While the multi-layer caching system (completed) caps overall memory, individual images can be wasteful. The current implementation:
- Loads all images in a chapter immediately (no lazy loading)
- Encodes images as base64 without size optimization (~33% overhead)
- Does not downscale oversized images
- Image cache infrastructure exists but is not yet utilized

**Goal:** Reduce per-image memory footprint and enable smarter image loading strategies while maintaining visual quality for reading.

---

## User Stories

- **As a reader**, I want to view image-heavy books without the app consuming excessive memory so that my system stays responsive.
- **As a reader**, I want images to load quickly when I scroll to them so that my reading flow is not interrupted.
- **As a reader**, I want high-quality images to display properly without pixelation so that diagrams and photos are clear.
- **As a reader with limited system resources**, I want the app to automatically optimize large images so that I can read books with high-res photos without performance degradation.

---

## Acceptance Criteria

### Core Functionality
- [ ] **Image Downscaling**: Images larger than screen resolution are automatically downscaled before base64 encoding
- [ ] **Lazy Image Loading**: Images load on-demand as they become visible in the viewport (not all at once)
- [ ] **Placeholder Rendering**: Show lightweight placeholders for images that haven't loaded yet
- [ ] **Progressive Enhancement**: Text content displays immediately, images load in background
- [ ] **Image Cache Utilization**: Processed images are stored in the existing ImageCache to avoid re-processing

### Performance Targets
- [ ] **Memory Reduction**: 30-50% reduction in per-chapter memory usage for image-heavy content
- [ ] **Render Speed**: Initial chapter text renders in <50ms (before images)
- [ ] **Image Load Time**: Individual image processing <100ms for typical images
- [ ] **No Visual Regression**: Downscaled images maintain acceptable quality for reading (no artifacts)

### Edge Cases
- [ ] **Missing Images**: Graceful fallback when image cannot be loaded (show broken image icon or placeholder)
- [ ] **Corrupted Images**: Handle corrupted image data without crashing
- [ ] **Oversized Images**: Images >10MB are downscaled aggressively to prevent memory spikes
- [ ] **SVG Images**: SVG images are not downscaled (they're vector-based)
- [ ] **Mixed Content**: Chapters with text + images don't block text rendering on slow image processing
- [ ] **Rapid Navigation**: Switching chapters before images load cancels pending image operations

---

## Implementation Phases

### Phase 1: Image Downscaling (Priority 2)

**Goal:** Reduce memory footprint of large images by downscaling before base64 encoding.

**Tasks:**
1. Add image dimension detection using PIL/Pillow
2. Implement downscaling logic:
   - Detect screen resolution (or use sensible max: 1920x1080)
   - Calculate target size maintaining aspect ratio
   - Downscale if image exceeds target
   - Skip SVG images (vector-based)
3. Integrate downscaling into `resolve_images_in_html()`
4. Add configuration for max image dimensions
5. Update ImageCache to store processed images
6. Add tests for downscaling logic (various sizes, aspect ratios, formats)
7. Performance test with large image EPUBs (e.g., Mamba Mentality)

**Estimated Effort:** Medium (6-8 hours)

**Dependencies:**
- Add `Pillow` library (`uv add pillow`)
- Existing ImageCache (Phase 3 - completed)

**Files to Modify:**
- `src/ereader/utils/html_resources.py` - Add downscaling to image resolution
- `src/ereader/utils/image_cache.py` - May need cache key adjustments
- `tests/test_utils/test_html_resources.py` - Add downscaling tests

---

### Phase 2: Lazy Image Loading (Priority 2)

**Goal:** Load images on-demand as they become visible in the viewport, reducing initial chapter load time and memory.

**Tasks:**
1. Research lazy loading approaches for QTextBrowser:
   - Option A: JavaScript-based (if QTextBrowser supports)
   - Option B: Custom scrolling detection in BookViewer
   - Option C: Placeholder images initially, replace on scroll
2. Implement placeholder HTML for unloaded images
3. Add scroll position monitoring in BookViewer
4. Implement image loading trigger when images enter viewport
5. Replace placeholders with actual images asynchronously
6. Update ImageCache to distinguish between placeholders and loaded images
7. Handle rapid scrolling (debounce/throttle load requests)
8. Add tests for lazy loading behavior
9. Performance test: compare initial load time with/without lazy loading

**Estimated Effort:** Large (10-12 hours)

**Dependencies:**
- Phase 1 (downscaling) - should complete first for maximum benefit
- May require async/await integration (builds on existing async loader architecture)
- QTextBrowser API research for dynamic content updates

**Files to Modify:**
- `src/ereader/utils/html_resources.py` - Add placeholder generation
- `src/ereader/views/book_viewer.py` - Add scroll monitoring and image loading triggers
- `src/ereader/utils/async_loader.py` - Add async image loading support
- `tests/test_views/test_book_viewer.py` - Add lazy loading tests

**Open Questions:**
1. Does QTextBrowser support JavaScript-based lazy loading? (Research needed)
2. Should we use `<img loading="lazy">` HTML attribute? (Browser support needed)
3. How do we handle images that are fully visible in initial viewport?
4. Should placeholder images have visual indicators (loading spinner)?

---

### Phase 3: Image Format Optimization (Priority 3)

**Goal:** Use more efficient image formats and compression for base64 encoding.

**Tasks:**
1. Analyze image formats in typical EPUBs (JPEG, PNG, GIF, WebP)
2. Implement format conversion:
   - Convert PNG to JPEG for photos (where appropriate)
   - Preserve PNG for transparency/diagrams
   - Use WebP if browser supports (detect capability)
3. Add quality-based compression for JPEG images
4. Implement size-vs-quality heuristics (e.g., larger images get lower quality)
5. Add configuration for compression quality levels
6. Update ImageCache to store format metadata
7. Add tests for format conversion and quality settings
8. Performance test: measure memory reduction vs. quality tradeoff

**Estimated Effort:** Medium (6-8 hours)

**Dependencies:**
- Phase 1 (downscaling) - builds on image processing pipeline
- Pillow library (already added in Phase 1)
- QTextBrowser format support verification

**Files to Modify:**
- `src/ereader/utils/html_resources.py` - Add format conversion logic
- New file: `src/ereader/utils/image_processor.py` - Extract image processing logic
- `tests/test_utils/test_image_processor.py` - Test format conversion

**Deferred:**
- WebP support (check QTextBrowser compatibility first)
- User-configurable quality settings (MVP uses sensible defaults)

---

## Technical Design

### Image Processing Pipeline

**Current Flow:**
```
Chapter HTML → resolve_images_in_html() → Base64 encode → Embed in HTML
```

**Optimized Flow (Phase 1):**
```
Chapter HTML → resolve_images_in_html() →
  Check ImageCache →
    MISS: Load image → Downscale if needed → Base64 encode → Store in ImageCache → Embed
    HIT: Retrieve from ImageCache → Embed
```

**Optimized Flow (Phase 2 - Lazy Loading):**
```
Chapter HTML → resolve_images_in_html() →
  Generate placeholders for images → Render HTML with placeholders →
  User scrolls → Images enter viewport → Trigger async load →
    Check ImageCache →
      MISS: Load → Downscale → Base64 → Cache → Replace placeholder
      HIT: Retrieve → Replace placeholder
```

---

### Image Downscaling Algorithm (Phase 1)

```python
def downscale_image(image_data: bytes, max_width: int = 1920, max_height: int = 1080) -> bytes:
    """Downscale image if it exceeds maximum dimensions.

    Args:
        image_data: Raw image bytes
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels

    Returns:
        Downscaled image bytes (or original if within limits)
    """
    # Open image with Pillow
    img = Image.open(BytesIO(image_data))

    # Skip if already small enough
    if img.width <= max_width and img.height <= max_height:
        return image_data

    # Calculate new size maintaining aspect ratio
    ratio = min(max_width / img.width, max_height / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))

    # Downscale using high-quality resampling
    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

    # Save to bytes
    output = BytesIO()
    img_resized.save(output, format=img.format or 'JPEG')
    return output.getvalue()
```

**Key Decisions:**
- Default max: 1920x1080 (common screen resolution)
- Use LANCZOS resampling (high quality)
- Preserve original format (JPEG stays JPEG, PNG stays PNG)
- Skip if already within limits (avoid unnecessary processing)

---

### Lazy Loading Strategies (Phase 2)

#### Option A: HTML5 Native Lazy Loading
```html
<img src="data:..." loading="lazy" />
```
**Pros:** Simple, browser-native, no JavaScript
**Cons:** May not work in QTextBrowser (needs verification)

#### Option B: Placeholder + Scroll Detection
```python
# Initial HTML
<img src="placeholder.png" data-real-src="images/photo.jpg" class="lazy-image" />

# In BookViewer scroll event handler
def on_scroll():
    visible_images = detect_visible_images()
    for img in visible_images:
        if not img.loaded:
            real_src = img.getAttribute("data-real-src")
            load_and_replace_image(real_src, img)
```
**Pros:** Full control, works in any widget
**Cons:** More complex, custom implementation

#### Option C: Async Background Loading
```python
# Load all images in background, replace as they complete
async def load_chapter_images(chapter_html: str):
    images = extract_image_references(chapter_html)
    for img_src in images:
        img_data = await load_image_async(img_src)
        emit_signal_to_replace_placeholder(img_src, img_data)
```
**Pros:** Progressive enhancement, smoother UX
**Cons:** All images still load (not truly "lazy")

**Recommended:** Start with Option B (most control), evaluate Option A if QTextBrowser supports it.

---

### Configuration

Add to a future `ImageConfig` class (or ReaderController settings):

```python
@dataclass
class ImageConfig:
    """Image processing configuration."""

    # Downscaling
    max_image_width: int = 1920
    max_image_height: int = 1080
    downscale_threshold_kb: int = 500  # Only downscale if >500KB

    # Lazy loading
    enable_lazy_loading: bool = True
    lazy_load_buffer_px: int = 200  # Load images 200px before visible

    # Compression (Phase 3)
    jpeg_quality: int = 85  # 0-100
    png_to_jpeg_threshold_kb: int = 1000  # Convert large PNGs to JPEG

    # Memory
    image_cache_max_mb: int = 50  # Already exists in ImageCache
```

**For MVP:** Hardcode sensible defaults, add UI configuration later.

---

## Edge Cases

### 1. Missing Images
**Scenario:** Image referenced in HTML doesn't exist in EPUB
**Current Behavior:** Logs warning, keeps original `<img>` tag (may show broken image)
**Desired Behavior:** Show placeholder with "Image not found" text
**Implementation:** Add fallback placeholder in `resolve_images_in_html()`

### 2. Corrupted Image Data
**Scenario:** Image file exists but data is corrupted
**Current Behavior:** May crash on base64 encoding or Pillow processing
**Desired Behavior:** Log error, show "Image corrupted" placeholder
**Implementation:** Wrap Pillow operations in try/except, catch `PIL.UnidentifiedImageError`

### 3. Extremely Large Images (>10MB)
**Scenario:** EPUB contains very high-res images (e.g., 8000x6000 photo)
**Current Behavior:** Loads into memory, causes memory spike
**Desired Behavior:** Aggressively downscale before processing
**Implementation:** Add size check, use lower max dimensions for huge images

### 4. SVG Images
**Scenario:** Vector graphics (SVG) should not be downscaled
**Current Behavior:** Attempts to process as raster image
**Desired Behavior:** Skip downscaling for SVGs (they scale perfectly)
**Implementation:** Check MIME type, skip Pillow processing for `image/svg+xml`

### 5. Animated GIFs
**Scenario:** EPUB contains animated GIF
**Current Behavior:** May only encode first frame
**Desired Behavior:** Preserve animation (or gracefully degrade to static)
**Implementation:** Special handling for GIFs (Pillow can handle, but may need `save_all=True`)

### 6. Rapid Chapter Navigation
**Scenario:** User switches chapters quickly before images finish loading
**Current Behavior:** Images from old chapter may still be loading
**Desired Behavior:** Cancel pending image loads, load new chapter's images
**Implementation:** Add task cancellation in async loader, clear pending requests on chapter change

---

## Out of Scope

**Not included in this feature:**

1. **User-configurable image settings UI** - Future enhancement (after MVP proves value)
2. **Disk-based image cache** - Keep in-memory only for MVP
3. **Image pre-fetching** - Don't pre-load next chapter's images (optimize current first)
4. **Image zooming/panning** - Separate feature (image viewer enhancement)
5. **Image metadata extraction** - Not needed for rendering optimization
6. **Thumbnail generation** - Not needed for reading view
7. **WebP format conversion** - Deferred until QTextBrowser support verified
8. **External image loading** - Only handle embedded EPUB images

---

## Dependencies

### New Dependencies
- **Pillow** (PIL fork): `uv add pillow`
  - Purpose: Image dimension detection, downscaling, format conversion
  - License: PIL License (permissive)
  - Size: ~3MB installed

### Existing Systems
- ✅ ImageCache (Phase 3) - Already implemented
- ✅ Multi-layer caching architecture - Already implemented
- ✅ MemoryMonitor - Already implemented
- ✅ AsyncLoader - Already implemented (may need extensions for image loading)

---

## Testing Strategy

### Unit Tests

**New Test Files:**
- `tests/test_utils/test_image_processor.py` - Image downscaling, format detection, optimization logic

**Updated Test Files:**
- `tests/test_utils/test_html_resources.py` - Add downscaling tests, lazy loading placeholder tests
- `tests/test_utils/test_image_cache.py` - Verify processed image caching

**Test Cases:**
1. **Downscaling:**
   - Image within limits (no downscaling)
   - Image exceeds width only
   - Image exceeds height only
   - Image exceeds both dimensions
   - Aspect ratio preservation
   - Various formats (JPEG, PNG, GIF)
   - SVG images (skip downscaling)

2. **Lazy Loading:**
   - Placeholder generation
   - Image loading on scroll
   - Multiple images in viewport
   - Rapid scrolling (load cancellation)

3. **Edge Cases:**
   - Missing image handling
   - Corrupted image data
   - Extremely large images (>10MB)
   - Zero-byte images
   - Invalid MIME types

### Integration Tests

**Test Files:**
- `tests/test_controllers/test_reader_controller.py` - Verify optimized images integrate with caching

**Test Scenarios:**
1. Load image-heavy chapter, verify downscaling applied
2. Navigate through multiple chapters, verify ImageCache utilization
3. Check memory usage with/without optimization
4. Lazy loading integration with BookViewer scrolling

### Performance Tests

**Update:** `scripts/profile_performance.py`

**Metrics to Track:**
1. **Memory Usage:**
   - Before optimization: ~559MB peak (Mamba Mentality)
   - After downscaling: Target ~350-400MB (30-40% reduction)
   - After lazy loading: Target ~200-250MB (depends on viewport)

2. **Render Speed:**
   - Initial chapter text render: <50ms (text only)
   - Per-image load time: <100ms
   - Full chapter with images: <500ms (progressive)

3. **Cache Hit Rates:**
   - Image cache hits: >60% for repeated viewing
   - ImageCache memory utilization: 70-90% of budget

**Test Books:**
- The Mamba Mentality (201MB, high-res images) - Primary test case
- The Body Keeps Score (3MB, diagrams) - Moderate images
- 1984 (0.65MB, minimal images) - Baseline (should not regress)

---

## Success Metrics

### Quantitative
- [ ] Memory reduction: 30-50% for image-heavy books
- [ ] Cache hit rate: >60% for ImageCache
- [ ] Initial render time: <50ms for text (before images)
- [ ] No linting errors, 80%+ test coverage
- [ ] All performance tests pass with new targets

### Qualitative
- [ ] No visible quality degradation in downscaled images
- [ ] Smooth reading experience (no janky image loading)
- [ ] Fast chapter navigation (text appears immediately)
- [ ] Professional feel (progressive enhancement, not broken placeholders)

---

## Rollout Plan

### Phase 1: Downscaling (First PR)
1. Add Pillow dependency
2. Implement downscaling logic
3. Integrate with ImageCache
4. Add unit tests (100% coverage of downscaling)
5. Performance test with Mamba Mentality
6. Create PR with before/after memory comparison

### Phase 2: Lazy Loading (Second PR)
1. Research QTextBrowser lazy loading capabilities
2. Implement chosen strategy (likely placeholder-based)
3. Add scroll detection in BookViewer
4. Integrate with async loader
5. Add integration tests
6. Performance test for initial render time
7. Create PR with UX evaluation

### Phase 3: Format Optimization (Third PR - Optional)
1. Implement format conversion logic
2. Add quality-based compression
3. Test across different image types
4. Performance test for size vs. quality
5. Create PR if benefits justify complexity

---

## Architecture Decision Record

**Decision:** Implement image optimization in three phases (downscaling → lazy loading → format optimization)

**Rationale:**
1. **Incremental Value:** Each phase provides independent benefits
2. **Risk Mitigation:** Downscaling is low-risk, lazy loading is complex (isolate)
3. **Learning Opportunity:** Phases align with learning goals (PIL, async, optimization)
4. **Testability:** Easier to test and measure each phase independently
5. **Flexibility:** Can stop after Phase 2 if Phase 3 doesn't justify effort

**Alternatives Considered:**
- All-in-one implementation - Rejected: Too risky, harder to debug
- Lazy loading only - Rejected: Doesn't solve large image memory issue
- Format conversion first - Rejected: Smaller wins than downscaling

**Consequences:**
- Three separate PRs (more overhead, better isolation)
- ImageCache infrastructure used progressively (not all at once)
- Performance improvements compound across phases

---

## Related Work

### Existing Issues
- Issue #31: True page-based pagination - May interact with lazy loading (scroll vs. page)
- Performance profiling (completed): Identified image memory as priority optimization

### Future Enhancements
- User-configurable image quality settings
- Image pre-fetching for next chapter
- Disk-based image cache (faster app startup)
- Image viewer with zoom/pan controls
- Reading mode: "Low memory mode" (aggressive optimization)

---

## References

### External Documentation
- [Pillow Documentation](https://pillow.readthedocs.io/) - Image processing
- [Lazy Loading Best Practices](https://web.dev/lazy-loading/) - Web standards
- [QTextBrowser Docs](https://doc.qt.io/qt-6/qtextbrowser.html) - Widget capabilities

### Internal Documentation
- [Performance Summary](../testing/performance-summary.md) - Original profiling data
- [Chapter Caching System](../architecture/chapter-caching-system.md) - Multi-layer cache architecture
- [EPUB Rendering Architecture](../architecture/epub-rendering-architecture.md) - Image resolution flow

---

## Implementation Guidance

### Recommended Commands
1. **Start Planning:** `/architect` - Design image processing component structure
2. **Research Phase:** `/study` - Deep dive into Pillow API and lazy loading techniques
3. **Implementation:** `/developer` - Implement Phase 1 with full workflow
4. **UX Evaluation:** `/ux evaluate` - After Phase 2, verify loading experience
5. **Quality Check:** `/test` + `/code-review` before each PR

### Learning Opportunities
- **Pillow Library:** Learn image processing fundamentals (resize, format conversion, quality)
- **Lazy Loading:** Understand viewport detection, async loading patterns
- **Optimization Tradeoffs:** Practice balancing memory vs. quality vs. performance
- **Progressive Enhancement:** Learn UX pattern for incremental content loading

### Suggested Workflow
1. **Phase 1 Branch:** `feature/image-downscaling`
   - Start with `/architect` for image processor design
   - TDD: Write tests for downscaling first, then implement
   - Use `/test` frequently (run after each function)
   - Performance test: Compare before/after on Mamba Mentality
   - `/code-review` before PR

2. **Phase 2 Branch:** `feature/lazy-image-loading`
   - Start with `/ux research` for lazy loading best practices
   - Research QTextBrowser capabilities (can it update HTML dynamically?)
   - Use `/architect` for integration design
   - Complex implementation: Use `/mentor` if stuck on async patterns
   - UX test: Does it "feel" smooth? Use `/ux evaluate`

3. **Phase 3 Branch:** `feature/image-format-optimization` (optional)
   - Evaluate Phase 1 & 2 results first (is this needed?)
   - If proceeding: Start with quality benchmarking (find optimal JPEG quality)
   - Implement incrementally: JPEG quality → Format conversion → Compression
   - A/B test: Visual quality comparison across quality levels

---

## Open Questions

### Must Resolve Before Implementation

1. **QTextBrowser Dynamic Updates:**
   - Q: Can QTextBrowser update `<img src>` dynamically after initial render?
   - A: Research needed - critical for lazy loading strategy choice
   - Action: Test with simple QTextBrowser example before Phase 2

2. **Async Integration:**
   - Q: Should image loading use existing AsyncLoader or new mechanism?
   - A: TBD - depends on QTextBrowser threading constraints
   - Action: Review AsyncLoader architecture, check Qt threading model

3. **Screen Resolution Detection:**
   - Q: How do we detect user's screen resolution for downscaling max?
   - A: Qt provides `QScreen.size()` - verify in PyQt6
   - Action: Simple test to get screen dimensions

4. **Placeholder Appearance:**
   - Q: What should lazy loading placeholders look like?
   - A: Options: Blank, "Loading...", spinner, low-res version
   - Action: Use `/ux design` for placeholder design decision

### Nice to Resolve

5. **WebP Support:**
   - Q: Does QTextBrowser support WebP images?
   - A: Unknown - defer to Phase 3
   - Action: Test WebP rendering if Phase 3 proceeds

6. **Cache Key Strategy:**
   - Q: Should downscaled images have different cache keys than originals?
   - A: Probably yes (include dimensions in key)
   - Action: Design cache key format in Phase 1 architecture

---

## Notes for Future Maintainers

### Why Three Phases?

This spec breaks image optimization into three phases intentionally:

- **Phase 1 (Downscaling)** is the highest ROI with lowest risk - do this first
- **Phase 2 (Lazy Loading)** is complex but enables true progressive enhancement
- **Phase 3 (Format Optimization)** is polish - only do if Phases 1-2 don't hit targets

Each phase can ship independently. If we hit memory targets after Phase 1, we might skip Phase 2. If lazy loading proves too complex, we can defer it.

### Configuration Philosophy

The spec mentions `ImageConfig` but recommends hardcoding defaults for MVP. This is intentional:

- **YAGNI:** Don't build configuration UI until we know defaults work
- **Learning:** Better to understand optimal values first, then parameterize
- **Simplicity:** Fewer variables = easier debugging

Add configuration in a future enhancement if user feedback indicates need.

### Testing Approach

This feature is performance-critical, so testing strategy emphasizes:

1. **Unit tests:** Verify correctness of image processing logic
2. **Integration tests:** Verify caching and loading behavior
3. **Performance tests:** Measure actual memory and speed improvements

Don't skip performance testing - that's how we validate the optimization works.

---

**Last Updated:** 2025-12-05
**Status:** Draft - Ready for Architecture Planning
**Next Steps:**
1. Review and refine spec with `/architect`
2. Create GitHub issues for each phase
3. Begin Phase 1 implementation
