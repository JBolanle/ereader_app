"""Toggle switch widget for mode selection.

This module provides a custom toggle switch widget that clearly indicates
state (on/off) versus action buttons. Used for navigation mode toggling.
"""

import logging

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFontMetrics, QKeyEvent, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ToggleSwitchWidget(QWidget):
    """Custom toggle switch widget for binary state selection.

    This widget displays a toggle switch with labels on both sides and
    a sliding handle that animates between two positions. It's designed
    to make state vs. action immediately clear to users.

    Visual design:
        Scroll  ◯──○  Page    (Scroll mode active)
        Scroll  ○──◯  Page    (Page mode active)

    Signals:
        toggled: Emitted when the switch is toggled (passes bool: True=checked).
    """

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        left_label: str = "Option A",
        right_label: str = "Option B",
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the toggle switch widget.

        Args:
            left_label: Label text for the left (unchecked) option.
            right_label: Label text for the right (checked) option.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        logger.debug("Initializing ToggleSwitchWidget: %s / %s", left_label, right_label)

        # State
        self._checked: bool = False  # False = left/unchecked, True = right/checked
        self._enabled: bool = True
        self._hovered: bool = False

        # Labels
        self._left_label: str = left_label
        self._right_label: str = right_label

        # Animation property (0.0 = left, 1.0 = right)
        self._handle_position: float = 0.0

        # Animation
        self._animation = QPropertyAnimation(self, b"handlePosition", self)
        self._animation.setDuration(200)  # 200ms as per spec
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Widget configuration
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(200, 40)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy()
        )

        logger.debug("ToggleSwitchWidget initialized")

    @pyqtProperty(float)
    def handlePosition(self) -> float:
        """Get the current handle position for animation.

        Returns:
            float: Handle position (0.0 = left, 1.0 = right).
        """
        return self._handle_position

    @handlePosition.setter
    def handlePosition(self, value: float) -> None:
        """Set the handle position for animation.

        Args:
            value: Handle position (0.0 = left, 1.0 = right).
        """
        self._handle_position = value
        self.update()  # Trigger repaint

    def isChecked(self) -> bool:
        """Check if the switch is in the checked (right) position.

        Returns:
            bool: True if checked (right position), False otherwise.
        """
        return self._checked

    def setChecked(self, checked: bool) -> None:
        """Set the switch checked state with animation.

        Args:
            checked: True to check (move to right), False to uncheck (move to left).
        """
        if self._checked == checked:
            return

        logger.debug("Setting toggle switch to %s", "checked" if checked else "unchecked")
        self._checked = checked

        # Animate handle to new position
        target_position = 1.0 if checked else 0.0
        self._animation.setStartValue(self._handle_position)
        self._animation.setEndValue(target_position)
        self._animation.start()

        # Emit signal
        self.toggled.emit(checked)

    def toggle(self) -> None:
        """Toggle the switch state."""
        self.setChecked(not self._checked)

    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the widget.

        Args:
            enabled: True to enable, False to disable.
        """
        self._enabled = enabled
        super().setEnabled(enabled)
        if not enabled:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to toggle the switch.

        Args:
            event: The mouse event.
        """
        if not self._enabled:
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            logger.debug("Toggle switch clicked")
            self.toggle()
            event.accept()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts for toggling.

        Supports:
        - Space/Enter: Toggle
        - Left Arrow: Set to unchecked (left)
        - Right Arrow: Set to checked (right)

        Args:
            event: The key press event.
        """
        if not self._enabled:
            event.ignore()
            return

        key = event.key()

        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            logger.debug("Toggle switch activated via keyboard (Space/Enter)")
            self.toggle()
            event.accept()
        elif key == Qt.Key.Key_Left:
            logger.debug("Toggle switch set to left via keyboard")
            self.setChecked(False)
            event.accept()
        elif key == Qt.Key.Key_Right:
            logger.debug("Toggle switch set to right via keyboard")
            self.setChecked(True)
            event.accept()
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event) -> None:
        """Handle mouse enter for hover state.

        Args:
            event: The enter event.
        """
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave for hover state.

        Args:
            event: The leave event.
        """
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        """Paint the toggle switch with custom drawing.

        Draws:
        - Track (rounded rectangle background)
        - Handle (circular thumb that slides)
        - Labels (text on left and right)

        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get colors from parent theme (navigation bar theme)
        # We'll use a simpler approach: extract from stylesheet or use defaults
        if self._enabled:
            text_color = self.palette().color(self.palette().ColorRole.WindowText)
            accent_color = QColor("#8B7355")  # Default accent from LIGHT_THEME
            border_color = QColor("#E8E3DD")  # Default border
            bg_color = self.palette().color(self.palette().ColorRole.Window)
        else:
            # Disabled state: greyscale
            text_color = QColor("#999999")
            accent_color = QColor("#CCCCCC")
            border_color = QColor("#DDDDDD")
            bg_color = self.palette().color(self.palette().ColorRole.Window)

        # Dimensions
        width = self.width()
        height = self.height()

        # Track dimensions (centered, pill-shaped)
        track_width = 80
        track_height = 28
        track_x = (width - track_width) / 2
        track_y = (height - track_height) / 2
        track_rect = QRectF(track_x, track_y, track_width, track_height)

        # Handle dimensions (circular)
        handle_radius = 10
        handle_y = height / 2
        # Animate handle position from left to right
        handle_x_left = track_x + handle_radius + 4
        handle_x_right = track_x + track_width - handle_radius - 4
        handle_x = handle_x_left + (handle_x_right - handle_x_left) * self._handle_position

        # Hover effect: scale handle slightly
        if self._hovered and self._enabled:
            handle_radius = int(handle_radius * 1.1)

        # Draw track
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(track_rect, track_height / 2, track_height / 2)

        # Draw handle
        if self._enabled:
            painter.setBrush(accent_color)
            painter.setPen(QPen(accent_color, 1))
        else:
            painter.setBrush(QColor("#CCCCCC"))
            painter.setPen(QPen(QColor("#CCCCCC"), 1))
        painter.drawEllipse(
            int(handle_x - handle_radius),
            int(handle_y - handle_radius),
            handle_radius * 2,
            handle_radius * 2
        )

        # Draw labels
        font = painter.font()
        font.setPixelSize(13)
        painter.setFont(font)

        font_metrics = QFontMetrics(font)

        # Left label
        left_text_width = font_metrics.horizontalAdvance(self._left_label)
        left_text_x = track_x - left_text_width - 12
        left_text_y = height / 2 + font_metrics.ascent() / 2

        # Right label
        right_text_x = track_x + track_width + 12
        right_text_y = height / 2 + font_metrics.ascent() / 2

        # Highlight active label with accent color
        if not self._checked:
            # Left label is active (bold and accent color)
            painter.setPen(accent_color if self._enabled else text_color)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(int(left_text_x), int(left_text_y), self._left_label)

            # Right label is inactive (normal color)
            painter.setPen(text_color)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(int(right_text_x), int(right_text_y), self._right_label)
        else:
            # Left label is inactive
            painter.setPen(text_color)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(int(left_text_x), int(left_text_y), self._left_label)

            # Right label is active (bold and accent color)
            painter.setPen(accent_color if self._enabled else text_color)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(int(right_text_x), int(right_text_y), self._right_label)

        # Draw focus indicator if focused
        if self.hasFocus():
            painter.setPen(QPen(accent_color, 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(2, 2, width - 4, height - 4, 4, 4)

        painter.end()
