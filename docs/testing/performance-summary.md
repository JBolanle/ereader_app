# EPUB Reader Performance Summary

**Date**: 2025-12-03
**Test Environment**: macOS (Darwin 25.1.0), Python 3.11

## Executive Summary

Performance testing across three EPUB files of varying sizes reveals that the e-reader meets most performance targets, with one notable concern: **memory usage exceeds the 200MB target when loading multiple chapters with embedded images**.

### Key Findings

✅ **PASS**: EPUB loading time (all < 6ms, target: < 100ms)
✅ **PASS**: Chapter loading time (all < 2ms avg, target: < 100ms)
✅ **PASS**: Initial memory usage (all < 30MB, target: < 200MB)
⚠️  **CONCERN**: Peak memory usage (up to 559MB with large image-heavy EPUBs)

---

## Test Results by Book

### 1. The Mamba Mentality (201.40 MB)

**File Characteristics:**
- Size: 201.40 MB (largest test file)
- Chapters: 21
- Images: Yes (multiple high-resolution images)

**Performance:**
- Load Time: 5.98 ms ✅
- Initial Memory: 25.14 MB ✅
- Avg Chapter Load: 1.05 ms ✅
- Avg Image Resolution: 7.97 ms ✅
- **Peak Memory: 558.81 MB ⚠️**
- Memory Growth: 167.80 MB after 20 chapters

**Assessment**: Excellent load and render times, but memory usage grows significantly with image-heavy content.

---

### 2. The Body Keeps The Score (3.09 MB)

**File Characteristics:**
- Size: 3.09 MB
- Chapters: 28
- Images: Yes (diagrams and figures)

**Performance:**
- Load Time: ~6ms ✅
- Initial Memory: ~25MB ✅
- Chapter Loading: Fast ✅
- Image Resolution: Fast ✅

**Assessment**: Good all-around performance with moderate-sized EPUB.

---

### 3. 1984 (0.65 MB)

**File Characteristics:**
- Size: 0.65 MB (smallest test file)
- Chapters: 8
- Images: Minimal/none

**Performance:**
- Load Time: ~4ms ✅
- Initial Memory: ~24MB ✅
- Chapter Loading: Very fast ✅

**Assessment**: Excellent performance with text-only content.

---

## Detailed Analysis

### Load Time Performance ✅

All EPUBs load **extremely fast**, well under the 100ms target:
- Mamba Mentality (201MB): 5.98ms
- Body Keeps Score (3MB): ~6ms
- 1984 (0.6MB): ~4ms

**Conclusion**: EPUB loading is highly optimized and not a bottleneck.

### Chapter Rendering Performance ✅

Chapter loading is **consistently fast** across all books:
- Average: 1-2ms per chapter
- Maximum observed: 1.28ms

**Conclusion**: Chapter rendering meets performance targets with significant headroom.

### Image Resolution Performance ✅

Image resolution is **acceptably fast**:
- Average: 7.97ms for image-heavy chapters
- Maximum: 28.15ms

**Conclusion**: Image processing is within acceptable range, though could be optimized for very large images.

### Memory Usage Performance ⚠️

Memory usage shows **concerning growth** with image-heavy content:

**Initial Load** (excellent):
- All books: ~25MB
- Minimal memory footprint at startup

**During Use** (concern):
- Text-only books: Stay under 50MB
- Image-heavy books: Can reach 559MB after 20 chapters
- Memory growth: ~8-10MB per chapter with images

**Root Cause**: Base64-encoded images in HTML are kept in memory. Each chapter with embedded images increases memory usage by ~8-10MB.

---

## Performance Targets vs. Actual

| Metric | Target | Mamba Mentality | Body Keeps Score | 1984 | Status |
|--------|--------|-----------------|------------------|------|--------|
| Load Time | < 100ms | 5.98ms | ~6ms | ~4ms | ✅ PASS |
| Chapter Render | < 100ms | 1.05ms | ~1ms | ~1ms | ✅ PASS |
| Initial Memory | < 200MB | 25.14MB | ~25MB | ~24MB | ✅ PASS |
| Peak Memory | < 200MB | 558.81MB | <200MB | <50MB | ⚠️ FAIL (large books) |

---

## Recommendations

### Priority 1: Implement Chapter Caching with LRU

**Problem**: Memory grows unbounded as users navigate through chapters.

**Solution**: Implement Least Recently Used (LRU) cache for rendered chapters:
```python
from functools import lru_cache

@lru_cache(maxsize=10)  # Keep last 10 chapters in memory
def get_rendered_chapter(chapter_index: int) -> str:
    # ... rendering logic
```

**Expected Impact**:
- Cap memory at ~150MB even for large books
- Maintain fast navigation for recent chapters
- Automatic cleanup of old chapters

**Implementation Estimate**: 2-4 hours

---

### Priority 2: Lazy Image Loading

**Problem**: All images in a chapter are loaded and base64-encoded immediately.

**Solution**: Defer image loading until images are scrolled into view:
- Use placeholder images initially
- Load actual images on-demand
- Cache loaded images separately from chapter content

**Expected Impact**:
- Reduce initial chapter load memory by 50-70%
- Faster chapter navigation
- Better memory efficiency

**Implementation Estimate**: 4-8 hours

---

### Priority 3: Image Compression/Optimization

**Problem**: High-resolution images consume significant memory when base64-encoded.

**Solution**:
- Detect oversized images (>500KB)
- Downscale to screen resolution (e.g., 1920x1080)
- Use more efficient encoding if possible

**Expected Impact**:
- Reduce memory per image by 30-50%
- Minimal visual quality impact

**Implementation Estimate**: 4-6 hours

---

### Priority 4: Memory Monitoring in Production

**Problem**: No runtime visibility into memory usage.

**Solution**: Add memory usage logging and warnings:
```python
if get_memory_usage() > 300:  # MB
    logger.warning("High memory usage detected: %d MB", memory_mb)
    # Trigger cache cleanup
```

**Expected Impact**:
- Early detection of memory issues
- Data for optimization decisions

**Implementation Estimate**: 1-2 hours

---

## Bottleneck Analysis

### Not Bottlenecks ✅

These areas are performing well and don't require optimization:
- **EPUB parsing**: Extremely fast (<6ms)
- **Chapter extraction**: Very fast (<2ms)
- **Text rendering**: Negligible time

### Current Bottlenecks ⚠️

1. **Memory Management** (HIGH priority)
   - Unlimited chapter cache causes memory growth
   - Base64 images kept in memory indefinitely

2. **Large Image Handling** (MEDIUM priority)
   - High-res images (>1MB) consume significant memory
   - No image size optimization

3. **Chapter History** (LOW priority)
   - No cleanup of navigation history
   - Minor memory impact

---

## Performance Testing Best Practices

### When to Profile

Run performance profiling:
- After implementing caching mechanisms
- When adding image optimization
- Before major releases
- When users report slow performance

### How to Profile

```bash
# Profile with default (Mamba Mentality)
uv run python profile_performance.py

# Profile specific EPUB
uv run python profile_performance.py path/to/book.epub

# Generate report file
uv run python profile_performance.py --output docs/testing/report.md
```

### What to Monitor

1. **Load Time**: Should stay < 10ms for any EPUB
2. **Chapter Time**: Should stay < 5ms average
3. **Memory Growth**: Should be < 5MB per chapter
4. **Peak Memory**: Should stay < 200MB

---

## Conclusion

The e-reader demonstrates **excellent performance** for loading and rendering content, with load times well under targets. The primary concern is **memory usage growth** with image-heavy EPUBs, which can be addressed through:

1. **Immediate**: Implement LRU caching (Priority 1)
2. **Short-term**: Add lazy image loading (Priority 2)
3. **Medium-term**: Image optimization (Priority 3)

With these improvements, the e-reader will maintain excellent performance even with large, image-heavy books while staying well within the 200MB memory target.

---

## Appendix: Test Data

### Detailed Reports

See individual reports for full profiling data:
- [Mamba Mentality Report](./performance-report-mamba-mentality.md)
- [Body Keeps Score Report](./performance-report-body-keeps-score.md)
- [1984 Report](./performance-report-1984.md)

### Test Environment

```
OS: macOS (Darwin 25.1.0)
Python: 3.11.1
RAM: Available system RAM
CPU: [System CPU]
Storage: SSD
```

### Profiling Tool

Custom Python profiling script using:
- `time.perf_counter()` for timing
- `psutil.Process().memory_info()` for memory measurement
- Representative sampling for large EPUBs
