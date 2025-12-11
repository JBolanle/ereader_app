"""Tests for the toast notification widget."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from ereader.views.toast_widget import ToastWidget


@pytest.fixture
def parent_widget(qtbot):
    """Create a parent widget for the toast."""
    widget = QWidget()
    widget.resize(800, 600)
    qtbot.addWidget(widget)
    widget.show()
    return widget


@pytest.fixture
def toast(qtbot, parent_widget):
    """Create a ToastWidget for testing."""
    toast = ToastWidget(parent_widget)
    qtbot.addWidget(toast)
    return toast


def test_toast_creation(toast):
    """Test that toast widget is created with correct properties."""
    assert toast is not None
    assert toast.width() == 320
    assert toast.height() == 70
    assert not toast.isVisible()  # Initially hidden


def test_show_message(toast, qtbot):
    """Test that toast appears when show_message is called."""
    toast.show_message("Test message")

    # Toast should be visible
    assert toast.isVisible()
    assert "Test message" in toast._label.text()


def test_show_message_with_icon(toast, qtbot):
    """Test that toast displays message with icon."""
    toast.show_message("Test message", "📄")

    assert toast.isVisible()
    label_text = toast._label.text()
    assert "📄" in label_text
    assert "Test message" in label_text


def test_toast_positioning(toast, parent_widget, qtbot):
    """Test that toast is positioned in bottom-right corner."""
    toast.show_message("Test")

    # Toast should be in bottom-right area of parent
    parent_rect = parent_widget.rect()
    toast_pos = toast.pos()

    # X position should be near right edge (within some margin)
    expected_x = parent_rect.width() - toast.width() - 20
    assert abs(toast_pos.x() - expected_x) < 50  # Allow some tolerance

    # Y position should be near bottom
    assert toast_pos.y() > parent_rect.height() / 2


def test_animation_sequence(toast, qtbot):
    """Test that toast animation completes and hides widget."""
    # Show toast
    toast.show_message("Test")
    assert toast.isVisible()

    # Wait for animation to complete
    with qtbot.waitSignal(toast.animation_complete, timeout=4000):
        pass

    # Toast should be hidden after animation
    qtbot.wait(100)  # Small delay for hide to take effect
    assert not toast.isVisible()


def test_animation_complete_signal(toast, qtbot):
    """Test that animation_complete signal is emitted."""
    signal_emitted = False

    def on_complete():
        nonlocal signal_emitted
        signal_emitted = True

    toast.animation_complete.connect(on_complete)

    toast.show_message("Test")

    # Wait for signal
    with qtbot.waitSignal(toast.animation_complete, timeout=4000):
        pass

    assert signal_emitted


def test_opacity_animation(toast, qtbot):
    """Test that opacity changes during animation."""
    toast.show_message("Test")

    # Initially, opacity should be increasing (fade in)
    qtbot.wait(100)
    initial_opacity = toast._opacity_effect.opacity()
    assert initial_opacity > 0.0

    # After fade in, opacity should be high
    qtbot.wait(300)
    high_opacity = toast._opacity_effect.opacity()
    assert high_opacity > 0.8


def test_multiple_toasts_via_queue(parent_widget, qtbot):
    """Test that multiple toasts can be queued through parent."""
    # Create main window mock with toast queue system
    toast1 = ToastWidget(parent_widget)
    toast2 = ToastWidget(parent_widget)
    qtbot.addWidget(toast1)
    qtbot.addWidget(toast2)

    # Show first toast
    toast1.show_message("First toast")
    assert toast1.isVisible()

    # Wait for first to complete
    with qtbot.waitSignal(toast1.animation_complete, timeout=4000):
        pass

    # Show second toast after first completes
    toast2.show_message("Second toast")
    assert toast2.isVisible()

    # Wait for second to complete
    with qtbot.waitSignal(toast2.animation_complete, timeout=4000):
        pass


def test_toast_text_content(toast):
    """Test that toast displays correct text content."""
    message = "Mode switched successfully"
    icon = "✓"

    toast.show_message(message, icon)

    label_text = toast._label.text()
    assert message in label_text
    assert icon in label_text


def test_toast_stays_on_top(toast, parent_widget, qtbot):
    """Test that toast has stay-on-top window flags."""
    flags = toast.windowFlags()
    assert Qt.WindowType.WindowStaysOnTopHint in flags
    assert Qt.WindowType.FramelessWindowHint in flags


def test_toast_translucent_background(toast):
    """Test that toast has translucent background attribute."""
    assert toast.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_animation_duration(toast, qtbot):
    """Test that toast animation takes approximately correct duration."""
    import time

    start_time = time.time()
    toast.show_message("Test")

    # Wait for animation to complete
    with qtbot.waitSignal(toast.animation_complete, timeout=4000):
        pass

    end_time = time.time()
    duration = end_time - start_time

    # Should be approximately 2.75 seconds (250ms + 2000ms + 500ms)
    assert 2.5 < duration < 3.2  # Allow some tolerance
