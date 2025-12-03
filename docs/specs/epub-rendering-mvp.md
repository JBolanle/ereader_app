# Feature: EPUB Rendering MVP

## Overview
Display EPUB book content in a desktop window using PyQt6. This is the first user-facing feature that brings together all the EPUB parsing work into a functional book reader.

**Learning Goal:** Build PyQt6 UI components from scratch, understand event handling, and integrate with existing domain models.

## User Stories
- As a reader, I want to open an EPUB file and see its content displayed, so I can start reading
- As a reader, I want to navigate to the next/previous chapter, so I can progress through the book
- As a reader, I want to see the book title and current chapter, so I know what I'm reading

## Acceptance Criteria
- [ ] User can select and open an EPUB file via file dialog
- [ ] Book content displays in a scrollable window with readable text
- [ ] HTML content from EPUB chapters renders correctly (basic formatting: paragraphs, headings, emphasis)
- [ ] User can navigate to next chapter (button or keyboard shortcut)
- [ ] User can navigate to previous chapter (button or keyboard shortcut)
- [ ] Window shows book title and current chapter title
- [ ] Application handles errors gracefully (corrupted file, unsupported format, missing chapters)
- [ ] Window is resizable and content adjusts appropriately

## Technical Approach

### Architecture (MVC Pattern)

**Model (already exists):**
- `EPUBBook` class from `src/ereader/models/epub.py`
- Provides: metadata, chapter list, chapter content

**View (new):**
- `MainWindow` - Top-level application window
- `BookViewer` - Widget for displaying chapter content (QTextBrowser or QWebEngineView)
- `NavigationBar` - Widget with next/prev controls
- `StatusBar` - Shows book title, chapter, progress

**Controller (new):**
- `ReaderController` - Coordinates between EPUBBook model and UI views
- Handles: file opening, chapter navigation, error handling

### PyQt6 Components to Learn

1. **QApplication** - Application lifecycle
2. **QMainWindow** - Top-level window with menu bar, status bar
3. **QTextBrowser or QWebEngineView** - HTML rendering widget (choose based on EPUB needs)
4. **QFileDialog** - File selection
5. **QPushButton** - Navigation buttons
6. **QVBoxLayout/QHBoxLayout** - Layout management
7. **Signals and Slots** - Event handling pattern

### Rendering Decision: QTextBrowser vs QWebEngineView

**QTextBrowser:**
- ✅ Lightweight, built into QtWidgets
- ✅ Supports basic HTML/CSS
- ✅ Good for simple EPUBs
- ❌ Limited CSS support
- ❌ No JavaScript support

**QWebEngineView:**
- ✅ Full Chromium engine
- ✅ Complete HTML5/CSS3 support
- ✅ Handles complex EPUB layouts
- ❌ Heavier dependency
- ❌ More complex

**Recommendation for MVP:** Start with **QTextBrowser** (simpler, lighter). Can upgrade to QWebEngineView later if needed.

## Implementation Tasks

### Phase 1: Basic Window (Small)
1. Create `src/ereader/views/main_window.py`
   - Set up QMainWindow with title
   - Add menu bar with "File > Open" action
   - Show empty window (just prove PyQt6 works)
2. Create `src/ereader/__main__.py`
   - Entry point for running the application
   - Initialize QApplication and MainWindow
3. Test: Can launch app and see empty window

### Phase 2: File Opening (Small)
1. Add QFileDialog to select EPUB file
2. Create `src/ereader/controllers/reader_controller.py`
   - Load EPUBBook from selected file
   - Handle file loading errors
3. Display book metadata in status bar (title, author)
4. Test: Can open EPUB and see metadata

### Phase 3: Content Display (Medium)
1. Create `src/ereader/views/book_viewer.py`
   - QTextBrowser widget
   - Method to load HTML content
   - Styling for readability (font size, margins)
2. Controller: Load first chapter and pass to viewer
3. Test: Can see first chapter content rendered

### Phase 4: Navigation (Medium)
1. Create `src/ereader/views/navigation_bar.py`
   - Previous/Next buttons
   - Keyboard shortcuts (Left/Right arrows or PgUp/PgDn)
2. Controller: Track current chapter index
   - Handle next/previous requests
   - Wrap at boundaries (disable at start/end)
3. Update status bar with chapter title and position (e.g., "Chapter 3 of 12")
4. Test: Can navigate through all chapters

### Phase 5: Error Handling (Small)
1. Handle corrupt EPUB files gracefully
2. Handle missing chapters gracefully
3. Show user-friendly error dialogs
4. Test error scenarios

### Phase 6: Polish (Small)
1. Set proper window icon
2. Remember window size/position between sessions (optional for MVP)
3. Add keyboard shortcut hints to tooltips
4. Ensure window is resizable and content reflows

## Edge Cases to Handle
- What happens when EPUB has no chapters?
- What if chapter content is empty?
- What if HTML is malformed?
- What if file can't be read (permissions, doesn't exist)?
- What if user tries to go next at last chapter?
- What if user tries to go previous at first chapter?
- Very long chapters (scrolling performance)
- Images in chapters (do we render them in MVP? Decision: Yes if using QTextBrowser with resource handler, defer if complex)

## Out of Scope (Defer to Later)
- PDF support
- Bookmarks
- Annotations/highlights
- Reading themes (light/dark)
- Font customization
- Search within book
- Table of contents sidebar
- Images embedded in chapters (if complex - revisit after basic text works)
- Multiple windows/tabs
- Reading progress persistence between sessions

## MVP Definition
The absolute minimum viable version:
1. Open an EPUB file
2. Display the first chapter
3. Navigate next/previous through chapters
4. Show book title

Everything else is enhancement.

## Dependencies
- Existing: `EPUBBook` model (already implemented)
- New: PyQt6 package (already added to dependencies)
- Learning: PyQt6 basics, signals/slots, layouts

## Testing Strategy

### Unit Tests
- `tests/test_controllers/test_reader_controller.py`
  - Test chapter navigation logic
  - Test error handling for bad files
  - Mock EPUBBook and views

### Integration Tests
- `tests/test_views/test_main_window.py`
  - Test with real EPUB files from `tests/fixtures/`
  - Verify UI elements are created
  - Test user interactions (button clicks)

### Manual Testing
- Open various EPUB files from different sources
- Test keyboard shortcuts
- Test window resize behavior
- Verify all error cases show appropriate messages

## Learning Resources

### PyQt6 Basics
- Official PyQt6 docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt for Python tutorial: https://doc.qt.io/qtforpython/
- Focus areas:
  - Application structure (QApplication, QMainWindow)
  - Signals and slots pattern
  - Layouts (QVBoxLayout, QHBoxLayout)
  - Widgets (QTextBrowser, QPushButton, QFileDialog)

### Specific Components
- **QTextBrowser**: https://doc.qt.io/qt-6/qtextbrowser.html
  - HTML subset it supports
  - setHtml() method
  - Resource loading for images
- **Signals/Slots**: Core Qt pattern for event handling
  - How to connect button clicks to functions
  - Custom signals if needed

## Implementation Guidance

### Recommended Workflow
1. **Study Phase** (parallel):
   - Use `/study PyQt6 basics` in another window
   - Focus on: QApplication, QMainWindow, QTextBrowser, signals/slots, layouts
   - Build tiny example: "Hello World" window with a button

2. **Architecture Phase**:
   - Use `/architect` to design the View and Controller classes
   - Sketch out the signals/slots connections
   - Decide on class responsibilities

3. **Development Phase**:
   - Use `/branch feature/epub-rendering-mvp`
   - Implement phase-by-phase (don't jump ahead)
   - Use `/developer` for each phase
   - Consider TDD for controller logic (easier to test than UI)
   - Manual testing for UI components

4. **Review Phase**:
   - Use `/code-review` before creating PR
   - Come back to `/pm` for transition assessment

### Pro Tips
- **Start tiny**: Get a window showing before adding complexity
- **Test early**: Run the app after each small change
- **UI debugging**: Print statements won't help—use Qt debugger or visual inspection
- **Iterate**: First version will be rough; refine through use
- **Learning**: This is new territory—expect to read docs, experiment, and iterate

### When to Ask for Help
- If stuck on PyQt6 patterns: Use `/hint` or `/mentor`
- If hitting bugs: Use `/debug`
- If architecture feels wrong: Use `/architect` to reconsider
- If concept is unclear: Use `/study` or `/mentor`

## Success Metrics
After this feature is complete, you should be able to:
- Open any valid EPUB file
- Read through it chapter by chapter
- Understand PyQt6 well enough to add more UI features
- Have working knowledge of signals/slots pattern
- Know how to integrate Qt UI with Python domain models

## Next Features After This
Once this MVP is working, natural next steps:
1. Reading themes (light/dark mode)
2. Reading progress tracking (remember position)
3. Table of contents sidebar
4. Bookmarks
5. Font/size customization

This MVP is the foundation for all of those.
