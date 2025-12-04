"""Main window for the e-reader application.

This module provides the top-level application window (QMainWindow) that serves
as the container for all UI components.
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from ereader.controllers.reader_controller import ReaderController
from ereader.views.book_viewer import BookViewer
from ereader.views.navigation_bar import NavigationBar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for the e-reader.

    This is the top-level window that contains the menu bar, status bar,
    and all other UI components. It serves as the primary user interface
    for the application.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        logger.debug("Initializing MainWindow")

        # Set window properties
        self.setWindowTitle("E-Reader")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Create controller
        self._controller = ReaderController()

        # Create UI components
        self._book_viewer = BookViewer(self)
        self._navigation_bar = NavigationBar(self)

        # Create central widget with layout
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self._book_viewer)
        layout.addWidget(self._navigation_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central_widget)

        # Setup UI
        self._setup_controller_connections()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_keyboard_shortcuts()

        logger.debug("MainWindow initialized successfully")

    def _setup_menu_bar(self) -> None:
        """Create and configure the menu bar."""
        logger.debug("Setting up menu bar")

        # Create File menu
        menu_bar = self.menuBar()
        if menu_bar is None:
            logger.error("Failed to get menu bar")
            return

        file_menu = menu_bar.addMenu("&File")

        # Add "Open" action
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an EPUB file")
        open_action.triggered.connect(self._handle_open_file)
        file_menu.addAction(open_action)

        # Add separator
        file_menu.addSeparator()

        # Add "Quit" action
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.setStatusTip("Exit the application")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        logger.debug("Menu bar setup complete")

    def _setup_status_bar(self) -> None:
        """Create and configure the status bar."""
        logger.debug("Setting up status bar")
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("Ready")
        logger.debug("Status bar setup complete")

    def _setup_controller_connections(self) -> None:
        """Connect controller signals to view slots."""
        logger.debug("Setting up controller signal connections")

        # Connect controller to main window
        self._controller.book_loaded.connect(self._on_book_loaded)
        self._controller.error_occurred.connect(self._on_error)
        self._controller.chapter_changed.connect(self._on_chapter_changed)
        self._controller.reading_progress_changed.connect(self._on_progress_changed)

        # Connect controller to book viewer
        self._controller.content_ready.connect(self._book_viewer.set_content)

        # Connect book viewer scroll events to controller
        self._book_viewer.scroll_position_changed.connect(self._controller.on_scroll_changed)

        # Connect controller to navigation bar
        self._controller.navigation_state_changed.connect(self._navigation_bar.update_buttons)

        # Connect navigation bar to controller
        self._navigation_bar.next_chapter_requested.connect(self._controller.next_chapter)
        self._navigation_bar.previous_chapter_requested.connect(self._controller.previous_chapter)

        logger.debug("Controller connections established")

    def _handle_open_file(self) -> None:
        """Handle File > Open menu action.

        Opens a file dialog to let the user select an EPUB file,
        then passes the selected file to the controller.
        """
        logger.debug("Opening file dialog")

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open EPUB File",
            "",  # Starting directory (empty = last used)
            "EPUB Files (*.epub);;All Files (*)",
        )

        if filepath:
            logger.info("User selected file: %s", filepath)
            self._controller.open_book(filepath)
        else:
            logger.debug("User cancelled file selection")

    def _on_book_loaded(self, title: str, author: str) -> None:
        """Handle book_loaded signal from controller.

        Updates the window title and status bar to show book information.

        Args:
            title: Book title.
            author: Book author(s).
        """
        logger.debug("Book loaded: %s by %s", title, author)

        # Update window title
        self.setWindowTitle(f"{title} - E-Reader")

        # Update status bar
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f"Opened: {title} by {author}")

    def _on_chapter_changed(self, current: int, total: int) -> None:
        """Handle chapter_changed signal from controller.

        Updates the status bar to show current chapter position.

        Args:
            current: Current chapter number (1-based).
            total: Total number of chapters.
        """
        logger.debug("Chapter changed: %d of %d", current, total)

        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f"Chapter {current} of {total}")

    def _on_error(self, title: str, message: str) -> None:
        """Handle error_occurred signal from controller.

        Displays an error dialog to the user.

        Args:
            title: Error dialog title.
            message: Error message to display.
        """
        logger.debug("Showing error dialog: %s - %s", title, message)
        QMessageBox.critical(self, title, message)

    def _on_progress_changed(self, progress: str) -> None:
        """Handle reading_progress_changed signal from controller.

        Updates the status bar with formatted progress string.

        Args:
            progress: Formatted progress string (e.g., "Chapter 3 of 15 • 45% through chapter").
        """
        logger.debug("Progress changed: %s", progress)

        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(progress)

    def _setup_keyboard_shortcuts(self) -> None:
        """Create and configure keyboard shortcuts for navigation."""
        logger.debug("Setting up keyboard shortcuts")

        # Chapter navigation (Left/Right arrows)
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(self._controller.previous_chapter)

        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(self._controller.next_chapter)

        # Within-chapter scrolling (Up/Down arrows - 50% viewport)
        up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        up_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(-0.5))

        down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        down_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(0.5))

        # Page scrolling (PageUp/PageDown - 100% viewport)
        page_up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        page_up_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(-1.0))

        page_down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        page_down_shortcut.activated.connect(lambda: self._book_viewer.scroll_by_pages(1.0))

        # Jump to top/bottom (Home/End)
        home_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Home), self)
        home_shortcut.activated.connect(self._book_viewer.scroll_to_top)

        end_shortcut = QShortcut(QKeySequence(Qt.Key.Key_End), self)
        end_shortcut.activated.connect(self._book_viewer.scroll_to_bottom)

        logger.debug("Keyboard shortcuts configured")
