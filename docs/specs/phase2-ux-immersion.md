# Feature Specification: Phase 2 UX Immersion Enhancements

**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: Medium-Large (14-18 hours)
**Created**: 2025-12-11
**Related Docs**:
- Phase 1 Spec: `docs/specs/phase1-ux-improvements.md`
- UX Evaluation: `docs/ux/mvp-ux-evaluation.md`
- Phase 1 Review: `docs/reviews/feature-phase1-ux-improvements.md`

---

## Overview

Implement 4 immersive UX improvements to transform the reading experience from "functional" to "immersive" by hiding UI chrome during reading. These improvements address the #1 gap identified in the MVP UX evaluation: making the app feel like a professional e-reader (Kindle, Apple Books, Kobo) rather than "a GUI with book content in it."

**Context**: Phase 1 (PR #54) implemented Editorial Elegance visual polish. Phase 2 focuses on immersion by auto-hiding UI chrome and improving interaction patterns.

---

## User Stories

### Primary User Story
As a reader, I want the e-reader interface to disappear when I'm focused on reading so that I can have an immersive, distraction-free reading experience like professional e-reader apps.

### Specific User Stories

1. **Auto-Hide Chrome**
   - As a reader, I want the navigation bar to fade away when I'm reading so that I have maximum screen space and minimal distraction.

2. **Clear State Controls**
   - As a reader, I want the mode toggle to look like a toggle switch (not a button) so that I immediately understand it's a state control and not an action button.

3. **Keyboard Shortcut Discovery**
   - As a user, I want to see all available keyboard shortcuts in one place so that I can discover and learn power-user features.

4. **Non-Intrusive Feedback**
   - As a reader, I want brief feedback when I change modes so that I know the action was successful, but without a disruptive modal dialog.

---

## Features

### Feature 1: Auto-Hide Navigation Bar

#### User Goal
As a reader, I want the navigation bar to fade away when I'm reading so that I have maximum screen space and minimal distraction.

#### User Flow

**Happy Path:**
1. User opens book → Navigation bar is **visible** (default state)
2. User starts reading (no mouse movement for 3 seconds) → Navigation bar **fades out** (500ms transition)
3. User moves mouse → Navigation bar **fades in** (250ms transition)
4. User hovers over navigation bar → Bar stays visible
5. User moves mouse away → 3-second timer restarts → Bar fades out again

**Alternative Paths:**
- **User uses keyboard shortcuts**: Navigation bar remains hidden (keyboard users don't need it visible)
- **User toggles mode with Ctrl+M**: Toast notification appears briefly, navigation bar stays hidden
- **User opens menu**: Navigation bar becomes visible and stays visible until menu closes

#### Interface Design

**Layout:**
- Navigation bar transitions from `opacity: 1.0` (visible) to `opacity: 0.0` (hidden)
- When hidden, navigation bar still occupies layout space (no layout shift)
- Smooth CSS-based opacity transition (no jarring appearance)

**Key Elements:**
- **Inactivity Timer**: QTimer that triggers after 3 seconds of no mouse movement
- **Mouse Tracking**: MainWindow tracks mouse movement events
- **Hover Protection**: Mouse enter/leave events on NavigationBar prevent hiding while hovering
- **Opacity Animation**: QPropertyAnimation for smooth fade in/out

**Information Hierarchy:**
1. **Content** (BookViewer) - Always 100% visible, never fades
2. **Navigation Bar** - Fades to transparent when inactive
3. **Status Bar** - Always visible (reading progress is important reference)
4. **Menu Bar** - Always visible (standard desktop convention)

#### Interaction Patterns

**Auto-hide behavior:**
- **Trigger**: 3 seconds of mouse inactivity (not moving, not hovering over nav bar)
- **Fade out**: 500ms smooth transition to `opacity: 0`
- **Reveal**: Any mouse movement → 250ms smooth transition to `opacity: 1`
- **Hover lock**: Hovering over nav bar pauses auto-hide timer indefinitely
- **Leave behavior**: Leaving nav bar restarts 3-second timer

**User control:**
- Keyboard shortcut to toggle auto-hide on/off: `Ctrl+Shift+H`
- Setting persists in QSettings
- Menu item: `View > Auto-Hide Navigation Bar` (checkbox)

#### States

**State 1: Visible (default)**
- `opacity: 1.0`
- Navigation bar fully interactive
- Timer inactive (mouse is moving or hovering)

**State 2: Fading Out**
- `opacity: 1.0 → 0.0` over 500ms
- Still interactive (clicking works)
- Triggered by 3-second inactivity timer

**State 3: Hidden**
- `opacity: 0.0`
- Still interactive (keyboard focus works, clicking works if you know where it is)
- Layout space still reserved (no content jump)

**State 4: Fading In**
- `opacity: 0.0 → 1.0` over 250ms
- Triggered by mouse movement
- Faster fade-in than fade-out (feels responsive)

#### Accessibility Considerations

- **Keyboard navigation**: Auto-hide does NOT affect keyboard shortcuts (all shortcuts work when hidden)
- **Focus visibility**: If user tabs to navigation bar while hidden, bar fades in automatically
- **Screen readers**: Navigation bar remains in accessibility tree even when hidden
- **User control**: Preference to disable auto-hide entirely
- **Mouse users**: Easy to reveal (just move mouse)

#### E-Reader Conventions

**Kindle:**
- Taps/clicks reveal full-screen menu overlay
- Auto-hides after inactivity
- All controls in overlay (progress, navigation, settings)

**Kobo:**
- Similar to Kindle: tap reveals overlay
- Auto-hides after 5 seconds
- Progress bar at bottom always visible

**Apple Books:**
- Click reveals navigation controls
- Auto-hides after 3 seconds
- Very minimal chrome during reading

**Recommendation**: Follow **Apple Books pattern** with continuous mouse movement detection (desktop-native behavior). Mobile patterns (tap to reveal) don't translate well to desktop where mouse is always "hovering."

#### Acceptance Criteria

- [ ] Navigation bar fades out after 3 seconds of mouse inactivity
- [ ] Navigation bar fades in on any mouse movement (250ms transition)
- [ ] Navigation bar stays visible while hovering over it
- [ ] 3-second timer restarts when mouse leaves navigation bar
- [ ] Keyboard shortcuts work regardless of navigation bar visibility
- [ ] Tabbing to navigation bar while hidden makes it fade in
- [ ] Menu item `View > Auto-Hide Navigation Bar` toggles feature on/off
- [ ] Keyboard shortcut `Ctrl+Shift+H` toggles feature on/off
- [ ] Setting persists in QSettings across sessions
- [ ] No layout shift when hiding/showing (occupies same space)
- [ ] Smooth 60fps animations (no jank)

---

### Feature 2: Visual Toggle Switch

#### User Goal
As a reader, I want the mode toggle to look like a toggle switch (not a button) so that I immediately understand it's a state control and not an action button.

#### Current State
- Mode toggle is a `QPushButton` with text "📜 Scroll Mode" or "📄 Page Mode"
- Looks identical to navigation buttons (Previous/Next)
- Button approach works but doesn't clearly communicate "state" vs "action"

#### Interface Design

**Layout:**
Replace button with custom toggle switch widget that shows:
- Left side: "Scroll" label
- Center: Toggle switch (slider)
- Right side: "Page" label

**Visual Design:**
```
┌─────────────────────────────┐
│  Scroll  ◯──○  Page         │  ← Scroll mode active
└─────────────────────────────┘

┌─────────────────────────────┐
│  Scroll  ○──◯  Page         │  ← Page mode active
└─────────────────────────────┘
```

**Key Elements:**
- **Track**: Background rail (pill-shaped, rounded)
- **Handle**: Circular thumb that slides left/right
- **Labels**: "Scroll" on left, "Page" on right
- **Active state**: Current mode's label highlighted with accent color
- **Hover state**: Handle scales slightly larger
- **Click target**: Entire widget is clickable, not just handle

**Information Hierarchy:**
1. **Current state** (highlighted label) - Most important
2. **Toggle handle** (visual indicator) - Secondary
3. **Alternative state** (dimmed label) - Tertiary

#### Interaction Patterns

**Toggle switch behavior:**
- **Click anywhere**: Toggles mode, handle slides with smooth animation
- **Keyboard (Space/Enter)**: Toggles mode when focused
- **Keyboard (Left/Right arrows)**: Also toggles mode (accessibility)
- **Animation**: 200ms ease-out handle slide
- **Tooltip**: "Toggle between scroll and page modes (Ctrl+M)"

**Visual feedback:**
- **Hover**: Handle grows 10%, track background brightens slightly
- **Active/Pressed**: Handle compresses slightly (tactile feel)
- **Focus**: Dashed outline around entire widget (keyboard accessibility)
- **Disabled**: Greyscale with 50% opacity (when no book loaded)

#### Implementation Notes

**PyQt6 Widgets Needed:**
- Custom `ToggleSwitchWidget(QWidget)` class
- Override `paintEvent()` to draw track, handle, and labels
- Override `mousePressEvent()` and `keyPressEvent()` for interaction
- Use `QPropertyAnimation` for smooth handle slide

**Complexity**: Medium (custom widget painting, but straightforward)

**Learning Value**:
- Custom widget creation from scratch
- QPainter for custom drawing
- QPropertyAnimation for smooth transitions
- Mouse and keyboard event handling

#### Acceptance Criteria

- [ ] Toggle switch widget replaces mode toggle button
- [ ] Switch shows "Scroll" on left, "Page" on right with slider in center
- [ ] Handle slides left (Scroll mode) or right (Page mode) with smooth animation
- [ ] Current mode's label is highlighted with accent color
- [ ] Click anywhere on widget toggles mode
- [ ] Space/Enter keys toggle mode when focused
- [ ] Left/Right arrow keys toggle mode when focused
- [ ] Hover state shows visual feedback (handle grows, track brightens)
- [ ] Focus state shows keyboard focus indicator (outline)
- [ ] Disabled state is greyscale when no book loaded
- [ ] Tooltip shows "Toggle between scroll and page modes (Ctrl+M)"
- [ ] Animation is smooth (200ms ease-out)

---

### Feature 3: Keyboard Shortcuts Help Dialog

#### User Goal
As a user, I want to see all available keyboard shortcuts in one place so that I can discover and learn power-user features.

#### User Flow

1. User opens menu: `Help > Keyboard Shortcuts` (or presses `Ctrl+?` or `F1`)
2. Modal dialog appears showing all shortcuts organized by category
3. User reviews shortcuts, optionally closes
4. Dialog closes, user returns to reading

#### Interface Design

**Layout:**
- Modal dialog (500x600px recommended size)
- Title: "Keyboard Shortcuts"
- Content: Table organized by category
- Footer: "Close" button

**Categories:**

1. **Navigation**
   - `Left/Right Arrow`: Navigate (scroll/page based on mode)
   - `Page Up/Down`: Full page navigation
   - `Home/End`: Jump to chapter beginning/end
   - `Ctrl+G`: Go to specific page

2. **Chapters**
   - `Ctrl+Left/Right`: Previous/Next chapter
   - `Ctrl+Home/End`: First/Last chapter

3. **View**
   - `Ctrl+M`: Toggle scroll/page mode
   - `Ctrl+Shift+H`: Toggle auto-hide navigation
   - `Ctrl+T`: Toggle theme (Light/Dark)

4. **File**
   - `Ctrl+O`: Open book
   - `Ctrl+Q`: Quit

5. **Help**
   - `F1` or `Ctrl+?`: Show keyboard shortcuts

**Information Hierarchy:**
1. **Category headings** - Bold, larger font, accent color
2. **Keyboard shortcuts** - Monospace font, styled as "keys" (rounded background)
3. **Action descriptions** - Regular text, secondary color

#### Accessibility Considerations

- **Keyboard navigation**: Tab to close button, Escape to dismiss
- **Screen reader**: Semantic structure with headings
- **Searchable**: Consider adding search box for power users (Phase 3)
- **Printable**: Copy-to-clipboard button (Phase 3)

#### Implementation Notes

**PyQt6 Widgets:**
- `QDialog` as container
- `QTableWidget` for shortcuts table (2 columns: shortcut, description)
- `QVBoxLayout` with category section headers
- `QPushButton` for Close button

**Complexity**: Low (simple dialog with static content)

**Learning Value**:
- Modal dialog creation
- QTableWidget usage
- User documentation patterns

#### Acceptance Criteria

- [ ] Menu item `Help > Keyboard Shortcuts` opens dialog
- [ ] `F1` keyboard shortcut opens dialog
- [ ] `Ctrl+?` keyboard shortcut opens dialog (if possible on platform)
- [ ] Dialog is modal (blocks interaction with main window)
- [ ] Dialog shows shortcuts organized by 5 categories
- [ ] Shortcuts are styled with monospace font
- [ ] Category headings are bold and use accent color
- [ ] Close button dismisses dialog
- [ ] Escape key dismisses dialog
- [ ] Dialog size is 500x600px (or appropriate for content)
- [ ] Dialog is centered on parent window

---

### Feature 4: Toast Notifications

#### User Goal
As a reader, I want brief feedback when I change modes so that I know the action was successful, but without a disruptive modal dialog.

#### User Flow

1. User toggles navigation mode (button click or `Ctrl+M`)
2. Toast appears in bottom-right corner: "📜 Switched to Scroll Mode" (or "📄 Switched to Page Mode")
3. Toast fades in (250ms), stays visible for 2 seconds, then fades out (500ms)
4. User continues reading without interruption

#### Interface Design

**Layout:**
- Small rounded rectangle (300x60px)
- Positioned in bottom-right corner (with 20px margin)
- Floats above content (z-index: 1000)
- Semi-transparent background (85% opacity)

**Visual Design:**
```
┌──────────────────────────────┐
│  📜 Switched to Scroll Mode  │
└──────────────────────────────┘
```

**Key Elements:**
- **Icon/Emoji**: Mode indicator (📜 for scroll, 📄 for page)
- **Message**: Short, clear text (< 30 characters)
- **Background**: Semi-transparent with theme-aware color
- **Shadow**: Subtle drop shadow for depth

**Animation:**
- **Fade in**: 250ms from `opacity: 0` to `opacity: 1`
- **Hold**: 2 seconds at full opacity
- **Fade out**: 500ms from `opacity: 1` to `opacity: 0`
- **Total duration**: 2.75 seconds

#### Interaction Patterns

**Toast behavior:**
- **Trigger**: Mode change event only (not for every action)
- **Non-blocking**: User can continue interacting with app
- **Auto-dismiss**: No close button needed (goes away automatically)
- **Queue**: If multiple toasts triggered, queue them (don't stack)
- **Non-intrusive**: Appears in corner, doesn't cover content

**When to show toasts:**
- ✅ Navigation mode change (Scroll ↔ Page)
- ❌ Chapter navigation (too frequent, would be annoying)
- ❌ Keyboard shortcuts (implied feedback from action)
- ❌ Theme change (immediate visual feedback already obvious)

#### Accessibility Considerations

- **Screen readers**: Announce toast message when it appears
- **Reduce motion**: Respect system preference (instant show/hide instead of fade)
- **High contrast**: Ensure toast background has sufficient contrast
- **Dismissible**: Allow clicking toast to dismiss early (optional)

#### Implementation Notes

**PyQt6 Widgets:**
- Custom `ToastWidget(QWidget)` class
- Positioned as child of MainWindow with absolute positioning
- Use `QPropertyAnimation` for fade in/out
- `QTimer` for auto-dismiss

**Complexity**: Low-Medium (custom widget with animations)

**Learning Value**:
- Non-modal feedback patterns
- Absolute positioning in Qt
- Animation sequencing (fade in → hold → fade out)
- User experience for transient notifications

#### Acceptance Criteria

- [ ] Toast appears in bottom-right corner when mode changes
- [ ] Toast shows emoji icon (📜 or 📄) and message text
- [ ] Toast fades in over 250ms
- [ ] Toast stays visible for 2 seconds at full opacity
- [ ] Toast fades out over 500ms
- [ ] Total duration is 2.75 seconds (fade in + hold + fade out)
- [ ] Multiple toasts queue (don't stack on top of each other)
- [ ] Toast doesn't block interaction with app
- [ ] Toast background is semi-transparent with theme-aware color
- [ ] Toast has subtle drop shadow
- [ ] Screen reader announces toast message
- [ ] Clicking toast dismisses it early (optional)

---

## Implementation Plan

### Recommended Order

1. **Keyboard Shortcuts Dialog** (Task 3) - Easiest, immediate value, no dependencies
2. **Toast Notifications** (Task 4) - Moderate complexity, useful for testing mode changes
3. **Visual Toggle Switch** (Task 2) - Custom widget, visually impressive
4. **Auto-Hide Navigation** (Task 1) - Most complex, ties everything together

**Rationale**: Start with quick wins (shortcuts dialog), build supporting infrastructure (toasts), add polish (toggle switch), then implement the most impactful feature (auto-hide).

### Dependencies Between Features

- **Toast notifications** should be implemented before **auto-hide** (toasts provide feedback when nav bar is hidden)
- **Toggle switch** can be developed independently
- **Keyboard shortcuts dialog** has no dependencies

### Estimated Effort

| Task | Complexity | Estimated Time |
|------|------------|----------------|
| Keyboard Shortcuts Dialog | Low | 2-3 hours |
| Toast Notifications | Low-Medium | 3-4 hours |
| Visual Toggle Switch | Medium | 4-5 hours |
| Auto-Hide Navigation | Medium | 5-6 hours |
| **Total** | | **14-18 hours** |

---

## Tasks

### Task 1: Keyboard Shortcuts Help Dialog

**Files to Create:**
- `src/ereader/views/shortcuts_dialog.py` - Dialog widget

**Files to Modify:**
- `src/ereader/views/main_window.py` - Add menu item and F1 shortcut

**Tests to Create:**
- `tests/test_views/test_shortcuts_dialog.py` - Dialog creation and content tests

**Implementation Steps:**
1. Create `ShortcutsDialog(QDialog)` class
2. Populate dialog with shortcuts table organized by category
3. Add Close button and Escape key handling
4. Add menu item `Help > Keyboard Shortcuts`
5. Add F1 keyboard shortcut to open dialog
6. Write unit tests for dialog creation and content

---

### Task 2: Toast Notifications

**Files to Create:**
- `src/ereader/views/toast_widget.py` - Toast notification widget

**Files to Modify:**
- `src/ereader/views/main_window.py` - Show toast on mode change
- `src/ereader/controllers/reader_controller.py` - Emit signal for mode change

**Tests to Create:**
- `tests/test_views/test_toast_widget.py` - Toast display and animation tests

**Implementation Steps:**
1. Create `ToastWidget(QWidget)` class with custom painting
2. Implement fade in/hold/fade out animation sequence
3. Add positioning logic (bottom-right corner with margin)
4. Add queue system for multiple toasts
5. Connect mode change signal to toast display
6. Add screen reader support (accessibility)
7. Write unit tests for toast lifecycle

---

### Task 3: Visual Toggle Switch

**Files to Create:**
- `src/ereader/views/toggle_switch.py` - Toggle switch widget

**Files to Modify:**
- `src/ereader/views/navigation_bar.py` - Replace button with toggle switch

**Tests to Create:**
- `tests/test_views/test_toggle_switch.py` - Toggle switch interaction tests

**Implementation Steps:**
1. Create `ToggleSwitchWidget(QWidget)` class
2. Implement custom `paintEvent()` for track, handle, and labels
3. Implement mouse interaction (`mousePressEvent`, `mouseReleaseEvent`)
4. Implement keyboard interaction (`keyPressEvent`)
5. Add hover and focus states
6. Add smooth animation for handle slide (QPropertyAnimation)
7. Replace mode toggle button in NavigationBar
8. Write unit tests for toggle interaction and states

---

### Task 4: Auto-Hide Navigation Bar

**Files to Modify:**
- `src/ereader/views/main_window.py` - Mouse tracking and timer logic
- `src/ereader/views/navigation_bar.py` - Hover detection
- `src/ereader/models/theme.py` - (no changes needed, uses opacity)

**Tests to Create:**
- `tests/test_views/test_main_window.py` - Auto-hide behavior tests (extend existing)

**Implementation Steps:**
1. Enable mouse tracking in MainWindow (`setMouseTracking(True)`)
2. Create QTimer for 3-second inactivity detection
3. Override `mouseMoveEvent()` to restart timer and show nav bar
4. Implement fade in/out animations (QPropertyAnimation on opacity)
5. Add hover detection in NavigationBar (pause timer on hover)
6. Add menu item `View > Auto-Hide Navigation Bar` (checkbox)
7. Add keyboard shortcut `Ctrl+Shift+H` to toggle feature
8. Persist setting in QSettings
9. Handle focus events (show nav bar when tabbing to it)
10. Write unit tests for auto-hide timer and mouse interaction

---

## Edge Cases

### Auto-Hide Navigation
- **Rapid mouse movement**: Timer restarts on every movement (expected)
- **Focus while hidden**: Nav bar fades in when focused via Tab key
- **Menu open**: Nav bar remains visible while menu is open
- **Disabled setting**: Nav bar always visible when auto-hide disabled
- **Keyboard-only users**: Nav bar hidden is fine (shortcuts still work)

### Visual Toggle Switch
- **Rapid toggling**: Animation completes even if toggled mid-animation
- **Theme change**: Switch colors update immediately
- **Disabled state**: Switch is greyscale when no book loaded
- **Very narrow window**: Labels may truncate gracefully

### Keyboard Shortcuts Dialog
- **Long shortcut list**: Dialog is scrollable if content exceeds height
- **Platform differences**: Some shortcuts may not work on all platforms (document this)
- **Multiple opens**: Only one dialog instance at a time

### Toast Notifications
- **Rapid mode changes**: Toasts queue, don't stack
- **Very long messages**: Text wraps or truncates to fit toast width
- **Theme change mid-toast**: Toast colors update immediately
- **Reduce motion**: Toast appears/disappears instantly without animation

---

## Out of Scope

This phase explicitly does NOT include:

- **Search box in shortcuts dialog** - Deferred to Phase 3
- **Print/copy shortcuts** - Deferred to Phase 3
- **Toast for all actions** - Only mode changes get toasts
- **Customizable auto-hide timing** - Fixed at 3 seconds for now
- **Animation preferences** - System reduce-motion respected, but no custom settings
- **Multiple toast positions** - Fixed at bottom-right

---

## Non-Functional Requirements

### Performance
- All animations run at 60fps (no dropped frames)
- Auto-hide timer has negligible performance impact
- Toast widget uses minimal memory (single instance, reused)
- Toggle switch painting is optimized (no unnecessary redraws)

### Accessibility
- All features work with keyboard only
- Screen readers announce important state changes
- Focus indicators visible for all interactive elements
- High contrast mode supported (system preference)
- Reduce motion preference respected

### Platform Compatibility
- **Primary target**: macOS (development environment)
- **Secondary**: Windows, Linux (best effort)
- **Known limitations**: Some shortcuts may not work on all platforms
- **Opacity animations**: May render slightly differently across platforms (acceptable)

---

## Success Criteria

Phase 2 is successful when:

### Functional Criteria
- [ ] All 4 features fully implemented and working
- [ ] All acceptance criteria met for each feature
- [ ] All unit tests pass (existing + new tests)
- [ ] Test coverage remains ≥80% (ideally ≥90%)
- [ ] All edge cases handled gracefully

### Quality Criteria
- [ ] Code follows CLAUDE.md standards (type hints, docstrings, logging)
- [ ] No ruff linting errors
- [ ] `/code-review` approval with no critical issues
- [ ] No performance regression (smooth scrolling, instant response)
- [ ] All animations are smooth (60fps)

### User Experience Criteria
- [ ] Reading experience feels immersive (navigation bar fades away)
- [ ] Mode toggle is immediately understandable (switch vs button)
- [ ] Keyboard shortcuts are discoverable (help dialog)
- [ ] Mode change feedback is helpful but not annoying (toast)
- [ ] UI feels like a professional e-reader (Kindle/Apple Books quality)

### Documentation Criteria
- [ ] All code changes have docstrings explaining purpose
- [ ] Architecture document created with technical details
- [ ] Implementation notes document any deviations from spec
- [ ] README or user documentation updated with new shortcuts

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Animations not smooth (jank) | Medium | High | Profile animations, use QPropertyAnimation, test on target hardware |
| Auto-hide timer fires at wrong times | Medium | Medium | Extensive testing, add logs, adjust timing based on feedback |
| Toggle switch looks unprofessional | Low | Medium | Reference professional designs, iterate on appearance |
| Toast notifications annoying | Low | High | Only show for mode changes, keep duration short (2.75s) |
| Keyboard shortcuts conflict with system | Low | Medium | Document platform differences, provide alternatives |
| Performance impact from mouse tracking | Very Low | Medium | Profile before/after, mouse tracking is low overhead |

---

## Future Enhancements (Phase 3+)

These improvements are explicitly deferred to future phases:

### Phase 3: Polish
- Search box in keyboard shortcuts dialog
- Print/copy shortcuts to clipboard
- Customizable auto-hide timing in preferences
- Toast notifications for other actions (chapter change, bookmark added)
- Loading indicators for book operations
- Animation preferences (beyond system reduce-motion)

### Phase 4: Advanced
- Customizable keyboard shortcuts
- Multiple toast positions (user preference)
- Gesture support (trackpad swipes for navigation)
- Full-screen mode (hide menu bar and status bar too)

---

## Definition of Done

A task is "done" when:
- [ ] Code is written following CLAUDE.md standards
- [ ] Type hints on all function signatures
- [ ] Docstrings on all public methods (Google style)
- [ ] Logging instead of print statements
- [ ] Unit tests written for logic and interactions
- [ ] Manual testing completed for visual/interaction features
- [ ] Tests pass (`/test` green)
- [ ] Coverage ≥80% maintained
- [ ] No linting errors (`ruff check` passes)
- [ ] Code committed with conventional commit message
- [ ] Edge cases documented in code comments

The entire feature is "done" when:
- [ ] All 4 tasks meet individual "done" criteria
- [ ] `/code-review` completed with no critical issues
- [ ] PR created with comprehensive description
- [ ] All CI checks pass (tests, coverage, linting)
- [ ] Manual QA completed (test all features, test interactions, test themes)
- [ ] Architecture document created with implementation notes
- [ ] User documentation updated (keyboard shortcuts, new features)

---

## References

- **UX Evaluation**: `docs/ux/mvp-ux-evaluation.md` - Identified Phase 2 improvements
- **Phase 1 Spec**: `docs/specs/phase1-ux-improvements.md` - Previous phase foundation
- **Phase 1 Review**: `docs/reviews/feature-phase1-ux-improvements.md` - Editorial Elegance implementation
- **Theme System**: `src/ereader/models/theme.py` - Current theme implementation
- **Navigation Bar**: `src/ereader/views/navigation_bar.py` - Current implementation
- **Main Window**: `src/ereader/views/main_window.py` - Window structure
- **Apple Books UX**: Reference for auto-hide behavior patterns
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/ - Accessibility guidelines

---

## Notes

### Why These 4 Improvements?

These were selected from the UX evaluation Phase 2 recommendations as **high-impact immersion features**:
- Auto-hide navigation is the #1 missing feature compared to Kindle/Apple Books
- Toggle switch improves clarity of state vs action controls
- Keyboard shortcuts dialog improves discoverability for power users
- Toast notifications provide feedback when nav bar is hidden

Together, these transform the reading experience from "always visible UI" to "content-first immersion."

### Learning Opportunities

This feature provides practice with:
- Qt animations (QPropertyAnimation, fade effects)
- Custom widget painting (QPainter)
- Mouse tracking and event handling
- Timer-based interactions (auto-hide)
- Modal dialogs
- Accessibility patterns (screen readers, keyboard navigation)
- Desktop UX conventions (toast notifications, toggle switches)

### Comparison to Professional E-Readers

After Phase 2, our e-reader will match or exceed:
- **Kindle**: ✅ Auto-hide UI (Kindle uses tap-to-reveal, we use mouse movement)
- **Apple Books**: ✅ 3-second auto-hide timer (same timing)
- **Kobo**: ✅ Minimal chrome during reading
- **All**: ✅ Keyboard shortcut discovery (many e-readers lack this!)

---

## Appendix: Design Mockups

### Auto-Hide Navigation Bar States

```
State 1: Visible (opacity: 1.0)
┌────────────────────────────────────────┐
│  File  View  Help                      │
├────────────────────────────────────────┤
│                                        │
│       [Book Content Area]              │
│                                        │
├────────────────────────────────────────┤
│  [Scroll/Page]  [← Prev]  [Next →]    │ ← Navigation bar visible
├────────────────────────────────────────┤
│  Chapter 1 | Page 5/20 | 25%           │
└────────────────────────────────────────┘

State 2: Hidden (opacity: 0.0)
┌────────────────────────────────────────┐
│  File  View  Help                      │
├────────────────────────────────────────┤
│                                        │
│       [Book Content Area]              │
│                                        │
│                                        │ ← Navigation bar hidden (space reserved)
├────────────────────────────────────────┤
│  Chapter 1 | Page 5/20 | 25%           │
└────────────────────────────────────────┘
```

### Toggle Switch States

```
Scroll Mode Active:
┌───────────────────────────────┐
│  Scroll  ◉────○  Page         │
│   (bold)            (normal)  │
└───────────────────────────────┘

Page Mode Active:
┌───────────────────────────────┐
│  Scroll  ○────◉  Page         │
│ (normal)           (bold)     │
└───────────────────────────────┘
```

### Toast Notification

```
┌────────────────────────────────────────┐
│                                        │
│       [Book Content Area]              │
│                                        │
│                   ┌──────────────────┐ │
│                   │ 📜 Scroll Mode   │ │ ← Toast in corner
│                   └──────────────────┘ │
├────────────────────────────────────────┤
│  Chapter 1 | Page 5/20 | 25%           │
└────────────────────────────────────────┘
```
