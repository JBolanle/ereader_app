"""Main window for the e-reader application.

This module provides the top-level application window (QMainWindow) that serves
as the container for all UI components.
"""

import logging

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from ereader.controllers.reader_controller import ReaderController
from ereader.models.theme import AVAILABLE_THEMES, DEFAULT_THEME, Theme
from ereader.views.book_viewer import BookViewer
from ereader.views.navigation_bar import NavigationBar
from ereader.views.shortcuts_dialog import ShortcutsDialog
from ereader.views.toast_widget import ToastWidget

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
        self.setGeometry(100, 100, 1100, 800)  # x, y, width, height (larger for comfortable reading)
        self.setMinimumSize(900, 700)  # Ensure minimum usable size

        # Initialize theme state
        self._current_theme: Theme = DEFAULT_THEME

        # Phase 2 UI components (lazy-loaded)
        self._shortcuts_dialog: ShortcutsDialog | None = None

        # Toast notification system
        self._toast_widget: ToastWidget | None = None
        self._toast_queue: list[tuple[str, str]] = []  # (message, icon)
        self._toast_active: bool = False

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

        # Load and apply saved theme preference
        self._load_theme_preference()

        logger.debug("MainWindow initialized successfully")

    def _setup_menu_bar(self) -> None:
        """Create and configure the menu bar."""
        logger.debug("Setting up menu bar")

        menu_bar = self.menuBar()
        if menu_bar is None:
            logger.error("Failed to get menu bar")
            return

        # Create File menu
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

        # Create View menu
        view_menu = menu_bar.addMenu("&View")

        # Create Theme submenu
        theme_menu = view_menu.addMenu("&Theme")

        # Create action group for radio button behavior
        theme_action_group = QActionGroup(self)
        theme_action_group.setExclusive(True)

        # Add theme actions
        for theme_id, theme in AVAILABLE_THEMES.items():
            theme_action = QAction(theme.name, self)
            theme_action.setCheckable(True)
            theme_action.setData(theme_id)  # Store theme ID for retrieval
            theme_action.triggered.connect(
                lambda checked, tid=theme_id: self._handle_theme_selection(tid)
            )
            theme_action_group.addAction(theme_action)
            theme_menu.addAction(theme_action)

            # Store action for later reference (to set checked state)
            if not hasattr(self, "_theme_actions"):
                self._theme_actions: dict[str, QAction] = {}
            self._theme_actions[theme_id] = theme_action

        # Create Help menu
        help_menu = menu_bar.addMenu("&Help")

        # Add "Keyboard Shortcuts" action
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.setStatusTip("Show keyboard shortcuts")
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)

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

        # Set book viewer reference in controller (needed for page navigation)
        self._controller._book_viewer = self._book_viewer

        # Connect controller to main window
        self._controller.book_loaded.connect(self._on_book_loaded)
        self._controller.error_occurred.connect(self._on_error)
        self._controller.chapter_changed.connect(self._on_chapter_changed)
        self._controller.reading_progress_changed.connect(self._on_progress_changed)
        self._controller.pagination_changed.connect(self._on_pagination_changed)
        self._controller.mode_changed.connect(self._on_mode_changed)  # Phase 2C

        # Connect controller to book viewer
        self._controller.content_ready.connect(self._book_viewer.set_content)
        self._controller.content_ready.connect(self._on_content_ready)

        # Connect book viewer scroll events to controller
        self._book_viewer.scroll_position_changed.connect(self._controller.on_scroll_changed)

        # Connect controller to navigation bar
        self._controller.navigation_state_changed.connect(self._navigation_bar.update_buttons)

        # Connect navigation bar to controller
        self._navigation_bar.next_chapter_requested.connect(self._controller.next_chapter)
        self._navigation_bar.previous_chapter_requested.connect(self._controller.previous_chapter)
        self._navigation_bar.mode_toggle_requested.connect(self._controller.toggle_navigation_mode)  # Phase 2C

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

        # Enable mode toggle button (Phase 2C)
        self._navigation_bar.enable_mode_toggle()

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

    def _on_pagination_changed(self, current_page: int, total_pages: int) -> None:
        """Handle pagination_changed signal from controller (Phase 2A).

        For now, just logs the pagination info. Progress display is handled
        by reading_progress_changed signal which formats based on current mode.

        Args:
            current_page: Current page number (1-indexed).
            total_pages: Total number of pages in current chapter.
        """
        logger.debug("Pagination changed: page %d of %d", current_page, total_pages)

    def _on_mode_changed(self, mode) -> None:
        """Handle mode_changed signal from controller (Phase 2C).

        Updates navigation bar button text based on new mode and shows
        a toast notification.

        Args:
            mode: New NavigationMode (SCROLL or PAGE).
        """
        from ereader.models.reading_position import NavigationMode

        logger.debug("Mode changed: %s", mode)
        self._navigation_bar.update_mode_button(mode)

        # Show toast notification for mode change
        if mode == NavigationMode.PAGE:
            self._show_toast("Switched to Page Mode", "📄")
        else:
            self._show_toast("Switched to Scroll Mode", "📜")

    def _on_content_ready(self, html: str) -> None:
        """Handle content_ready signal to trigger pagination calculation (Phase 2A/2B).

        When new content is loaded, we need to recalculate page breaks based
        on the rendered content dimensions.

        Args:
            html: HTML content (not used, but required by signal signature).
        """
        logger.debug("Content ready, triggering pagination recalculation")

        # Use a small delay to ensure content is fully rendered
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(
            50, lambda: self._controller._recalculate_pages(self._book_viewer)
        )

    def _setup_keyboard_shortcuts(self) -> None:
        """Create and configure keyboard shortcuts for navigation (Phase 2B/2C)."""
        logger.debug("Setting up keyboard shortcuts")

        # Left/Right arrows: Chapter navigation in scroll mode, page navigation in page mode
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(self._handle_left_key)

        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(self._handle_right_key)

        # Ctrl+M: Toggle navigation mode (Phase 2C)
        mode_toggle_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        mode_toggle_shortcut.activated.connect(self._controller.toggle_navigation_mode)

        # Within-chapter scrolling (Up/Down arrows - 50% viewport in scroll mode)
        # TODO Phase 2C: These will also check mode
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

    def _handle_left_key(self) -> None:
        """Handle left arrow key based on current navigation mode (Phase 2B)."""
        from ereader.models.reading_position import NavigationMode

        if self._controller._current_mode == NavigationMode.PAGE:
            self._controller.previous_page()
        else:
            self._controller.previous_chapter()

    def _handle_right_key(self) -> None:
        """Handle right arrow key based on current navigation mode (Phase 2B)."""
        from ereader.models.reading_position import NavigationMode

        if self._controller._current_mode == NavigationMode.PAGE:
            self._controller.next_page()
        else:
            self._controller.next_chapter()

    def _handle_theme_selection(self, theme_id: str) -> None:
        """Handle theme selection from View menu.

        Args:
            theme_id: ID of the selected theme (e.g., "light", "dark").
        """
        logger.debug("Theme selected: %s", theme_id)

        theme = AVAILABLE_THEMES.get(theme_id)
        if theme is None:
            logger.error("Invalid theme ID: %s", theme_id)
            return

        # Apply the theme
        self._apply_theme(theme)

        # Save preference
        self._save_theme_preference(theme_id)

    def _apply_theme(self, theme: Theme) -> None:
        """Apply a theme to all UI components.

        Args:
            theme: The theme to apply.
        """
        logger.debug("Applying theme: %s", theme.name)

        # Update current theme
        self._current_theme = theme

        # Apply global stylesheet to main window (includes menu bar, status bar, etc.)
        self.setStyleSheet(theme.get_global_stylesheet())

        # Apply to book viewer
        self._book_viewer.apply_theme(theme)

        # Apply to navigation bar
        self._navigation_bar.apply_theme(theme)

        logger.debug("Theme applied: %s", theme.name)

    def _load_theme_preference(self) -> None:
        """Load saved theme preference from QSettings and apply it."""
        logger.debug("Loading theme preference")

        settings = QSettings("EReader", "EReader")
        theme_id = settings.value("theme", "light")  # Default to "light"

        logger.debug("Loaded theme preference: %s", theme_id)

        theme = AVAILABLE_THEMES.get(theme_id, DEFAULT_THEME)
        self._apply_theme(theme)

        # Update menu checkboxes
        if hasattr(self, "_theme_actions") and theme_id in self._theme_actions:
            self._theme_actions[theme_id].setChecked(True)

    def _save_theme_preference(self, theme_id: str) -> None:
        """Save theme preference to QSettings.

        Args:
            theme_id: ID of the theme to save (e.g., "light", "dark").
        """
        logger.debug("Saving theme preference: %s", theme_id)

        settings = QSettings("EReader", "EReader")
        settings.setValue("theme", theme_id)

    def _show_shortcuts_dialog(self) -> None:
        """Show the keyboard shortcuts help dialog.

        Creates the dialog on first invocation and reuses it for
        subsequent calls.
        """
        logger.debug("Showing keyboard shortcuts dialog")

        if self._shortcuts_dialog is None:
            self._shortcuts_dialog = ShortcutsDialog(self)

        self._shortcuts_dialog.exec()

    def _show_toast(self, message: str, icon: str = "") -> None:
        """Show a toast notification or queue if one is already showing.

        Args:
            message: The message text to display.
            icon: Optional emoji icon to show before the message.
        """
        logger.debug("Toast requested: %s %s", icon, message)

        if self._toast_active:
            # Queue the toast if one is already showing
            self._toast_queue.append((message, icon))
            logger.debug("Toast queued (active toast in progress)")
        else:
            # Create toast widget on first use
            if self._toast_widget is None:
                self._toast_widget = ToastWidget(self)
                self._toast_widget.animation_complete.connect(self._on_toast_complete)

            # Show the toast
            self._toast_active = True
            self._toast_widget.show_message(message, icon)

    def _on_toast_complete(self) -> None:
        """Handle toast animation completion and show next queued toast if any."""
        logger.debug("Toast complete")
        self._toast_active = False

        # Check if there are queued toasts
        if self._toast_queue:
            message, icon = self._toast_queue.pop(0)
            logger.debug("Showing next queued toast")
            self._show_toast(message, icon)

        logger.debug("Theme preference saved")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle application close event (Phase 2D).

        Saves the current reading position before closing the application.

        Args:
            event: QCloseEvent from Qt.
        """
        logger.debug("Application closing, saving reading position")

        # Save current position if a book is loaded
        self._controller.save_current_position()

        # Accept the close event
        event.accept()
        logger.debug("Application closed")
