# Key Learnings from MVP Development

**Date**: December 4, 2024
**Context**: Completed E-Reader Application MVP (v0.1.0-mvp)

This document captures the technical and professional skills learned during the MVP development cycle, organized by domain.

---

## 🎨 PyQt6 & GUI Development

### Concepts Mastered

#### Signals and Slots ⭐⭐⭐
**What I learned:**
- Signals are type-safe event emitters in Qt
- Slots are methods that respond to signals
- Signal chains enable MVC architecture (View → Controller → Model)
- Custom signals: `signal_name = pyqtSignal(arg_types)`

**Real implementation:**
```python
# In BookViewer (View)
chapter_changed = pyqtSignal()
scroll_position_changed = pyqtSignal(int)

# In ReaderController (Controller)
self.view.chapter_changed.connect(self._update_progress)
self.view.scroll_position_changed.connect(self._handle_scroll)

# In MainWindow (Parent View)
self.controller.progress_changed.connect(self._update_status_bar)
```

**Key insight:** Signals decouple components. Views don't know about controllers, controllers don't know about other views. Pure message passing.

#### QShortcut System ⭐⭐
**What I learned:**
- QShortcut provides keyboard handling separate from widget focus
- Application-wide shortcuts work regardless of focus
- Can specify context: ApplicationShortcut, WindowShortcut, WidgetShortcut

**Real implementation:**
```python
# Application-wide shortcuts (work everywhere)
QShortcut(QKeySequence("Ctrl+O"), self, self.open_book)
QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

# Widget-specific shortcuts (BookViewer only)
QShortcut(QKeySequence("Left"), self.book_viewer, self.previous_chapter)
QShortcut(QKeySequence("Right"), self.book_viewer, self.next_chapter)
```

**Key insight:** Keyboard shortcuts are first-class citizens in Qt. Don't hack them with keyPressEvent unless you must.

#### QScrollBar API ⭐⭐⭐
**What I learned:**
- QScrollBar has `value()`, `maximum()`, `minimum()`
- Percentage calculation: `value / (maximum - minimum) * 100`
- Signals: `valueChanged(int)` emits on every scroll
- Can manipulate programmatically: `setValue()`, `setRange()`

**Real implementation:**
```python
def get_scroll_percentage(self) -> int:
    scrollbar = self.verticalScrollBar()
    max_value = scrollbar.maximum()
    if max_value == 0:
        return 100  # Fully visible content
    return int((scrollbar.value() / max_value) * 100)
```

**Key insight:** Scrollbar maximum isn't the content height - it's `content_height - viewport_height`. If content fits viewport, maximum is 0.

#### Responsive CSS in Qt ⭐⭐
**What I learned:**
- QTextBrowser supports a good subset of CSS
- `max-width: 100%` makes images responsive
- `aspect-ratio` maintained automatically
- Can inject CSS into HTML before rendering

**Real implementation:**
```python
css = """
    img {
        max-width: 100%;
        height: auto;
    }
"""
html = f"<style>{css}</style>{content}"
self.text_browser.setHtml(html)
```

**Key insight:** Standard web CSS patterns work in Qt. Don't reinvent the wheel with JavaScript.

#### QSettings for Persistence ⭐
**What I learned:**
- QSettings provides cross-platform preference storage
- Automatically uses platform conventions (registry on Windows, plist on macOS, ini on Linux)
- Simple key-value API: `setValue()`, `value(default)`

**Real implementation:**
```python
# Save theme preference
settings = QSettings("EReader", "Theme")
settings.setValue("current_theme", "dark")

# Load on startup with default
theme_name = settings.value("current_theme", "light")
```

**Key insight:** Qt handles platform differences. You write once, it works everywhere.

#### QActionGroup for Radio Buttons ⭐
**What I learned:**
- QActionGroup makes menu actions mutually exclusive
- Automatically handles check/uncheck logic
- Cleaner than manual state tracking

**Real implementation:**
```python
theme_group = QActionGroup(self)
theme_group.setExclusive(True)

light_action = QAction("Light", self, checkable=True)
dark_action = QAction("Dark", self, checkable=True)

theme_group.addAction(light_action)
theme_group.addAction(dark_action)

light_action.triggered.connect(lambda: self.set_theme("light"))
```

**Key insight:** Qt provides widgets for common patterns. Look for built-in solutions before rolling your own.

### Skills In Progress

- **Layout management** (basic QVBoxLayout/QHBoxLayout used)
- **Custom widgets** (haven't created custom subclass yet)
- **Qt Designer** (writing code directly for learning)
- **QWebEngineView** (using QTextBrowser, might upgrade later)

---

## 📖 EPUB Format

### Concepts Mastered

#### ZIP-Based Structure ⭐⭐⭐
**What I learned:**
- EPUB is just a ZIP file with specific structure
- Python's `zipfile` module handles extraction
- Must preserve file structure (paths matter)

**EPUB anatomy:**
```
book.epub (ZIP archive)
├── META-INF/
│   └── container.xml          # Points to content.opf
├── OEBPS/ (or other name)
│   ├── content.opf            # Book metadata, manifest, spine
│   ├── toc.ncx                # Table of contents
│   ├── chapter1.xhtml         # Actual content
│   ├── images/
│   │   └── cover.jpg
│   └── styles/
│       └── stylesheet.css
└── mimetype                   # "application/epub+zip"
```

**Key insight:** Understanding the structure is 80% of parsing. The rest is XML.

#### Navigation Chain ⭐⭐
**What I learned:**
- Start: `META-INF/container.xml`
- Find: `<rootfile full-path="..." />`
- Parse: `content.opf` at that path
- Extract: Metadata, manifest, spine from OPF

**Real implementation:**
```python
# 1. Read container.xml
container = self._parse_xml("META-INF/container.xml")

# 2. Find OPF path
opf_path = container.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile").get("full-path")

# 3. Parse OPF
opf = self._parse_xml(opf_path)

# 4. Extract components
metadata = opf.find(".//{http://www.idpf.org/2007/opf}metadata")
manifest = opf.find(".//{http://www.idpf.org/2007/opf}manifest")
spine = opf.find(".//{http://www.idpf.org/2007/opf}spine")
```

**Key insight:** XML namespaces are annoying but necessary. Use full namespace URIs in XPath.

#### Path Resolution ⭐⭐⭐
**What I learned:**
- Paths in manifest are relative to OPF location
- Image paths in chapters are relative to chapter location
- Must normalize paths (handle `../`, `./`, etc.)
- Use `pathlib.PurePosixPath` for platform-independent paths

**Complex example:**
```
OPF at: OEBPS/content.opf
Chapter at: OEBPS/text/chapter1.xhtml
Image in chapter: <img src="../images/photo.jpg" />

Resolution:
1. Chapter path: "OEBPS/text/chapter1.xhtml"
2. Chapter dir: "OEBPS/text/"
3. Image relative to chapter: "../images/photo.jpg"
4. Resolved: "OEBPS/text/../images/photo.jpg" → "OEBPS/images/photo.jpg"
```

**Key insight:** Always track the "relative to" path when resolving. Context matters.

#### Encoding Fallback ⭐
**What I learned:**
- Modern EPUBs: UTF-8
- Older EPUBs: Latin-1, Windows-1252, etc.
- Strategy: Try UTF-8, fallback to latin-1 (never fails)

**Real implementation:**
```python
def _read_text(self, path: str) -> str:
    data = self.zip_file.read(path)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")
```

**Key insight:** Latin-1 never raises UnicodeDecodeError. Use as final fallback.

### Metadata Extraction ⭐⭐

**What I learned:**
- Metadata uses Dublin Core namespaces (`dc:` or `dcterms:`)
- Some EPUBs use `dc`, others use `dcterms` (need fallback)
- XPath with multiple namespaces: Try both

**Real implementation:**
```python
# Try dc: namespace
title = metadata.find(".//{http://purl.org/dc/elements/1.1/}title")

# Fallback to dcterms: namespace
if title is None:
    title = metadata.find(".//{http://purl.org/dc/terms/}title")
```

---

## ✅ Testing (pytest + pytest-qt)

### Concepts Mastered

#### pytest-qt Fundamentals ⭐⭐⭐
**What I learned:**
- `qtbot` fixture provides Qt test utilities
- `qtbot.waitSignal()` for reliable signal testing
- Automatic cleanup prevents memory leaks
- Can test headless (no display required)

**Before (manual, unreliable):**
```python
def test_signal():
    widget = MyWidget()
    widget.my_signal.connect(callback)
    widget.trigger_action()
    # Hope callback was called? 🤞
```

**After (pytest-qt, reliable):**
```python
def test_signal(qtbot):
    widget = MyWidget()
    with qtbot.waitSignal(widget.my_signal, timeout=1000):
        widget.trigger_action()
    # If signal didn't emit, test fails explicitly ✅
```

**Key insight:** `waitSignal()` solves the async testing problem for signals. No more race conditions.

#### Testing Signal Chains ⭐⭐⭐
**What I learned:**
- Can test multi-hop signals (View → Controller → View)
- Each hop can be verified independently
- Integration tests verify end-to-end flow

**Real implementation:**
```python
def test_scroll_updates_progress(qtbot):
    # Test: BookViewer scroll → Controller → MainWindow status bar

    # 1. Set up signal spy on controller
    with qtbot.waitSignal(controller.progress_changed):
        # 2. Trigger scroll in view
        viewer.scroll_to(50)

    # 3. Verify final result in parent view
    assert "50%" in main_window.status_bar.text()
```

**Key insight:** Test each layer, then test integration. Both are necessary.

#### Keyboard Testing ⭐⭐
**What I learned:**
- `qtbot.keyClick()` simulates key presses
- Can test modifiers: `qtbot.keyClick(widget, Qt.Key_O, Qt.ControlModifier)`
- Tests actual QShortcut paths, not fake events

**Real implementation:**
```python
def test_left_arrow_previous_chapter(qtbot):
    with qtbot.waitSignal(viewer.chapter_changed):
        qtbot.keyClick(viewer, Qt.Key_Left)
```

**Key insight:** Testing keyboard shortcuts validates the entire input path, including QShortcut setup.

#### Test Organization ⭐⭐
**What I learned:**
- Unit tests: Single class/function in isolation
- Integration tests: Multiple components interacting
- Separate test files mirror source structure

**Project structure:**
```
tests/
├── test_models/
│   ├── test_epub.py              # Unit: EPUBBook
│   └── test_theme.py             # Unit: Theme dataclass
├── test_controllers/
│   └── test_reader_controller.py # Integration: Controller + Model
├── test_views/
│   ├── test_book_viewer.py       # Unit: BookViewer signals
│   └── test_main_window.py       # Integration: MainWindow + Controller
└── test_integration/
    └── test_real_epub_files.py   # End-to-end: Real files
```

**Key insight:** Clear test organization makes tests maintainable. Like knows like.

#### Coverage Analysis ⭐⭐
**What I learned:**
- Coverage percentage is a metric, not a goal
- Focus on **meaningful coverage** (critical paths)
- Document deferred tests (why not tested)
- Trend matters: Coverage shouldn't decrease

**Coverage evaluation framework:**
1. **Is this critical?** (User-facing or data integrity) → Test
2. **What's the risk?** (High risk) → Test
3. **What's the effort?** (Low effort) → Just test it
4. **Is it defensive?** (Logging, malformed input) → Can defer

**Key insight:** 91% coverage with meaningful tests > 95% coverage with meaningless tests.

### Skills In Progress

- **Advanced mocking** (basic mocks used, not complex scenarios)
- **Property-based testing** (hypothesis library)
- **Performance testing** (benchmarks)
- **Mutation testing** (testing the tests)

---

## 🏗️ Software Architecture

### Concepts Mastered

#### MVC Pattern ⭐⭐⭐
**What I learned:**
- **Model**: Data and business logic (EPUBBook)
- **View**: UI presentation (MainWindow, BookViewer)
- **Controller**: Coordination (ReaderController)

**Benefits:**
- Views are stateless (just render)
- Controllers are testable (no GUI dependency)
- Models are reusable (could have CLI, TUI, GUI)

**Real implementation:**
```python
# Model: Pure data operations
class EPUBBook:
    def get_chapter_content(self, index: int) -> str:
        # No UI knowledge

# Controller: Coordination
class ReaderController:
    def __init__(self, model: EPUBBook, view: BookViewerProtocol):
        self.model = model
        self.view = view
        self.view.next_chapter.connect(self._handle_next)

    def _handle_next(self) -> None:
        content = self.model.get_chapter_content(self.current + 1)
        self.view.display_content(content)

# View: Presentation only
class BookViewer(QWidget):
    next_chapter = pyqtSignal()

    def display_content(self, html: str) -> None:
        self.text_browser.setHtml(html)
```

**Key insight:** MVC turns a monolithic UI into testable components. Controllers can be unit-tested without Qt.

#### Protocol-Based Abstraction ⭐⭐⭐
**What I learned:**
- Protocols define interfaces via structural subtyping
- Unlike ABC, no inheritance required
- Type checkers verify protocol compliance
- Enables swapping implementations (QTextBrowser ↔ QWebEngineView)

**Real implementation:**
```python
from typing import Protocol

class BookViewerProtocol(Protocol):
    """Interface for any book viewer implementation."""

    def display_content(self, html: str) -> None: ...
    def get_scroll_percentage(self) -> int: ...

    next_chapter: pyqtSignal
    previous_chapter: pyqtSignal

# ReaderController depends on protocol, not concrete class
class ReaderController:
    def __init__(self, view: BookViewerProtocol):
        self.view = view  # Could be QTextBrowser, QWebEngineView, etc.
```

**Key insight:** Protocols are Python's answer to Go's interfaces. Design to interfaces, not implementations.

#### Custom Exceptions Hierarchy ⭐⭐
**What I learned:**
- Base exception for domain: `EReaderError`
- Specific exceptions for use cases: `InvalidEPUBError`, `RenderError`
- No bare `except:` clauses (always catch specific types)
- Logging before raising (context preservation)

**Real implementation:**
```python
class EReaderError(Exception):
    """Base exception for all e-reader errors."""

class EPUBError(EReaderError):
    """EPUB-specific errors."""

class InvalidEPUBError(EPUBError):
    """Not a valid EPUB file."""

# Usage:
try:
    book = EPUBBook(path)
except InvalidEPUBError as e:
    logger.error(f"Invalid EPUB: {e}")
    show_error_dialog("Could not open book")
```

**Key insight:** Exception hierarchy enables precise error handling. Catch broad for recovery, narrow for specifics.

#### Lazy Loading ⭐
**What I learned:**
- Load resources on-demand, not upfront
- Cache frequently accessed items
- Trade complexity for memory savings

**Real implementation:**
```python
class EPUBBook:
    def __init__(self, path: str):
        self.zip_file = zipfile.ZipFile(path)
        self._metadata = None  # Lazy load

    @property
    def metadata(self) -> dict:
        if self._metadata is None:
            self._metadata = self._parse_metadata()
        return self._metadata
```

#### LRU Cache ⭐⭐
**What I learned:**
- Least Recently Used eviction policy
- OrderedDict provides insertion order + fast deletion
- Track hits/misses for optimization feedback

**Real implementation:**
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[str]:
        if key not in self.cache:
            return None
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)  # Evict oldest
```

**Key insight:** Custom implementation gives full control over eviction policy and stats.

---

## 🔧 Development Tools

### Tools Mastered

#### uv Package Manager ⭐⭐
**What I learned:**
- Fast alternative to pip/poetry
- `uv sync` for dependencies
- `uv add` / `uv add --dev` for packages
- `uv run` for executing scripts

**Why uv over pip:**
- Faster dependency resolution
- Better lockfile management
- Modern Python tooling

#### pytest ⭐⭐⭐
**What I learned:**
- `pytest` discovers tests automatically (test_*.py)
- Fixtures provide reusable test setup
- Parametrize runs same test with different inputs
- Coverage plugin: `pytest --cov=src/`

**Real implementation:**
```python
@pytest.fixture
def sample_epub(tmp_path):
    """Fixture: Create a minimal valid EPUB for testing."""
    epub_path = tmp_path / "test.epub"
    # ... create EPUB structure
    return epub_path

def test_open_epub(sample_epub):
    book = EPUBBook(sample_epub)
    assert book.title == "Test Book"
```

#### ruff Linter ⭐⭐
**What I learned:**
- Lightning-fast Python linter (Rust-based)
- Replaces flake8, isort, pycodestyle
- `ruff check --fix` auto-fixes many issues
- Enforces PEP 8 + modern best practices

#### GitHub CLI (gh) ⭐⭐
**What I learned:**
- `gh issue create/list/view` for issue management
- `gh pr create/status/view` for pull requests
- `gh repo view` for repository info
- Faster than web interface for common tasks

**Workflow:**
```bash
# Create issue
gh issue create --title "Add bookmarks" --body "..."

# Create PR
gh pr create --title "feat: add bookmarks" --body "..."

# Check status
gh pr status
```

---

## 🎯 Professional Practices

### Practices Mastered

#### Conventional Commits ⭐⭐⭐
**Format:** `type(scope): description`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code restructuring
- `chore`: Maintenance

**Examples:**
```
feat(epub): add metadata extraction from content.opf
fix(ui): prevent crash when book has no cover
test(models): add edge cases for empty chapters
docs: update README with usage instructions
```

**Key insight:** Commit messages tell a story. Make them scannable and meaningful.

#### Feature Branch Workflow ⭐⭐
**What I learned:**
- Main branch is always stable
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Squash and merge for clean history

**Workflow:**
```bash
# Create feature branch
git checkout -b feature/bookmarks

# Work, commit
git commit -m "feat: implement bookmark model"

# Push and create PR
git push -u origin feature/bookmarks
gh pr create
```

#### Code Review ⭐⭐
**What I learned:**
- Self-review before PR (catch obvious issues)
- Use `/code-review` command for automated checks
- Address all review comments or explain why not
- Keep PRs focused and reasonably sized

**Pre-PR checklist:**
- [ ] Tests pass (`pytest`)
- [ ] Linting clean (`ruff check`)
- [ ] Coverage maintained (`pytest --cov`)
- [ ] Self-reviewed (`/code-review`)
- [ ] Documentation updated

#### Documentation-Driven Development ⭐⭐
**What I learned:**
- Document decisions before implementing
- ADRs (Architecture Decision Records) in docs/architecture/
- Specs in docs/specs/ before complex features
- README is the front door (keep it current)

**Documents created:**
- ADRs: project-structure, epub-rendering-architecture, etc.
- Specs: feature-image-rendering, keyboard-navigation-architecture
- Guides: pytest-qt-patterns, performance-summary

---

## 📊 Performance & Optimization

### Concepts Mastered

#### Profiling Before Optimizing ⭐⭐⭐
**What I learned:**
- Measure before assuming bottlenecks
- Build profiling tools (don't guess)
- Statistical analysis (min/max/avg/median)
- Data-driven optimization decisions

**Profiling system built:**
- EPUB loading time
- Chapter rendering time
- Memory usage tracking
- Image resolution performance

**Result:** Identified 559MB memory growth → targeted caching optimization

#### Memory Profiling ⭐⭐
**What I learned:**
- `tracemalloc` for Python memory tracking
- Base64 images increase memory (~33% larger than raw)
- Chapter caching reduces memory predictably
- Measure before/after optimization

**Real measurement:**
```python
import tracemalloc

tracemalloc.start()
# ... load chapters
current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
```

**Result:** 559MB → 150MB with 10-chapter LRU cache (73% reduction)

#### Time Profiling ⭐
**What I learned:**
- `time.perf_counter()` for high-resolution timing
- Sample chapters evenly (e.g., every 10th of 100)
- Statistical analysis more robust than single measurements

**Real implementation:**
```python
import time

start = time.perf_counter()
content = book.get_chapter_content(0)
elapsed = time.perf_counter() - start
print(f"Chapter load: {elapsed * 1000:.2f}ms")
```

---

## 🎨 UX & Design

### Practices Mastered

#### UX Research ⭐⭐
**What I learned:**
- Research before implementing (don't guess)
- Desktop conventions matter (users have expectations)
- Accessibility standards exist (WCAG AAA)
- Small details have big impact

**Research conducted:**
- Scroll amounts (50% vs 100% overlap)
- Keyboard conventions (arrows vs Page Up/Down)
- Theme contrast ratios (WCAG AAA: 7:1 minimum)

**Key insight:** UX research takes 30 minutes, prevents weeks of rework.

#### Accessibility By Default ⭐⭐
**What I learned:**
- WCAG AAA: 7:1 contrast minimum (we did 15:1 and 12:1)
- Keyboard shortcuts must be comprehensive (no mouse-only features)
- Status bar announcements for screen readers

**Implementation:**
- Light theme: Black (#000000) on Cream (#F5F5DC) = 15:1
- Dark theme: Light Gray (#CCCCCC) on Dark Gray (#2B2B2B) = 12:1
- All features accessible via keyboard

**Key insight:** Accessibility isn't a feature, it's a baseline. Build it in from start.

#### Progressive Enhancement ⭐
**What I learned:**
- Ship MVP, iterate based on usage
- Virtual pagination (Phase 1) → True pagination (Phase 2)
- Fast shipping > perfect initially

**Example:**
- MVP: Scroll-based navigation (works, not perfect)
- Post-MVP: Page-based pagination (better UX)

---

## 💭 Soft Skills

### Skills Developed

#### Decision Documentation ⭐⭐⭐
**What I learned:**
- Document WHY, not just WHAT
- Future you will forget context
- ADRs capture trade-offs and reasoning

**Decisions Log in CLAUDE.md captures:**
- What was decided
- Why that choice was made
- What alternatives were considered
- Links to detailed docs

#### Scope Management ⭐⭐
**What I learned:**
- Define MVP clearly (4 features)
- Defer nice-to-haves (pagination Phase 2)
- Ship iteratively (14 PRs, each shippable)
- Resist feature creep

**Example:**
- In scope: Light/Dark themes
- Out of scope: Custom color themes (deferred)
- Rationale: MVP needs basic themes, customization can wait

#### Time Boxing ⭐
**What I learned:**
- 4-day MVP sprint (strict timeline)
- One feature per day average
- Quality gates prevent rushing (tests, linting, coverage)

---

## 🚀 What's Next?

### Immediate Goals
- **mypy Integration** - Type checking (deferred during MVP)
- **Advanced Mocking** - Complex test scenarios
- **Performance Benchmarks** - Regression detection

### Medium-term Goals
- **CI/CD Pipeline** - GitHub Actions
- **Packaging** - PyPI distribution
- **Cross-platform Testing** - Windows, macOS, Linux

### Long-term Goals
- **Async/Await Mastery** - Beyond basic usage
- **QWebEngineView** - Upgrade from QTextBrowser
- **Plugin Architecture** - Extensibility

---

## 📚 Resources That Helped

### Documentation
- **PyQt6 Docs**: https://doc.qt.io/qtforpython-6/
- **EPUB Spec**: https://www.w3.org/publishing/epub3/
- **pytest-qt Docs**: https://pytest-qt.readthedocs.io/
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

### Tools
- **Context7 MCP**: Up-to-date library documentation during development
- **Claude Code**: Workflow automation and AI assistance
- **GitHub CLI**: Issue/PR management

---

## 🎓 Key Takeaways

1. **Learn by building** - Reading docs < implementing features
2. **Test as you go** - 91% coverage from day one, not retrofitted
3. **Document decisions** - ADRs saved time during iteration
4. **Measure, don't guess** - Profiling led to right optimization
5. **Ship iteratively** - 14 PRs better than one big-bang
6. **UX research pays off** - 30 minutes research > weeks of rework
7. **Architecture upfront** - MVC + Protocols enabled everything
8. **Quality gates work** - Tests + linting caught regressions instantly

---

**Most important lesson:** You can ship production-quality software while learning. The key is disciplined process, not prior knowledge.

---

*This document will be updated as post-MVP development continues.*
