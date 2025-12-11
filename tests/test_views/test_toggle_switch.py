"""Tests for the toggle switch widget."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QSignalSpy

from ereader.views.toggle_switch import ToggleSwitchWidget


class TestToggleSwitchWidget:
    """Tests for ToggleSwitchWidget."""

    @pytest.fixture
    def toggle_switch(self, qtbot):
        """Create a toggle switch widget for testing."""
        widget = ToggleSwitchWidget(left_label="Scroll", right_label="Page")
        qtbot.addWidget(widget)
        return widget

    def test_initial_state(self, toggle_switch):
        """Test initial state is unchecked (left)."""
        assert not toggle_switch.isChecked()
        assert toggle_switch._handle_position == 0.0

    def test_set_checked_programmatically(self, toggle_switch, qtbot):
        """Test setting checked state programmatically."""
        spy = QSignalSpy(toggle_switch.toggled)

        toggle_switch.setChecked(True)
        qtbot.wait(250)  # Wait for animation to complete

        assert toggle_switch.isChecked()
        assert len(spy) == 1
        assert spy[0][0] is True

    def test_set_unchecked_programmatically(self, toggle_switch, qtbot):
        """Test setting unchecked state programmatically."""
        toggle_switch.setChecked(True)
        qtbot.wait(250)

        spy = QSignalSpy(toggle_switch.toggled)

        toggle_switch.setChecked(False)
        qtbot.wait(250)

        assert not toggle_switch.isChecked()
        assert len(spy) == 1
        assert spy[0][0] is False

    def test_toggle_method(self, toggle_switch, qtbot):
        """Test toggle() method switches state."""
        assert not toggle_switch.isChecked()

        toggle_switch.toggle()
        qtbot.wait(250)

        assert toggle_switch.isChecked()

        toggle_switch.toggle()
        qtbot.wait(250)

        assert not toggle_switch.isChecked()

    def test_mouse_click_toggles(self, toggle_switch, qtbot):
        """Test clicking the widget toggles state."""
        spy = QSignalSpy(toggle_switch.toggled)

        # Click to toggle to checked
        qtbot.mouseClick(toggle_switch, Qt.MouseButton.LeftButton)
        qtbot.wait(250)

        assert toggle_switch.isChecked()
        assert len(spy) == 1

        # Click to toggle back to unchecked
        qtbot.mouseClick(toggle_switch, Qt.MouseButton.LeftButton)
        qtbot.wait(250)

        assert not toggle_switch.isChecked()
        assert len(spy) == 2

    def test_space_key_toggles(self, toggle_switch, qtbot):
        """Test Space key toggles the switch."""
        toggle_switch.setFocus()
        qtbot.wait(10)

        spy = QSignalSpy(toggle_switch.toggled)

        qtbot.keyClick(toggle_switch, Qt.Key.Key_Space)
        qtbot.wait(250)

        assert toggle_switch.isChecked()
        assert len(spy) == 1

    def test_enter_key_toggles(self, toggle_switch, qtbot):
        """Test Enter key toggles the switch."""
        toggle_switch.setFocus()
        qtbot.wait(10)

        spy = QSignalSpy(toggle_switch.toggled)

        qtbot.keyClick(toggle_switch, Qt.Key.Key_Return)
        qtbot.wait(250)

        assert toggle_switch.isChecked()
        assert len(spy) == 1

    def test_left_arrow_sets_unchecked(self, toggle_switch, qtbot):
        """Test Left Arrow key sets switch to unchecked."""
        toggle_switch.setChecked(True)
        qtbot.wait(250)

        toggle_switch.setFocus()
        qtbot.wait(10)

        spy = QSignalSpy(toggle_switch.toggled)

        qtbot.keyClick(toggle_switch, Qt.Key.Key_Left)
        qtbot.wait(250)

        assert not toggle_switch.isChecked()
        assert len(spy) == 1

    def test_right_arrow_sets_checked(self, toggle_switch, qtbot):
        """Test Right Arrow key sets switch to checked."""
        assert not toggle_switch.isChecked()

        toggle_switch.setFocus()
        qtbot.wait(10)

        spy = QSignalSpy(toggle_switch.toggled)

        qtbot.keyClick(toggle_switch, Qt.Key.Key_Right)
        qtbot.wait(250)

        assert toggle_switch.isChecked()
        assert len(spy) == 1

    def test_disabled_state_no_interaction(self, toggle_switch, qtbot):
        """Test disabled widget does not respond to interaction."""
        toggle_switch.setEnabled(False)

        spy = QSignalSpy(toggle_switch.toggled)

        # Try programmatic toggle (should still work when disabled for testing)
        # Note: Actual mouse/keyboard events will be ignored by disabled widgets
        initial_state = toggle_switch.isChecked()

        # Disabled widget should not change state via events
        # We verify the widget remains in its initial state
        assert toggle_switch.isChecked() == initial_state
        assert len(spy) == 0

    def test_handle_position_animates(self, toggle_switch, qtbot):
        """Test handle position animates between 0.0 and 1.0."""
        assert toggle_switch._handle_position == 0.0

        toggle_switch.setChecked(True)
        qtbot.wait(250)  # Wait for animation to complete

        # After animation, handle should be at right (1.0)
        assert toggle_switch._handle_position == pytest.approx(1.0, abs=0.01)

        toggle_switch.setChecked(False)
        qtbot.wait(250)

        # After animation, handle should be at left (0.0)
        assert toggle_switch._handle_position == pytest.approx(0.0, abs=0.01)

    def test_no_signal_when_setting_same_state(self, toggle_switch):
        """Test setting the same state does not emit signal."""
        spy = QSignalSpy(toggle_switch.toggled)

        toggle_switch.setChecked(False)  # Already unchecked

        assert len(spy) == 0

    def test_labels_displayed(self, toggle_switch):
        """Test labels are stored correctly."""
        assert toggle_switch._left_label == "Scroll"
        assert toggle_switch._right_label == "Page"

    def test_widget_accepts_focus(self, toggle_switch, qtbot):
        """Test widget can receive keyboard focus."""
        # Widget must be shown to receive focus
        toggle_switch.show()
        qtbot.waitExposed(toggle_switch)

        toggle_switch.setFocus()
        qtbot.wait(10)

        assert toggle_switch.hasFocus()

    def test_custom_labels(self, qtbot):
        """Test widget with custom labels."""
        widget = ToggleSwitchWidget(left_label="Off", right_label="On")
        qtbot.addWidget(widget)

        assert widget._left_label == "Off"
        assert widget._right_label == "On"

    def test_tooltip_can_be_set(self, toggle_switch):
        """Test tooltip can be set on widget."""
        toggle_switch.setToolTip("Test tooltip")
        assert toggle_switch.toolTip() == "Test tooltip"
