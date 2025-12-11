"""Tests for the keyboard shortcuts help dialog."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialogButtonBox, QPushButton

from ereader.views.shortcuts_dialog import SHORTCUTS_DATA, ShortcutsDialog


@pytest.fixture
def dialog(qtbot):
    """Create a ShortcutsDialog for testing."""
    dialog = ShortcutsDialog()
    qtbot.addWidget(dialog)
    return dialog


def test_dialog_creation(dialog):
    """Test that dialog is created with correct properties."""
    assert dialog.windowTitle() == "Keyboard Shortcuts"
    assert dialog.isModal()
    assert dialog.width() == 550
    assert dialog.height() == 650


def test_all_categories_present(dialog):
    """Test that all shortcut categories are displayed."""
    expected_categories = ["Navigation", "Chapters", "View", "File", "Help"]

    for category in expected_categories:
        # Find group box with this category name
        group_boxes = dialog.findChildren(type(dialog.layout().itemAt(1).widget()))
        category_names = [gb.title() for gb in group_boxes]
        assert category in category_names, f"Category '{category}' not found in dialog"


def test_shortcuts_data_populated(dialog):
    """Test that shortcuts are populated from SHORTCUTS_DATA."""
    # Verify navigation shortcuts are present
    navigation_shortcuts = SHORTCUTS_DATA["Navigation"]
    assert len(navigation_shortcuts) > 0

    # Check that expected shortcuts exist in data
    shortcuts_text = {shortcut for shortcut, _ in navigation_shortcuts}
    assert "Left/Right Arrow" in shortcuts_text
    assert "Page Up/Down" in shortcuts_text


def test_close_button_exists(dialog):
    """Test that Close button is present and functional."""
    close_buttons = dialog.findChildren(QPushButton)
    close_button = None

    for button in close_buttons:
        if button.text() == "Close":
            close_button = button
            break

    assert close_button is not None
    assert close_button.isDefault()  # Should be default button (Enter to close)


def test_close_button_dismisses_dialog(dialog, qtbot):
    """Test that clicking Close button dismisses the dialog."""
    # Find close button
    close_buttons = dialog.findChildren(QPushButton)
    close_button = None

    for button in close_buttons:
        if button.text() == "Close":
            close_button = button
            break

    assert close_button is not None

    # Show dialog (non-blocking for test)
    dialog.show()
    qtbot.waitForWindowShown(dialog)

    # Click close button
    with qtbot.waitSignal(dialog.finished, timeout=1000):
        close_button.click()

    # Dialog should be closed
    assert not dialog.isVisible()


def test_escape_key_dismisses_dialog(dialog, qtbot):
    """Test that Escape key dismisses the dialog."""
    # Show dialog
    dialog.show()
    qtbot.waitForWindowShown(dialog)

    # Press Escape key
    with qtbot.waitSignal(dialog.finished, timeout=1000):
        qtbot.keyPress(dialog, Qt.Key.Key_Escape)

    # Dialog should be closed
    assert not dialog.isVisible()


def test_dialog_reuse(qtbot):
    """Test that dialog can be opened, closed, and reopened."""
    dialog = ShortcutsDialog()
    qtbot.addWidget(dialog)

    # First open
    dialog.show()
    qtbot.waitForWindowShown(dialog)
    assert dialog.isVisible()

    # Close
    dialog.reject()
    qtbot.wait(100)
    assert not dialog.isVisible()

    # Reopen
    dialog.show()
    qtbot.waitForWindowShown(dialog)
    assert dialog.isVisible()

    # Close again
    dialog.accept()
    qtbot.wait(100)
    assert not dialog.isVisible()


def test_shortcuts_data_structure():
    """Test that SHORTCUTS_DATA has correct structure."""
    assert isinstance(SHORTCUTS_DATA, dict)
    assert len(SHORTCUTS_DATA) > 0

    for category, shortcuts in SHORTCUTS_DATA.items():
        assert isinstance(category, str)
        assert isinstance(shortcuts, list)
        assert len(shortcuts) > 0

        for item in shortcuts:
            assert isinstance(item, tuple)
            assert len(item) == 2
            shortcut, action = item
            assert isinstance(shortcut, str)
            assert isinstance(action, str)
            assert len(shortcut) > 0
            assert len(action) > 0


def test_all_shortcuts_documented():
    """Test that key shortcuts from the app are documented."""
    # Expected shortcuts that should be in the dialog
    expected_shortcuts = [
        "Ctrl+O",  # Open file
        "Ctrl+Q",  # Quit
        "Ctrl+M",  # Toggle mode
        "Ctrl+T",  # Toggle theme
        "F1",  # Show shortcuts
        "Left/Right Arrow",  # Navigation
        "Page Up/Down",  # Page navigation
    ]

    # Flatten all shortcuts from SHORTCUTS_DATA
    all_shortcuts = []
    for shortcuts_list in SHORTCUTS_DATA.values():
        for shortcut, _ in shortcuts_list:
            all_shortcuts.append(shortcut)

    # Check that expected shortcuts are present
    for expected in expected_shortcuts:
        assert any(
            expected in shortcut for shortcut in all_shortcuts
        ), f"Shortcut '{expected}' not found in shortcuts dialog"
