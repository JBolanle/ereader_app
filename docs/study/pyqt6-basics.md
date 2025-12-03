# Study Session: PyQt6 Basics

**Date:** 2025-12-02
**Topic:** PyQt6 Basics
**Duration:** ~30 minutes

---

## What It Is

PyQt6 is a Python binding for Qt6—a powerful, cross-platform C++ framework for building desktop applications. Think of it as a bridge that lets you use Qt's mature, native-looking GUI widgets from Python.

When you create a PyQt6 application, you're essentially:
1. Creating widgets (buttons, text areas, windows, etc.)
2. Arranging them in layouts
3. Connecting user actions (clicks, typing) to Python functions via "signals and slots"

It's event-driven, meaning your code responds to user interactions rather than running top-to-bottom like a script.

## Why It Matters

For our e-reader, PyQt6 gives us:
- **Native HTML rendering** via `QWebEngineView` (perfect for EPUB content)
- **Professional appearance** with native platform widgets
- **Rich text support** with full CSS styling
- **Mature ecosystem** with tons of examples and documentation
- **Cross-platform** works on Linux, Windows, macOS without changes

We chose PyQt6 specifically because it aligns with your learning goals (write UI from scratch) and because rendering EPUB content (which is HTML/CSS internally) is straightforward with Qt's web engine.

## Simple Example

Here's a minimal PyQt6 app with a window and a button:

```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
import sys

# Every PyQt6 app needs a QApplication instance
app = QApplication(sys.argv)

# Create a main window
window = QMainWindow()
window.setWindowTitle("My First PyQt6 App")
window.resize(400, 300)

# Create a button
button = QPushButton("Click Me!", parent=window)
button.move(150, 120)  # Position it

# Connect button click to a function (signal → slot)
button.clicked.connect(lambda: print("Button was clicked!"))

# Show window and start event loop
window.show()
sys.exit(app.exec())
```

**Key concepts:**
- `QApplication`: Manages the application lifecycle and event loop
- `QMainWindow`: A top-level window with menu bar, status bar support
- `QPushButton`: A clickable button widget
- `clicked.connect(...)`: Connects the button's "clicked" signal to your function

## In Our E-Reader

Here's how PyQt6 concepts map to our e-reader:

| PyQt6 Component | E-Reader Use Case |
|-----------------|-------------------|
| `QMainWindow` | Main application window with menu (File → Open, Settings, etc.) |
| `QWebEngineView` | Display rendered EPUB chapters (HTML content) |
| `QToolBar` | Navigation controls (prev/next chapter, bookmarks) |
| `QSplitter` | Divide screen between chapter list and content area |
| `QListWidget` | Table of contents / chapter navigation |
| Signals & Slots | Handle page turns, bookmark clicks, theme changes |
| `QSettings` | Save reading position, preferences across sessions |

**Example flow:**
1. User clicks "Next Chapter" button
2. Button emits `clicked` signal
3. Signal connected to controller method `on_next_chapter()`
4. Controller loads next chapter HTML from EPUB
5. Controller tells `QWebEngineView` to render new HTML
6. View updates display

## Exercises

### Exercise 1: Counter App (5 minutes)

```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
import sys

class CounterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Counter")
        self.resize(300, 200)

        # Central widget (QMainWindow requires one)
        central = QWidget()
        self.setCentralWidget(central)

        # Layout (arranges widgets vertically)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Counter display
        self.counter = 0
        self.label = QLabel(f"Count: {self.counter}")
        layout.addWidget(self.label)

        # Buttons
        inc_button = QPushButton("Increment")
        dec_button = QPushButton("Decrement")
        reset_button = QPushButton("Reset")

        layout.addWidget(inc_button)
        layout.addWidget(dec_button)
        layout.addWidget(reset_button)

        # TODO: Connect signals to slots
        # Hint: inc_button.clicked.connect(...)
        # Write methods: increment(), decrement(), reset()

    # TODO: Implement these methods
    def increment(self):
        pass

    def decrement(self):
        pass

    def reset(self):
        pass

app = QApplication(sys.argv)
window = CounterWindow()
window.show()
sys.exit(app.exec())
```

**Your task:** Complete the TODOs so clicking buttons updates the counter.

### Exercise 2: Text Display (10 minutes)

Once Exercise 1 works, add:
- A `QLineEdit` (text input box)
- A button "Display Text"
- A `QLabel` that shows whatever was typed when button is clicked

**Hint:** Use `line_edit.text()` to get the typed text.

### Challenge (15 minutes)

Create a simple e-reader prototype:
- A `QPushButton` labeled "Load EPUB"
- A `QLabel` to display the title
- When clicked, use your existing `EPUBReader` to open `tests/fixtures/test-epub.epub`
- Display the book's title in the label

**Hint:**
```python
from ereader.models.epub_reader import EPUBReader

def load_epub(self):
    reader = EPUBReader("tests/fixtures/test-epub.epub")
    metadata = reader.get_metadata()
    self.label.setText(f"Title: {metadata['title']}")
```

## Resources for Further Study

### Official Documentation
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt6 Official Docs](https://doc.qt.io/qt-6/) (C++ docs, but concepts translate)

### Tutorials
- [Real Python: PyQt Layouts](https://realpython.com/python-pyqt-layout/)
- [ZetCode PyQt6 Tutorial](https://zetcode.com/pyqt6/) (progressively harder examples)

### Key Concepts to Study Next
1. **Layouts** (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`) - how to arrange widgets properly
2. **Signals and Slots** - the event system in depth
3. **QWebEngineView** - for rendering HTML (crucial for EPUB)
4. **Model/View Architecture** - Qt's pattern for displaying data (like book chapters)

### Context7 Usage
When you're ready to implement something specific:
- "Use context7 to get PyQt6 QWebEngineView documentation" (for HTML rendering)
- "Use context7 to get PyQt6 layout manager examples"
- "Use context7 to get PyQt6 signals and slots examples"

---

## Notes and Reflections

<!-- Add your notes after completing exercises -->
