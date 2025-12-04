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
