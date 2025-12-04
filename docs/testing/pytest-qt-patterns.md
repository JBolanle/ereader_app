# pytest-qt Testing Patterns

This document describes pytest-qt testing patterns used in the e-reader application UI tests.

## Overview

pytest-qt is a pytest plugin that provides fixtures for testing PyQt6 applications. It simplifies UI testing by providing:

- **qtbot fixture**: Main fixture for widget testing and event simulation
- **Signal testing**: Reliable signal/slot testing with `qtbot.waitSignal()`
- **Widget management**: Automatic cleanup of widgets
- **Event processing**: Better control over Qt event loop

## Basic Patterns

### Creating Widget Fixtures

Use `qtbot.addWidget()` to register widgets for automatic cleanup:

```python
@pytest.fixture
def viewer(qtbot):
    """Create a BookViewer instance for testing."""
    viewer = BookViewer()
    qtbot.addWidget(viewer)  # Automatic cleanup when test ends
    return viewer
```

### Event Processing

Use `qtbot.wait()` instead of `QApplication.processEvents()`:

```python
# Before (without pytest-qt)
viewer.set_content(html)
QApplication.processEvents()

# After (with pytest-qt)
viewer.set_content(html)
qtbot.wait(10)  # Wait 10ms for events to process
```

### Signal Testing

Use `qtbot.waitSignal()` for reliable signal testing:

```python
# Test that a signal is emitted
with qtbot.waitSignal(viewer.scroll_position_changed, timeout=1000) as blocker:
    viewer.scroll_by_pages(0.5)

# Verify signal arguments
emitted_percentage = blocker.args[0]
assert isinstance(emitted_percentage, float)
assert 0 <= emitted_percentage <= 100
```

### Testing with Mock Decorators

When using `@patch` decorator with pytest fixtures, parameter order matters:

```python
@patch('ereader.controllers.reader_controller.resolve_images_in_html')
def test_navigation(self, mock_resolve, qtbot, main_window):
    """Mock parameter comes first, then fixtures."""
    mock_resolve.side_effect = lambda content, *args, **kwargs: content
    # ... test code
```

## Common Patterns in Our Tests

### Test Structure

```python
class TestFeature:
    """Test a specific feature."""

    def test_specific_behavior(self, qtbot, fixture_name):
        """Test description."""
        # Arrange
        widget = fixture_name

        # Act
        widget.do_something()
        qtbot.wait(10)  # Allow Qt events to process

        # Assert
        assert expected_result
```

### Scrollable Content Fixture

```python
@pytest.fixture
def viewer_with_scrollable_content(qtbot, viewer):
    """Create a viewer with content that requires scrolling."""
    long_html = "<html><body>"
    for i in range(200):
        long_html += f"<p>Paragraph {i}...</p>"
    long_html += "</body></html>"

    viewer.set_content(long_html)
    viewer.show()
    viewer.resize(800, 600)
    qtbot.wait(10)  # Wait for layout

    viewer.scroll_to_top()
    qtbot.wait(10)  # Ensure at top

    return viewer
```

### Signal Chain Testing

Test full signal chains across components:

```python
def test_signal_chain(self, qtbot, main_window_with_book):
    """Test BookViewer → Controller → MainWindow signal chain."""
    window = main_window_with_book

    # Trigger action in BookViewer
    window._book_viewer.scroll_by_pages(0.5)
    qtbot.wait(10)

    # Verify effect in MainWindow
    status_text = window.statusBar().currentMessage()
    assert "Chapter 3 of 5" in status_text
    assert "%" in status_text
```

## Advantages Over Manual Testing

### Before pytest-qt

```python
# Manual QApplication management
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

# Manual event processing
QApplication.processEvents()

# Mock-based signal testing
signal_spy = Mock()
widget.signal.connect(signal_spy)
# ... trigger action ...
assert signal_spy.called
```

### After pytest-qt

```python
# Automatic QApplication provided by qtbot fixture
def test_feature(qtbot, widget):
    pass

# Cleaner event processing
qtbot.wait(10)

# Built-in signal testing
with qtbot.waitSignal(widget.signal, timeout=1000) as blocker:
    # ... trigger action ...
    pass
# Signal verified automatically, args available in blocker.args
```

## Benefits

1. **Reliability**: `qtbot.waitSignal()` is more reliable than Mock for signal testing
2. **Cleanup**: Automatic widget cleanup prevents resource leaks
3. **Readability**: More expressive than manual QApplication management
4. **Debugging**: Better error messages when signals don't fire
5. **Standardization**: Industry-standard approach to PyQt testing

## References

- pytest-qt documentation: https://pytest-qt.readthedocs.io/
- Qt Test framework: https://doc.qt.io/qt-6/qtest-overview.html
- Our test files:
  - `tests/test_views/test_book_viewer.py`
  - `tests/test_views/test_main_window.py`

## When to Use qtbot vs Direct Testing

**Use qtbot for:**
- Widget lifecycle testing
- Signal/slot interactions
- Event-driven behavior
- Integration tests across components

**Direct testing (without qtbot) is fine for:**
- Pure logic in controllers or models
- Utility functions
- Non-Qt code

## Common Gotchas

### 1. Wait Times

Use short waits (10ms typically sufficient):

```python
qtbot.wait(10)  # Good: 10ms is usually enough
qtbot.wait(1000)  # Avoid: Makes tests slow
```

### 2. Signal Timeouts

Default timeout is 5 seconds, but you can adjust:

```python
with qtbot.waitSignal(signal, timeout=1000):  # 1 second
    trigger_action()
```

### 3. Fixture Scope

Most widget fixtures should have function scope (default):

```python
@pytest.fixture  # Function scope - new instance per test
def viewer(qtbot):
    return BookViewer()
```

### 4. Mock Decorator Order

With `@patch`, mock parameters come before fixture parameters:

```python
@patch('module.function')
def test_something(self, mock_func, qtbot, fixture):
    pass  # Correct order
```

## Migration Checklist

When migrating existing tests to pytest-qt:

- [ ] Replace custom `qapp` fixture with `qtbot` parameter
- [ ] Use `qtbot.addWidget()` for widget registration
- [ ] Replace `QApplication.processEvents()` with `qtbot.wait(10)`
- [ ] Replace `Mock()` signal spies with `qtbot.waitSignal()`
- [ ] Update fixture docstrings to mention qtbot
- [ ] Remove unused imports (QApplication, Mock if no longer needed)
- [ ] Verify all tests pass
- [ ] Update pyproject.toml if pytest-qt not in dependencies

## Troubleshooting

Common issues when running pytest-qt tests and their solutions.

### Headless Display Issues in CI

**Problem:** Tests fail in CI with `"Could not connect to display"` or `"QXcbConnection: Could not connect to display"`.

**Solution:** Use Xvfb (X Virtual Frame Buffer) for headless testing:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    sudo apt-get install -y xvfb
    xvfb-run -a pytest
```

Or use pytest-xvfb plugin:
```bash
uv add --dev pytest-xvfb
# Tests will automatically run in virtual display
```

### Platform-Specific Quirks

#### Wayland vs X11

**Problem:** Tests behave differently on Wayland vs X11 display servers.

**Solution:**
- Force X11 backend: `export QT_QPA_PLATFORM=xcb`
- Or use offscreen platform: `export QT_QPA_PLATFORM=offscreen`
- Add to pyproject.toml:
  ```toml
  [tool.pytest.ini_options]
  env = [
      "QT_QPA_PLATFORM=offscreen"
  ]
  ```

#### macOS Specific

**Problem:** Tests hang on macOS or require GUI access permissions.

**Solution:**
- Run tests with `pytest --no-qt-log` to reduce Qt logging
- Grant Terminal/IDE permissions in System Preferences > Security & Privacy

### Docker/Container Considerations

**Problem:** Qt tests fail in Docker containers.

**Solution:** Use offscreen rendering in containers:

```dockerfile
# Dockerfile
ENV QT_QPA_PLATFORM=offscreen
ENV QT_DEBUG_PLUGINS=0

RUN apt-get update && apt-get install -y \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxcb-shape0
```

### Slow Test Execution

**Problem:** Qt tests run slowly.

**Solution:**
- Reduce wait times: Use `qtbot.wait(10)` instead of longer waits
- Use `pytest-xdist` for parallel execution: `uv add --dev pytest-xdist`
- Run with: `pytest -n auto` (auto-detect CPU count)
- Be careful with GUI tests in parallel - may need serial execution

### Signal Timeout Errors

**Problem:** `SignalTimeoutError: Signal 'scroll_position_changed' not emitted after 1000 ms`

**Solution:**
1. Increase timeout if operation is legitimately slow:
   ```python
   with qtbot.waitSignal(signal, timeout=5000):  # 5 seconds
       slow_operation()
   ```

2. Check if signal is actually being emitted:
   ```python
   # Debug: manually verify signal emission
   received = []
   signal.connect(lambda: received.append(True))
   operation()
   qtbot.wait(100)
   assert received, "Signal was not emitted"
   ```

3. Ensure Qt event loop is running:
   ```python
   qtbot.wait(10)  # Process pending events before waiting for signal
   with qtbot.waitSignal(signal):
       operation()
   ```

### Flaky Tests

**Problem:** Tests pass sometimes but fail intermittently.

**Solution:**
- Add small waits before assertions: `qtbot.wait(10)`
- Use `qtbot.waitUntil()` for conditions:
  ```python
  qtbot.waitUntil(lambda: widget.isVisible(), timeout=1000)
  ```
- Avoid race conditions by waiting for signals instead of fixed delays
- Ensure proper widget initialization before testing

### Memory Leaks in Tests

**Problem:** Memory usage grows with each test run.

**Solution:**
- Ensure `qtbot.addWidget()` is used for all widgets
- Explicitly close windows in fixture teardown:
  ```python
  @pytest.fixture
  def window(qtbot):
      win = MainWindow()
      qtbot.addWidget(win)
      yield win
      win.close()  # Explicit cleanup
  ```
- Check for circular references in signal connections
- Use weak references for long-lived connections

### Qt Warnings Causing Test Failures

**Problem:** Qt warnings treated as errors with `qt_log_level_fail = "WARNING"`.

**Solution:**
1. Fix the warnings (preferred)
2. Temporarily allow specific warnings:
   ```python
   @pytest.mark.qt_log_ignore("QLayout: Attempting to add QLayout")
   def test_something(qtbot):
       pass
   ```
3. Adjust threshold in pyproject.toml:
   ```toml
   [tool.pytest.ini_options]
   qt_log_level_fail = "CRITICAL"  # Only fail on critical issues
   ```

### ImportError: No module named 'PyQt6.QtTest'

**Problem:** pytest-qt can't find Qt test module.

**Solution:**
- Ensure PyQt6 is fully installed: `uv add pyqt6`
- Verify Qt installation: `python -c "from PyQt6 import QtTest; print('OK')"`
- Reinstall if needed: `uv add --force-reinstall pyqt6 pytest-qt`

## Getting Help

If you encounter issues not covered here:

1. **Check pytest-qt documentation:** https://pytest-qt.readthedocs.io/
2. **Qt Test documentation:** https://doc.qt.io/qt-6/qtest-overview.html
3. **Search pytest-qt issues:** https://github.com/pytest-dev/pytest-qt/issues
4. **Enable debug output:** Run with `pytest -vv --qt-debug` for detailed Qt logs
