# Manual Testing Checklist - EPUB Rendering MVP

## Date
2025-12-03

## Branch
`feature/epub-rendering-mvp`

## Issue
#18 - EPUB Rendering MVP Implementation

## Tester
_[Your name here]_

## Testing Environment
- **OS**: macOS / Linux / Windows
- **Python Version**: `python --version`
- **PyQt6 Version**: `uv run python -c "from PyQt6.QtCore import qVersion; print(qVersion())"`
- **Branch**: `git rev-parse --short HEAD`

---

## Instructions

Run through this checklist manually to verify all functionality works correctly. Check each box as you complete the test.

To run the application:
```bash
uv run python -m ereader
```

---

## Test Suite

### 1. Application Launch ✅

#### 1.1 Basic Startup
- [x] Application launches without errors
- [x] Window appears on screen
- [x] Window title shows "E-Reader"
- [x] Window is resizable
- [x] Status bar shows "Ready"

#### 1.2 Initial State
- [x] Welcome message displays in center
- [x] Message says "Welcome to E-Reader"
- [x] Instructions show "Open an EPUB file to start reading"
- [x] Instructions show "File → Open (Ctrl+O)"
- [x] Previous/Next buttons are disabled (grayed out)

#### 1.3 Menu Bar
- [x] Menu bar is visible
- [x] "File" menu exists
- [x] File menu contains "Open..." option
- [x] File menu contains "Quit" option
- [x] Menu items show keyboard shortcuts (Ctrl+O, Ctrl+Q)

**Notes:**
```
So far so good.
```

---

### 2. File Opening 📂

#### 2.1 File Dialog
- [x] Click File → Open (or press Ctrl+O)
- [x] File dialog appears
- [x] Dialog filters to "EPUB Files (*.epub)"
- [x] Can navigate to EPUB files
- [x] Can cancel dialog (nothing happens)

#### 2.2 Open Valid EPUB
Test with: `scratch/EPUBS/1984 (George Orwell) (Z-Library).epub`

- [x] Select and open the file
- [x] No errors or crashes
- [x] Window title updates to "[Book Title] - E-Reader"
- [ ] Status bar shows "Opened: [Title] by [Author]"
- [x] First chapter content displays
- [x] Content is readable (not garbled text)
- [x] Previous button is DISABLED (at first chapter)
- [x] Next button is ENABLED (can move forward)

#### 2.3 Chapter Content Display
- [x] Text is readable (12pt font, good padding)
- [x] Paragraphs are separated correctly
- [x] Headings are larger/bold
- [x] Content scrolls if longer than window
- [x] No overlap with navigation buttons

**Book Tested:** _[e.g., 1984 by George Orwell]_

**Notes:**
```
- Status bar only shows current chapter location
```

---

### 3. Chapter Navigation 📖

#### 3.1 Next Button Navigation
- [x] Click "Next" button
- [x] Chapter changes (content updates)
- [x] Status bar updates: "Chapter 2 of X"
- [x] Previous button becomes ENABLED
- [x] Navigation is instant (no delay)
- [x] Click "Next" multiple times - works smoothly

#### 3.2 Previous Button Navigation
- [x] Navigate to chapter 3+ (use Next button)
- [x] Click "Previous" button
- [x] Goes back one chapter
- [x] Status bar updates correctly
- [x] Can navigate backward multiple times

#### 3.3 Boundary Conditions
Navigate to **first chapter**:
- [x] Previous button is DISABLED
- [x] Clicking disabled button does nothing
- [x] Status bar shows "Chapter 1 of X"

Navigate to **last chapter** (click Next repeatedly):
- [x] Next button becomes DISABLED
- [x] Clicking disabled button does nothing
- [x] Status bar shows "Chapter X of X" (last)

#### 3.4 Keyboard Shortcuts
- [ ] Press Right Arrow key → navigates forward
- [ ] Press Left Arrow key → navigates backward
- [x] Press Page Down → navigates forward
- [x] Press Page Up → navigates backward
- [x] Shortcuts work from anywhere in the app
- [x] Shortcuts respect boundaries (disabled at first/last)

**Chapters Navigated:** _[e.g., 1 → 5 → 3 → 1]_

**Notes:**
```
- Right and left arrow keys do not change chapter
```

---

### 4. Error Handling 🚨

#### 4.1 Non-Existent File
- [x] Manually type a non-existent path in file dialog (if possible)
- [x] Error dialog appears
- [x] Dialog title: "File Not Found"
- [x] Message mentions the file path
- [x] Click OK → dialog closes
- [x] Application doesn't crash
- [x] Previous state is maintained

#### 4.2 Invalid File Type
Create a test file: `echo "not an epub" > /tmp/fake.epub`

- [x] Try to open the fake EPUB file
- [x] Error dialog appears
- [x] Dialog title: "Invalid EPUB"
- [x] Message mentions it's not a valid EPUB
- [x] Click OK → dialog closes
- [x] Application doesn't crash

#### 4.3 Corrupted EPUB
Create a corrupt file: `truncate -s 1000 /path/to/book.epub`
(or use a known corrupted file)

- [x] Try to open corrupted EPUB
- [x] Error dialog appears
- [x] Error message is user-friendly (not a stack trace)
- [x] Application doesn't crash

**Notes:**
```
[Add any observations]
```

---

### 5. Multiple Books 📚

#### 5.1 Open Different Book
- [x] Open first book (e.g., 1984)
- [x] Navigate to chapter 3
- [x] Open second book (File → Open)
- [x] Second book loads correctly
- [x] Window title updates to new book
- [x] Status bar updates to new book
- [x] Chapter resets to 1
- [x] Previous book is replaced (not kept in memory)

**Books Tested:**
1. _[1984]_
2. _[The body keeps the score]_

**Notes:**
```
[Add any observations]
```

---

### 6. Window Behavior 🪟

#### 6.1 Resize
- [x] Make window smaller → content reflows
- [x] Make window larger → content uses space
- [x] Make window very narrow → still readable
- [x] Navigation buttons stay visible
- [x] Status bar stays visible

#### 6.2 Close and Quit
- [x] Click X button (window close) → app closes
- [x] Reopen app → starts fresh (no state saved)
- [x] Use File → Quit → app closes
- [x] Use Ctrl+Q → app closes

**Notes:**
```
[Add any observations]
```

---

### 7. Performance ⚡

#### 7.1 Opening Books
- [x] Small EPUB (<1MB) opens instantly (<1 second)
- [x] Large EPUB (>5MB) opens quickly (<2 seconds)
- [x] No freezing or hanging

#### 7.2 Navigation Speed
- [x] Chapter navigation is instant (<100ms perceived)
- [x] No lag when clicking buttons rapidly
- [x] No memory warnings or slowdowns

**Book Sizes Tested:**
- Small: _[1984, 683kb]_
- Large: _[mamba mentality, 211.2mb]_

**Notes:**
```
[Add any observations]
```

---

### 8. Edge Cases 🔍

#### 8.1 Single Chapter Book
(If you have one, or create a minimal EPUB)

- [x] Opens correctly
- [x] Both Previous and Next are DISABLED
- [x] Status bar shows "Chapter 1 of 1"
- [x] No errors or crashes

#### 8.2 Long Chapter
- [x] Open book with very long chapter
- [x] Scrollbar appears
- [x] Can scroll through entire chapter
- [x] No performance issues

#### 8.3 Special Characters
Open book with Unicode/special characters (e.g., "Mamba Mentality")

- [x] Title displays correctly in window title
- [x] Author displays correctly in status bar
- [x] Content with special characters renders correctly
- [x] No encoding errors or garbled text

**Notes:**
```
[Add any observations]
```

---

## Overall Assessment

### Bugs Found 🐛

List any bugs or issues discovered:

1. Images don't load
2. Keyboard arrows (left and right) don't change chapters
3.

### Pass/Fail Criteria

**MVP Acceptance Criteria** (from spec):
- [x] User can select and open an EPUB file via file dialog
- [x] Book content displays in a scrollable window with readable text
- [x] HTML content from EPUB chapters renders correctly (basic formatting)
- [x] User can navigate to next chapter (button or keyboard shortcut)
- [x] User can navigate to previous chapter (button or keyboard shortcut)
- [x] Window shows book title and current chapter title
- [x] Application handles errors gracefully (corrupted file, unsupported format, missing chapters)
- [x] Window is resizable and content adjusts appropriately

### Test Results

**Total Tests:** _[Count checked boxes]_
**Passed:** _[Number passed]_
**Failed:** _[Number failed]_
**Blocked:** _[Number blocked by bugs]_

### Recommendation

- [ ] ✅ **PASS** - Ready for merge (all critical tests pass)
- [x] ⚠️ **PASS WITH NOTES** - Minor issues, document and defer
- [ ] ❌ **FAIL** - Critical issues, must fix before merge

### Notes and Observations

```
[Add overall thoughts, suggestions, or concerns here]
```

---

## Sign-Off

**Tested By:** _[Olajumoke Bolanle]_
**Date:** _[12-03-2025]_
**Time Spent:** _[10 minutes]_

**Status:** [x] COMPLETE

---

## Next Steps

After completing this checklist:

1. Update the code review action items with completion status
2. Document any bugs found as new issues
3. If PASS: Proceed with creating PR for #18
4. If FAIL: Fix critical issues and re-test

**Related Documents:**
- Code Review: `docs/reviews/feature-epub-rendering-mvp.md`
- Testing Strategy: `docs/testing/gui-testing-strategy.md`
- Spec: `docs/specs/epub-rendering-mvp.md`
