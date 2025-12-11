"""Toast notification widget for transient user feedback.

This module provides a ToastWidget that displays brief, non-intrusive notifications
to the user. Toasts fade in, hold for a short duration, and fade out automatically.
"""

import logging

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class ToastWidget(QWidget):
    """Transient notification widget with automatic fade in/out.

    Visual design:
        ┌────────────────────────┐
        │  📜 Switched to Scroll │
        └────────────────────────┘

    Animation sequence:
    1. Fade in: 250ms (0 → 1.0 opacity)
    2. Hold: 2000ms at full opacity
    3. Fade out: 500ms (1.0 → 0 opacity)
    4. Auto-hide when complete

    Signals:
        animation_complete: Emitted when toast animation finishes.
    """

    animation_complete = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        """Initialize the toast widget.

        Args:
            parent: Parent widget (typically MainWindow).
        """
        super().__init__(parent)
        logger.debug("Initializing ToastWidget")

        # Widget setup
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 70)

        # Create label for message
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
            }
        """
        )

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.setContentsMargins(0, 0, 0, 0)

        # Opacity effect for fading
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        # Animation state
        self._animation_group: QSequentialAnimationGroup | None = None

        # Initially hidden
        self.hide()

        logger.debug("ToastWidget initialized")

    def show_message(self, message: str, icon: str = "") -> None:
        """Show toast with message and optional icon.

        Args:
            message: The message text to display.
            icon: Optional emoji icon to show before the message.
        """
        logger.debug("Showing toast: %s %s", icon, message)

        # Set message text
        display_text = f"{icon}  {message}" if icon else message
        self._label.setText(display_text)

        # Position toast in bottom-right corner of parent
        self._position_toast()

        # Show widget and start animation
        self.show()
        self.raise_()  # Bring to front
        self._start_animation_sequence()

    def _position_toast(self) -> None:
        """Position toast in bottom-right corner of parent with margin."""
        if self.parent():
            parent_rect = self.parent().rect()
            margin = 20

            x = parent_rect.width() - self.width() - margin
            y = parent_rect.height() - self.height() - margin - 30  # Extra space for status bar

            self.move(x, y)
            logger.debug("Toast positioned at (%d, %d)", x, y)

    def _start_animation_sequence(self) -> None:
        """Run fade-in → hold → fade-out → hide sequence."""
        # Stop any existing animation
        if self._animation_group and self._animation_group.state() == QPropertyAnimation.State.Running:
            self._animation_group.stop()

        # Create animation sequence
        self._animation_group = QSequentialAnimationGroup(self)

        # 1. Fade in (250ms)
        fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_in.setDuration(250)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(0.95)  # Slightly transparent
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation_group.addAnimation(fade_in)

        # 2. Hold (2000ms) - use a pause animation
        hold = QPropertyAnimation(self._opacity_effect, b"opacity")
        hold.setDuration(2000)
        hold.setStartValue(0.95)
        hold.setEndValue(0.95)
        self._animation_group.addAnimation(hold)

        # 3. Fade out (500ms)
        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(0.95)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation_group.addAnimation(fade_out)

        # Connect completion signal
        self._animation_group.finished.connect(self._on_animation_complete)

        # Start the sequence
        self._animation_group.start()
        logger.debug("Toast animation sequence started")

    def _on_animation_complete(self) -> None:
        """Handle animation completion - hide widget and emit signal."""
        logger.debug("Toast animation complete")
        self.hide()
        self.animation_complete.emit()

    def paintEvent(self, event) -> None:
        """Paint the toast background with rounded corners.

        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw semi-transparent rounded background
        painter.setBrush(QColor(60, 60, 60, 230))  # Dark gray, mostly opaque
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
