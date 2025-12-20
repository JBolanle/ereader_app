"""Tests for LibraryView drag-and-drop functionality."""

from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent

from ereader.views.library_view import LibraryView


@pytest.fixture
def mock_repository():
    """Create a mock LibraryRepository."""
    mock_repo = MagicMock()
    mock_repo.filter_books.return_value = []
    return mock_repo


@pytest.fixture
def library_view(qtbot, mock_repository):
    """Create a LibraryView for testing."""
    view = LibraryView(mock_repository)
    qtbot.addWidget(view)
    return view


@pytest.fixture
def drag_overlay(qtbot, library_view):
    """Get the DragDropOverlay from LibraryView."""
    return library_view._drag_overlay


class TestDragDropOverlay:
    """Tests for DragDropOverlay widget."""

    def test_overlay_initialization(self, drag_overlay):
        """Test that overlay is created with correct properties."""
        assert drag_overlay is not None
        assert not drag_overlay.isVisible()  # Initially hidden

    def test_overlay_styling(self, drag_overlay):
        """Test that overlay has correct styling."""
        # Check that stylesheet contains expected properties
        stylesheet = drag_overlay.styleSheet()
        assert "background-color" in stylesheet
        assert "rgba" in stylesheet or "128" in stylesheet  # Semi-transparent


class TestLibraryViewDragDrop:
    """Tests for LibraryView drag-and-drop functionality."""

    def test_drag_drop_enabled(self, library_view):
        """Test that drag-and-drop is enabled."""
        assert library_view.acceptDrops()

    def test_drag_enter_with_local_files(self, library_view, qtbot):
        """Test drag enter event with local file URLs."""
        # Show library view so overlay can become visible
        library_view.show()
        qtbot.wait(50)

        # Create MIME data with local file URL
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("/path/to/book.epub")])

        # Create drag enter event
        event = QDragEnterEvent(
            QPoint(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Trigger event
        library_view.dragEnterEvent(event)
        qtbot.wait(10)  # Small wait for Qt to process show()

        # Overlay should be shown
        assert library_view._drag_overlay.isVisible()
        # Event should be accepted
        assert event.isAccepted()

    def test_drag_enter_with_non_local_urls(self, library_view, qtbot):
        """Test drag enter event with non-local URLs (http://)."""
        # Create MIME data with http URL
        mime_data = QMimeData()
        mime_data.setUrls([QUrl("http://example.com/book.epub")])

        # Create drag enter event
        event = QDragEnterEvent(
            QPoint(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Trigger event
        library_view.dragEnterEvent(event)

        # Overlay should NOT be shown
        assert not library_view._drag_overlay.isVisible()
        # Event should be ignored
        assert not event.isAccepted()

    def test_drag_enter_without_urls(self, library_view, qtbot):
        """Test drag enter event without URLs in MIME data."""
        # Create MIME data without URLs
        mime_data = QMimeData()
        mime_data.setText("Some text")

        # Create drag enter event
        event = QDragEnterEvent(
            QPoint(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Trigger event
        library_view.dragEnterEvent(event)

        # Overlay should NOT be shown
        assert not library_view._drag_overlay.isVisible()
        # Event should be ignored
        assert not event.isAccepted()

    def test_drag_move(self, library_view, qtbot):
        """Test drag move event with URLs."""
        # Create MIME data with local file URL
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("/path/to/book.epub")])

        # Create drag move event
        event = QDragMoveEvent(
            QPoint(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Trigger event
        library_view.dragMoveEvent(event)

        # Event should be accepted
        assert event.isAccepted()

    def test_drag_leave(self, library_view, qtbot):
        """Test drag leave event hides overlay."""
        # Show library view so overlay can become visible
        library_view.show()
        qtbot.wait(50)

        # First show overlay with drag enter
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("/path/to/book.epub")])

        enter_event = QDragEnterEvent(
            QPoint(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        library_view.dragEnterEvent(enter_event)
        qtbot.wait(10)  # Wait for show() to process
        assert library_view._drag_overlay.isVisible()

        # Now trigger drag leave
        leave_event = QDragLeaveEvent()
        library_view.dragLeaveEvent(leave_event)
        qtbot.wait(10)  # Wait for hide() to process

        # Overlay should be hidden
        assert not library_view._drag_overlay.isVisible()

    def test_drop_event_emits_signal(self, library_view, qtbot):
        """Test drop event emits files_dropped signal with correct paths."""
        # Create MIME data with local file URLs
        mime_data = QMimeData()
        mime_data.setUrls([
            QUrl.fromLocalFile("/path/to/book1.epub"),
            QUrl.fromLocalFile("/path/to/book2.epub"),
        ])

        # Create drop event (PyQt6 expects QPointF)
        event = QDropEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Connect signal and verify emission
        with qtbot.waitSignal(library_view.files_dropped, timeout=1000) as blocker:
            library_view.dropEvent(event)

        # Verify signal emitted with correct file paths
        emitted_paths = blocker.args[0]
        assert len(emitted_paths) == 2
        assert "/path/to/book1.epub" in emitted_paths
        assert "/path/to/book2.epub" in emitted_paths

    def test_drop_event_hides_overlay(self, library_view, qtbot):
        """Test drop event hides the overlay."""
        # Show library view so overlay can become visible
        library_view.show()
        qtbot.wait(50)

        # Show overlay first
        library_view._drag_overlay.show()
        qtbot.wait(10)
        assert library_view._drag_overlay.isVisible()

        # Create MIME data with local file URL
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("/path/to/book.epub")])

        # Create drop event (PyQt6 expects QPointF)
        event = QDropEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Trigger event
        library_view.dropEvent(event)
        qtbot.wait(10)

        # Overlay should be hidden
        assert not library_view._drag_overlay.isVisible()

    def test_drop_event_with_non_local_files(self, library_view, qtbot):
        """Test drop event with non-local URLs."""
        # Create MIME data with http URL
        mime_data = QMimeData()
        mime_data.setUrls([QUrl("http://example.com/book.epub")])

        # Create drop event (PyQt6 expects QPointF)
        event = QDropEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Drop event should be ignored (no signal emitted)
        # We can't use waitSignal here because it will timeout if no signal emitted
        signal_emitted = False

        def on_signal(paths):
            nonlocal signal_emitted
            signal_emitted = True

        library_view.files_dropped.connect(on_signal)
        library_view.dropEvent(event)

        # Signal should NOT be emitted
        qtbot.wait(100)  # Small wait to ensure no signal
        assert not signal_emitted

    def test_drop_event_filters_local_files_only(self, library_view, qtbot):
        """Test drop event with mixed local and non-local URLs."""
        # Create MIME data with mixed URLs
        mime_data = QMimeData()
        mime_data.setUrls([
            QUrl.fromLocalFile("/path/to/book1.epub"),
            QUrl("http://example.com/book2.epub"),
            QUrl.fromLocalFile("/path/to/book3.epub"),
        ])

        # Create drop event (PyQt6 expects QPointF)
        event = QDropEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Connect signal and verify emission
        with qtbot.waitSignal(library_view.files_dropped, timeout=1000) as blocker:
            library_view.dropEvent(event)

        # Verify only local files emitted
        emitted_paths = blocker.args[0]
        assert len(emitted_paths) == 2
        assert "/path/to/book1.epub" in emitted_paths
        assert "/path/to/book3.epub" in emitted_paths

    def test_resize_event_updates_overlay(self, library_view, qtbot):
        """Test that resizing window updates overlay geometry."""
        # Show the widget first
        library_view.show()
        qtbot.wait(50)

        # Resize library view
        library_view.resize(1000, 800)
        qtbot.waitUntil(
            lambda: library_view._drag_overlay.geometry() == library_view.rect(),
            timeout=500,
        )

        # Overlay geometry should match library view
        assert library_view._drag_overlay.geometry() == library_view.rect()

        # Resize again
        library_view.resize(1200, 900)
        qtbot.waitUntil(
            lambda: library_view._drag_overlay.geometry() == library_view.rect(),
            timeout=500,
        )

        # Overlay should update again
        assert library_view._drag_overlay.geometry() == library_view.rect()
