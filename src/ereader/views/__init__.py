"""
Views package - UI components.

This package contains:
- Main reader window
- Library view
- Settings dialogs
- UI widgets and helpers
"""

from ereader.views.book_viewer import BookViewer
from ereader.views.main_window import MainWindow
from ereader.views.navigation_bar import NavigationBar

__all__ = ["BookViewer", "MainWindow", "NavigationBar"]
