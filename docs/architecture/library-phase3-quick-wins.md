# Library Phase 3 Quick Wins Architecture

## Date
2025-12-15

## Context

Phase 3 of the library management system adds polish and advanced features. This document covers the architecture for the first three "quick win" features:

1. **Context menus** - Right-click on books for quick actions
2. **Book details dialog** - View comprehensive book information
3. **Remove from library** - Delete books with confirmation

These features integrate with the existing library system (Phase 1 & 2) which includes:
- LibraryRepository for database operations
- LibraryController for state management
- BookGridWidget for displaying books
- MainWindow with ToastWidget for notifications

### UX Requirements

Full UX design is documented in the conversation history. Key requirements:
- Context menu with actions: Open, Book Details, Mark as [Status], Remove from Library
- Book details dialog showing metadata, file info, reading progress, library info
- Remove confirmation dialog with option to delete file (destructive action)
- Toast notifications for success/error feedback

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ MainWindow                                                      │
│                                                                 │
│  ┌──────────────────┐          ┌────────────────────────────┐  │
│  │ BookGridWidget   │          │ LibraryController          │  │
│  │                  │          │                            │  │
│  │ • Context Menu   │──signals→│ • remove_book()            │  │
│  │ • Action Signals │          │ • update_book_status()     │  │
│  └──────────────────┘          │ • get_book_by_id()         │  │
│          │                     └────────────────────────────┘  │
│          │ signals                         │                   │
│          ↓                                 ↓                   │
│  ┌──────────────────┐          ┌────────────────────────────┐  │
│  │ Dialogs          │          │ LibraryRepository          │  │
│  │                  │          │                            │  │
│  │ • BookDetails    │          │ • delete_book()            │  │
│  │ • RemoveBook     │          │ • update_book()            │  │
│  └──────────────────┘          │ • get_book_by_id()         │  │
│                                └────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │ ToastWidget      │←─── success/error feedback               │
│  └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Designs

### 1. Context Menu (BookGridWidget Extension)

**Location:** Modify `src/ereader/views/book_grid_widget.py`

**Changes:**
- Override `contextMenuEvent(event)` to show context menu
- Create QMenu with actions dynamically based on book status
- Emit granular signals for each action

**New Signals:**
```python
# In BookGridWidget class
book_details_requested = pyqtSignal(int)  # book_id
book_status_update_requested = pyqtSignal(int, str)  # book_id, new_status
book_remove_requested = pyqtSignal(int)  # book_id
```

**Implementation Pattern:**
```python
def contextMenuEvent(self, event: QContextMenuEvent) -> None:
    """Show context menu on right-click."""
    # Get book at cursor position
    index = self.indexAt(event.pos())
    if not index.isValid():
        return

    book = self._model.get_book(index)
    if not book:
        return

    # Create menu
    menu = QMenu(self)

    # Add actions
    open_action = menu.addAction("Open")
    menu.addSeparator()
    details_action = menu.addAction("Book Details...")
    menu.addSeparator()

    # Dynamic status actions (show only statuses != current)
    status_menu = menu.addMenu("Mark as...")
    # Add status actions based on book.status

    menu.addSeparator()
    remove_action = menu.addAction("Remove from Library...")

    # Show menu and handle selection
    action = menu.exec(event.globalPos())

    if action == open_action:
        self.book_activated.emit(book.id)
    elif action == details_action:
        self.book_details_requested.emit(book.id)
    elif action == remove_action:
        self.book_remove_requested.emit(book.id)
    # ... handle status actions
```

**Decision:** Context menu created and shown in BookGridWidget
- **Rationale:** Follows Qt conventions, keeps menu definition close to widget, cleaner separation of concerns
- **Alternative:** Emit signal and have MainWindow create menu - rejected as more complex

### 2. Book Details Dialog

**Location:** New file `src/ereader/views/book_details_dialog.py`

**Class Design:**
```python
class BookDetailsDialog(QDialog):
    """Modal dialog displaying comprehensive book information.

    Shows read-only book metadata, file information, reading progress,
    and library information in a structured layout.

    This dialog is non-modal for reading view, modal for library view.
    """

    def __init__(self, book: BookMetadata, parent=None) -> None:
        """Initialize book details dialog.

        Args:
            book: BookMetadata to display.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        self.setWindowTitle("Book Details")
        self.setMinimumSize(500, 600)

        self._book = book
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI layout."""
        # Main layout
        layout = QVBoxLayout(self)

        # Header section (cover + title/author)
        # File information section
        # Reading progress section
        # Library information section
        # OK button

    def _format_file_size(self, size_bytes: int | None) -> str:
        """Format file size in human-readable format."""
        # MB/KB formatting

    def _format_datetime(self, dt: datetime | None) -> str:
        """Format datetime in user-friendly format."""
        # "December 14, 2025 at 3:42 PM"
```

**UI Sections:**

1. **Header** (QHBoxLayout):
   - Left: Cover image (QLabel with QPixmap, 150×200px)
   - Right: Title (large QLabel), Author, Genre/Pages (small QLabel)

2. **File Information** (QGroupBox):
   - Location: Full file path
   - Size: Formatted MB/KB
   - Format: "EPUB"

3. **Reading Progress** (QGroupBox):
   - Progress bar (QProgressBar) + percentage
   - Pages read / total (calculated from progress)
   - Current chapter name
   - Status badge

4. **Library Information** (QGroupBox):
   - Added date
   - Last opened (with time, or "Never")
   - Collections (comma-separated list, or "None")

5. **Actions**:
   - OK button (bottom-right)

**State Handling:**
- Missing file: Show warning icon "⚠️ File not found at location"
- Never opened: "Last Opened: Never"
- No collections: "Collections: None"
- No author: "Author: Unknown"

### 3. Remove Book Confirmation Dialog

**Location:** New file `src/ereader/views/remove_book_dialog.py`

**Enum for Result:**
```python
from enum import Enum

class RemoveBookResult(Enum):
    """Result of remove book dialog."""
    CANCEL = 0
    REMOVE_ONLY = 1
    REMOVE_AND_DELETE = 2
```

**Class Design:**
```python
class RemoveBookDialog(QDialog):
    """Confirmation dialog for removing books from library.

    Provides two options:
    1. Remove from library only (safe - keeps file on disk)
    2. Remove from library AND delete file (destructive)

    Uses double confirmation for file deletion.
    """

    def __init__(self, book: BookMetadata, parent=None) -> None:
        """Initialize remove book dialog.

        Args:
            book: BookMetadata of book to remove.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        self.setWindowTitle("Remove Book from Library?")
        self.setMinimumWidth(500)

        self._book = book
        self._result = RemoveBookResult.CANCEL
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI layout."""
        # Main layout
        # Title + author display
        # Explanation text
        # Checkbox: "Also delete file from disk (permanent)"
        # File path display
        # Buttons: Cancel, Remove/Delete (text changes based on checkbox)

    def _on_checkbox_changed(self, state: Qt.CheckState) -> None:
        """Handle checkbox state change - update button text/style."""
        if state == Qt.CheckState.Checked:
            self._remove_button.setText("Delete Book and File")
            self._remove_button.setStyleSheet("background-color: #d32f2f; color: white;")
        else:
            self._remove_button.setText("Remove from Library")
            self._remove_button.setStyleSheet("")

    def _on_remove_clicked(self) -> None:
        """Handle remove/delete button click."""
        if self._delete_checkbox.isChecked():
            # Show second confirmation for destructive action
            reply = QMessageBox.warning(
                self,
                "⚠️ Delete Book and File?",
                f"This will PERMANENTLY DELETE the file:\n\n{self._book.file_path}\n\n"
                "This action cannot be undone.\n"
                "The book will be removed from your library and the file will be deleted from your disk.",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Ok:
                self._result = RemoveBookResult.REMOVE_AND_DELETE
                self.accept()
        else:
            self._result = RemoveBookResult.REMOVE_ONLY
            self.accept()

    def get_result(self) -> RemoveBookResult:
        """Get dialog result after exec()."""
        return self._result
```

**Decision:** Use enum return value instead of bool
- **Rationale:** Supports three-way choice (cancel/remove/delete), clearer semantics, more maintainable
- **Alternative:** Multiple bools - rejected as ambiguous

### 4. LibraryController Extensions

**Location:** Modify `src/ereader/controllers/library_controller.py`

**New Methods:**
```python
def get_book_by_id(self, book_id: int) -> BookMetadata | None:
    """Get book metadata by ID.

    Args:
        book_id: Database ID of book.

    Returns:
        BookMetadata if found, None otherwise.
    """
    try:
        return self._repository.get_book_by_id(book_id)
    except DatabaseError as e:
        logger.error("Failed to get book %d: %s", book_id, e)
        return None

def remove_book(self, book_id: int, delete_file: bool = False) -> None:
    """Remove book from library, optionally deleting file.

    Args:
        book_id: Database ID of book to remove.
        delete_file: If True, also delete the EPUB file from disk.

    Emits:
        book_removed: On successful removal (book_id, deleted_file).
        book_remove_failed: On failure (book_id, error_message).
    """
    logger.debug("Removing book %d (delete_file=%s)", book_id, delete_file)

    try:
        # Get book metadata before deletion (for file path)
        book = self._repository.get_book_by_id(book_id)
        if not book:
            raise DatabaseError(f"Book not found: {book_id}")

        # Delete from database
        self._repository.delete_book(book_id)

        # Delete file if requested
        file_deleted = False
        if delete_file:
            try:
                file_path = Path(book.file_path)
                if file_path.exists():
                    file_path.unlink()
                    file_deleted = True
                    logger.info("Deleted file: %s", file_path)
                else:
                    logger.warning("File not found: %s", file_path)
            except OSError as e:
                # File deletion failed, but database record is already gone
                error_msg = f"Failed to delete file: {e}"
                logger.error(error_msg)
                self.book_remove_failed.emit(book_id, error_msg)
                return

        # Emit success signal
        self.book_removed.emit(book_id, file_deleted)
        logger.info("Book %d removed successfully", book_id)

    except DatabaseError as e:
        error_msg = f"Failed to remove book: {e}"
        logger.error(error_msg)
        self.book_remove_failed.emit(book_id, error_msg)

    except Exception as e:
        error_msg = f"Unexpected error removing book: {e}"
        logger.exception(error_msg)
        self.book_remove_failed.emit(book_id, error_msg)

def update_book_status(self, book_id: int, new_status: str) -> None:
    """Update book reading status.

    Args:
        book_id: Database ID of book.
        new_status: New status ("not_started", "reading", or "finished").

    Emits:
        book_status_updated: On success (book_id, status).
        error_occurred: On failure.
    """
    logger.debug("Updating book %d status to: %s", book_id, new_status)

    try:
        # Validate status
        valid_statuses = ["not_started", "reading", "finished"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        # Update in database
        self._repository.update_book(book_id, {"status": new_status})

        # Emit success signal
        self.book_status_updated.emit(book_id, new_status)
        logger.info("Book %d status updated to: %s", book_id, new_status)

    except (DatabaseError, ValueError) as e:
        error_msg = f"Failed to update book status: {e}"
        logger.error(error_msg)
        self.error_occurred.emit("Update Error", error_msg)
```

**New Signals:**
```python
# In LibraryController class
book_removed = pyqtSignal(int, bool)  # book_id, file_deleted
book_remove_failed = pyqtSignal(int, str)  # book_id, error_message
book_status_updated = pyqtSignal(int, str)  # book_id, new_status
```

**Decision:** File deletion logic in Controller, not Repository
- **Rationale:** Repository should only handle database operations, file I/O is business logic
- **Alternative:** File deletion in Repository - rejected as mixing concerns

### 5. LibraryRepository Extensions

**Location:** Modify `src/ereader/models/library_database.py`

**New Method:**
```python
def get_book_by_id(self, book_id: int) -> BookMetadata | None:
    """Get a single book by database ID.

    Args:
        book_id: Database ID of book.

    Returns:
        BookMetadata if found, None if not found.

    Raises:
        DatabaseError: If database operation fails.
    """
    logger.debug("Getting book by ID: %d", book_id)

    try:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, title, author, file_path, cover_path, added_date,
                   last_opened_date, reading_progress, current_chapter_index,
                   scroll_position, status, file_size
            FROM books
            WHERE id = ?
            """,
            (book_id,),
        )

        row = cursor.fetchone()
        if not row:
            logger.debug("Book not found: %d", book_id)
            return None

        return self._row_to_book_metadata(row)

    except sqlite3.Error as e:
        error_msg = f"Failed to get book: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg) from e
```

**Note:** The `delete_book()` method already exists (line 511), so we'll reuse it.

### 6. MainWindow Integration

**Location:** Modify `src/ereader/views/main_window.py`

**New Signal Connections:**
```python
# In __init__ after library_view creation
if self._library_view:
    # Connect context menu signals from BookGridWidget
    grid = self._library_view._grid_widget
    grid.book_details_requested.connect(self._on_book_details_requested)
    grid.book_status_update_requested.connect(self._on_book_status_update_requested)
    grid.book_remove_requested.connect(self._on_book_remove_requested)

    # Connect LibraryController signals
    self._library_controller.book_removed.connect(self._on_book_removed)
    self._library_controller.book_remove_failed.connect(self._on_book_remove_failed)
    self._library_controller.book_status_updated.connect(self._on_book_status_updated)
```

**New Slot Methods:**
```python
def _on_book_details_requested(self, book_id: int) -> None:
    """Show book details dialog."""
    book = self._library_controller.get_book_by_id(book_id)
    if not book:
        self._show_toast("⚠️ Book not found", "error")
        return

    from ereader.views.book_details_dialog import BookDetailsDialog
    dialog = BookDetailsDialog(book, self)
    dialog.exec()

def _on_book_status_update_requested(self, book_id: int, new_status: str) -> None:
    """Update book reading status."""
    self._library_controller.update_book_status(book_id, new_status)

def _on_book_remove_requested(self, book_id: int) -> None:
    """Show remove book confirmation dialog."""
    book = self._library_controller.get_book_by_id(book_id)
    if not book:
        self._show_toast("⚠️ Book not found", "error")
        return

    from ereader.views.remove_book_dialog import RemoveBookDialog, RemoveBookResult
    dialog = RemoveBookDialog(book, self)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        result = dialog.get_result()

        if result == RemoveBookResult.REMOVE_ONLY:
            self._library_controller.remove_book(book_id, delete_file=False)
        elif result == RemoveBookResult.REMOVE_AND_DELETE:
            self._library_controller.remove_book(book_id, delete_file=True)

def _on_book_removed(self, book_id: int, file_deleted: bool) -> None:
    """Handle successful book removal."""
    if file_deleted:
        self._show_toast("✓ Book and file deleted", "success")
    else:
        self._show_toast("✓ Book removed from library", "success")

    # Reload library to refresh grid
    self._library_controller.load_library()

def _on_book_remove_failed(self, book_id: int, error_message: str) -> None:
    """Handle book removal failure."""
    self._show_toast(f"⚠️ Failed to remove book: {error_message}", "error")

def _on_book_status_updated(self, book_id: int, new_status: str) -> None:
    """Handle successful status update."""
    status_labels = {
        "not_started": "Not Started",
        "reading": "Reading",
        "finished": "Finished"
    }
    label = status_labels.get(new_status, new_status)
    self._show_toast(f"✓ Marked as {label}", "success")

    # Reload library to refresh grid
    self._library_controller.load_library()
```

## Signal Flow Diagrams

### Context Menu → Book Details

```
User right-clicks book
    ↓
BookGridWidget.contextMenuEvent()
    ↓
User clicks "Book Details..."
    ↓
BookGridWidget.book_details_requested(book_id)
    ↓
MainWindow._on_book_details_requested(book_id)
    ↓
LibraryController.get_book_by_id(book_id) → BookMetadata
    ↓
BookDetailsDialog(book_metadata).exec()
    ↓
User views info and clicks OK
```

### Context Menu → Mark as Status

```
User right-clicks book
    ↓
BookGridWidget.contextMenuEvent()
    ↓
User clicks "Mark as Reading"
    ↓
BookGridWidget.book_status_update_requested(book_id, "reading")
    ↓
MainWindow._on_book_status_update_requested(book_id, status)
    ↓
LibraryController.update_book_status(book_id, status)
    ↓
Repository.update_book(book_id, {"status": status})
    ↓
LibraryController.book_status_updated(book_id, status)
    ↓
MainWindow._on_book_status_updated()
    ↓
Show toast "✓ Marked as Reading"
    ↓
Reload library (refresh grid)
```

### Context Menu → Remove Book

```
User right-clicks book
    ↓
BookGridWidget.contextMenuEvent()
    ↓
User clicks "Remove from Library..."
    ↓
BookGridWidget.book_remove_requested(book_id)
    ↓
MainWindow._on_book_remove_requested(book_id)
    ↓
LibraryController.get_book_by_id(book_id) → BookMetadata
    ↓
RemoveBookDialog(book_metadata).exec()
    ↓
User checks "Also delete file" and clicks "Delete Book and File"
    ↓
Double confirmation dialog shown
    ↓
User confirms
    ↓
Dialog returns REMOVE_AND_DELETE
    ↓
MainWindow calls LibraryController.remove_book(book_id, delete_file=True)
    ↓
LibraryController:
  - Gets book file_path
  - Calls Repository.delete_book(book_id)
  - Deletes file from disk
  - Emits book_removed(book_id, True)
    ↓
MainWindow._on_book_removed(book_id, file_deleted=True)
    ↓
Show toast "✓ Book and file deleted"
    ↓
Reload library (refresh grid)
```

## Implementation Order

### Phase 1: Foundation (Low Risk)
1. **Add LibraryRepository.get_book_by_id()** - Simple query, well-tested pattern
2. **Add BookDetailsDialog** - Self-contained, no side effects, easy to test
3. **Add signals to BookGridWidget** - Just signal definitions, no behavior yet

### Phase 2: Core Features (Medium Risk)
4. **Implement context menu in BookGridWidget** - UI only, emits signals
5. **Add LibraryController methods** (remove_book, update_book_status, get_book_by_id)
6. **Connect book details in MainWindow** - Wire up dialog to signals

### Phase 3: Destructive Actions (Higher Risk)
7. **Add RemoveBookDialog** - Complex state management, double confirmation
8. **Connect remove book in MainWindow** - Wire up dialog to controller
9. **Test remove functionality** - Verify database deletion, file deletion, error handling

### Phase 4: Polish
10. **Add "Mark as Status" actions to context menu** - Dynamic menu items
11. **Connect status updates in MainWindow** - Wire up to controller
12. **Handle all error states** - File not found, permission denied, etc.

## Testing Strategy

### Unit Tests

**BookDetailsDialog:**
- `test_dialog_displays_book_info` - All fields shown correctly
- `test_dialog_formats_dates` - Date formatting works
- `test_dialog_formats_file_size` - MB/KB formatting works
- `test_dialog_handles_missing_data` - Null/None values handled

**RemoveBookDialog:**
- `test_dialog_default_state` - Checkbox unchecked, button "Remove from Library"
- `test_dialog_checkbox_changes_button` - Button text/style updates
- `test_dialog_cancel` - Returns CANCEL result
- `test_dialog_remove_only` - Returns REMOVE_ONLY result
- `test_dialog_remove_and_delete` - Shows confirmation, returns REMOVE_AND_DELETE
- `test_dialog_remove_and_delete_cancelled` - User cancels second confirmation

**LibraryController:**
- `test_get_book_by_id_success` - Returns book
- `test_get_book_by_id_not_found` - Returns None
- `test_remove_book_database_only` - Deletes from DB, doesn't touch file
- `test_remove_book_with_file` - Deletes from DB and file
- `test_remove_book_file_missing` - Handles missing file gracefully
- `test_remove_book_file_permission_denied` - Emits error signal
- `test_update_book_status_success` - Updates status, emits signal
- `test_update_book_status_invalid` - Rejects invalid status

**BookGridWidget:**
- `test_context_menu_shows` - Right-click shows menu
- `test_context_menu_actions` - Actions emit correct signals
- `test_context_menu_dynamic_status` - Status actions based on current status

### Integration Tests

**End-to-End Flows:**
- `test_book_details_flow` - Right-click → Details → View → Close
- `test_remove_book_only_flow` - Right-click → Remove → Confirm → Success toast
- `test_remove_book_and_file_flow` - Right-click → Remove → Check box → Double confirm → Success toast
- `test_update_status_flow` - Right-click → Mark as Reading → Success toast

### Manual Testing

**Context Menu:**
- Right-click on various books
- Verify menu appears at cursor
- Verify status actions are dynamic (only show statuses != current)
- Test keyboard navigation in menu

**Book Details:**
- Open dialog for various books (with/without author, covers, collections)
- Verify all fields display correctly
- Verify date/time formatting
- Verify file size formatting
- Test with missing file (warning shown)

**Remove Confirmation:**
- Test remove only (file kept on disk)
- Test remove + delete (file deleted)
- Test double confirmation for file deletion
- Test canceling at each stage
- Test with missing file (checkbox hidden)
- Test with permission denied (error handled)

## Error Handling

### Repository Errors
- **Book not found**: Return None from `get_book_by_id()`, let controller handle
- **Database locked**: Raise DatabaseError, caught by controller
- **Delete fails**: Raise DatabaseError, emit error signal

### Controller Errors
- **Book not found**: Emit `error_occurred` signal
- **File deletion fails**: Emit `book_remove_failed` signal with details
- **Invalid status**: Catch ValueError, emit `error_occurred`

### Dialog Errors
- **File missing**: Show warning icon in details dialog
- **File missing on remove**: Hide "delete file" checkbox

### MainWindow Error Display
- **All errors**: Show toast with error icon and message
- **Critical errors**: Show QMessageBox in addition to toast

## Performance Considerations

### Dialog Performance
- **Book details**: O(1) - Single book lookup, minimal rendering
- **Remove confirmation**: O(1) - Simple dialog, no heavy operations

### Context Menu
- **Creation**: O(1) - Menu created on-demand, lightweight
- **Dynamic actions**: O(1) - 3-4 status options max

### File Operations
- **Delete file**: Potentially slow for large files, but rare operation
- **Future**: Could show progress bar for large files (> 50MB)

## Security Considerations

### File Deletion
- **Double confirmation** - Prevents accidental deletion
- **Full path shown** - User sees exactly what will be deleted
- **No wildcards** - Only deletes specific file, not directories
- **Error handling** - Permission denied handled gracefully

### SQL Injection
- All queries use parameterized statements (existing pattern)
- No new injection vectors introduced

## Future Enhancements (Out of Scope)

These were considered but deferred to future phases:

1. **Batch operations** - Remove multiple books at once
2. **Undo remove** - Restore recently removed books (would need soft delete)
3. **Edit metadata** - Make book details dialog editable
4. **Cover image editing** - Upload custom covers
5. **Collection management from context menu** - Add/remove from collections
6. **Advanced confirmations** - Remember "don't ask again" preferences

## Open Questions

None - all design decisions made and documented.

## Implementation Guidance

### For Developers

1. **Start with foundation** - Get `get_book_by_id()` and `BookDetailsDialog` working first
2. **Test thoroughly** - These features modify/delete data, bugs are costly
3. **Follow signal patterns** - Use granular signals, not generic action signals
4. **Use type hints** - Especially for dialog return values (RemoveBookResult enum)
5. **Log everything** - File deletions, status updates, errors

### Code Style

- Follow existing patterns in `library_view.py` and `library_controller.py`
- Use Google-style docstrings for all new classes and methods
- Add type hints to all function signatures
- Use logging, not print statements
- Keep dialog classes self-contained (minimal dependencies)

### Testing Requirements

- Minimum 90% coverage for new code
- All dialog states must have tests
- All error paths must have tests
- Integration tests for complete flows

## Decision Summary

| Decision | Chosen Option | Rationale |
|----------|---------------|-----------|
| Context menu location | In BookGridWidget | Follows Qt conventions, cleaner separation |
| Signal granularity | Granular signals per action | Type-safe, self-documenting, easier to maintain |
| Dialog return value | Enum (RemoveBookResult) | Clearer semantics, supports three-way choice |
| File deletion logic | In LibraryController | Repository handles DB only, controller handles business logic |
| Error feedback | Toast notifications | Consistent with existing app patterns |
| Double confirmation | Yes, for file deletion | Prevents accidental data loss |

## Consequences

### Enables
- Quick access to common book actions
- Comprehensive book information viewing
- Safe book removal with optional file deletion
- Clear user feedback for all actions

### Constrains
- Context menu limited to single book (no batch operations yet)
- Book details read-only (editing in future phase)
- File deletion is permanent (no undo)

### Watch Out For
- File deletion permission errors (need clear error messages)
- Large file deletion (might appear to hang - future: add progress bar)
- Concurrent modifications (refresh library after operations)
- Memory leaks (properly clean up dialogs)

## Related Documents

- **UX Design**: Conversation history (2025-12-15)
- **Library Phase 1**: `docs/specs/library-management-system.md`
- **Library Phase 2**: `docs/architecture/library-phase2-organization.md`
- **Toast Notifications**: `src/ereader/views/toast_widget.py`

---

**Next Step:** Proceed with implementation using `/developer`, following the implementation order outlined above.
