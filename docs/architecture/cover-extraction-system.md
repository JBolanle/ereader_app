# Cover Extraction System Architecture

## Date
2025-12-15

## Context

The library grid currently displays book cards with placeholder covers (gray rectangle with book emoji). We need to extract actual cover images from EPUB files and display them in the book cards for a more professional, visually appealing library experience.

### Requirements

1. Extract cover images from EPUBs during the import process
2. Handle multiple EPUB cover specifications (EPUB 2, EPUB 3, fallbacks)
3. Cache extracted covers to disk for fast loading
4. Display cached covers in BookCard Delegate
5. Fallback gracefully to placeholder if no cover found or loading fails
6. Maintain good performance during import (target: <200ms overhead per book)

### Constraints

- EPUB cover specifications vary significantly across publishers
- Some EPUBs may not have covers at all
- Import process should remain reasonably fast
- Cover cache should be persistent and survive app restarts
- Must work with existing EPUBBook, LibraryController, BookCardDelegate

## EPUB Cover Specification Research

### EPUB 3 (Current Standard)

Covers are specified via `properties="cover-image"` attribute in manifest:

```xml
<manifest>
  <item id="cover" href="images/cover.jpg"
        media-type="image/jpeg" properties="cover-image"/>
</manifest>
```

**Detection:** Find manifest item with `properties` attribute containing "cover-image".

### EPUB 2 (Legacy)

Covers use a two-step reference:
1. Metadata contains `<meta name="cover" content="cover-id"/>`
2. Manifest item with id="cover-id" contains the cover href

```xml
<metadata>
  <meta name="cover" content="cover-image"/>
</metadata>
<manifest>
  <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg"/>
</manifest>
```

**Detection:**
1. Find `<meta name="cover">` in metadata
2. Get its `content` attribute (the item ID)
3. Look up that ID in manifest to get href

### Fallback Strategies

When standard methods fail, use heuristics:

1. **Filename heuristic:** Find images with "cover" in filename
   - Search manifest for items with media-type="image/*" and href containing "cover"
   - Examples: "cover.jpg", "Cover.png", "images/cover-front.jpeg"

2. **First image heuristic:** Use first image in reading order
   - Get first spine item
   - Parse its HTML
   - Find first `<img>` tag
   - Extract src attribute

**Note:** We'll implement strategies 1-2 for Phase 3. Strategy 3 (first image) deferred to future enhancement.

## Options Considered

### Option A: Extract During Import (Synchronous)

**Approach:**
- Extract covers immediately when book is imported
- Save to disk cache before adding to database
- Cover path is set in metadata at creation time

**Pros:**
- Simpler implementation (no threading/async needed)
- Covers ready immediately when library loads
- Consistent user experience (no delayed loading)
- Easy error handling (part of import error flow)

**Cons:**
- Slows down import process (~100-200ms per book)
- User waits longer during import
- Wasted work if covers are never viewed

**Performance Impact:**
- Single book import: +150ms (barely noticeable)
- 10 books: +1.5s (acceptable)
- 100 books: +15s (noticeable but acceptable for one-time operation)

### Option B: Extract On-Demand (Async)

**Approach:**
- Import books without extracting covers
- When book card is painted, trigger async cover extraction
- Update card when cover is ready

**Pros:**
- Fast imports (no cover extraction overhead)
- Only extract covers for viewed books
- More responsive initial library loading

**Cons:**
- Complex implementation (threading, signals, thread safety)
- UI jank/flicker as covers load
- Race conditions possible (multiple cards requesting same cover)
- Harder to test
- More error cases to handle

### Option C: Hybrid (Extract in Background Task)

**Approach:**
- Import books quickly (no cover extraction)
- Launch background thread to extract all covers
- Update library as covers become available

**Pros:**
- Fast initial import
- Eventually all covers are extracted
- No per-card complexity

**Cons:**
- Most complex implementation
- Still have UI updates/flicker
- Background task management
- What if user quits before completion?

## Decision

**Selected: Option A (Extract During Import)**

### Reasoning

1. **Simplicity trumps premature optimization**
   - Covers are a one-time extraction cost
   - 150ms per book is acceptable for a one-time import
   - Simpler code is easier to maintain and test

2. **User experience consistency**
   - Users see complete library immediately
   - No delayed loading or UI flicker
   - Predictable import time

3. **YAGNI principle**
   - Don't build async complexity until it's proven necessary
   - Can refactor to async later if imports become too slow
   - Start simple, optimize if needed

4. **Professional convention**
   - Similar apps (Calibre, Apple Books) extract covers during import
   - Users expect import to be "complete" when it finishes

### When to Reconsider

Revisit this decision if:
- Import times exceed 30 seconds for typical imports (>100 books)
- Users complain about slow imports
- We add batch import feature (drag 1000 books at once)

For those scenarios, implement Option C (background extraction).

## Architecture Design

### Component: CoverExtractor

**Location:** `src/ereader/utils/cover_extractor.py`

**Responsibility:** Extract cover image from EPUB using multiple strategies.

**Interface:**

```python
class CoverExtractor:
    """Extract cover images from EPUB files."""

    @staticmethod
    def extract_cover(epub_path: str | Path) -> tuple[bytes, str] | None:
        """Extract cover image from EPUB.

        Tries multiple extraction strategies in order:
        1. EPUB 3 properties="cover-image"
        2. EPUB 2 <meta name="cover">
        3. Filename heuristic ("cover" in filename)

        Args:
            epub_path: Path to EPUB file.

        Returns:
            Tuple of (image_bytes, file_extension) or None if no cover found.
            Example: (b'\\xff\\xd8\\xff...', 'jpg')

        Raises:
            FileNotFoundError: If EPUB doesn't exist.
            InvalidEPUBError: If file is not a valid EPUB.
        """

    @staticmethod
    def _try_epub3_cover(epub: EPUBBook) -> tuple[bytes, str] | None:
        """Try EPUB 3 properties='cover-image' method."""

    @staticmethod
    def _try_epub2_cover(epub: EPUBBook) -> tuple[bytes, str] | None:
        """Try EPUB 2 <meta name='cover'> method."""

    @staticmethod
    def _try_filename_heuristic(epub: EPUBBook) -> tuple[bytes, str] | None:
        """Try finding image with 'cover' in filename."""

    @staticmethod
    def _get_image_extension(media_type: str, href: str) -> str:
        """Get file extension from media-type or href."""
```

**Key Design Points:**

1. **Stateless utility class** - All methods are static, no instance state
2. **Returns bytes + extension** - Caller decides how to save
3. **Multiple extraction strategies** - Ordered from most specific to most general
4. **Detailed logging** - Log which strategy succeeded/failed for debugging

### Integration: LibraryController

**Changes to `import_books()` method:**

```python
def import_books(self, filepaths: list[str]) -> None:
    for filepath in filepaths:
        try:
            # Existing: Parse EPUB
            book = EPUBBook(filepath)

            # NEW: Extract cover
            cover_data = CoverExtractor.extract_cover(filepath)

            # Existing: Create metadata
            metadata = BookMetadata(...)

            # Existing: Add to database
            book_id = self._repository.add_book(metadata)

            # NEW: Save cover to cache if extracted
            if cover_data:
                cover_bytes, ext = cover_data
                cover_path = self._save_cover(book_id, cover_bytes, ext)
                # Update database with cover path
                self._repository.update_book(book_id, cover_path=cover_path)
        except Exception as e:
            # Handle errors
```

**New method:**

```python
def _save_cover(self, book_id: int, cover_bytes: bytes, extension: str) -> str:
    """Save cover image to cache directory.

    Args:
        book_id: Database ID of book.
        cover_bytes: Cover image data.
        extension: File extension (jpg, png, etc.).

    Returns:
        Absolute path to saved cover file.
    """
    covers_dir = Path.home() / ".ereader" / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)

    cover_path = covers_dir / f"{book_id}.{extension}"
    cover_path.write_bytes(cover_bytes)

    logger.info("Saved cover for book %d: %s", book_id, cover_path)
    return str(cover_path)
```

### Integration: BookCardDelegate

**Changes to `paint()` method:**

```python
def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
    book = index.data(Qt.ItemDataRole.UserRole)

    # ... existing code ...

    # Draw cover
    cover_rect = QRect(...)

    if book.cover_path and Path(book.cover_path).exists():
        # Load and display actual cover
        pixmap = QPixmap(book.cover_path)
        if not pixmap.isNull():
            # Scale to fit cover_rect while preserving aspect ratio
            scaled = pixmap.scaled(
                cover_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # Center in cover_rect
            x = cover_rect.x() + (cover_rect.width() - scaled.width()) // 2
            y = cover_rect.y() + (cover_rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            # Pixmap failed to load, use placeholder
            self._draw_placeholder_cover(painter, cover_rect)
    else:
        # No cover or file missing, use placeholder
        self._draw_placeholder_cover(painter, cover_rect)
```

**New method:**

```python
def _draw_placeholder_cover(self, painter: QPainter, cover_rect: QRect) -> None:
    """Draw placeholder cover (current implementation)."""
    painter.fillRect(cover_rect, QColor("#E0E0E0"))
    painter.setPen(QPen(QColor("#BDBDBD"), 1))
    painter.drawRect(cover_rect)
    painter.setPen(QColor("#757575"))
    icon_font = QFont("Arial", 48)
    painter.setFont(icon_font)
    painter.drawText(cover_rect, Qt.AlignmentFlag.AlignCenter, "📕")
```

### Cache Management

**Cache Directory:** `~/.ereader/covers/`

**File Naming:** `{book_id}.{ext}`
- Examples: `123.jpg`, `456.png`, `789.jpeg`
- Why book_id? Unique, survives file moves, simple to manage

**Cache Lifecycle:**
- **Created:** During book import (if cover found)
- **Updated:** Never (covers don't change)
- **Deleted:** When book is removed from library (optional - "delete file" checkbox)

**Cache Size Estimation:**
- Average cover: ~50KB
- 1000 books: ~50MB (acceptable)
- 10,000 books: ~500MB (still acceptable)

**Cache Cleanup:** Deferred to future enhancement (Phase 4+)
- Could add "Clean orphaned covers" maintenance task
- For now, covers persist even if book is removed (negligible space impact)

## Data Flow

### Import with Cover Extraction

```
1. User selects EPUB file(s) to import
   ↓
2. LibraryController.import_books() loops through files
   ↓
3. For each file:
   a. Parse EPUB metadata (EPUBBook) - existing
   b. Extract cover (CoverExtractor) - NEW
      - Try EPUB 3 method
      - Try EPUB 2 method
      - Try filename heuristic
      - Return (bytes, ext) or None
   c. Create BookMetadata object - existing
   d. Insert into database → get book_id - existing
   e. Save cover to cache (if extracted) - NEW
      - Write bytes to ~/.ereader/covers/{book_id}.{ext}
   f. Update database with cover_path - NEW
   ↓
4. Emit import_completed signal
   ↓
5. Library reloads and displays with covers
```

### Displaying Covers in Library

```
1. LibraryView displays BookGridWidget
   ↓
2. BookGridWidget uses BookCardDelegate to paint each card
   ↓
3. BookCardDelegate.paint() for each book:
   a. Check if book.cover_path exists
   b. Check if file exists on disk
   c. Load as QPixmap
   d. If successful: Scale and draw pixmap
   e. If failed: Draw placeholder
```

## Error Handling

### Cover Extraction Failures

**Scenario:** EPUB has no cover, or extraction fails

**Handling:**
- `CoverExtractor.extract_cover()` returns `None`
- `LibraryController` logs warning but continues import
- `metadata.cover_path` remains `None`
- `BookCardDelegate` shows placeholder

**User Impact:** Book imported successfully, just no cover shown

### Cache Write Failures

**Scenario:** Can't write to `~/.ereader/covers/` (permissions, disk full, etc.)

**Handling:**
- `_save_cover()` catches `OSError`, logs error
- Returns `None` instead of cover path
- Book import succeeds, just no cover cached

**User Impact:** Book imported, no cover shown

### Cover Display Failures

**Scenario:** Cover file exists but QPixmap can't load it (corrupted, unsupported format)

**Handling:**
- `pixmap.isNull()` check catches load failures
- Falls back to placeholder automatically

**User Impact:** Placeholder shown instead of cover

### Missing Cover Files

**Scenario:** `book.cover_path` is set but file doesn't exist (cache deleted, moved, etc.)

**Handling:**
- `Path(cover_path).exists()` check prevents load attempt
- Falls back to placeholder

**User Impact:** Placeholder shown

## Performance Considerations

### Import Performance

**Baseline (no covers):** ~50ms per book
**With cover extraction:** ~200ms per book
**Breakdown:**
- Open EPUB ZIP: ~20ms
- Parse OPF: ~30ms (reused from metadata extraction)
- Extract image: ~50ms
- Write to disk: ~50ms

**Mitigation:**
- Acceptable for one-time import operation
- Can show progress bar with current filename
- Can add "Import without covers" option if needed (future)

### Display Performance

**Baseline (placeholder):** ~1ms per card
**With pixmap loading:** ~3-5ms per card (first paint)
**After first load:** ~1ms (Qt caches pixmaps)

**Mitigation:**
- QPixmap is efficient for repeated painting
- Qt automatically caches loaded images
- Scrolling performance should be acceptable

**Future Optimization (if needed):**
- Pre-load covers for visible cards only
- Generate thumbnails during import (150x200 instead of full size)
- Use QImage instead of QPixmap for better caching control

## Testing Strategy

### Unit Tests for CoverExtractor

**Test Files Needed:**
- `test_epub_epub3_cover.epub` - Has EPUB 3 cover
- `test_epub_epub2_cover.epub` - Has EPUB 2 cover
- `test_epub_filename_cover.epub` - Has "cover.jpg" file
- `test_epub_no_cover.epub` - No cover at all

**Test Cases:**
1. `test_extract_epub3_cover()` - Verifies EPUB 3 detection
2. `test_extract_epub2_cover()` - Verifies EPUB 2 detection
3. `test_extract_filename_heuristic()` - Verifies fallback
4. `test_extract_no_cover_returns_none()` - Handles missing covers
5. `test_get_image_extension()` - Extension detection

### Integration Tests

**Test Cases:**
1. `test_import_book_with_cover()` - Full flow: import → cache → display
2. `test_import_book_without_cover()` - Handles missing cover gracefully
3. `test_cache_directory_created()` - Creates ~/.ereader/covers/
4. `test_cover_path_in_database()` - Verifies database update

### Manual Testing Checklist

- [ ] Import book with EPUB 3 cover → displays correctly
- [ ] Import book with EPUB 2 cover → displays correctly
- [ ] Import book with no cover → shows placeholder
- [ ] Restart app → covers still display (cache persistence)
- [ ] Delete cache file manually → falls back to placeholder
- [ ] Import 10 books → performance acceptable
- [ ] Scroll through library → smooth rendering

## Implementation Order

1. **Phase 1: Core extraction logic**
   - Create `CoverExtractor` class
   - Implement EPUB 3 and EPUB 2 methods
   - Add filename heuristic
   - Write unit tests

2. **Phase 2: Cache management**
   - Add `_save_cover()` method to LibraryController
   - Create cache directory structure
   - Handle file write errors

3. **Phase 3: Integration**
   - Integrate extraction into `import_books()`
   - Update BookCardDelegate to display covers
   - Update LibraryRepository if needed (cover_path column)

4. **Phase 4: Testing**
   - Create test EPUB files
   - Write unit and integration tests
   - Manual testing

## Future Enhancements

### Phase 4+

1. **Thumbnail generation**
   - Generate fixed-size thumbnails (150x200) during import
   - Faster loading, smaller cache size
   - Keep original for book details dialog

2. **Cover download/editing**
   - Allow users to change cover manually
   - Download cover from online sources (Open Library, Google Books)

3. **Async extraction**
   - If import performance becomes an issue
   - Background task with progress updates

4. **Cache maintenance**
   - "Clean orphaned covers" tool
   - Automatic cache size management

5. **Advanced fallbacks**
   - First image in first chapter heuristic
   - Generate cover from title/author (programmatic)

## Dependencies

### New Dependencies

None! Uses only standard library and existing PyQt6.

### Existing Dependencies Used

- `xml.etree.ElementTree` - Parse OPF XML
- `zipfile` - Access EPUB contents
- `pathlib.Path` - File path handling
- `PyQt6.QtGui.QPixmap` - Image loading and display

## Migration Considerations

### Existing Libraries

Books already in the database have `cover_path=None`. Two options:

**Option A: Lazy extraction**
- Leave existing books as-is
- Add "Extract Covers" action to library menu
- Users can trigger extraction for existing books

**Option B: Automatic backfill**
- On first app launch after update, extract covers for all books
- Show progress dialog ("Updating library...")
- May take several minutes for large libraries

**Decision: Option A (Lazy)**
- Less intrusive
- Users control when extraction happens
- Can be deferred to Phase 4

### Database Schema

`BookMetadata.cover_path` field already exists (added in Phase 1).
No schema changes needed.

## Consequences

### Enables

- Visual library grid with actual book covers
- More professional appearance
- Better book recognition (visual vs. text)
- Foundation for Continue Reading widget (shows covers)
- Foundation for book details dialog (display larger cover)

### Constrains

- Import process takes ~4x longer (acceptable tradeoff)
- Cache directory grows with library size (~50KB per book)
- Cover quality limited by EPUB source

### Watch Out For

- **Slow imports:** Monitor performance with large batches
- **Cache size:** Could grow large for huge libraries (10k+ books)
- **Missing covers:** Some EPUBs genuinely have no cover
- **Format variations:** EPUB publishers use inconsistent cover markup

## Decision Log

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2025-12-15 | Extract during import (sync) | Simplicity, consistency, acceptable performance |
| 2025-12-15 | Cache in ~/.ereader/covers/ | User data directory, cross-platform compatible |
| 2025-12-15 | Filename: {book_id}.{ext} | Simple, unique, survives file moves |
| 2025-12-15 | Keep original image format | No conversion overhead, maintains quality |
| 2025-12-15 | Lazy migration for existing books | Less intrusive, user control |

## References

- [EPUB 3 Specification - Cover Images](http://www.idpf.org/epub/30/spec/epub30-publications.html#sec-cover-image)
- [EPUB 2 Specification - OPF Metadata](http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.2)
- Existing architecture: `docs/architecture/epub-rendering-architecture.md`
- Existing architecture: `docs/architecture/library-phase3-quick-wins.md`
