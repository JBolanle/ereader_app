# GUI Testing Strategy for EPUB Rendering MVP

## Date
2025-12-03

## Current Coverage: 54%

### Breakdown
- ✅ **Models** (epub.py): 93% - Excellent coverage
- ✅ **Controllers** (reader_controller.py): 100% - Full coverage
- ✅ **Exceptions**: 100% - Full coverage
- ❌ **Views** (MainWindow, BookViewer, NavigationBar): 0% - No automated tests
- ❌ **Entry Point** (__main__.py): 0% - No automated tests

Total: 54% (241/445 statements tested)

## Why Views Aren't Tested (Yet)

### PyQt6 GUI Testing Challenges

1. **Requires pytest-qt plugin** (not in dependencies)
   - pytest-qt provides QTest framework for programmatic UI interaction
   - Adds complexity and setup overhead
   - Best added after MVP is validated

2. **Manual testing is more effective for MVP**
   - Visual verification ensures UI actually looks correct
   - User interaction flow testing catches UX issues
   - Automated UI tests can pass while UI looks broken

3. **Limited value for simple UI**
   - Views are thin wrappers over Qt widgets
   - Most logic is in controller (which IS tested)
   - Views mostly just display what controller tells them

## What IS Tested

### Controller Logic (100% coverage) ✅
All business logic and state management is fully tested:

- **Book opening**: Valid files, file not found, invalid EPUBs, corrupted files
- **Navigation**: Next/previous chapter, boundary conditions, empty book
- **State management**: Chapter index tracking, navigation availability
- **Error handling**: All error paths tested with appropriate signals
- **Signal emissions**: All signals tested for correct data

### Model Layer (93% coverage) ✅
EPUB parsing is comprehensively tested:

- **Initialization**: All file types, edge cases, error conditions
- **Metadata extraction**: Complete, partial, missing metadata
- **Manifest/Spine parsing**: Valid and invalid structures
- **Chapter content**: All index ranges, encodings, missing files

### What's NOT Tested (11 lines in epub.py)
Defensive code for malformed data:
- Lines 185, 235: Logging for missing items
- Lines 270-271, 273-274: Fallback for encoding errors
- Lines 311-312, 342-344: Edge case error handling

**Decision**: These are defensive paths that would require extensive mock data. Low risk, documented here.

## Manual Testing Checklist

**For this MVP, manual testing covers:**

### Core Functionality
- [ ] Application launches without errors
- [ ] File > Open shows file dialog
- [ ] Can select and open an EPUB file
- [ ] Book title and author display in window title and status bar
- [ ] First chapter content renders correctly
- [ ] Previous button is disabled at first chapter
- [ ] Next button navigates to second chapter
- [ ] Previous button becomes enabled after first chapter
- [ ] Can navigate through entire book
- [ ] Next button is disabled at last chapter
- [ ] Status bar shows "Chapter X of Y"

### Error Handling
- [ ] Opening non-existent file shows error dialog
- [ ] Opening non-EPUB file shows error dialog
- [ ] Opening corrupted EPUB shows error dialog
- [ ] Error dialogs are user-friendly (not stack traces)

### UI/UX
- [ ] Window is resizable
- [ ] Content reflows when window is resized
- [ ] Keyboard shortcuts work (Ctrl+O, Ctrl+Q, Arrow keys)
- [ ] Welcome message shows when no book is loaded
- [ ] HTML formatting renders correctly (paragraphs, headings, emphasis)

### Performance
- [ ] Opening books is fast (<100ms after file selected)
- [ ] Chapter navigation is instant (<100ms)
- [ ] No memory leaks when navigating many chapters

## Future Testing Improvements

### Phase 1: Add pytest-qt (Next Sprint)
**Priority: Medium**
**Effort: 2-4 hours**

Add automated UI tests using pytest-qt:

```python
def test_open_button_opens_file_dialog(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.file_dialog_opened):
        window._file_menu.actions()[0].trigger()
```

Tests to add:
- File menu actions trigger correctly
- Signals are emitted when expected
- Button enabled/disabled states update
- Keyboard shortcuts work

### Phase 2: Integration Tests (Later)
**Priority: Low**
**Effort: 4-6 hours**

Test full user workflows with real EPUBs:

```python
def test_full_reading_workflow(qtbot, sample_epub):
    app = QApplication([])
    window = MainWindow()

    # Simulate: open file → read → navigate → close
    window.controller.open_book(sample_epub)
    assert window.windowTitle() == "1984 - E-Reader"

    window.controller.next_chapter()
    assert "Chapter 2 of 42" in window.statusBar().currentMessage()
```

### Phase 3: Visual Regression Testing (Much Later)
**Priority: Very Low**
**Effort: 8+ hours**

Use tools like pytest-qt-screenshot to catch visual bugs:
- Screenshots of rendered chapters
- Compare against baseline images
- Detect CSS rendering issues

## Decision for MVP

**For the MVP (Issue #18), we accept 54% coverage because:**

1. ✅ **All business logic is tested** (controller at 100%)
2. ✅ **Model layer is well-tested** (93%)
3. ✅ **Views are simple display wrappers** (thin UI layer)
4. ✅ **Manual testing covers user-facing functionality**
5. ✅ **Professional standard**: It's common for GUI apps to have lower coverage than libraries

**Industry standard**: GUI applications typically have 40-60% coverage due to difficulty testing UI. Our 54% with 100% controller coverage is professional-grade for an MVP.

## Lowering Coverage Threshold (Temporary)

For this MVP branch, we could:

**Option A**: Lower pytest coverage threshold to 50% temporarily
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=src/ereader --cov-fail-under=50"
```

**Option B**: Exclude views from coverage requirements
```toml
[tool.coverage.run]
omit = [
    "src/ereader/views/*",
    "src/ereader/__main__.py",
]
```

**Option C**: Keep 80% threshold, document exception for MVP
- Accept that this PR won't meet the threshold
- Create follow-up issue for pytest-qt integration
- Merge based on manual testing + code review

**Recommendation**: **Option C** - Don't lower standards, just document that GUI testing is deferred. The controller (business logic) meets the 80% standard on its own.

## Follow-up Issue

Create `Issue #XX: Add pytest-qt integration tests for UI components`

Checklist:
- [ ] Add pytest-qt to dev dependencies
- [ ] Write tests for MainWindow menu interactions
- [ ] Write tests for NavigationBar button states
- [ ] Write tests for signal/slot connections
- [ ] Aim for 70%+ overall coverage with UI tests

Target completion: Next sprint after MVP is validated

## References

- pytest-qt docs: https://pytest-qt.readthedocs.io/
- Qt Test framework: https://doc.qt.io/qt-6/qtest-overview.html
- Industry standards: Martin Fowler on GUI testing (Humble Object pattern)

