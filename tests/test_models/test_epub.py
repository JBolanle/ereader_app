"""Tests for EPUBBook class."""

import zipfile
from pathlib import Path

import pytest

from ereader.exceptions import InvalidEPUBError
from ereader.models.epub import EPUBBook


class TestEPUBBookInit:
    """Test EPUBBook initialization and validation."""

    def test_init_with_valid_epub(self, tmp_path: Path) -> None:
        """Test initialization with a valid EPUB file (ZIP archive)."""
        # Create a minimal valid EPUB (ZIP with container.xml)
        epub_file = tmp_path / "test.epub"
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", "<?xml version='1.0'?>")

        book = EPUBBook(epub_file)
        assert book.filepath == epub_file

    def test_init_with_string_path(self, tmp_path: Path) -> None:
        """Test initialization with a string path (not Path object)."""
        epub_file = tmp_path / "test.epub"
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", "<?xml version='1.0'?>")

        # Pass string instead of Path object
        book = EPUBBook(str(epub_file))
        assert book.filepath == epub_file

    def test_init_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test initialization with a file that doesn't exist."""
        nonexistent_file = tmp_path / "does_not_exist.epub"

        with pytest.raises(FileNotFoundError) as exc_info:
            EPUBBook(nonexistent_file)

        assert "not found" in str(exc_info.value).lower()

    def test_init_with_directory(self, tmp_path: Path) -> None:
        """Test initialization with a directory path instead of a file."""
        directory = tmp_path / "not_a_file"
        directory.mkdir()

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(directory)

        assert "not a file" in str(exc_info.value).lower()

    def test_init_with_non_zip_file(self, tmp_path: Path) -> None:
        """Test initialization with a non-ZIP file."""
        text_file = tmp_path / "not_an_epub.epub"
        text_file.write_text("This is just a text file, not a ZIP archive")

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(text_file)

        assert "not a valid" in str(exc_info.value).lower()
        assert "zip" in str(exc_info.value).lower()

    def test_init_with_empty_file(self, tmp_path: Path) -> None:
        """Test initialization with an empty file."""
        empty_file = tmp_path / "empty.epub"
        empty_file.touch()

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(empty_file)

        assert "not a valid" in str(exc_info.value).lower()

    def test_init_with_special_characters_in_path(self, tmp_path: Path) -> None:
        """Test initialization with special characters in the file path."""
        epub_file = tmp_path / "test book (2023) - author's name.epub"
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", "<?xml version='1.0'?>")

        book = EPUBBook(epub_file)
        assert book.filepath == epub_file

    def test_init_with_unicode_in_path(self, tmp_path: Path) -> None:
        """Test initialization with unicode characters in the file path."""
        epub_file = tmp_path / "书名-作者.epub"
        with zipfile.ZipFile(epub_file, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", "<?xml version='1.0'?>")

        book = EPUBBook(epub_file)
        assert book.filepath == epub_file

    def test_init_with_zip_without_container_xml(self, tmp_path: Path) -> None:
        """Test initialization with a ZIP file missing META-INF/container.xml."""
        zip_file = tmp_path / "not_an_epub.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("some_file.txt", "random content")

        with pytest.raises(InvalidEPUBError) as exc_info:
            EPUBBook(zip_file)

        assert "container.xml" in str(exc_info.value).lower()
