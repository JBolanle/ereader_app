# Phase 1 UX Improvements Architecture

## Date
2024-12-06

## Context

After MVP completion and UX evaluation, we identified that while the e-reader is functionally solid, the **visual hierarchy needs improvement** to make the reading experience more comfortable and immersive. The interface currently competes with the content for attention rather than receding into the background.

**UX Evaluation:** See `docs/ux/mvp-ux-evaluation.md`

**Phase 1 Goals:**
- Make content surface visually elevated and prominent
- Improve readability of progress information
- Clarify navigation button affordances based on mode
- Make mode toggle state clearer
- Improve keyboard navigation visibility

**Constraints:**
- Minimize changes to existing architecture
- Use existing signal/slot infrastructure
- Maintain 80%+ test coverage
- Keep changes localized to affected components

---

## Phase 1 Improvements Overview

| # | Improvement | Component(s) | Complexity |
|---|-------------|--------------|------------|
| 1 | Content elevation (box-shadow) | Theme, BookViewer | Small |
| 2 | Status bar readability | Theme, MainWindow | Small |
| 3 | Dynamic navigation labels | NavigationBar | Small |
| 4 | Mode toggle clarity | NavigationBar | Small |
| 5 | Focus indicators | Theme | Small |

---

## Component Changes

### 1. Content Elevation (Box-Shadow)

#### Problem
Content surface (#FFFFFF) on background (#FAF8F5) has only 3% contrast. No visual separation between reading area and UI chrome.

#### Solution
Add subtle shadow to BookViewer to create elevation effect, making content "lift" off the page.

#### Implementation

**Theme Model (`src/ereader/models/theme.py`):**
- Extend `get_book_viewer_stylesheet()` to include box-shadow on QTextBrowser
- Use PyQt6's `border` property with transparent color trick for shadow effect
- Alternative: Use QGraphicsDropShadowEffect if QSS shadow insufficient

**Shadow Specifications:**
```css
/* Light theme shadow (subtle) */
border: 1px solid rgba(0, 0, 0, 0.06);
/* Note: QSS doesn't support box-shadow directly, will need QGraphicsDropShadowEffect */
```

**PyQt6 Approach:**
```python
# In BookViewer.__init__() after creating _renderer
shadow = QGraphicsDropShadowEffect(self._renderer)
shadow.setBlurRadius(8)
shadow.setXOffset(0)
shadow.setYOffset(2)
shadow.setColor(QColor(0, 0, 0, 15))  # Alpha = 15/255 ≈ 6%
self._renderer.setGraphicsEffect(shadow)
```

**Files to Modify:**
- `src/ereader/views/book_viewer.py` - Add shadow effect in `__init__()`
- `src/ereader/models/theme.py` - Add shadow color to Theme dataclass

**Testing:**
- Manual visual verification (shadow visible in both themes)
- No automated test needed (purely visual)

---

### 2. Status Bar Readability

#### Problem
Status bar uses 12px gray text that's hard to read at a glance. Progress information is important but visually deprioritized.

#### Solution
Increase font size to 13px and improve contrast for readability. Keep text-based approach for Phase 1 (visual progress bar deferred to Phase 2).

#### Implementation

**Theme Model (`src/ereader/models/theme.py`):**
- Update `get_global_stylesheet()` status bar styling:
  - Font size: 12px → 13px
  - Color: Use `text` instead of `text_secondary` for better contrast
  - Add slight padding for breathing room

```css
QStatusBar {
    background-color: {self.status_bg};
    color: {self.text};  /* Changed from text_secondary */
    border-top: 1px solid {self.border};
    font-size: 13px;  /* Increased from 12px */
    padding: 6px 12px;  /* Added padding */
}
```

**Files to Modify:**
- `src/ereader/models/theme.py` - Update status bar stylesheet

**Testing:**
- Manual visual verification
- Verify status bar messages still fit at larger size

**Future Enhancement (Phase 2):**
Add QProgressBar widget to MainWindow status bar and connect to `reading_progress_changed` signal for visual progress representation.

---

### 3. Dynamic Navigation Button Labels

#### Problem
Navigation buttons always say "Previous" and "Next", but their behavior changes based on mode:
- Scroll Mode: Navigate chapters
- Page Mode: Navigate pages

This creates confusion about what action will happen.

#### Solution
Update button text dynamically based on current navigation mode to match behavior.

#### Implementation

**NavigationBar (`src/ereader/views/navigation_bar.py`):**

Add method to update button labels based on mode:
```python
def update_button_labels(self, mode: NavigationMode) -> None:
    """Update navigation button labels based on current mode.

    Args:
        mode: Current NavigationMode (SCROLL or PAGE).
    """
    if mode == NavigationMode.PAGE:
        self._previous_button.setText("← Page")
        self._next_button.setText("Page →")
        self._previous_button.setToolTip("Go to previous page (Left Arrow)")
        self._next_button.setToolTip("Go to next page (Right Arrow)")
    else:  # SCROLL mode
        self._previous_button.setText("← Chapter")
        self._next_button.setText("Chapter →")
        self._previous_button.setToolTip("Go to previous chapter (Left Arrow)")
        self._next_button.setToolTip("Go to next chapter (Right Arrow)")
```

Call this method from existing `update_mode_button()` to keep labels in sync with mode.

**Signal Flow:**
```
Controller.toggle_navigation_mode()
  → emits mode_changed signal
  → MainWindow._on_mode_changed()
  → NavigationBar.update_mode_button()
  → NavigationBar.update_button_labels()  [NEW]
```

**Files to Modify:**
- `src/ereader/views/navigation_bar.py` - Add `update_button_labels()`, call from `update_mode_button()`

**Testing:**
- Add test to verify button text changes with mode
- Existing tests should pass (button clicks still emit same signals)

---

### 4. Mode Toggle Clarity

#### Problem
Mode toggle button shows the **target mode** (where you're going), not the **current mode** (where you are). This is confusing:
- When in Scroll mode, button says "Page Mode"
- Users think "I'm in Page Mode" when they're actually in Scroll mode

#### Solution
Change button to show **current mode** with a toggle indicator (⇄ or similar) to clarify it's a switch.

#### Implementation

**NavigationBar (`src/ereader/views/navigation_bar.py`):**

Update `update_mode_button()` to show current mode instead of target:
```python
def update_mode_button(self, mode: NavigationMode) -> None:
    """Update mode toggle button text based on current mode.

    Args:
        mode: Current NavigationMode (SCROLL or PAGE).
    """
    if mode == NavigationMode.PAGE:
        self._mode_toggle_button.setText("📄 Page Mode")
        self._mode_toggle_button.setToolTip("Switch to scroll mode (Ctrl+M)")
        logger.debug("Mode button updated: Page Mode (current)")
    else:
        self._mode_toggle_button.setText("📜 Scroll Mode")
        self._mode_toggle_button.setToolTip("Switch to page mode (Ctrl+M)")
        logger.debug("Mode button updated: Scroll Mode (current)")

    # Also update navigation button labels
    self.update_button_labels(mode)
```

**Alternative (no emoji):**
- "Page Mode ⇄" / "Scroll Mode ⇄"
- Use Unicode symbol instead of emoji for better font compatibility

**Files to Modify:**
- `src/ereader/views/navigation_bar.py` - Update `update_mode_button()` logic

**Testing:**
- Update test to verify button shows current mode, not target
- Verify tooltip shows opposite mode as target

---

### 5. Focus Indicators for Keyboard Navigation

#### Problem
No explicit focus indicators on buttons for keyboard navigation. Relying on Qt defaults, which may not be visible enough.

#### Solution
Add custom focus styling to buttons via Theme stylesheet for clear visual feedback when navigating with keyboard.

#### Implementation

**Theme Model (`src/ereader/models/theme.py`):**

Update `get_navigation_bar_stylesheet()` to include focus state:
```css
QPushButton:focus {
    outline: 2px solid {self.accent};
    outline-offset: 2px;
}
```

**Note:** QSS `outline` support varies by platform. Alternative approach:
```css
QPushButton:focus {
    border: 2px solid {self.accent};
}
```

**Files to Modify:**
- `src/ereader/models/theme.py` - Add focus state to navigation bar stylesheet

**Testing:**
- Manual verification: Tab through buttons, verify visible focus ring
- Test on both Light and Dark themes

---

## Updated Theme Model

### New Theme Attributes

Add optional attributes for shadow effects:

```python
@dataclass(frozen=True)
class Theme:
    # ... existing attributes ...

    # Shadow settings (optional, for content elevation)
    shadow_color: str = "#000000"  # Black
    shadow_alpha: int = 15  # Alpha value 0-255 (15 ≈ 6% opacity)
    shadow_blur: int = 8  # Blur radius in pixels
    shadow_offset_y: int = 2  # Vertical offset
```

### Updated Theme Definitions

```python
LIGHT_THEME = Theme(
    # ... existing attributes ...
    shadow_color="#000000",
    shadow_alpha=15,  # 6% opacity for subtle shadow
)

DARK_THEME = Theme(
    # ... existing attributes ...
    shadow_color="#000000",
    shadow_alpha=25,  # Slightly stronger shadow for dark theme
)
```

---

## Signal Flow (No Changes Required)

All improvements leverage existing signal infrastructure:

```
Controller Mode Change:
  toggle_navigation_mode()
  → mode_changed signal (existing)
  → MainWindow._on_mode_changed()
  → NavigationBar.update_mode_button()
  → [NEW] NavigationBar.update_button_labels()

No new signals needed.
```

---

## File Modification Summary

| File | Changes | LOC Impact |
|------|---------|------------|
| `src/ereader/models/theme.py` | Add shadow attrs, update stylesheets | +20 |
| `src/ereader/views/book_viewer.py` | Add shadow effect in `__init__()` | +10 |
| `src/ereader/views/navigation_bar.py` | Add `update_button_labels()`, update `update_mode_button()` | +25 |
| `tests/test_views/test_navigation_bar.py` | Add tests for dynamic labels and mode button clarity | +30 |

**Total Impact:** ~85 LOC added/modified

---

## Testing Strategy

### Unit Tests

**NavigationBar:**
- `test_dynamic_button_labels_scroll_mode()` - Verify "← Chapter" / "Chapter →" in scroll mode
- `test_dynamic_button_labels_page_mode()` - Verify "← Page" / "Page →" in page mode
- `test_mode_button_shows_current_mode()` - Verify button shows current mode, not target
- `test_mode_button_tooltip_shows_target()` - Verify tooltip indicates where toggle will go

**BookViewer:**
- No new tests needed (shadow is visual only)

### Manual Testing

**Visual Verification:**
- [ ] Content has subtle shadow/elevation in both Light and Dark themes
- [ ] Status bar text is readable (13px, proper contrast)
- [ ] Navigation buttons update labels when mode changes
- [ ] Mode toggle shows current mode clearly
- [ ] Focus indicators visible when tabbing through buttons
- [ ] All themes still apply correctly

**Interaction Testing:**
- [ ] Toggle mode → labels update immediately
- [ ] Navigate with keyboard → focus indicators visible
- [ ] All keyboard shortcuts still work

---

## Implementation Order

1. **Theme Model Updates** (foundation)
   - Add shadow attributes
   - Update status bar stylesheet
   - Add focus indicator styles

2. **BookViewer Shadow** (visual improvement)
   - Add shadow effect in `__init__()`
   - Test with both themes

3. **NavigationBar Labels** (UX clarity)
   - Add `update_button_labels()`
   - Update `update_mode_button()` logic
   - Write tests

4. **Manual Testing** (verification)
   - Visual verification of all changes
   - Keyboard navigation testing

---

## Performance Considerations

**Shadow Effect:**
- `QGraphicsDropShadowEffect` has minimal performance impact for static widgets
- No impact on reading/scrolling performance (shadow applied to container, not content)

**Button Label Updates:**
- Updates happen on mode toggle only (infrequent)
- No performance concern

**Status Bar:**
- Font size change has no measurable impact

**Overall:** No performance degradation expected.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Shadow not visible on some platforms | Low | Test on macOS, Linux, Windows if available |
| Focus outline not visible in QSS | Low | Fall back to border instead of outline |
| Button labels too long for small windows | Low | Test at minimum window size (900x700) |
| Emoji not rendering on all platforms | Low | Use Unicode symbols or text-only fallback |

---

## Future Enhancements (Phase 2)

These improvements are **deferred** to Phase 2:

- **Visual progress bar** - Add QProgressBar to status bar for graphical progress
- **Auto-hide navigation bar** - Implement fade-out after inactivity
- **Toggle switch widget** - Replace button with proper toggle switch UI
- **Toast notifications** - Brief feedback when changing modes

---

## Success Criteria

Phase 1 is successful when:
- [ ] Content visually stands out from UI chrome (elevation visible)
- [ ] Status bar is easily readable at a glance
- [ ] Navigation button labels clearly indicate action (page vs chapter)
- [ ] Mode toggle clearly shows current mode
- [ ] Keyboard focus is visible when tabbing through UI
- [ ] All tests pass with 80%+ coverage maintained
- [ ] No performance degradation

---

## References

- UX Evaluation: `docs/ux/mvp-ux-evaluation.md`
- Existing Theme Architecture: `src/ereader/models/theme.py`
- Reading Themes Decision: CLAUDE.md architectural decisions log

---

## Decision

**Approved Architecture:**
- Extend Theme model with shadow attributes
- Use `QGraphicsDropShadowEffect` for content elevation
- Add `update_button_labels()` method to NavigationBar
- Change mode toggle to show current mode instead of target
- Enhance focus indicators via Theme stylesheet

This approach:
- ✅ Leverages existing architecture (Theme, signals)
- ✅ Keeps changes localized and testable
- ✅ Maintains consistency with editorial design language
- ✅ Requires no new dependencies
- ✅ Can be implemented incrementally

**Implementation can proceed.**
