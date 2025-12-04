# Reading Themes Architecture

## Date
2025-12-04

## Context

We need to implement a reading themes system (light/dark mode) to support comfortable reading in different lighting conditions. This is the final MVP feature.

### UX Requirements
- Two themes for MVP: Light (default), Dark
- Menu-based selection: View → Theme
- Immediate application (no "Apply" button)
- Persistence across sessions
- Radio button indicators showing current theme
- All UI components styled consistently

### Constraints
- Keep it simple (MVP feature)
- Follow existing MVC pattern
- Maintain testability
- Support future expansion (Sepia, auto-detection)

## Options Considered

### Option 1: Signal-Based Theme Broadcasting
**Architecture:**
- `ThemeManager` class emits `theme_changed` signal
- Each widget connects to signal and applies its own styles
- Decoupled - widgets don't know about manager

**Pros:**
- Follows existing MVC signal pattern in codebase
- Decoupled architecture - easy to add new themed widgets
- Each widget responsible for its own styling
- Highly testable in isolation

**Cons:**
- More complex for simple MVP (only 2-3 widgets need theming)
- Each widget needs theme application logic
- Overhead of signal chain for simple feature

### Option 2: Direct Widget Styling (Centralized)
**Architecture:**
- Theme definitions as simple dataclasses/constants
- `MainWindow` owns theme state and menu
- `MainWindow` directly calls styling methods on widgets
- Use `QSettings` for persistence

**Pros:**
- Simple and straightforward for MVP
- No signal overhead
- Clear ownership (MainWindow coordinates UI state)
- Easy to understand and maintain
- Can refactor to signals later if needed

**Cons:**
- MainWindow coupled to themed widgets
- Less extensible than signal-based approach
- Must modify MainWindow to add new themed components

### Option 3: Global QApplication Stylesheet
**Architecture:**
- Apply single stylesheet to `QApplication`
- All widgets inherit styles automatically

**Pros:**
- Simplest possible implementation
- Automatic propagation to all widgets
- Minimal code

**Cons:**
- Less granular control over individual widgets
- Can have unexpected cascading effects
- Harder to test components in isolation
- Qt stylesheet specificity can be tricky

## Decision

**Choose Option 2: Direct Widget Styling (Centralized)**

### Reasoning

For this MVP feature, we prioritize **simplicity over extensibility**:

1. **YAGNI Principle**: We only have 2-3 widgets that need theming for MVP
2. **Matches Current Patterns**: MainWindow already coordinates UI-level concerns (see menu handling, status updates)
3. **Easier to Learn**: Direct method calls are clearer than signal chains for this case
4. **Testable**: Can still test theme application in unit tests
5. **Refactorable**: If we add many themed components post-MVP, we can refactor to signals

This follows the project philosophy: "Make it work, make it right, make it fast" - start simple, refactor when patterns emerge.

## Architecture Design

### Component Structure

```
src/ereader/
├── models/
│   ├── theme.py          # NEW: Theme dataclass and predefined themes
│   └── ...
├── views/
│   ├── main_window.py    # MODIFIED: Theme menu, coordination, persistence
│   ├── book_viewer.py    # MODIFIED: Apply theme method
│   └── ...
```

### Data Model

**`src/ereader/models/theme.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    """Represents a visual theme for the e-reader.

    Attributes:
        name: Display name (e.g., "Light", "Dark")
        background: Background color (hex)
        text: Text color (hex)
        status_bg: Status bar background color (hex)
    """
    name: str
    background: str
    text: str
    status_bg: str

# Predefined themes
LIGHT_THEME = Theme(
    name="Light",
    background="#ffffff",
    text="#1a1a1a",
    status_bg="#f5f5f5"
)

DARK_THEME = Theme(
    name="Dark",
    background="#1e1e1e",
    text="#e0e0e0",
    status_bg="#252526"
)

# Registry of all available themes
AVAILABLE_THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}

# Default theme
DEFAULT_THEME = LIGHT_THEME
```

### View Layer Changes

**`src/ereader/views/main_window.py`**

Additions:
1. **Theme menu in View menu**
   - Create View menu (new)
   - Add Theme submenu
   - Use `QActionGroup` for radio button behavior

2. **Theme state management**
   - `self._current_theme: Theme` - current active theme
   - `_load_theme_preference()` - load from QSettings on startup
   - `_save_theme_preference()` - save to QSettings on change

3. **Theme application**
   - `_apply_theme(theme: Theme)` - coordinates applying theme to all widgets
   - Calls theme methods on BookViewer, updates MainWindow styles

4. **QSettings integration**
   - Organization: "EReader"
   - Application: "EReader"
   - Key: "theme" (stores theme identifier: "light" or "dark")

**`src/ereader/views/book_viewer.py`**

Modifications:
1. **Refactor `_setup_default_style()`**
   - Change to `apply_theme(theme: Theme)`
   - Accept Theme parameter
   - Generate stylesheet from theme colors
   - Public method (can be called from MainWindow)

2. **Initial theme**
   - Welcome message uses default theme initially
   - MainWindow calls `apply_theme()` after loading preference

### Persistence Strategy

**QSettings Configuration:**
```python
from PyQt6.QtCore import QSettings

settings = QSettings("EReader", "EReader")
settings.setValue("theme", "dark")  # Save
theme_id = settings.value("theme", "light")  # Load with default
```

**Settings Location:**
- Linux: `~/.config/EReader/EReader.conf`
- macOS: `~/Library/Preferences/com.EReader.EReader.plist`
- Windows: Registry under `HKEY_CURRENT_USER\Software\EReader\EReader`

### Stylesheet Generation

Each themed widget generates its own stylesheet:

```python
def apply_theme(self, theme: Theme) -> None:
    """Apply theme to book viewer.

    Args:
        theme: Theme to apply.
    """
    stylesheet = f"""
        QTextBrowser {{
            padding: 20px;
            background-color: {theme.background};
            color: {theme.text};
        }}
    """
    self._renderer.setStyleSheet(stylesheet)
```

## Consequences

### What This Enables
- ✅ Light and Dark themes for MVP
- ✅ Simple, maintainable code
- ✅ Easy to test theme application
- ✅ Clear coordination in MainWindow
- ✅ Persistent user preference
- ✅ Foundation for future theme features

### What This Constrains
- ⚠️ Adding new themed widgets requires MainWindow modification
- ⚠️ Theme state is centralized (but this is acceptable for MVP)

### Future Enhancements (Post-MVP)
If we add many themed components, we can refactor to signal-based:
1. Extract `ThemeManager` class with signals
2. Move theme coordination out of MainWindow
3. Widgets subscribe to `theme_changed` signal
4. Maintains same Theme dataclass and QSettings persistence

### What to Watch Out For
- **Initialization order**: Load theme preference before creating widgets, or update after creation
- **Testing**: Mock QSettings in tests to avoid filesystem dependencies
- **Stylesheet specificity**: Be careful with nested stylesheets (child widgets)

## Implementation Plan

### Phase 1: Data Model (Small)
1. Create `src/ereader/models/theme.py`
2. Define `Theme` dataclass
3. Define `LIGHT_THEME` and `DARK_THEME` constants
4. Write unit tests for theme data model

**Estimated complexity:** Low
**Learning value:** Dataclasses, module-level constants

### Phase 2: BookViewer Theme Support (Small)
1. Refactor `_setup_default_style()` to `apply_theme(theme: Theme)`
2. Generate stylesheet from theme colors
3. Test theme application with fixtures

**Estimated complexity:** Low
**Learning value:** Dynamic stylesheet generation

### Phase 3: MainWindow Integration (Medium)
1. Add View menu to menu bar
2. Create Theme submenu with QActionGroup
3. Connect theme actions to handler method
4. Implement `_apply_theme()` coordinator
5. Test theme switching

**Estimated complexity:** Medium
**Learning value:** QMenu, QActionGroup, radio button behavior

### Phase 4: Persistence (Small)
1. Implement `_load_theme_preference()` using QSettings
2. Implement `_save_theme_preference()` using QSettings
3. Call load on init, save on theme change
4. Test persistence with temporary settings

**Estimated complexity:** Low
**Learning value:** QSettings for user preferences

### Phase 5: Integration Testing (Small)
1. Test full theme switching workflow
2. Test persistence across "sessions" (restart sim)
3. Manual testing in real app
4. Verify WCAG contrast compliance

**Estimated complexity:** Low
**Learning value:** Integration testing patterns

## Testing Strategy

### Unit Tests
- `test_models/test_theme.py`: Theme dataclass validation
- `test_views/test_book_viewer.py`: Add `test_apply_theme()` method
- `test_views/test_main_window.py`: Add theme menu and switching tests

### Integration Tests
- Theme preference persistence (save/load cycle)
- Full theme application across all components
- Theme switching with book loaded

### Manual Testing Checklist
- [ ] Theme menu appears in View menu
- [ ] Radio indicators show current theme
- [ ] Clicking theme instantly updates UI
- [ ] All text remains readable in both themes
- [ ] Theme persists after app restart
- [ ] Welcome message uses correct theme
- [ ] No console warnings or errors

## Learning Goals

Through implementing this feature, you'll learn:

1. **QActionGroup** - Radio button menu behavior
2. **QSettings** - Persistent user preferences across sessions
3. **Dynamic stylesheets** - Generating and applying CSS at runtime
4. **Dataclasses** - Frozen dataclasses for immutable data
5. **UI coordination** - Managing state across multiple widgets
6. **WCAG compliance** - Accessible color contrast ratios

## Related Documents

- UX Design: (in session context, see `/ux design` output)
- Project structure: `docs/architecture/project-structure.md`
- MVC pattern: `docs/architecture/epub-rendering-architecture.md`

## Notes

- This is an **MVP implementation** focused on simplicity
- Can be enhanced post-MVP with signals, more themes, auto-detection
- Follows project philosophy: "First implementation: simplest thing that works"
- Architecture matches current codebase patterns (MainWindow as coordinator)
