"""Protocol interfaces for view components.

This module defines Protocol interfaces that allow different implementations
to be swapped without changing controller code. This follows the principle
of programming to interfaces rather than concrete implementations.
"""

from typing import Protocol


class BookRenderer(Protocol):
    """Protocol for widgets that can render book content.

    This protocol defines the interface between the controller and
    rendering widgets, allowing different implementations (QTextBrowser,
    QWebEngineView, etc.) to be swapped without changing controller code.

    Implementations must provide methods to display HTML content and clear
    the display. The protocol uses structural subtyping (PEP 544), so any
    class that implements these methods automatically satisfies the protocol.
    """

    def set_content(self, html: str) -> None:
        """Display HTML content in the renderer.

        Args:
            html: HTML content to display (XHTML from EPUB chapter).
        """
        ...

    def clear(self) -> None:
        """Clear all displayed content."""
        ...
