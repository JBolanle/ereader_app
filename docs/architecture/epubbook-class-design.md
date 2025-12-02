# EPUBBook Class Architecture

## Date
2025-12-02

## Context

Issue #2 requires implementing the `EPUBBook` class skeleton, which is the foundational model for EPUB parsing. This class will:

1. Represent a parsed EPUB file
2. Validate EPUB structure
3. Extract and provide access to metadata
4. Provide access to book content (chapters)
5. Handle EPUB-specific errors

This is a critical architectural decision because:
- It's the primary interface for all EPUB operations
- Other components (UI, reading state) will depend on its API
- Performance and memory characteristics are established here
- The design impacts testability of the entire parsing subsystem

**Key constraints from CLAUDE.md:**
- Memory usage <200MB for typical books
- Type hints required on all methods
- Custom exceptions for error handling
- Logging instead of print statements
- This is a learning implementation (simplicity preferred)

## Design Questions to Answer

1. **Initialization strategy**: Parse everything upfront (eager) or on-demand (lazy)?
2. **State management**: What data to keep in memory vs. read from disk?
3. **API design**: What methods and properties should be public?
4. **Error handling**: When to validate and when to fail?
5. **Performance**: How to balance speed vs. memory usage?

## Options Considered

### Option 1: Eager Loading (Parse Everything in `__init__`)

```python
class EPUBBook:
    def __init__(self, filepath: Path | str):
        # Parse and store ALL data immediately
        self.filepath = Path(filepath)
        self._validate_epub()
        self.metadata = self._parse_metadata()
        self.spine = self._parse_spine()
        self.manifest = self._parse_manifest()
        self.chapters = [self._load_chapter(i) for i in range(len(self.spine))]
        # All data loaded, ZIP file closed
```

**Pros:**
- ✅ Fail-fast: All validation happens in `__init__`
- ✅ Simple API: No lazy initialization complexity
- ✅ Predictable: Always know what state the object is in
- ✅ Easy to test: Construct once, use many times

**Cons:**
- ❌ Slow initialization: Must parse entire book to construct object
- ❌ Memory intensive: Stores all chapter content in RAM
- ❌ Wasteful: If you only need metadata, you've loaded everything
- ❌ Fails performance requirement: >200MB for large books

**Example usage:**
```python
book = EPUBBook("1984.epub")  # Slow for large books
print(book.title)  # Fast - already in memory
content = book.chapters[0]  # Fast - already in memory
```

### Option 2: Lazy Loading (Parse On-Demand)

```python
class EPUBBook:
    def __init__(self, filepath: Path | str):
        # Minimal validation only
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        # Defer all parsing until accessed

    @property
    def title(self) -> str:
        if not hasattr(self, '_metadata'):
            self._metadata = self._parse_metadata()
        return self._metadata.get('title', 'Unknown Title')
```

**Pros:**
- ✅ Fast initialization: Just stores filepath
- ✅ Memory efficient: Only loads what's accessed
- ✅ Flexible: Can access metadata without loading content

**Cons:**
- ❌ Late failures: Invalid EPUBs aren't detected until use
- ❌ Complex: Requires lazy property pattern throughout
- ❌ Unpredictable: First access is slow, later accesses fast
- ❌ Error-prone: Easy to forget lazy initialization checks
- ❌ Harder to test: Must test initialization paths for each method

**Example usage:**
```python
book = EPUBBook("broken.epub")  # Fast, but invalid file not detected!
print(book.title)  # Fails HERE instead of at construction
```

### Option 3: Hybrid Approach (Validate + Parse Structure, Defer Content)

```python
class EPUBBook:
    def __init__(self, filepath: Path | str):
        # Parse critical data upfront, defer heavy content
        self.filepath = Path(filepath)
        self._validate_epub()  # Ensure it's a valid EPUB
        self._opf_path = self._parse_container()  # Find content.opf
        self._metadata = self._parse_metadata()  # Extract metadata
        self._spine = self._parse_spine()  # Get reading order
        self._manifest = self._parse_manifest()  # Get file list
        # Defer: Don't load chapter content yet
        self._chapter_cache: dict[int, str] = {}

    def get_chapter_content(self, index: int) -> str:
        # Load on-demand and cache
        if index not in self._chapter_cache:
            self._chapter_cache[index] = self._load_chapter(index)
        return self._chapter_cache[index]
```

**Pros:**
- ✅ Balanced: Fast initialization, defers heavy content
- ✅ Fail-fast: Validates EPUB structure in `__init__`
- ✅ Memory efficient: Only loads accessed chapters
- ✅ Simple caching: Easy to add LRU cache later
- ✅ Predictable errors: If `__init__` succeeds, object is valid
- ✅ Meets requirements: Structure in memory (~KB), content on-demand

**Cons:**
- ⚠️ Moderate complexity: More complex than eager, simpler than full lazy
- ⚠️ Still parses XML: Must parse OPF upfront (but this is small)

**Example usage:**
```python
book = EPUBBook("1984.epub")  # Validates and parses structure (~fast)
print(book.title)  # Fast - parsed in __init__
content = book.get_chapter_content(0)  # First access: loads from disk
content = book.get_chapter_content(0)  # Second access: from cache
```

## Decision

**Choose Option 3: Hybrid Approach**

### Rationale

1. **Performance requirements**: Meets CLAUDE.md's <200MB memory constraint
   - Metadata + structure typically <100KB
   - Chapter content loaded on-demand
   - Cache can be bounded to 50 chapters (per CLAUDE.md)

2. **Fail-fast validation**: Catches invalid EPUBs at construction time
   - Better user experience (errors happen when opening file)
   - Easier to debug (clear point of failure)
   - Simpler error handling (don't need try/except around every property access)

3. **Learning goals**: Good balance of simplicity and real-world patterns
   - Not too simple (eager loading teaches bad habits for large files)
   - Not too complex (full lazy loading is harder to understand)
   - Demonstrates on-demand loading and caching (useful patterns)

4. **Extensibility**: Easy to optimize later
   - Can add LRU caching for chapters without API changes
   - Can add pre-fetching for next/previous chapters
   - Can add async loading without changing public API

5. **Testability**: Straightforward to test
   - Validation tested via `__init__` calls with invalid files
   - Metadata/structure tested via property access
   - Content loading tested via `get_chapter_content()`

### What Gets Parsed in `__init__` (Upfront)

```python
def __init__(self, filepath: Path | str):
    """Initialize EPUBBook and parse structure.

    This validates the EPUB file and parses metadata and structure upfront,
    but defers loading chapter content until accessed.

    Raises:
        FileNotFoundError: If the file doesn't exist
        InvalidEPUBError: If the file is not a valid EPUB
        CorruptedEPUBError: If the EPUB structure is damaged
    """
    self.filepath = Path(filepath)
    self._validate_epub()          # ~instant (file checks)
    self._opf_path = self._parse_container()  # ~instant (tiny XML)
    self._parse_opf()              # ~fast (parse metadata + structure)
    self._chapter_cache: dict[int, str] = {}
```

**Parsed upfront (~fast, <100KB memory):**
- ✅ File exists and is readable
- ✅ File is a valid ZIP archive
- ✅ `META-INF/container.xml` exists and is valid
- ✅ `content.opf` exists and is valid XML
- ✅ Metadata fields (title, author, language, etc.)
- ✅ Spine (reading order - list of IDs)
- ✅ Manifest (file map - ID to path)

**Deferred until accessed:**
- ⏭️ Chapter content (XHTML files)
- ⏭️ Images and media files
- ⏭️ CSS stylesheets
- ⏭️ Table of contents (NCX/NAV - future enhancement)

## Class Design

### Public API

```python
from pathlib import Path
from typing import Optional

class EPUBBook:
    """Represents a parsed EPUB book.

    This class handles EPUB file parsing, metadata extraction, and content access.
    The EPUB structure is parsed during initialization, but chapter content is
    loaded on-demand to optimize memory usage.

    Example:
        >>> book = EPUBBook("path/to/book.epub")
        >>> print(book.title)
        "1984"
        >>> content = book.get_chapter_content(0)
        >>> print(f"Book has {book.chapter_count} chapters")

    Attributes:
        filepath: Path to the EPUB file
        title: Book title from metadata
        author: Book author from metadata (or "Unknown Author")
        language: Book language code (or "Unknown")
        chapter_count: Number of chapters in the spine
    """

    def __init__(self, filepath: Path | str) -> None:
        """Initialize EPUBBook and validate EPUB structure.

        Args:
            filepath: Path to the EPUB file to open

        Raises:
            FileNotFoundError: If the file doesn't exist
            InvalidEPUBError: If the file is not a valid EPUB
            CorruptedEPUBError: If the EPUB structure is damaged
        """

    @property
    def title(self) -> str:
        """Get book title (or 'Unknown Title' if missing)."""

    @property
    def author(self) -> str:
        """Get book author (or 'Unknown Author' if missing)."""

    @property
    def language(self) -> str:
        """Get book language code (or 'Unknown' if missing)."""

    @property
    def chapter_count(self) -> int:
        """Get the number of chapters in the book."""

    def get_chapter_content(self, index: int) -> str:
        """Get the content of a chapter by spine index.

        Args:
            index: Chapter index (0-based, following spine order)

        Returns:
            The XHTML content of the chapter as a string

        Raises:
            IndexError: If index is out of range
            CorruptedEPUBError: If chapter file is missing or corrupted
        """
```

### Internal State

```python
class EPUBBook:
    # Public attributes (set in __init__)
    filepath: Path

    # Private attributes (set in __init__)
    _opf_path: str  # Path to content.opf within ZIP
    _metadata: dict[str, str]  # Extracted metadata
    _spine: list[str]  # List of manifest item IDs in reading order
    _manifest: dict[str, str]  # Map of item ID -> file path
    _chapter_cache: dict[int, str]  # Cache of loaded chapters
```

### Private Methods

```python
def _validate_epub(self) -> None:
    """Validate that the file is a valid EPUB.

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidEPUBError: If not a valid ZIP or missing required files
    """

def _parse_container(self) -> str:
    """Parse META-INF/container.xml to find content.opf path.

    Returns:
        Path to content.opf within the ZIP archive

    Raises:
        CorruptedEPUBError: If container.xml is missing or malformed
    """

def _parse_opf(self) -> None:
    """Parse content.opf to extract metadata, spine, and manifest.

    Sets: self._metadata, self._spine, self._manifest

    Raises:
        CorruptedEPUBError: If content.opf is missing or malformed
    """

def _load_chapter(self, index: int) -> str:
    """Load chapter content from the EPUB file.

    Args:
        index: Chapter index in spine

    Returns:
        XHTML content as string

    Raises:
        IndexError: If index out of range
        CorruptedEPUBError: If chapter file missing or unreadable
    """
```

## Implementation Strategy for Issue #2

Issue #2 is the **skeleton** phase. Implement in this order:

### Step 1: Basic Structure
```python
class EPUBBook:
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = Path(filepath)
        # More to come...
```

### Step 2: File Validation
```python
def _validate_epub(self) -> None:
    # Check file exists
    # Check is valid ZIP
    # Check has container.xml
```

### Step 3: Logging Setup
```python
import logging

logger = logging.getLogger(__name__)

def __init__(self, filepath: Path | str) -> None:
    logger.info("Opening EPUB: %s", filepath)
    # ...
```

### Step 4: Comprehensive Docstrings
- Class docstring with example
- Method docstrings with Args/Returns/Raises
- Follow Google style (per CLAUDE.md)

### Step 5: Type Hints
- All method signatures
- All return types
- Use `Path | str` for filepath flexibility

**For Issue #2, DO NOT IMPLEMENT YET:**
- ❌ Metadata parsing (Issue #3)
- ❌ Spine/manifest parsing (Issue #4)
- ❌ Chapter content loading (Issue #5)
- ❌ Caching logic (future optimization)

The skeleton should:
1. Accept a filepath
2. Validate it's a ZIP file
3. Check `META-INF/container.xml` exists
4. Raise appropriate exceptions on failure
5. Log operations
6. Have complete docstrings and type hints

## Error Handling Strategy

### Validation Sequence in `__init__`

```python
def __init__(self, filepath: Path | str) -> None:
    self.filepath = Path(filepath)

    # 1. Check file exists (FileNotFoundError)
    if not self.filepath.exists():
        raise FileNotFoundError(f"EPUB file not found: {filepath}")

    # 2. Check is valid ZIP (InvalidEPUBError)
    if not zipfile.is_zipfile(self.filepath):
        raise InvalidEPUBError(f"Not a valid ZIP file: {filepath}")

    # 3. Check has container.xml (InvalidEPUBError)
    with ZipFile(self.filepath) as zf:
        if 'META-INF/container.xml' not in zf.namelist():
            raise InvalidEPUBError("Missing META-INF/container.xml")

    logger.info("Validated EPUB: %s", filepath)
```

### Exception Choice Guide

- **FileNotFoundError**: Built-in exception, file doesn't exist
- **InvalidEPUBError**: Not a valid EPUB (wrong format, missing required files)
- **CorruptedEPUBError**: Valid EPUB structure, but damaged/malformed content
- **IndexError**: Built-in, chapter index out of range

## Testing Strategy

### Test Structure (`tests/test_models/test_epub.py`)

```python
import pytest
from pathlib import Path
from ereader.models.epub import EPUBBook
from ereader.exceptions import InvalidEPUBError, CorruptedEPUBError

class TestEPUBBookInit:
    """Test EPUBBook initialization and validation."""

    def test_valid_epub_initializes(self, valid_epub_path):
        """Test that a valid EPUB file initializes successfully."""
        book = EPUBBook(valid_epub_path)
        assert book.filepath == Path(valid_epub_path)

    def test_nonexistent_file_raises_error(self):
        """Test that opening a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            EPUBBook("does_not_exist.epub")

    def test_non_zip_file_raises_invalid_error(self, text_file_path):
        """Test that opening a non-ZIP file raises InvalidEPUBError."""
        with pytest.raises(InvalidEPUBError, match="Not a valid ZIP"):
            EPUBBook(text_file_path)

    def test_zip_without_container_raises_invalid_error(self, empty_zip_path):
        """Test that a ZIP without container.xml raises InvalidEPUBError."""
        with pytest.raises(InvalidEPUBError, match="container.xml"):
            EPUBBook(empty_zip_path)
```

### Required Test Fixtures

Create fixtures in `tests/conftest.py`:
- `valid_epub_path`: Path to a real, valid EPUB file
- `text_file_path`: Path to a text file (not a ZIP)
- `empty_zip_path`: Path to a ZIP file without EPUB structure

## Performance Characteristics

### Memory Usage (after full implementation)

| Component | Memory | When Loaded |
|-----------|--------|-------------|
| Filepath | ~100 bytes | `__init__` |
| Metadata | ~1 KB | `__init__` |
| Spine | ~1 KB (100 chapters) | `__init__` |
| Manifest | ~10 KB (200 files) | `__init__` |
| **Structure total** | **~12 KB** | **`__init__`** |
| Single chapter | ~50 KB avg | On-demand |
| Cached chapters (50) | ~2.5 MB | As accessed |
| **Max total** | **~3 MB** | **With cache** |

✅ **Well under 200MB requirement**

### Timing Estimates

- `__init__` for typical EPUB: <100ms
- First chapter access: ~10ms (disk I/O)
- Cached chapter access: <1ms (memory)

## Consequences

### What This Enables

- ✅ Fast EPUB opening (validates structure without loading content)
- ✅ Low memory footprint (structure ~KB, content on-demand)
- ✅ Simple error handling (fail-fast in `__init__`)
- ✅ Easy to extend (add caching, pre-fetching, async later)
- ✅ Testable (clear separation of validation, parsing, loading)

### What This Constrains

- 📍 Must always parse OPF in `__init__` (can't defer if only need filepath)
- 📍 ZIP file opened/closed multiple times (once for validation, once per chapter)
- 📍 Cache management needed later to prevent unbounded memory growth

### What to Watch Out For

- ⚠️ **ZIP file locking**: Ensure ZIP file is closed after each operation
- ⚠️ **Thread safety**: Not thread-safe by default (add locks if needed for UI)
- ⚠️ **Cache eviction**: Will need LRU cache later to bound memory (future enhancement)
- ⚠️ **Large files**: Chapters >10MB could cause slowdowns (rare for EPUBs)

## Future Enhancements

After initial implementation works:

### Enhancement 1: LRU Caching
```python
from functools import lru_cache

@lru_cache(maxsize=50)  # Per CLAUDE.md
def get_chapter_content(self, index: int) -> str:
    ...
```

### Enhancement 2: Async Loading
```python
async def get_chapter_content_async(self, index: int) -> str:
    """Load chapter content without blocking UI."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self._load_chapter, index)
```

### Enhancement 3: Pre-fetching
```python
def prefetch_chapters(self, start: int, count: int = 3) -> None:
    """Pre-load upcoming chapters in background."""
    for i in range(start, min(start + count, self.chapter_count)):
        if i not in self._chapter_cache:
            self.get_chapter_content(i)
```

### Enhancement 4: Rich Metadata
```python
@property
def metadata(self) -> dict[str, Any]:
    """Get all available metadata fields."""
    return {
        'title': self.title,
        'author': self.author,
        'language': self.language,
        'publisher': self._metadata.get('publisher'),
        'published_date': self._metadata.get('date'),
        'isbn': self._metadata.get('identifier'),
    }
```

## References

- [EPUB Specifications](https://www.w3.org/TR/epub-overview-33/)
- docs/specs/epub-parsing.md - Full feature specification
- CLAUDE.md - Performance requirements and code standards
- docs/architecture/project-structure.md - Exception handling patterns

## Implementation Checklist (Issue #2)

For the skeleton implementation:

- [ ] Create `src/ereader/models/epub.py`
- [ ] Import required modules (zipfile, pathlib, logging, typing)
- [ ] Create `EPUBBook` class with docstring
- [ ] Implement `__init__` with filepath parameter and type hints
- [ ] Implement `_validate_epub()` method
  - [ ] Check file exists (raise FileNotFoundError)
  - [ ] Check is ZIP file (raise InvalidEPUBError)
  - [ ] Check has container.xml (raise InvalidEPUBError)
- [ ] Set up logging for the class
- [ ] Add comprehensive docstrings (Google style)
- [ ] Create `tests/test_models/test_epub.py`
- [ ] Write tests for initialization and validation
- [ ] Run tests: `uv run pytest tests/test_models/test_epub.py`
- [ ] Run linter: `uv run ruff check src/ereader/models/epub.py`
- [ ] Commit with conventional commit message

**Next Issues (Future):**
- Issue #3: Implement metadata parsing
- Issue #4: Implement spine and manifest parsing
- Issue #5: Implement chapter content loading
