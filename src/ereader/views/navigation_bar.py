"""Navigation bar widget for chapter navigation.

This module provides the NavigationBar widget with Previous/Next buttons
and keyboard shortcuts for navigating between chapters.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ereader.models.theme import DEFAULT_THEME, Theme

logger = logging.getLogger(__name__)


class NavigationBar(QWidget):
    """Navigation bar with Previous/Next chapter buttons and mode toggle.

    This widget provides UI controls for navigating between book chapters
    and toggling between scroll and page navigation modes.
    It emits signals when the user requests navigation and responds to
    signals about navigation state (e.g., disable Previous at first chapter).

    Signals:
        next_chapter_requested: Emitted when user wants to go to next chapter.
        previous_chapter_requested: Emitted when user wants to go to previous chapter.
        mode_toggle_requested: Emitted when user wants to toggle navigation mode.
    """

    # Signals for navigation requests
    next_chapter_requested = pyqtSignal()
    previous_chapter_requested = pyqtSignal()
    mode_toggle_requested = pyqtSignal()  # Phase 2C

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the navigation bar.

        Args:
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing NavigationBar")

        # Create buttons
        self._previous_button = QPushButton("Previous", self)
        self._next_button = QPushButton("Next", self)
        self._mode_toggle_button = QPushButton("Page Mode", self)  # Phase 2C

        # Configure buttons
        self._previous_button.setToolTip("Go to previous chapter (Left Arrow)")
        self._next_button.setToolTip("Go to next chapter (Right Arrow)")
        self._mode_toggle_button.setToolTip("Toggle between scroll and page modes (Ctrl+M)")

        # Initially disable navigation buttons (no book loaded)
        self._previous_button.setEnabled(False)
        self._next_button.setEnabled(False)
        self._mode_toggle_button.setEnabled(False)  # Disabled until book is loaded

        # Connect button signals
        self._previous_button.clicked.connect(self._on_previous_clicked)
        self._next_button.clicked.connect(self._on_next_clicked)
        self._mode_toggle_button.clicked.connect(self._on_mode_toggle_clicked)

        # Setup layout
        layout = QHBoxLayout(self)
        layout.addWidget(self._mode_toggle_button)  # Left side: mode toggle
        layout.addStretch()  # Push navigation buttons to center
        layout.addWidget(self._previous_button)
        layout.addSpacing(12)  # Space between buttons
        layout.addWidget(self._next_button)
        layout.addStretch()  # Push buttons to center
        layout.setContentsMargins(20, 10, 20, 10)  # More generous padding

        # Set minimum height for navigation bar
        self.setMinimumHeight(52)

        # Apply default theme
        self.apply_theme(DEFAULT_THEME)

        logger.debug("NavigationBar initialized")

    def apply_theme(self, theme: Theme) -> None:
        """Apply a visual theme to the navigation bar.

        This method updates the stylesheet to use the colors and styling
        defined in the provided theme.

        Args:
            theme: The theme to apply.
        """
        logger.debug("Applying theme to navigation bar: %s", theme.name)
        self.setStyleSheet(theme.get_navigation_bar_stylesheet())
        logger.debug("Theme applied to navigation bar: %s", theme.name)

    def update_buttons(self, can_go_back: bool, can_go_forward: bool) -> None:
        """Update navigation button enabled/disabled state.

        This slot receives signals from the controller about whether
        navigation is possible in each direction.

        Args:
            can_go_back: Whether navigation to previous chapter is possible.
            can_go_forward: Whether navigation to next chapter is possible.
        """
        logger.debug("Updating buttons: back=%s, forward=%s", can_go_back, can_go_forward)
        self._previous_button.setEnabled(can_go_back)
        self._next_button.setEnabled(can_go_forward)

    def update_mode_button(self, mode) -> None:
        """Update mode toggle button to show current mode (Phase 2C).

        Button displays the CURRENT mode with an icon, and tooltip indicates
        the mode that will be activated on click (the opposite mode).

        Args:
            mode: Current NavigationMode (SCROLL or PAGE).
        """
        from ereader.models.reading_position import NavigationMode

        if mode == NavigationMode.PAGE:
            self._mode_toggle_button.setText("📄 Page Mode")
            self._mode_toggle_button.setToolTip("Switch to scroll mode (Ctrl+M)")
            logger.debug("Mode button updated: Page Mode (current)")
        else:  # SCROLL mode
            self._mode_toggle_button.setText("📜 Scroll Mode")
            self._mode_toggle_button.setToolTip("Switch to page mode (Ctrl+M)")
            logger.debug("Mode button updated: Scroll Mode (current)")

        # Update navigation button labels to match mode
        self.update_button_labels(mode)

    def update_button_labels(self, mode) -> None:
        """Update navigation button labels based on current mode.

        Changes button text and tooltips to clearly indicate whether
        buttons will navigate by page or by chapter.

        Args:
            mode: Current NavigationMode (SCROLL or PAGE).
        """
        from ereader.models.reading_position import NavigationMode

        if mode == NavigationMode.PAGE:
            self._previous_button.setText("← Page")
            self._next_button.setText("Page →")
            self._previous_button.setToolTip("Go to previous page (Left Arrow)")
            self._next_button.setToolTip("Go to next page (Right Arrow)")
            logger.debug("Button labels updated for PAGE mode")
        else:  # SCROLL mode
            self._previous_button.setText("← Chapter")
            self._next_button.setText("Chapter →")
            self._previous_button.setToolTip("Go to previous chapter (Left Arrow)")
            self._next_button.setToolTip("Go to next chapter (Right Arrow)")
            logger.debug("Button labels updated for SCROLL mode")

    def enable_mode_toggle(self) -> None:
        """Enable the mode toggle button (Phase 2C).

        Called when a book is loaded to enable mode switching.
        """
        logger.debug("Enabling mode toggle button")
        self._mode_toggle_button.setEnabled(True)

    def _on_previous_clicked(self) -> None:
        """Handle Previous button click.

        Emits the previous_chapter_requested signal.
        """
        logger.debug("Previous button clicked")
        self.previous_chapter_requested.emit()

    def _on_next_clicked(self) -> None:
        """Handle Next button click.

        Emits the next_chapter_requested signal.
        """
        logger.debug("Next button clicked")
        self.next_chapter_requested.emit()

    def _on_mode_toggle_clicked(self) -> None:
        """Handle mode toggle button click (Phase 2C).

        Emits the mode_toggle_requested signal.
        """
        logger.debug("Mode toggle button clicked")
        self.mode_toggle_requested.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts for navigation.

        Supports:
        - Left Arrow / Page Up: Previous chapter
        - Right Arrow / Page Down: Next chapter

        Args:
            event: The key press event.
        """
        key = event.key()

        if key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            if self._previous_button.isEnabled():
                logger.debug("Left/PageUp key pressed, navigating to previous")
                self.previous_chapter_requested.emit()
            event.accept()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            if self._next_button.isEnabled():
                logger.debug("Right/PageDown key pressed, navigating to next")
                self.next_chapter_requested.emit()
            event.accept()
        else:
            # Let parent handle other keys
            super().keyPressEvent(event)
