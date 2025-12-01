# Feature: EPUB File Parsing

## Overview

Implement core EPUB parsing functionality to extract book metadata, structure, and content. This is the foundational component for Feature #1 (Open and render EPUB files) and will support all future EPUB-related features.

**Priority:** Core MVP (Feature #1 foundation)

## User Stories

- As a reader, I want to open an EPUB file so that I can access its content
- As a reader, I want to see book metadata (title, author) so that I know what I'm reading
- As a reader, I want the app to handle the book's structure so that I can navigate chapters

## Acceptance Criteria

### Metadata Extraction
- [ ] Extract book title from content.opf
- [ ] Extract author(s) from content.opf
- [ ] Extract language from content.opf
- [ ] Handle books with missing metadata gracefully (use "Unknown Title", "Unknown Author")

### Structure Parsing
- [ ] Parse the spine (reading order) from content.opf
- [ ] Parse the manifest (file list) from content.opf
- [ ] Map spine items to actual content files
- [ ] Handle NCX table of contents (if present)

### Content Access
- [ ] Read chapter content (XHTML files) from the EPUB
- [ ] Handle different text encodings (UTF-8, etc.)
- [ ] Extract chapter titles from content or TOC

### Error Handling
- [ ] Detect and reject non-EPUB files with clear error messages
- [ ] Detect and report corrupted EPUB files (invalid ZIP, missing container.xml)
- [ ] Handle malformed XML gracefully
- [ ] Handle missing required files (container.xml, content.opf)

### Code Quality
- [ ] Type hints on all functions
- [ ] Docstrings (Google style) on all public functions
- [ ] PEP 8 compliant
- [ ] Logging for debugging (not print statements)

### Testing
- [ ] Unit tests for metadata extraction
- [ ] Unit tests for spine/manifest parsing
- [ ] Unit tests for error cases
- [ ] Test with at least 3 different real EPUB files

## Edge Cases

### Malformed EPUBs
- **Missing metadata**: Some EPUBs lack title/author → Use defaults
- **Multiple authors**: `<dc:creator>` can appear multiple times → Store as list
- **Missing spine**: Technically invalid but exists in the wild → Error or use manifest order
- **Non-standard paths**: OPF file not in typical location → Follow container.xml

### Content Issues
- **Non-UTF-8 encoding**: Older EPUBs may use other encodings → Detect and decode properly
- **Mixed namespaces**: Different EPUB versions use different XML namespaces → Use `{*}` wildcards
- **Large files**: Books with hundreds of chapters → Don't load all content at once

### File System
- **File permissions**: User may not have read access → Clear error message
- **File path edge cases**: Paths with spaces, unicode, special chars → Handle properly
- **Locked files**: File may be open in another program → Clear error message

## Out of Scope

This spec explicitly does NOT include:
- ❌ Rendering EPUB content in a UI (separate feature)
- ❌ Images/media extraction (will add later)
- ❌ CSS/style parsing (will add later)
- ❌ DRM-protected EPUBs (future consideration)
- ❌ EPUB 2 vs EPUB 3 distinction (accept both for now)
- ❌ Validation against EPUB spec (be forgiving)
- ❌ Performance optimization (make it work first)

## Dependencies

### External
- Python 3.11+
- Standard library only: `zipfile`, `xml.etree.ElementTree`, `pathlib`

### Internal
- None - this is the first feature implementation

## Implementation Approach

### Phase 1: Core Model (YOU implement - learning goal)
Create `src/ereader/models/epub.py` with:
- `EPUBBook` class to represent a parsed EPUB
- Methods: `extract_metadata()`, `parse_spine()`, `parse_manifest()`, `get_chapter_content()`

### Phase 2: Custom Exceptions (YOU implement)
Create `src/ereader/exceptions.py` with:
- `InvalidEPUBError` - Not a valid EPUB file
- `CorruptedEPUBError` - EPUB is damaged/incomplete
- `UnsupportedEPUBError` - EPUB format not supported

### Phase 3: Tests (YOU implement - learning goal)
Create `tests/test_models/test_epub.py` with:
- Fixtures for valid EPUB, corrupted EPUB, non-EPUB file
- Tests for metadata extraction
- Tests for spine/manifest parsing
- Tests for error cases

### Phase 4: Integration Testing
- Test with real-world EPUB files from your collection
- Document any quirks/issues found

## Tasks

### Task 1: Set up project structure (Small)
- Create `src/ereader/models/` directory
- Create `src/ereader/exceptions.py`
- Create test directory structure
- Configure pytest if needed

### Task 2: Implement EPUBBook class skeleton (Small)
- Create `EPUBBook` class with `__init__`
- Add basic file validation (is it a ZIP?)
- Add logging setup
- Write docstrings

### Task 3: Implement metadata extraction (Medium)
- Parse container.xml to find OPF path
- Parse OPF XML to extract `<dc:title>`, `<dc:creator>`, `<dc:language>`
- Handle XML namespaces properly
- Handle missing metadata with defaults
- Add unit tests

### Task 4: Implement spine and manifest parsing (Medium)
- Parse `<spine>` element from OPF
- Parse `<manifest>` element from OPF
- Map spine itemrefs to manifest items
- Store reading order
- Add unit tests

### Task 5: Implement chapter content reading (Medium)
- Method to get chapter content by spine index
- Handle file paths correctly (relative to OPF location)
- Handle text encoding
- Add unit tests

### Task 6: Implement error handling (Small)
- Create custom exception classes
- Add validation for required files
- Add try/except blocks with proper error messages
- Add tests for error cases

### Task 7: Integration testing with real EPUBs (Small)
- Test with 3+ real EPUB files
- Document any issues found
- Add edge case tests as needed

## Success Metrics

**This feature is complete when:**
1. All acceptance criteria are met
2. All tests pass
3. Code review approves the implementation
4. You can programmatically open an EPUB and extract:
   - Title, author, language
   - Chapter list in reading order
   - Content of any chapter

## Next Steps After This Feature

Once EPUB parsing is complete, we'll move to:
1. **UI Framework Decision**: Choose between tkinter, PyQt6, or textual
2. **Basic EPUB Rendering**: Display chapter content in the chosen UI
3. **Chapter Navigation**: Next/previous chapter buttons

---

## Notes for Developer

- **This is a learning feature**: Take your time to understand each piece
- **Start simple**: Get basic cases working before handling edge cases
- **Ask questions**: If stuck on XML namespaces, async patterns, or testing, use `/mentor`
- **Iterate**: First implementation doesn't need to be perfect
- **Experiment**: Keep using the playground to test ideas before implementing

**Estimated effort:** 1-2 weeks at a learning pace
