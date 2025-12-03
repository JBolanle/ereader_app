"""Navigation bar widget for chapter navigation.

This module provides the NavigationBar widget with Previous/Next buttons
and keyboard shortcuts for navigating between chapters.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

logger = logging.getLogger(__name__)


class NavigationBar(QWidget):
    """Navigation bar with Previous/Next chapter buttons.

    This widget provides UI controls for navigating between book chapters.
    It emits signals when the user requests navigation and responds to
    signals about navigation state (e.g., disable Previous at first chapter).

    Signals:
        next_chapter_requested: Emitted when user wants to go to next chapter.
        previous_chapter_requested: Emitted when user wants to go to previous chapter.
    """

    # Signals for navigation requests
    next_chapter_requested = pyqtSignal()
    previous_chapter_requested = pyqtSignal()

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

        # Configure buttons
        self._previous_button.setToolTip("Go to previous chapter (Left Arrow)")
        self._next_button.setToolTip("Go to next chapter (Right Arrow)")

        # Initially disable both (no book loaded)
        self._previous_button.setEnabled(False)
        self._next_button.setEnabled(False)

        # Connect button signals
        self._previous_button.clicked.connect(self._on_previous_clicked)
        self._next_button.clicked.connect(self._on_next_clicked)

        # Setup layout
        layout = QHBoxLayout(self)
        layout.addStretch()  # Push buttons to center
        layout.addWidget(self._previous_button)
        layout.addWidget(self._next_button)
        layout.addStretch()  # Push buttons to center
        layout.setContentsMargins(10, 5, 10, 5)

        logger.debug("NavigationBar initialized")

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

    def keyPressEvent(self, event) -> None:
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
