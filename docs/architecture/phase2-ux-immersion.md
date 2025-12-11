# Phase 2 UX Immersion Architecture

## Date
2025-12-11

## Context

Following Phase 1 visual polish (PR #54), Phase 2 focuses on creating an immersive reading experience by implementing auto-hiding UI chrome and improved interaction patterns. This addresses the #1 gap identified in UX evaluation: transforming the app from "GUI with book content" to "professional e-reader experience."

**UX Design:** See `docs/specs/phase2-ux-immersion.md`
**Phase 1 Foundation:** See `docs/architecture/phase1-ux-improvements.md`

**Phase 2 Goals:**
- Auto-hide navigation bar after inactivity (Apple Books pattern)
- Replace mode toggle button with visual toggle switch
- Add keyboard shortcuts help dialog for discoverability
- Implement toast notifications for mode changes

**Constraints:**
- Maintain existing MVC architecture
- Use existing signal/slot infrastructure where possible
- Keep view components stateless (state in controller)
- Smooth 60fps animations (QPropertyAnimation)
- Maintain 80%+ test coverage

---

## Architecture Overview

### Component Hierarchy

```
MainWindow (orchestrates all Phase 2 features)
├── Auto-Hide Manager (mouse tracking, timer, animations)
├── NavigationBar
│   └── ToggleSwitchWidget (replaces mode button)
├── BookViewer (unchanged)
├── ShortcutsDialog (modal, on-demand)
└── ToastWidget (floating, animated)
```

### New Components

| Component | Type | Responsibility | Parent |
|-----------|------|----------------|--------|
| `ToggleSwitchWidget` | Custom widget | Visual toggle switch for mode | NavigationBar |
| `ShortcutsDialog` | QDialog | Display keyboard shortcuts | MainWindow |
| `ToastWidget` | Custom widget | Transient notifications | MainWindow |
| Auto-hide logic | MainWindow methods | Mouse tracking & nav bar hiding | MainWindow |

---

## Feature 1: Auto-Hide Navigation Bar

### Problem Statement

Professional e-readers (Kindle, Apple Books, Kobo) hide UI chrome during reading to maximize content focus. Our navigation bar is always visible, creating visual distraction.

### Architecture Decision

**Auto-hide logic lives in MainWindow** because:
- MainWindow owns the NavigationBar widget
- MainWindow handles top-level mouse events
- MainWindow already manages keyboard shortcuts
- Keeps NavigationBar stateless (no timer logic in view)

### Component Responsibilities

**MainWindow (orchestrator):**
- Track mouse movement events (enable mouse tracking)
- Manage 3-second inactivity timer (QTimer)
- Trigger fade in/out animations on NavigationBar
- Handle menu item "View > Auto-Hide Navigation Bar" (toggle on/off)
- Persist auto-hide preference in QSettings
- Show nav bar when menu bar is activated

**NavigationBar (view):**
- Emit hover events (enterEvent/leaveEvent)
- Accept opacity changes from MainWindow
- Remain functional even when opacity=0 (keyboard shortcuts work)
- No auto-hide logic (stateless view)

**Controller (no changes):**
- Controller remains unaware of auto-hide feature
- No new signals or state needed

### State Management

```python
# In MainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        # Auto-hide state
        self._auto_hide_enabled: bool = True  # Default on
        self._nav_bar_hover: bool = False  # Track hover state

        # Timer for inactivity detection
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(3000)  # 3 seconds
        self._hide_timer.timeout.connect(self._fade_out_nav_bar)

        # Animation for fade effects
        self._nav_bar_animation: QPropertyAnimation | None = None
```

### Signal Flow

```
User moves mouse
  → MainWindow.mouseMoveEvent()
  → Restart hide timer
  → Show nav bar (if hidden)

Timer expires (3 seconds)
  → MainWindow._hide_timer.timeout
  → MainWindow._fade_out_nav_bar()
  → QPropertyAnimation(opacity: 1.0 → 0.0, 500ms)

User hovers over nav bar
  → NavigationBar.enterEvent()
  → MainWindow._on_nav_bar_enter()
  → Stop hide timer

User leaves nav bar
  → NavigationBar.leaveEvent()
  → MainWindow._on_nav_bar_leave()
  → Restart hide timer
```

### Implementation Details

#### Mouse Tracking Setup

```python
def __init__(self):
    # Enable mouse tracking for the entire window
    self.setMouseTracking(True)

    # Also enable for central widget to catch all events
    central_widget = self.centralWidget()
    if central_widget:
        central_widget.setMouseTracking(True)

    # Connect NavigationBar hover events
    self._navigation_bar.installEventFilter(self)
```

#### Event Filter for Hover Detection

```python
def eventFilter(self, obj: QObject, event: QEvent) -> bool:
    """Handle hover events for NavigationBar."""
    if obj == self._navigation_bar:
        if event.type() == QEvent.Type.Enter:
            self._on_nav_bar_enter()
        elif event.type() == QEvent.Type.Leave:
            self._on_nav_bar_leave()
    return super().eventFilter(obj, event)
```

#### Animation Strategy

Use `QPropertyAnimation` on `QGraphicsOpacityEffect` for smooth fading:

```python
def _setup_nav_bar_opacity_effect(self) -> None:
    """Setup opacity effect for nav bar animations."""
    self._nav_bar_opacity_effect = QGraphicsOpacityEffect(self._navigation_bar)
    self._nav_bar_opacity_effect.setOpacity(1.0)  # Start visible
    self._navigation_bar.setGraphicsEffect(self._nav_bar_opacity_effect)

def _fade_out_nav_bar(self) -> None:
    """Fade out navigation bar over 500ms."""
    if not self._auto_hide_enabled:
        return

    self._nav_bar_animation = QPropertyAnimation(
        self._nav_bar_opacity_effect, b"opacity"
    )
    self._nav_bar_animation.setDuration(500)  # 500ms
    self._nav_bar_animation.setStartValue(1.0)
    self._nav_bar_animation.setEndValue(0.0)
    self._nav_bar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    self._nav_bar_animation.start()

def _fade_in_nav_bar(self) -> None:
    """Fade in navigation bar over 250ms."""
    self._nav_bar_animation = QPropertyAnimation(
        self._nav_bar_opacity_effect, b"opacity"
    )
    self._nav_bar_animation.setDuration(250)  # 250ms (faster reveal)
    self._nav_bar_animation.setStartValue(
        self._nav_bar_opacity_effect.opacity()
    )
    self._nav_bar_animation.setEndValue(1.0)
    self._nav_bar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    self._nav_bar_animation.start()
```

#### Settings Persistence

```python
# Use existing QSettings pattern from theme management
def _save_auto_hide_preference(self) -> None:
    """Save auto-hide preference to settings."""
    settings = QSettings("EReader", "EReader")
    settings.setValue("ui/auto_hide_navigation", self._auto_hide_enabled)

def _load_auto_hide_preference(self) -> None:
    """Load auto-hide preference from settings."""
    settings = QSettings("EReader", "EReader")
    self._auto_hide_enabled = settings.value(
        "ui/auto_hide_navigation", True, type=bool
    )
```

### Edge Cases

1. **Menu bar activation**: Stop timer and show nav bar when menu is clicked
2. **Keyboard focus**: Show nav bar when user tabs to navigation buttons
3. **Rapid mouse movement**: Restart timer on every movement (debouncing handled by timer)
4. **Animation interruption**: Stop current animation before starting new one
5. **Disabled state**: When auto-hide is off, nav bar always visible (opacity=1.0)

### Files to Modify/Create

- **Modify:** `src/ereader/views/main_window.py` - Add auto-hide logic, mouse tracking, animations
- **Modify:** `src/ereader/views/navigation_bar.py` - No changes needed (hover events handled via event filter)
- **Test:** `tests/test_views/test_main_window.py` - Add auto-hide behavior tests

---

## Feature 2: Visual Toggle Switch Widget

### Problem Statement

Mode toggle button looks identical to navigation buttons, making it unclear that it's a state control vs an action button. Users want immediate visual indication of current mode.

### Architecture Decision

**Create custom ToggleSwitchWidget** because:
- QPushButton doesn't convey "toggle" affordance
- Custom painting allows precise control over appearance
- Reusable component for future toggle needs
- Clean separation of concerns (standalone widget)

### Component Design

```python
class ToggleSwitchWidget(QWidget):
    """Custom toggle switch widget for mode selection.

    Visual design:
        [ Scroll  ◯──○  Page ]  ← Scroll mode active
        [ Scroll  ○──◯  Page ]  ← Page mode active

    Signals:
        toggled: Emitted when switch is clicked (bool: True=Page, False=Scroll)
    """

    toggled = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None):
        self._is_page_mode: bool = False  # Current state
        self._handle_x: float = 0.0  # For animation
        self._theme: Theme = DEFAULT_THEME

        # Animation for handle slide
        self._handle_animation: QPropertyAnimation | None = None

    # Public interface
    def set_mode(self, is_page_mode: bool) -> None:
        """Set current mode (triggers animation)."""

    def apply_theme(self, theme: Theme) -> None:
        """Apply theme colors."""

    # Painting and interaction
    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom painting of track, handle, and labels."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle clicks anywhere on widget."""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle Space/Enter and Left/Right arrow keys."""
```

### Visual Specifications

```
Widget dimensions: 180px wide × 36px tall

Track:
  - Pill shape (18px border radius)
  - Width: 60px, Height: 24px
  - Background: theme.bg_secondary (off state)
  - Background: theme.accent (active side)

Handle:
  - Circle: 20px diameter
  - Color: theme.bg (white/cream)
  - Shadow: 2px blur, 1px offset
  - Position: Slides 30px left/right

Labels:
  - "Scroll" on left (30px from left edge)
  - "Page" on right (30px from right edge)
  - Font: 12px, theme.text
  - Active label: bold, theme.accent color
  - Inactive label: regular, theme.text_secondary
```

### Painting Strategy

```python
def paintEvent(self, event: QPaintEvent) -> None:
    """Paint the toggle switch."""
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Calculate positions
    rect = self.rect()
    center_x = rect.width() // 2
    center_y = rect.height() // 2

    # Draw labels
    self._draw_label(painter, "Scroll", left_side=True)
    self._draw_label(painter, "Page", left_side=False)

    # Draw track (pill shape)
    track_rect = QRect(
        center_x - 30, center_y - 12,
        60, 24
    )
    self._draw_track(painter, track_rect)

    # Draw handle (circle at animated position)
    handle_center_x = center_x + self._handle_x
    self._draw_handle(painter, handle_center_x, center_y)
```

### Animation Strategy

```python
def _animate_handle(self, target_x: float) -> None:
    """Animate handle to target position."""
    self._handle_animation = QPropertyAnimation(self, b"handle_x")
    self._handle_animation.setDuration(200)  # 200ms
    self._handle_animation.setStartValue(self._handle_x)
    self._handle_animation.setEndValue(target_x)
    self._handle_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    self._handle_animation.start()

# Property for animation target
@pyqtProperty(float)
def handle_x(self) -> float:
    return self._handle_x

@handle_x.setter
def handle_x(self, value: float) -> None:
    self._handle_x = value
    self.update()  # Trigger repaint
```

### Integration with NavigationBar

Replace existing `QPushButton` with `ToggleSwitchWidget`:

```python
# In NavigationBar.__init__()
# OLD: self._mode_toggle_button = QPushButton("Page Mode", self)
# NEW:
self._mode_toggle = ToggleSwitchWidget(self)
self._mode_toggle.toggled.connect(self._on_mode_toggle_clicked)
self._mode_toggle.setToolTip("Toggle between scroll and page modes (Ctrl+M)")

# In layout:
layout.addWidget(self._mode_toggle)
```

### Files to Create/Modify

- **Create:** `src/ereader/views/toggle_switch.py` - New ToggleSwitchWidget class
- **Modify:** `src/ereader/views/navigation_bar.py` - Replace button with switch
- **Test:** `tests/test_views/test_toggle_switch.py` - Widget painting and interaction tests

---

## Feature 3: Keyboard Shortcuts Help Dialog

### Problem Statement

Keyboard shortcuts are powerful but hidden. Users need a discoverable way to learn all available shortcuts without reading documentation.

### Architecture Decision

**Simple QDialog with static content** because:
- No complex state or logic needed
- Standard Qt modal dialog pattern
- One-time creation, reused on subsequent opens
- Minimal architectural impact

### Component Design

```python
class ShortcutsDialog(QDialog):
    """Modal dialog displaying keyboard shortcuts organized by category.

    Categories:
    - Navigation (arrow keys, page up/down)
    - Chapters (ctrl+arrow, ctrl+home/end)
    - View (themes, modes, auto-hide)
    - File (open, quit)
    - Help (this dialog)
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.resize(500, 600)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create dialog layout with shortcuts table."""
        layout = QVBoxLayout(self)

        # Category sections
        layout.addWidget(self._create_category_section("Navigation"))
        layout.addWidget(self._create_category_section("Chapters"))
        layout.addWidget(self._create_category_section("View"))
        layout.addWidget(self._create_category_section("File"))
        layout.addWidget(self._create_category_section("Help"))

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def _create_category_section(self, category: str) -> QWidget:
        """Create a section with category heading and shortcuts table."""
        # Returns QGroupBox with QTableWidget inside
```

### Data Structure for Shortcuts

```python
SHORTCUTS_DATA = {
    "Navigation": [
        ("Left/Right Arrow", "Navigate (scroll/page based on mode)"),
        ("Page Up/Down", "Full page navigation"),
        ("Home/End", "Jump to chapter beginning/end"),
        ("Ctrl+G", "Go to specific page"),
    ],
    "Chapters": [
        ("Ctrl+Left/Right", "Previous/Next chapter"),
        ("Ctrl+Home/End", "First/Last chapter"),
    ],
    "View": [
        ("Ctrl+M", "Toggle scroll/page mode"),
        ("Ctrl+Shift+H", "Toggle auto-hide navigation"),
        ("Ctrl+T", "Toggle theme (Light/Dark)"),
    ],
    "File": [
        ("Ctrl+O", "Open book"),
        ("Ctrl+Q", "Quit"),
    ],
    "Help": [
        ("F1 or Ctrl+?", "Show keyboard shortcuts"),
    ],
}
```

### Integration with MainWindow

```python
# In MainWindow.__init__()
self._shortcuts_dialog: ShortcutsDialog | None = None

# In _setup_menu_bar()
help_menu = menu_bar.addMenu("&Help")
shortcuts_action = QAction("&Keyboard Shortcuts", self)
shortcuts_action.setShortcut("F1")
shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
help_menu.addAction(shortcuts_action)

# Handler
def _show_shortcuts_dialog(self) -> None:
    """Show keyboard shortcuts help dialog."""
    if self._shortcuts_dialog is None:
        self._shortcuts_dialog = ShortcutsDialog(self)
    self._shortcuts_dialog.exec()
```

### Files to Create/Modify

- **Create:** `src/ereader/views/shortcuts_dialog.py` - New ShortcutsDialog class
- **Modify:** `src/ereader/views/main_window.py` - Add menu item and F1 shortcut
- **Test:** `tests/test_views/test_shortcuts_dialog.py` - Dialog creation and content tests

---

## Feature 4: Toast Notifications

### Problem Statement

When navigation bar auto-hides, users need non-intrusive feedback for mode changes. Modal dialogs are too disruptive, status bar messages are easy to miss.

### Architecture Decision

**Custom ToastWidget as floating overlay** because:
- Non-modal, non-blocking feedback
- Positioned absolutely (bottom-right corner)
- Self-animating and self-dismissing
- Reusable for future notifications

### Component Design

```python
class ToastWidget(QWidget):
    """Transient notification widget that fades in, holds, and fades out.

    Visual design:
        ┌────────────────────────┐
        │  📜 Switched to Scroll │
        └────────────────────────┘

    Animation sequence:
    1. Fade in: 250ms (0 → 1.0 opacity)
    2. Hold: 2000ms at full opacity
    3. Fade out: 500ms (1.0 → 0 opacity)
    4. Auto-hide when complete
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        # Widget setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 60)

        # Message state
        self._message: str = ""
        self._icon: str = ""

        # Animation state
        self._opacity: float = 0.0
        self._animation_sequence: list[QPropertyAnimation] = []

    def show_message(self, message: str, icon: str = "") -> None:
        """Show toast with message and optional icon."""
        self._message = message
        self._icon = icon

        # Position in bottom-right corner
        self._position_toast()

        # Start animation sequence
        self._start_animation_sequence()

    def _start_animation_sequence(self) -> None:
        """Run fade-in → hold → fade-out → hide sequence."""
        # Fade in (250ms)
        fade_in = QPropertyAnimation(self, b"opacity")
        fade_in.setDuration(250)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)

        # Hold (2000ms) - use QTimer
        # Fade out (500ms)
        # Hide widget when done
```

### Toast Queue System

For handling multiple rapid toasts:

```python
# In MainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        self._toast_widget = ToastWidget(self)
        self._toast_queue: list[tuple[str, str]] = []  # (message, icon)
        self._toast_active: bool = False

    def _show_toast(self, message: str, icon: str = "") -> None:
        """Show toast or queue if one is already showing."""
        if self._toast_active:
            self._toast_queue.append((message, icon))
        else:
            self._toast_active = True
            self._toast_widget.show_message(message, icon)
            # When toast completes, check queue

    def _on_toast_complete(self) -> None:
        """Handle toast animation completion."""
        self._toast_active = False
        if self._toast_queue:
            message, icon = self._toast_queue.pop(0)
            self._show_toast(message, icon)
```

### Integration with Mode Changes

```python
# In MainWindow._on_mode_changed()
def _on_mode_changed(self, mode: NavigationMode) -> None:
    """Handle mode change signal from controller."""
    # Update navigation bar
    self._navigation_bar.update_mode_button(mode)

    # Show toast notification
    if mode == NavigationMode.PAGE:
        self._show_toast("Switched to Page Mode", "📄")
    else:
        self._show_toast("Switched to Scroll Mode", "📜")
```

### Visual Styling

```python
def paintEvent(self, event: QPaintEvent) -> None:
    """Paint toast background, icon, and message."""
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw semi-transparent rounded background
    painter.setOpacity(self._opacity * 0.9)  # 90% max opacity
    bg_color = QColor(self._theme.bg)
    painter.setBrush(bg_color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(self.rect(), 8, 8)

    # Draw icon and text
    painter.setOpacity(self._opacity)
    # ... text drawing logic
```

### Files to Create/Modify

- **Create:** `src/ereader/views/toast_widget.py` - New ToastWidget class
- **Modify:** `src/ereader/views/main_window.py` - Create toast widget, show on mode changes
- **Test:** `tests/test_views/test_toast_widget.py` - Toast animation and queue tests

---

## Animation Strategy Summary

### Performance Requirements

All animations must run at 60fps (16.7ms per frame) for smooth experience.

### Animation Patterns

| Feature | Animation Type | Duration | Easing Curve |
|---------|---------------|----------|--------------|
| Auto-hide fade out | Opacity | 500ms | InOutQuad |
| Auto-hide fade in | Opacity | 250ms | InOutQuad |
| Toggle switch slide | Position | 200ms | InOutQuad |
| Toast fade in | Opacity | 250ms | InOutQuad |
| Toast fade out | Opacity | 500ms | InOutQuad |

### Animation Implementation

All animations use `QPropertyAnimation` for hardware-accelerated smooth transitions:

```python
# Standard pattern
animation = QPropertyAnimation(target, b"propertyName")
animation.setDuration(duration_ms)
animation.setStartValue(start)
animation.setEndValue(end)
animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
animation.start()
```

### Animation Cancellation

Handle animation interruption gracefully:

```python
def _stop_animation_if_running(self) -> None:
    """Stop current animation before starting new one."""
    if self._animation and self._animation.state() == QAbstractAnimation.State.Running:
        self._animation.stop()
```

---

## Signal Flow Summary

### Existing Signals (No Changes)

```
Controller signals (all existing, unchanged):
- book_loaded(str, str)
- chapter_changed(int, int)
- navigation_state_changed(bool, bool)
- content_ready(str)
- reading_progress_changed(str)
- pagination_changed(int, int)
- mode_changed(NavigationMode)
- error_occurred(str, str)
```

### New Component Signals

```
ToggleSwitchWidget (replaces QPushButton):
- toggled(bool)  [equivalent to clicked signal]

No new controller signals needed!
```

### Signal Flow for Phase 2 Features

**Auto-Hide:**
```
Mouse movement
  → MainWindow.mouseMoveEvent() [no signal]
  → Internal timer and animation logic
```

**Toggle Switch:**
```
User clicks switch
  → ToggleSwitchWidget.toggled(bool)
  → NavigationBar._on_mode_toggle_clicked()
  → NavigationBar.mode_toggle_requested  [existing signal]
  → Controller.toggle_navigation_mode()
  → Controller.mode_changed(NavigationMode)  [existing signal]
  → MainWindow._on_mode_changed()
  → Show toast + update nav bar
```

**Keyboard Shortcuts Dialog:**
```
User presses F1
  → MainWindow keyboard shortcut [no signal]
  → MainWindow._show_shortcuts_dialog()
```

**Toast Notifications:**
```
Mode changes
  → Controller.mode_changed(NavigationMode)  [existing signal]
  → MainWindow._on_mode_changed()
  → MainWindow._show_toast(message, icon)
  → ToastWidget.show_message() [no signal]
```

---

## State Management

### Where State Lives

Following MVC architecture, state placement:

| State | Location | Rationale |
|-------|----------|-----------|
| Auto-hide enabled | MainWindow | UI preference, persisted in QSettings |
| Nav bar hover state | MainWindow | Tracked for timer control |
| Toggle switch mode | ToggleSwitchWidget | Visual state only, reflects controller state |
| Current navigation mode | Controller (existing) | Business logic state |
| Toast queue | MainWindow | UI orchestration state |
| Shortcuts dialog instance | MainWindow | UI component lifecycle |

### Settings Persistence

Using existing QSettings pattern:

```python
# Auto-hide preference
settings.setValue("ui/auto_hide_navigation", bool)

# No other Phase 2 settings need persistence
# (mode is already persisted per-book, theme already persisted)
```

---

## Testing Strategy

### Unit Tests

**ToggleSwitchWidget:**
- `test_initial_state()` - Starts in scroll mode
- `test_click_toggles_state()` - Click changes state
- `test_keyboard_toggle()` - Space/Enter toggle state
- `test_arrow_keys_toggle()` - Left/Right arrows work
- `test_theme_application()` - Colors update with theme
- `test_animation_completes()` - Handle slides smoothly

**ShortcutsDialog:**
- `test_dialog_creation()` - Dialog initializes correctly
- `test_all_shortcuts_displayed()` - All categories present
- `test_close_button()` - Close button dismisses dialog
- `test_escape_key()` - Escape dismisses dialog

**ToastWidget:**
- `test_show_message()` - Toast appears with message
- `test_animation_sequence()` - Fade in → hold → fade out
- `test_queue_multiple_toasts()` - Second toast waits for first
- `test_positioning()` - Toast in bottom-right corner

**MainWindow (auto-hide):**
- `test_mouse_movement_shows_navbar()` - Movement reveals nav bar
- `test_inactivity_hides_navbar()` - 3 seconds hides nav bar
- `test_hover_prevents_hiding()` - Hovering over nav bar pauses timer
- `test_auto_hide_toggle()` - Menu item toggles feature on/off
- `test_focus_shows_navbar()` - Tabbing to nav bar reveals it

### Manual Testing

**Visual Verification:**
- [ ] Nav bar fades smoothly (no jank)
- [ ] Toggle switch handle slides smoothly
- [ ] Toast appears/disappears smoothly
- [ ] All animations run at 60fps
- [ ] Toggle switch looks professional (good alignment, colors)
- [ ] Toast is readable on both themes

**Interaction Testing:**
- [ ] Auto-hide works with mouse movement
- [ ] Auto-hide respects hover state
- [ ] Toggle switch works with mouse and keyboard
- [ ] Shortcuts dialog shows all shortcuts
- [ ] Toast queues multiple notifications correctly
- [ ] Auto-hide can be disabled via menu

**Edge Cases:**
- [ ] Rapid mode changes queue toasts correctly
- [ ] Animation interruption handled gracefully
- [ ] Focus navigation works with hidden nav bar
- [ ] Menu activation shows nav bar
- [ ] Theme switching updates all components

---

## Implementation Order

### Phase 2A: Keyboard Shortcuts Dialog (2-3 hours)
**Rationale:** Simplest feature, no dependencies, immediate value

1. Create `ShortcutsDialog` class with static content
2. Add menu item and F1 shortcut to MainWindow
3. Write dialog tests
4. Manual verification

### Phase 2B: Toast Notifications (3-4 hours)
**Rationale:** Needed before auto-hide for feedback

1. Create `ToastWidget` with painting and animations
2. Add toast queue system to MainWindow
3. Connect to mode_changed signal
4. Write toast tests
5. Manual verification (animation smoothness)

### Phase 2C: Visual Toggle Switch (4-5 hours)
**Rationale:** Standalone component, visual polish

1. Create `ToggleSwitchWidget` with custom painting
2. Implement handle animation
3. Add mouse and keyboard interaction
4. Replace button in NavigationBar
5. Write toggle switch tests
6. Manual verification (appearance and interaction)

### Phase 2D: Auto-Hide Navigation (5-6 hours)
**Rationale:** Most complex, ties everything together

1. Add mouse tracking to MainWindow
2. Create inactivity timer
3. Add opacity effect and animations
4. Implement hover detection
5. Add menu item and keyboard shortcut
6. Add settings persistence
7. Write auto-hide tests
8. Manual verification (all edge cases)

**Total Estimate:** 14-18 hours

---

## File Change Summary

### New Files

| File | LOC | Purpose |
|------|-----|---------|
| `src/ereader/views/toggle_switch.py` | ~200 | Custom toggle switch widget |
| `src/ereader/views/shortcuts_dialog.py` | ~150 | Keyboard shortcuts help dialog |
| `src/ereader/views/toast_widget.py` | ~150 | Toast notification widget |
| `tests/test_views/test_toggle_switch.py` | ~100 | Toggle switch tests |
| `tests/test_views/test_shortcuts_dialog.py` | ~60 | Shortcuts dialog tests |
| `tests/test_views/test_toast_widget.py` | ~80 | Toast widget tests |

### Modified Files

| File | Changes | LOC Impact |
|------|---------|------------|
| `src/ereader/views/main_window.py` | Auto-hide logic, toast, shortcuts, menu | +150 |
| `src/ereader/views/navigation_bar.py` | Replace button with toggle switch | +10 |
| `tests/test_views/test_main_window.py` | Auto-hide behavior tests | +80 |
| `tests/test_views/test_navigation_bar.py` | Update for toggle switch | +20 |

**Total Impact:** ~1000 LOC added

---

## Performance Considerations

### Auto-Hide Mouse Tracking

- Mouse events are lightweight (< 1ms processing)
- Timer only active when mouse is idle (no continuous polling)
- Animation uses hardware-accelerated opacity (GPU)
- **Expected impact:** Negligible (< 1% CPU during animation)

### Toggle Switch Painting

- Custom painting triggers on state change only (rare)
- QPainter with anti-aliasing is optimized by Qt
- Widget size is small (180×36px)
- **Expected impact:** < 2ms per paint event

### Toast Animations

- Opacity animation is hardware-accelerated
- Single widget reused (no allocation overhead)
- Short animation duration (2.75s total)
- **Expected impact:** < 1% CPU during toast display

### Memory

- `ToggleSwitchWidget`: ~1KB
- `ShortcutsDialog`: ~5KB (created once, reused)
- `ToastWidget`: ~1KB
- Auto-hide timer and animation: ~1KB
- **Total memory impact:** < 10KB

**Overall:** All performance targets met (<100ms interactions, smooth 60fps animations).

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Animations not smooth (jank) | Medium | High | Profile animations, use hardware acceleration, test on target hardware |
| Toggle switch looks unprofessional | Low | Medium | Reference professional designs (iOS, Material Design), iterate based on feedback |
| Auto-hide timer fires at wrong times | Medium | Medium | Extensive testing, add logging, adjust timing based on user feedback |
| Toast notifications annoying | Low | High | Only show for mode changes, keep duration short (2.75s), easy to dismiss |
| Mouse tracking performance impact | Very Low | Medium | Mouse events are native Qt, well-optimized. Profile if concerned |
| Platform differences (animations) | Low | Low | Test on macOS primarily, document known limitations |

---

## Future Enhancements (Phase 3+)

These improvements are explicitly deferred:

### Phase 3: Polish
- Search box in keyboard shortcuts dialog
- Print/copy shortcuts functionality
- Customizable auto-hide timing (preferences dialog)
- Toast notifications for other actions
- Loading indicators for book operations
- Full-screen mode (hide menu and status bar)

### Phase 4: Advanced
- Customizable keyboard shortcuts (rebinding)
- Multiple toast positions (user preference)
- Gesture support (trackpad swipes)
- Advanced animation preferences
- Toast notification history

---

## Success Criteria

Phase 2 is successful when:

### Functional Criteria
- [ ] Auto-hide works smoothly with configurable on/off
- [ ] Toggle switch clearly shows current mode
- [ ] Keyboard shortcuts dialog shows all shortcuts
- [ ] Toast notifications appear for mode changes
- [ ] All animations run at 60fps
- [ ] All tests pass with 80%+ coverage

### Quality Criteria
- [ ] Code follows CLAUDE.md standards
- [ ] No ruff linting errors
- [ ] `/code-review` passes with no critical issues
- [ ] No performance regression
- [ ] Animations are smooth on target hardware

### User Experience Criteria
- [ ] Reading experience feels immersive (nav bar fades away)
- [ ] Mode toggle is immediately understandable
- [ ] Keyboard shortcuts are discoverable
- [ ] Toast feedback is helpful, not annoying
- [ ] UI feels like professional e-reader (Kindle/Apple Books quality)

---

## References

- **UX Spec:** `docs/specs/phase2-ux-immersion.md` - Feature requirements and user stories
- **Phase 1 Architecture:** `docs/architecture/phase1-ux-improvements.md` - Foundation for Phase 2
- **Existing MVC:** `src/ereader/controllers/reader_controller.py` - Current controller signals
- **Qt Animation:** https://doc.qt.io/qt-6/qpropertyanimation.html
- **Qt Custom Widgets:** https://doc.qt.io/qt-6/custom-widgets.html
- **Apple Books UX:** Reference for auto-hide behavior patterns

---

## Decision

**Approved Architecture:**

1. **Auto-hide:** Logic in MainWindow, using QTimer and QPropertyAnimation on opacity
2. **Toggle Switch:** Custom widget with QPainter, replacing QPushButton
3. **Shortcuts Dialog:** Simple QDialog with static content table
4. **Toast:** Custom floating widget with animation sequence and queue system

This approach:
- ✅ Maintains existing MVC architecture (views stateless, controller owns business logic)
- ✅ Uses existing signal infrastructure (no new controller signals)
- ✅ Leverages Qt animation framework (smooth 60fps)
- ✅ Keeps components decoupled and testable
- ✅ Follows existing patterns (QSettings, Theme application)
- ✅ Minimal architectural complexity (straightforward implementations)

**Implementation can proceed.**

---

## Next Steps

1. Create GitHub issue for Phase 2 implementation (use `/issues`)
2. Create feature branch `feature/phase2-ux-immersion`
3. Implement in order: Shortcuts Dialog → Toast → Toggle Switch → Auto-Hide
4. Run `/test` after each component
5. Manual verification of animations and interactions
6. Run `/code-review` before PR
7. Create PR when all 4 features complete

Let's build an immersive reading experience! 📖✨
