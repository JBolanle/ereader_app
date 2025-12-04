---
name: pyqt-design
description: Create distinctive, production-grade PyQt6 desktop interfaces with high design quality. Use this skill when building UI components, windows, dialogs, or widgets for the e-reader application. Generates creative, polished PyQt6 code that avoids generic desktop app aesthetics.
license: MIT
---

This skill guides creation of distinctive, production-grade PyQt6 desktop interfaces that avoid generic application aesthetics. Implement real working code with exceptional attention to visual details and creative choices appropriate for desktop applications.

The user provides UI requirements: a window, dialog, widget, or component to build. They may include context about the purpose, user workflow, or technical constraints.

## Design Thinking for Desktop Applications

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What user task does this interface serve? What's the reading context?
- **Desktop Paradigm**: Choose your approach: Clean reader-first (minimal chrome, content focus), Professional tool (editor-style with toolbars), Modern app (card-based, floating panels), Classic application (menu-driven, traditional), Immersive experience (fullscreen, cinematic), or something entirely unique.
- **Tone**: Pick an extreme: brutally minimal, richly detailed, retro/nostalgic, ultra-modern, warm/organic, technical/precise, editorial/magazine-like, artistic/creative, etc.
- **Constraints**: PyQt6 capabilities, performance for book rendering, accessibility, platform conventions.
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing users will remember about the interface?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. The best desktop apps have a strong point of view. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working PyQt6 code that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail
- Properly integrated with PyQt6's architecture (signals/slots, layouts, etc.)

## PyQt6 Desktop Aesthetics Guidelines

Focus on:

### Typography & Fonts
- **Font Selection**: Use QFont with distinctive font families. Avoid generic defaults like "Sans Serif" or "Arial".
- **System Font Integration**: Leverage platform-specific fonts (SF Pro on Mac, Segoe UI on Windows, Roboto on Linux) when appropriate, or choose distinctive fonts that match your aesthetic.
- **Reading Fonts**: For e-reader content, prioritize readability: Serif fonts for body text (Georgia, Palatino, Baskerville, etc.), proper line height (1.5-1.8), generous margins.
- **UI Fonts**: Use clean, modern fonts for interface elements that contrast with content fonts.
- **Font Rendering**: Set proper antialiasing with `QFont.PreferAntialias` or `QFont.PreferQuality`.

### Color & Theme
- **Qt Stylesheets**: Use QSS (Qt Style Sheets) for cohesive theming across the application.
- **Color Palettes**: Use `QPalette` for system integration or custom QSS for full control.
- **Dark/Light Modes**: Implement both with distinct personalities - not just inverted colors.
- **Semantic Colors**: Define purpose-driven colors (accent, text-primary, text-secondary, background, surface, etc.).
- **Dominant Colors**: Commit to a bold color identity. Sharp accents outperform timid, evenly-distributed palettes.

Example QSS structure:
```python
stylesheet = """
QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
}

QPushButton {
    background-color: #2d5f8d;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    color: white;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3d7fb8;
}
"""
```

### Motion & Animations
- **QPropertyAnimation**: Use for smooth transitions (opacity, geometry, colors).
- **Animation Groups**: Combine multiple animations with `QParallelAnimationGroup` or `QSequentialAnimationGroup`.
- **Easing Curves**: Choose appropriate easing (`QEasingCurve.OutCubic`, `InOutQuad`, etc.) for natural motion.
- **High-Impact Moments**: Focus on meaningful transitions - page turns, dialog appearances, state changes.
- **Performance**: Keep animations smooth (16ms per frame). Use `QTimer` for custom animation loops when needed.

Example animation:
```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

animation = QPropertyAnimation(widget, b"geometry")
animation.setDuration(300)
animation.setStartValue(start_rect)
animation.setEndValue(end_rect)
animation.setEasingCurve(QEasingCurve.Type.OutCubic)
animation.start()
```

### Spatial Composition & Layout
- **Layout Management**: Use `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QStackedLayout` effectively.
- **Spacing & Margins**: Be intentional. Generous negative space OR controlled density.
- **Alignment**: Use asymmetry when appropriate. Not everything needs to be centered.
- **Nested Layouts**: Create sophisticated compositions by nesting layouts strategically.
- **Custom Widgets**: Create custom `QWidget` subclasses for unique compositions that break the grid.
- **Overlapping Elements**: Use `raise_()`, `lower()`, and absolute positioning for layered effects.

### Visual Details & Polish
- **Custom Painting**: Override `paintEvent()` for unique visual elements using `QPainter`.
- **Drop Shadows**: Use `QGraphicsDropShadowEffect` for depth (but sparingly - performance impact).
- **Transparency**: Use `setWindowOpacity()` or alpha channels in colors for layered interfaces.
- **Rounded Corners**: Apply via QSS `border-radius` or custom painting.
- **Gradients**: Use `QLinearGradient`, `QRadialGradient`, `QConicalGradient` for rich backgrounds.
- **Custom Cursors**: Set unique cursors with `setCursor(QCursor(Qt.CursorShape))`.
- **Icons**: Use `QIcon` with SVG for sharp, scalable icons. Consider custom icon sets that match your aesthetic.

Example custom painting:
```python
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Create gradient background
    gradient = QLinearGradient(0, 0, self.width(), self.height())
    gradient.setColorAt(0, QColor("#1a1a1a"))
    gradient.setColorAt(1, QColor("#2d2d2d"))
    
    painter.fillRect(self.rect(), gradient)
```

### Desktop-Specific Considerations
- **Window Chrome**: Customize or hide title bars with `Qt.WindowType.FramelessWindowHint` for immersive designs.
- **System Integration**: Use native dialogs (`QFileDialog`, `QColorDialog`) when appropriate, or create custom versions that match your aesthetic.
- **Keyboard Shortcuts**: Implement comprehensive keyboard navigation with `QAction` and `QShortcut`.
- **Context Menus**: Create rich, contextual right-click menus with `QMenu`.
- **Toolbars & Dock Widgets**: For complex apps, use `QToolBar` and `QDockWidget` with custom styling.
- **Status Bar**: Use `QStatusBar` for subtle feedback that doesn't interrupt reading.

## Code Quality Standards (from CLAUDE.md)

ALL PyQt6 code must follow these standards:
- **Type Hints**: Required on all functions - `from PyQt6.QtWidgets import QWidget` etc.
- **Docstrings**: Google-style on all public methods
- **Error Handling**: Use custom exceptions from `src/ereader/exceptions.py`
- **Logging**: Use `logging` module, never `print()`
- **Signals/Slots**: Properly connect and disconnect to avoid memory leaks
- **Resource Management**: Clean up resources in `closeEvent()` or use context managers

## Architecture Integration

Components should integrate with the e-reader's MVC architecture:
- **Views**: Inherit from appropriate PyQt6 base classes (`QMainWindow`, `QWidget`, `QDialog`)
- **Signals**: Emit signals for user actions, don't directly call controller methods
- **Separation**: Keep business logic in models, UI code in views
- **Testability**: Design for testing - avoid tight coupling to QApplication

Example structure:
```python
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BookView(QWidget):
    """Main book reading view.
    
    Signals:
        page_changed: Emitted when user navigates to different page (page_number: int)
        bookmark_requested: Emitted when user wants to bookmark (page_number: int)
    """
    
    page_changed = pyqtSignal(int)
    bookmark_requested = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self) -> None:
        """Initialize UI components and layout."""
        # UI setup code
        
    def _apply_styling(self) -> None:
        """Apply custom stylesheet and theming."""
        # Styling code
```

## NEVER Use Generic Desktop Aesthetics

Avoid:
- Default Qt widgets without styling (gray buttons, plain scrollbars)
- Generic system fonts without intentional choice
- Predictable layouts (everything centered, uniform spacing)
- Cliched color schemes (especially purple-blue gradients on gray)
- Cookie-cutter dialogs and windows
- Over-reliance on stock icons without customization

## Pattern Library Examples

### For Minimal/Reader-First Aesthetic:
- Borderless window with custom title bar
- Content fills screen with generous margins
- Subtle, non-intrusive navigation (fade in on mouse movement)
- Monochromatic or sepia color schemes
- Serif fonts for reading, clean sans-serif for UI
- Smooth page transitions

### For Professional/Editor Aesthetic:
- Rich toolbar with organized tool groups
- Multiple panels with splitters
- Keyboard shortcut indicators
- Technical, precise typography
- Neutral colors with strategic accent colors
- Crisp, immediate interactions

### For Immersive/Cinematic Aesthetic:
- Fullscreen with hidden chrome
- Dramatic shadows and depth
- Bold typography choices
- Rich, atmospheric backgrounds
- Smooth, theatrical transitions
- Focus on the reading experience

## Implementation Workflow

1. **Understand Requirements**: What specific UI component/window is needed?
2. **Choose Aesthetic Direction**: Commit to a bold, clear design direction
3. **Sketch Layout**: Plan the widget hierarchy and layout structure
4. **Implement Base Structure**: Create the widget class with proper signals/slots
5. **Add Styling**: Write comprehensive QSS or custom painting
6. **Implement Interactions**: Add animations, hover states, transitions
7. **Polish Details**: Refine spacing, colors, typography, micro-interactions
8. **Test Integration**: Ensure it works with the MVC architecture

## Performance Considerations (from CLAUDE.md)

For the e-reader application:
- Page renders in <100ms
- Memory usage <200MB for typical books
- Smooth scrolling and transitions
- Background page pre-fetching
- Cached page limit: 50 pages

Optimize PyQt6 code:
- Use `QTimer.singleShot()` for deferred operations
- Implement lazy loading for complex widgets
- Cache rendered content when appropriate
- Use `QPixmap` cache for repeated graphics
- Profile with `cProfile` if performance issues arise

## Remember

The best desktop applications have a strong visual identity and clear purpose. Every PyQt6 widget you create should feel intentional, crafted, and appropriate for a reading application. Don't hold back - create interfaces that make users excited to read.

Balance aesthetics with functionality. An e-reader must be beautiful AND comfortable for hours of reading. The interface should disappear when reading, but delight when interacting.

**Match implementation complexity to the aesthetic vision**: Detailed designs need elaborate code with rich styling and animations. Minimal designs need precision, restraint, and careful attention to typography and spacing.

Claude is capable of extraordinary creative work with PyQt6. Show what can truly be created when thinking outside the box and committing fully to a distinctive desktop application vision.
