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
- [ ] Application launches without errors
- [ ] Window appears on screen
- [ ] Window title shows "E-Reader"
- [ ] Window is resizable
- [ ] Status bar shows "Ready"

#### 1.2 Initial State
- [ ] Welcome message displays in center
- [ ] Message says "Welcome to E-Reader"
- [ ] Instructions show "Open an EPUB file to start reading"
- [ ] Instructions show "File → Open (Ctrl+O)"
- [ ] Previous/Next buttons are disabled (grayed out)

#### 1.3 Menu Bar
- [ ] Menu bar is visible
- [ ] "File" menu exists
- [ ] File menu contains "Open..." option
- [ ] File menu contains "Quit" option
- [ ] Menu items show keyboard shortcuts (Ctrl+O, Ctrl+Q)

**Notes:**
```
[Add any observations or issues here]
```

---

### 2. File Opening 📂

#### 2.1 File Dialog
- [ ] Click File → Open (or press Ctrl+O)
- [ ] File dialog appears
- [ ] Dialog filters to "EPUB Files (*.epub)"
- [ ] Can navigate to EPUB files
- [ ] Can cancel dialog (nothing happens)

#### 2.2 Open Valid EPUB
Test with: `scratch/EPUBS/1984 (George Orwell) (Z-Library).epub`

- [ ] Select and open the file
- [ ] No errors or crashes
- [ ] Window title updates to "[Book Title] - E-Reader"
- [ ] Status bar shows "Opened: [Title] by [Author]"
- [ ] First chapter content displays
- [ ] Content is readable (not garbled text)
- [ ] Previous button is DISABLED (at first chapter)
- [ ] Next button is ENABLED (can move forward)

#### 2.3 Chapter Content Display
- [ ] Text is readable (12pt font, good padding)
- [ ] Paragraphs are separated correctly
- [ ] Headings are larger/bold
- [ ] Content scrolls if longer than window
- [ ] No overlap with navigation buttons

**Book Tested:** _[e.g., 1984 by George Orwell]_

**Notes:**
```
[Add any observations]
```

---

### 3. Chapter Navigation 📖

#### 3.1 Next Button Navigation
- [ ] Click "Next" button
- [ ] Chapter changes (content updates)
- [ ] Status bar updates: "Chapter 2 of X"
- [ ] Previous button becomes ENABLED
- [ ] Navigation is instant (no delay)
- [ ] Click "Next" multiple times - works smoothly

#### 3.2 Previous Button Navigation
- [ ] Navigate to chapter 3+ (use Next button)
- [ ] Click "Previous" button
- [ ] Goes back one chapter
- [ ] Status bar updates correctly
- [ ] Can navigate backward multiple times

#### 3.3 Boundary Conditions
Navigate to **first chapter**:
- [ ] Previous button is DISABLED
- [ ] Clicking disabled button does nothing
- [ ] Status bar shows "Chapter 1 of X"

Navigate to **last chapter** (click Next repeatedly):
- [ ] Next button becomes DISABLED
- [ ] Clicking disabled button does nothing
- [ ] Status bar shows "Chapter X of X" (last)

#### 3.4 Keyboard Shortcuts
- [ ] Press Right Arrow key → navigates forward
- [ ] Press Left Arrow key → navigates backward
- [ ] Press Page Down → navigates forward
- [ ] Press Page Up → navigates backward
- [ ] Shortcuts work from anywhere in the app
- [ ] Shortcuts respect boundaries (disabled at first/last)

**Chapters Navigated:** _[e.g., 1 → 5 → 3 → 1]_

**Notes:**
```
[Add any observations]
```

---

### 4. Error Handling 🚨

#### 4.1 Non-Existent File
- [ ] Manually type a non-existent path in file dialog (if possible)
- [ ] Error dialog appears
- [ ] Dialog title: "File Not Found"
- [ ] Message mentions the file path
- [ ] Click OK → dialog closes
- [ ] Application doesn't crash
- [ ] Previous state is maintained

#### 4.2 Invalid File Type
Create a test file: `echo "not an epub" > /tmp/fake.epub`

- [ ] Try to open the fake EPUB file
- [ ] Error dialog appears
- [ ] Dialog title: "Invalid EPUB"
- [ ] Message mentions it's not a valid EPUB
- [ ] Click OK → dialog closes
- [ ] Application doesn't crash

#### 4.3 Corrupted EPUB
Create a corrupt file: `truncate -s 1000 /path/to/book.epub`
(or use a known corrupted file)

- [ ] Try to open corrupted EPUB
- [ ] Error dialog appears
- [ ] Error message is user-friendly (not a stack trace)
- [ ] Application doesn't crash

**Notes:**
```
[Add any observations]
```

---

### 5. Multiple Books 📚

#### 5.1 Open Different Book
- [ ] Open first book (e.g., 1984)
- [ ] Navigate to chapter 3
- [ ] Open second book (File → Open)
- [ ] Second book loads correctly
- [ ] Window title updates to new book
- [ ] Status bar updates to new book
- [ ] Chapter resets to 1
- [ ] Previous book is replaced (not kept in memory)

**Books Tested:**
1. _[First book]_
2. _[Second book]_

**Notes:**
```
[Add any observations]
```

---

### 6. Window Behavior 🪟

#### 6.1 Resize
- [ ] Make window smaller → content reflows
- [ ] Make window larger → content uses space
- [ ] Make window very narrow → still readable
- [ ] Navigation buttons stay visible
- [ ] Status bar stays visible

#### 6.2 Close and Quit
- [ ] Click X button (window close) → app closes
- [ ] Reopen app → starts fresh (no state saved)
- [ ] Use File → Quit → app closes
- [ ] Use Ctrl+Q → app closes

**Notes:**
```
[Add any observations]
```

---

### 7. Performance ⚡

#### 7.1 Opening Books
- [ ] Small EPUB (<1MB) opens instantly (<1 second)
- [ ] Large EPUB (>5MB) opens quickly (<2 seconds)
- [ ] No freezing or hanging

#### 7.2 Navigation Speed
- [ ] Chapter navigation is instant (<100ms perceived)
- [ ] No lag when clicking buttons rapidly
- [ ] No memory warnings or slowdowns

**Book Sizes Tested:**
- Small: _[filename, size]_
- Large: _[filename, size]_

**Notes:**
```
[Add any observations]
```

---

### 8. Edge Cases 🔍

#### 8.1 Single Chapter Book
(If you have one, or create a minimal EPUB)

- [ ] Opens correctly
- [ ] Both Previous and Next are DISABLED
- [ ] Status bar shows "Chapter 1 of 1"
- [ ] No errors or crashes

#### 8.2 Long Chapter
- [ ] Open book with very long chapter
- [ ] Scrollbar appears
- [ ] Can scroll through entire chapter
- [ ] No performance issues

#### 8.3 Special Characters
Open book with Unicode/special characters (e.g., "Mamba Mentality")

- [ ] Title displays correctly in window title
- [ ] Author displays correctly in status bar
- [ ] Content with special characters renders correctly
- [ ] No encoding errors or garbled text

**Notes:**
```
[Add any observations]
```

---

## Overall Assessment

### Bugs Found 🐛

List any bugs or issues discovered:

1.
2.
3.

### Pass/Fail Criteria

**MVP Acceptance Criteria** (from spec):
- [ ] User can select and open an EPUB file via file dialog
- [ ] Book content displays in a scrollable window with readable text
- [ ] HTML content from EPUB chapters renders correctly (basic formatting)
- [ ] User can navigate to next chapter (button or keyboard shortcut)
- [ ] User can navigate to previous chapter (button or keyboard shortcut)
- [ ] Window shows book title and current chapter title
- [ ] Application handles errors gracefully (corrupted file, unsupported format, missing chapters)
- [ ] Window is resizable and content adjusts appropriately

### Test Results

**Total Tests:** _[Count checked boxes]_
**Passed:** _[Number passed]_
**Failed:** _[Number failed]_
**Blocked:** _[Number blocked by bugs]_

### Recommendation

- [ ] ✅ **PASS** - Ready for merge (all critical tests pass)
- [ ] ⚠️ **PASS WITH NOTES** - Minor issues, document and defer
- [ ] ❌ **FAIL** - Critical issues, must fix before merge

### Notes and Observations

```
[Add overall thoughts, suggestions, or concerns here]
```

---

## Sign-Off

**Tested By:** _[Your name]_
**Date:** _[Date completed]_
**Time Spent:** _[Approximate time]_

**Status:** [ ] COMPLETE

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
