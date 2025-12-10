# Feature Specification: Phase 1 UX Improvements

**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: Medium
**Created**: 2024-12-06
**Related Docs**:
- UX Evaluation: `docs/ux/mvp-ux-evaluation.md`
- Architecture: `docs/architecture/phase1-ux-improvements.md`

---

## Overview

Implement 5 targeted UX improvements to elevate the reading experience from "functional" to "comfortable and immersive". These improvements address visual hierarchy issues identified in the MVP UX evaluation, making the content stand out while the UI chrome recedes into the background.

**Context**: The Editorial Elegance color palette and QSS stylesheets were implemented in PR #37. This feature builds on that foundation to address specific usability issues in the interface.

---

## User Stories

### Primary User Story
As a reader, I want the e-reader interface to fade into the background so that I can focus on the book content without visual distractions.

### Specific User Stories

1. **Content Elevation**
   - As a reader, I want the content area to visually stand out from the UI chrome so that my eyes are naturally drawn to the book text.

2. **Status Bar Readability**
   - As a reader, I want to easily see my reading progress at a glance without straining my eyes.

3. **Navigation Clarity**
   - As a reader, I want navigation button labels to clearly indicate what action they perform (navigate pages vs chapters) so I'm not confused about what will happen when I click.

4. **Mode Toggle Clarity**
   - As a reader, I want to know which navigation mode I'm currently in so I understand the current state of the application.

5. **Keyboard Navigation Visibility**
   - As a keyboard user, I want clear visual feedback showing which button has focus so I can navigate efficiently with Tab and Enter keys.

---

## Acceptance Criteria

### 1. Content Elevation
- [ ] Content area (BookViewer) has subtle shadow/elevation effect visible in both Light and Dark themes
- [ ] Shadow creates visual separation between content and background without being distracting
- [ ] Shadow parameters: 8px blur radius, 2px vertical offset, ~6% opacity (light theme) / ~10% (dark theme)
- [ ] No performance degradation (smooth scrolling maintained)

### 2. Status Bar Readability
- [ ] Status bar text uses primary text color (not secondary) for better contrast
- [ ] Font size increased from 12px to 13px
- [ ] Padding added for breathing room (6px vertical, 12px horizontal)
- [ ] Status bar messages remain readable on small windows (900x700 minimum)

### 3. Dynamic Navigation Button Labels
- [ ] In Scroll Mode: buttons display "← Chapter" and "Chapter →"
- [ ] In Page Mode: buttons display "← Page" and "Page →"
- [ ] Labels update immediately when navigation mode changes
- [ ] Tooltips also update to reflect current mode and keyboard shortcuts
- [ ] Button width accommodates label changes without layout shift

### 4. Mode Toggle Clarity
- [ ] Mode toggle button shows CURRENT mode (not target mode)
- [ ] In Scroll Mode: button displays "📜 Scroll Mode" (or text equivalent)
- [ ] In Page Mode: button displays "📄 Page Mode" (or text equivalent)
- [ ] Tooltip indicates what mode will be activated on click (opposite of current)
- [ ] State is immediately clear to users without needing to click

### 5. Focus Indicators for Keyboard Navigation
- [ ] Navigation buttons show visible focus ring when focused via keyboard (Tab key)
- [ ] Focus indicator uses accent color for visibility
- [ ] Focus styling works in both Light and Dark themes
- [ ] Focus ring has 2px border with 2px offset (or equivalent visible styling)
- [ ] Focus indicators don't interfere with button text readability

---

## Edge Cases

### Content Elevation
- **Multiple theme switches**: Shadow updates correctly when switching between Light/Dark themes
- **Window resize**: Shadow remains visible and properly rendered at different window sizes
- **Platform differences**: Shadow rendering tested on macOS (primary), Windows/Linux (if available)

### Status Bar Readability
- **Long chapter titles**: Status bar text truncates gracefully if chapter title is very long
- **Small windows**: Text remains readable at minimum window size (900x700)
- **Theme changes**: Status bar updates immediately when theme changes

### Dynamic Navigation Labels
- **Rapid mode toggling**: Labels update correctly even when toggling mode quickly
- **First load**: Labels display correct mode on initial book load (default: Scroll Mode)
- **Last chapter/page**: Labels remain clickable (disabled state) but text stays consistent
- **Button layout**: Changing labels doesn't cause navigation bar layout shift

### Mode Toggle Clarity
- **Initial state**: Button shows correct initial mode (Scroll Mode by default)
- **Emoji rendering**: Fallback to text-only if emoji not supported on platform
- **Tooltip updates**: Tooltip accurately reflects opposite mode after toggle
- **Screen readers**: Button text is accessible (emoji doesn't break accessibility)

### Keyboard Navigation Focus
- **Tab order**: Focus moves logically through buttons (Previous → Next → Mode Toggle)
- **Keyboard shortcuts still work**: Arrow keys, Page Up/Down work regardless of focus state
- **Focus after click**: Clicking a button shows focus ring
- **Focus persistence**: Focus remains visible after button state changes (enabled/disabled)

---

## Out of Scope

This phase explicitly does NOT include:

- **Visual progress bar** - Deferred to Phase 2 (requires QProgressBar widget integration)
- **Auto-hide navigation bar** - Deferred to Phase 2 (significant complexity)
- **Toggle switch widget** - Using button with clear state indication instead
- **Toast notifications** - Deferred to Phase 2
- **Keyboard shortcuts help dialog** - Phase 3 polish item
- **Loading indicators** - Phase 3 polish item

---

## Dependencies

### Required Components (Already Exist)
- ✅ Theme dataclass with Editorial Elegance palette (PR #37)
- ✅ QSS stylesheet generation methods (`get_global_stylesheet()`, etc.)
- ✅ Navigation mode system (`NavigationMode` enum, mode switching)
- ✅ Signal infrastructure (`mode_changed` signal)

### No New Dependencies
All improvements use existing Qt widgets and styling capabilities. No new packages required.

---

## Tasks

### Task 1: Content Elevation (Shadow Effect)
**Estimate**: Small (~1-2 hours)

**Implementation**:
1. Add shadow attributes to Theme dataclass (shadow_color, shadow_alpha, shadow_blur, shadow_offset_y)
2. Update LIGHT_THEME and DARK_THEME with shadow parameters
3. In BookViewer.__init__(), create QGraphicsDropShadowEffect and apply to _renderer
4. Manual test shadow visibility in both themes

**Files to Modify**:
- `src/ereader/models/theme.py` - Add shadow attributes
- `src/ereader/views/book_viewer.py` - Apply shadow effect

**Testing**: Manual visual verification (shadow is purely visual, no unit test needed)

---

### Task 2: Status Bar Readability
**Estimate**: Small (~30 minutes)

**Implementation**:
1. Update `get_global_stylesheet()` in Theme class
2. Change status bar font size from 12px to 13px
3. Change status bar color from `text_secondary` to `text`
4. Add padding: 6px 12px

**Files to Modify**:
- `src/ereader/models/theme.py` - Update QStatusBar styling in get_global_stylesheet()

**Testing**: Manual verification - check status bar at minimum window size

---

### Task 3: Dynamic Navigation Button Labels
**Estimate**: Medium (~2-3 hours)

**Implementation**:
1. Add `update_button_labels(mode: NavigationMode)` method to NavigationBar
2. Update button text and tooltips based on mode
3. Call from existing `update_mode_button()` method to keep labels in sync
4. Write unit tests for label updates

**Files to Modify**:
- `src/ereader/views/navigation_bar.py` - Add update_button_labels() method

**Testing**:
- Unit test: `test_dynamic_button_labels_scroll_mode()`
- Unit test: `test_dynamic_button_labels_page_mode()`
- Unit test: `test_button_labels_update_on_mode_change()`

---

### Task 4: Mode Toggle Clarity
**Estimate**: Medium (~2-3 hours)

**Implementation**:
1. Modify `update_mode_button()` in NavigationBar to show current mode instead of target
2. Update button text: "📜 Scroll Mode" or "📄 Page Mode"
3. Update tooltip to indicate opposite mode (where toggle will go)
4. Update existing tests to verify new button text pattern

**Files to Modify**:
- `src/ereader/views/navigation_bar.py` - Modify update_mode_button() logic

**Testing**:
- Update existing test: `test_mode_button_shows_current_mode_not_target()`
- Update existing test: `test_mode_button_tooltip_indicates_target()`

---

### Task 5: Focus Indicators for Keyboard Navigation
**Estimate**: Small (~1 hour)

**Implementation**:
1. Update `get_navigation_bar_stylesheet()` in Theme class
2. Add QPushButton:focus styling with accent color border
3. Test with Tab key navigation to verify visibility

**Files to Modify**:
- `src/ereader/models/theme.py` - Add focus state to get_navigation_bar_stylesheet()

**Testing**: Manual verification with keyboard navigation (Tab through buttons)

---

## Implementation Guidance

### Recommended Order
1. **Status Bar** (Task 2) - Easiest, pure CSS change, immediate visual improvement
2. **Focus Indicators** (Task 5) - Also CSS-only, quick win
3. **Content Elevation** (Task 1) - Visual improvement, requires testing shadow on both themes
4. **Navigation Labels** (Task 3) - Requires logic changes and unit tests
5. **Mode Toggle** (Task 4) - Requires logic changes and test updates

### Development Workflow
- Use `/branch` to create `feature/phase1-ux-improvements` branch
- Use `/developer` to implement each task incrementally
- Run `/test` after each task to maintain coverage
- Commit after each task completes (5 commits total)
- Use `/code-review` before creating PR
- Use `/pr` when all tasks complete

### Testing Strategy
- **Unit tests**: Navigation button label logic, mode toggle text logic
- **Manual tests**: Visual verification of shadows, focus rings, status bar readability
- **Coverage target**: Maintain 80%+ coverage (aim for 90%+)
- **Smoke test**: Open book, toggle modes, use keyboard navigation, switch themes

---

## Non-Functional Requirements

### Performance
- No measurable performance degradation
- Shadow effect has minimal impact (static widget, no animations)
- Button label updates happen on mode toggle only (infrequent operation)
- Target: All UI interactions remain <100ms

### Accessibility
- **Keyboard navigation**: All improvements enhance keyboard usability
- **Focus visibility**: WCAG 2.1 Level AA compliance (2.4.7 Focus Visible)
- **Color contrast**: Maintain WCAG AAA contrast ratios (>7:1)
- **Screen readers**: Button text changes are announced by screen readers

### Platform Compatibility
- **Primary target**: macOS (development environment)
- **Secondary**: Windows, Linux (best effort)
- **Shadow rendering**: May vary slightly across platforms (acceptable)
- **Font rendering**: Status bar text may render differently across OS (acceptable)

---

## Success Criteria

Phase 1 is successful when:

### Functional Criteria
- [ ] All 5 acceptance criteria sections are fully met
- [ ] All unit tests pass (existing + new tests)
- [ ] Test coverage remains ≥80% (ideally ≥90%)
- [ ] All edge cases handled gracefully

### Quality Criteria
- [ ] Code follows CLAUDE.md standards (type hints, docstrings, logging)
- [ ] No ruff linting errors
- [ ] `/code-review` approval with no critical issues
- [ ] No performance regression (smooth scrolling, instant theme switching)

### User Experience Criteria
- [ ] Content visually stands out from UI chrome (elevation visible)
- [ ] Status bar is easily readable at a glance
- [ ] Navigation button labels clearly indicate action (no confusion)
- [ ] Mode toggle clearly shows current mode (no guessing)
- [ ] Keyboard focus is visible when tabbing through UI

### Documentation Criteria
- [ ] All code changes have docstrings explaining purpose
- [ ] Architecture document reflects implementation
- [ ] Any deviations from architecture are documented

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Shadow not visible on some platforms | Low | Medium | Test on macOS primarily, document platform differences |
| Focus outline not visible in QSS | Low | Low | Use border fallback if outline not supported |
| Button labels too long for small windows | Very Low | Low | Test at 900x700 minimum size, truncate if needed |
| Emoji not rendering on all platforms | Low | Low | Provide text-only fallback ("Scroll Mode ⇄") |
| Performance impact from shadow effect | Very Low | Medium | Profile before/after, remove if >5ms impact |
| Breaking existing tests | Medium | Medium | Run tests after each change, update tests incrementally |

---

## Future Enhancements (Phase 2+)

These improvements are explicitly deferred to future phases:

### Phase 2: Immersion
- Visual progress bar (QProgressBar in status bar)
- Auto-hide navigation bar (fade out after inactivity)
- Toggle switch widget (replace button with proper toggle UI)
- Toast notifications (brief feedback on mode change)

### Phase 3: Polish
- Keyboard shortcuts help dialog (Help > Keyboard Shortcuts)
- Loading indicators for book operations
- Differentiate mode toggle from navigation buttons visually
- Use reading font for welcome message

---

## Definition of Done

A task is "done" when:
- [ ] Code is written following CLAUDE.md standards
- [ ] Type hints on all function signatures
- [ ] Docstrings on all public methods (Google style)
- [ ] Logging instead of print statements
- [ ] Unit tests written for logic changes (if applicable)
- [ ] Manual testing completed for visual changes
- [ ] Tests pass (`/test` green)
- [ ] Coverage ≥80% maintained
- [ ] No linting errors (`ruff check` passes)
- [ ] Code committed with conventional commit message
- [ ] Edge cases documented in code comments

The entire feature is "done" when:
- [ ] All 5 tasks meet individual "done" criteria
- [ ] `/code-review` completed with no critical issues
- [ ] PR created with comprehensive description
- [ ] All CI checks pass (tests, coverage, linting)
- [ ] Manual QA completed (open book, test all modes, test themes)
- [ ] Architecture document updated with any implementation notes

---

## References

- **UX Evaluation**: `docs/ux/mvp-ux-evaluation.md` - Identified issues and recommendations
- **Architecture Design**: `docs/architecture/phase1-ux-improvements.md` - Technical implementation approach
- **Code Review**: `docs/reviews/feature-visual-polish-phase1.md` - Editorial Elegance implementation review
- **Theme System**: `src/ereader/models/theme.py` - Current theme implementation
- **WCAG 2.1 Focus Visible**: https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html

---

## Notes

### Why These 5 Improvements?
These were selected from the UX evaluation as **quick wins with high impact**:
- All leverage existing architecture (no major refactors)
- All can be implemented incrementally (5 independent tasks)
- Together they address the #1 issue: "Interface competes with content for attention"
- Total estimated effort: ~7-10 hours (reasonable for a focused session)

### Why Not Bigger Changes?
- **Auto-hide navigation** is Phase 2 because it requires mouse tracking, timers, animations (much more complex)
- **Visual progress bar** is Phase 2 because it requires widget addition and signal connections (moderate complexity)
- **Toggle switch widget** is Phase 2 because current button approach with clear labels is sufficient

### Learning Opportunities
This feature provides practice with:
- Qt graphics effects (QGraphicsDropShadowEffect)
- QSS pseudo-states (:focus, :hover)
- Dynamic UI updates based on application state
- Accessibility considerations (focus visibility, screen readers)
- Incremental development (5 small tasks vs 1 big task)
